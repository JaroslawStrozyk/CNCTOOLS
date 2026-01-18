#!/usr/bin/env python3
"""
CNC Tools - Production Server
Uruchamia tylko Django (bez Vite HMR)
Zatrzymanie: Ctrl+C
"""
import os
import signal
import subprocess
import sys

# Automatyczne wykrywanie i użycie virtualenv
def ensure_virtualenv():
    """Sprawdza czy działa w virtualenv, jeśli nie - re-wykonuje się z właściwym interpreterem"""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    # Struktura: .../CNCTOOLS/run_prod.py -> env jest w .../env/
    project_root = os.path.dirname(script_dir)
    venv_python = os.path.join(project_root, "env", "bin", "python3")

    # Sprawdź czy env istnieje
    if not os.path.isfile(venv_python):
        print(f"BŁĄD: Nie znaleziono virtualenv w {venv_python}")
        print(f"Utwórz virtualenv: python3 -m venv {os.path.join(project_root, 'env')}")
        sys.exit(1)

    # Sprawdź czy już działamy w tym env
    current_python = os.path.realpath(sys.executable)
    expected_python = os.path.realpath(venv_python)

    if current_python != expected_python:
        # Re-wykonaj skrypt z właściwym interpreterem
        os.execv(venv_python, [venv_python] + sys.argv)

ensure_virtualenv()

# Tryb produkcyjny - wyłącz DEBUG
os.environ['DJANGO_DEBUG'] = '0'

# Kolory ANSI
GREEN = '\033[0;32m'
YELLOW = '\033[1;33m'
BLUE = '\033[0;34m'
NC = '\033[0m'

# Konfiguracja
PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
DJANGO_PORT = 1971

# Proces
django_proc = None


def cleanup(signum=None, frame=None):
    """Zatrzymuje serwer"""
    print(f"\n{YELLOW}Zatrzymywanie serwera...{NC}")

    if django_proc and django_proc.poll() is None:
        print(f"{BLUE}Zatrzymuję Django (PID: {django_proc.pid})...{NC}")
        django_proc.terminate()
        try:
            django_proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            django_proc.kill()

    print(f"{GREEN}Serwer zatrzymany.{NC}")
    sys.exit(0)


def main():
    global django_proc

    # Obsługa sygnałów
    signal.signal(signal.SIGINT, cleanup)
    signal.signal(signal.SIGTERM, cleanup)

    os.chdir(PROJECT_DIR)

    # Banner
    print(f"{GREEN}")
    print("╔══════════════════════════════════════════════════════════════╗")
    print("║               CNC TOOLS - Production Server                  ║")
    print("║                                                              ║")
    print(f"║  Django:  http://0.0.0.0:{DJANGO_PORT}  (dostepny z kazdego IP)     ║")
    print("║                                                              ║")
    print("║  Zatrzymanie: Ctrl+C                                         ║")
    print("╚══════════════════════════════════════════════════════════════╝")
    print(f"{NC}")

    # Sprawdź czy są zbudowane pliki statyczne
    static_dir = os.path.join(PROJECT_DIR, "static_dev")
    if not os.path.isdir(static_dir) or not os.listdir(static_dir):
        print(f"{YELLOW}UWAGA: Brak zbudowanych plików w static_dev/{NC}")
        print(f"{YELLOW}Zbuduj je na maszynie deweloperskiej: npm run build{NC}")

    # Uruchom Django
    print(f"{BLUE}Uruchamiam Django server...{NC}")
    django_proc = subprocess.Popen([
        sys.executable, "./manage.py", "runserver", f"0.0.0.0:{DJANGO_PORT}"
    ])

    print(f"\n{GREEN}Serwer uruchomiony!{NC}")
    print(f"Django PID: {django_proc.pid}")
    print(f"\n{YELLOW}Naciśnij Ctrl+C aby zatrzymać...{NC}\n")

    # Czekaj na proces
    try:
        django_proc.wait()
    except KeyboardInterrupt:
        cleanup()


if __name__ == "__main__":
    main()
