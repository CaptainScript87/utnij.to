# Utnij.to - Skracacz Linków

Prosty skracacz linków napisany w Pythonie przy użyciu frameworka Flask, z aktualizacjami liczby kliknięć w czasie rzeczywistym dzięki WebSockets (Flask-SocketIO).

## Główne Funkcje

* Skracanie długich adresów URL.
* Generowanie unikalnych, krótkich aliasów.
* Przekierowywanie z krótkich aliasów na oryginalne adresy URL.
* Zliczanie liczby kliknięć dla każdego skróconego linku.
* Aktualizacja licznika kliknięć na stronie w czasie rzeczywistym (przy użyciu WebSockets).
* Walidacja wprowadzanych adresów URL.
* Zapobieganie skracaniu linków z domeny samego skracacza.
* Bezpieczne przechowywanie klucza `SECRET_KEY` przy użyciu plików `.env`.

## Technologie

* **Backend:** Python, Flask, Flask-SocketIO
* **Serwer WebSocket:** python-eventlet
* **Baza danych:** SQLite
* **Frontend:** HTML, CSS, JavaScript (dla obsługi WebSockets)
* **Zarządzanie zależnościami:** Pip, venv
* **Zmienne środowiskowe:** python-dotenv
* **Walidacja:** validators

## Lokalna Konfiguracja i Uruchomienie

Aby uruchomić projekt lokalnie, postępuj zgodnie z poniższymi krokami:

1.  **Wymagania wstępne:**
    * Python 3.8+
    * Pip (manager pakietów Pythona)
    * Git

2.  **Sklonuj repozytorium (jeśli pobierasz z GitHuba):**
    ```bash
    git clone [https://github.com/CaptainScript87/utnij.to.git](https://github.com/CaptainScript87/utnij.to.git)
    cd utnij.to
    ```

3.  **Utwórz i aktywuj środowisko wirtualne:**
    ```bash
    python -m venv venv
    # Windows
    .\venv\Scripts\activate
    # macOS/Linux
    # source venv/bin/activate
    ```

4.  **Zainstaluj zależności:**
    Upewnij się, że masz plik `requirements.txt` w głównym folderze projektu.
    ```bash
    pip install -r requirements.txt
    ```

5.  **Skonfiguruj zmienne środowiskowe:**
    * Utwórz plik `.env` w głównym folderze projektu.
    * Dodaj do niego swój `SECRET_KEY`:
        ```env
        SECRET_KEY="twoj_bardzo_dlugi_i_tajny_klucz_tutaj"
        ```
        (Zastąp powyższy klucz swoim własnym, wygenerowanym np. przez `import os; os.urandom(24).hex()`).

6.  **Zainicjuj bazę danych:**
    (Upewnij się, że jesteś w głównym folderze projektu z aktywnym środowiskiem wirtualnym)
    ```bash
    flask init-db
    ```

7.  **Uruchom aplikację:**
    ```bash
    python app.py
    ```
    Aplikacja powinna być dostępna pod adresem `http://localhost:5000` lub `http://127.0.0.1:5000`.

## Użycie

1.  Otwórz aplikację w przeglądarce pod adresem `http://localhost:5000`.
2.  Wklej długi adres URL w pole formularza.
3.  Kliknij przycisk "Skróć".
4.  Wygenerowany krótki link oraz oryginalny URL zostaną wyświetlone poniżej.
5.  Licznik kliknięć dla nowo utworzonego linku będzie wynosił 0. Po kliknięciu w skrócony link, licznik powinien zaktualizować się w czasie rzeczywistym na stronie (jeśli WebSockets działają poprawnie).

## Status Projektu

Obecnie trwa debugowanie funkcjonalności WebSockets w celu zapewnienia aktualizacji licznika kliknięć w czasie rzeczywistym.

---

*Projekt stworzony w ramach nauki i eksploracji technologii webowych.*
*Data ostatniej aktualizacji README: 11 maja 2025*