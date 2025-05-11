import sqlite3
import string
import random
from flask import Flask, render_template, request, redirect, g, url_for
import click
from flask.cli import with_appcontext
import validators
from flask_socketio import SocketIO, emit
import os
from dotenv import load_dotenv

# Wczytaj zmienne środowiskowe z pliku .env (jeśli istnieje)
# Powinno to być na samym początku skryptu.
load_dotenv()

app = Flask(__name__)

# --- Konfiguracja SECRET_KEY ---
# Wczytaj SECRET_KEY ze zmiennej środowiskowej (ustawionej przez .env lub bezpośrednio w systemie)
CONFIG_SECRET_KEY = os.environ.get('SECRET_KEY')

if not CONFIG_SECRET_KEY:
    # Jeśli klucz nie został znaleziony, logujemy krytyczny błąd i przerywamy działanie.
    app.logger.critical("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
    app.logger.critical("!!! KRYTYCZNY BŁĄD: Zmienna środowiskowa SECRET_KEY nie jest ustawiona!")
    app.logger.critical("!!! Upewnij się, że plik .env istnieje w głównym katalogu projektu")
    app.logger.critical("!!! i zawiera poprawny wpis, np.: SECRET_KEY='twoj_dlugi_losowy_klucz'")
    app.logger.critical("!!! Aplikacja nie może bezpiecznie działać bez tego klucza.")
    app.logger.critical("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
    raise ValueError("Krytyczny błąd konfiguracji: Brak SECRET_KEY. Sprawdź plik .env lub zmienne środowiskowe.")
else:
    app.config['SECRET_KEY'] = CONFIG_SECRET_KEY
    if app.debug: # Logowanie tylko w trybie debug
        app.logger.info(f"SECRET_KEY wczytany pomyślnie (długość: {len(CONFIG_SECRET_KEY)}).")


DATABASE = 'links.db' # Nazwa pliku bazy danych

# Inicjalizacja SocketIO
# async_mode='eventlet' jest jednym z zalecanych trybów, upewnij się, że eventlet jest zainstalowany
socketio = SocketIO(app, async_mode='eventlet', logger=True, engineio_logger=True) # Dodano logger i engineio_logger dla SocketIO

# --- Konfiguracja Bazy Danych ---
def get_db():
    # Pobiera połączenie z bazą danych z kontekstu aplikacji 'g' lub tworzy nowe.
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
        db.row_factory = sqlite3.Row # Umożliwia dostęp do kolumn po nazwie
    return db

@app.teardown_appcontext
def close_connection(exception):
    # Zamyka połączenie z bazą danych po zakończeniu obsługi żądania.
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

def init_db():
    # Inicjalizuje bazę danych, tworząc tabele zdefiniowane w schema.sql.
    with app.app_context():
        db = get_db()
        with app.open_resource('schema.sql', mode='r') as f:
            db.cursor().executescript(f.read())
        db.commit()

# --- Funkcja do generowania krótkiego kodu ---
def generate_short_code(length=6):
    # Generuje losowy, krótki kod alfanumeryczny.
    characters = string.ascii_letters + string.digits
    short_code = ''.join(random.choice(characters) for _ in range(length))
    return short_code

# --- Routing ---
@app.route('/', methods=['GET', 'POST'])
def index():
    # Główna strona aplikacji, obsługuje wyświetlanie formularza i skracanie linków.
    template_vars = {} # Słownik do przekazywania zmiennych do szablonu
    if request.method == 'POST':
        original_url_input = request.form.get('original_url') # Pobranie URL z formularza
        template_vars['original_url_input'] = original_url_input # Zachowanie inputu użytkownika

        if not original_url_input:
            template_vars['error'] = "Proszę podać URL."
            return render_template('index.html', **template_vars)

        # Dodanie protokołu http, jeśli go brakuje
        if not (original_url_input.startswith('http://') or original_url_input.startswith('https://')):
            original_url_with_protocol = 'http://' + original_url_input
        else:
            original_url_with_protocol = original_url_input

        # Walidacja URL
        if not validators.url(original_url_with_protocol):
            template_vars['error'] = "Podany URL jest nieprawidłowy."
            return render_template('index.html', **template_vars)

        # Zapobieganie skracaniu linków z domeny samego skracacza
        if original_url_with_protocol.startswith(request.host_url):
            template_vars['error'] = "Nie można skracać linków z tej samej domeny."
            return render_template('index.html', **template_vars)

        db = get_db()
        cursor = db.cursor()
        # Sprawdzenie, czy URL już istnieje w bazie
        cursor.execute("SELECT short_code, clicks FROM links WHERE original_url = ?", (original_url_with_protocol,))
        existing_link = cursor.fetchone()

        actual_short_code = "" # Przechowa sam krótki kod, np. "aB1Cd2"
        clicks = 0

        if existing_link:
            actual_short_code = existing_link['short_code']
            clicks = existing_link['clicks']
        else:
            # Generowanie unikalnego krótkiego kodu
            while True:
                actual_short_code = generate_short_code()
                cursor.execute("SELECT short_code FROM links WHERE short_code = ?", (actual_short_code,))
                if cursor.fetchone() is None: # Jeśli kod nie istnieje w bazie
                    break # Kod jest unikalny
            
            clicks = 0 # Nowy link, więc 0 kliknięć
            # Zapis nowego linku do bazy
            cursor.execute("INSERT INTO links (original_url, short_code, clicks) VALUES (?, ?, ?)",
                           (original_url_with_protocol, actual_short_code, clicks))
            db.commit()

        # Przygotowanie zmiennych do wyświetlenia w szablonie
        template_vars['short_url'] = request.host_url + actual_short_code # Pełny skrócony URL
        template_vars['original_url_display'] = original_url_with_protocol # Oryginalny URL z protokołem
        template_vars['clicks'] = clicks # Liczba kliknięć
        template_vars['short_code_for_js'] = actual_short_code # Sam krótki kod dla JavaScriptu

    return render_template('index.html', **template_vars)

@app.route('/<short_code>')
def redirect_to_url(short_code):
    # Obsługuje przekierowanie ze skróconego kodu na oryginalny URL i zlicza kliknięcia.
    db = get_db()
    cursor = db.cursor()
    # Pobranie oryginalnego URL i liczby kliknięć na podstawie krótkiego kodu
    cursor.execute("SELECT original_url, clicks FROM links WHERE short_code = ?", (short_code,))
    link_record = cursor.fetchone()

    if link_record:
        try:
            new_clicks = link_record['clicks'] + 1
            # Aktualizacja licznika kliknięć w bazie
            cursor.execute("UPDATE links SET clicks = ? WHERE short_code = ?", (new_clicks, short_code))
            db.commit() # Zapisanie zmian w bazie
            
            # Logowanie przed emisją zdarzenia WebSocket
            app.logger.critical(f"DEBUG SERVER: Próba emisji 'click_update' dla {short_code} z {new_clicks} kliknięciami.")
            # Emisja zdarzenia WebSocket do wszystkich podłączonych klientów
            socketio.emit('click_update', {'short_code': short_code, 'clicks': new_clicks})
            # Dodatkowy log informacyjny
            app.logger.info(f"SocketIO emit: 'click_update' dla {short_code} - nowa liczba kliknięć: {new_clicks}")

        except sqlite3.Error as e:
            app.logger.error(f"Błąd bazy danych podczas aktualizacji licznika kliknięć dla {short_code}: {e}")
        except Exception as e:
            app.logger.error(f"Nieoczekiwany błąd podczas obsługi przekierowania dla {short_code}: {e}")
        
        # Przekierowanie na oryginalny URL
        return redirect(link_record['original_url'])
    else:
        # Jeśli krótki kod nie istnieje, wyświetl stronę błędu 404
        return render_template('404.html'), 404

# --- Komendy CLI ---
@click.command('init-db')
@with_appcontext
def init_db_command():
    """Czyści istniejące dane i tworzy nowe tabele (zgodnie ze schema.sql)."""
    init_db()
    click.echo('Zainicjowano bazę danych.')

app.cli.add_command(init_db_command) # Rejestracja komendy w aplikacji Flask

# --- Obsługa zdarzeń SocketIO ---
@socketio.on('connect')
def handle_connect():
    # Handler zdarzenia, gdy klient nawiązuje połączenie WebSocket.
    app.logger.critical('DEBUG SERVER: KLIENT POŁĄCZONY PRZEZ WEBSOCKET (SID: %s)', request.sid)


@socketio.on('disconnect')
def handle_disconnect():
    # Handler zdarzenia, gdy klient rozłącza się z WebSocket.
    app.logger.critical('DEBUG SERVER: KLIENT ROZŁĄCZONY Z WEBSOCKET (SID: %s)', request.sid)

# Główny punkt uruchomienia aplikacji
if __name__ == '__main__':
    # Uruchomienie aplikacji za pomocą serwera SocketIO (eventlet).
    app.logger.info("Uruchamianie serwera Flask-SocketIO...")
    socketio.run(app, host='0.0.0.0', port=5000, debug=True, use_reloader=True)
