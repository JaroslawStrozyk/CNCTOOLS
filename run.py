#!/usr/bin/env python3
"""
CNC Tools - Development Server
Uruchamia Django + Vite dev server
Zatrzymanie: Ctrl+C
"""
import os
import signal
import subprocess
import sys
import time

# Automatyczne wykrywanie i użycie virtualenv
def ensure_virtualenv():
    """Sprawdza czy działa w virtualenv, jeśli nie - re-wykonuje się z właściwym interpreterem"""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    # Struktura: .../CNCTOOLS/run.py -> env jest w .../env/
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

# Kolory ANSI
GREEN = '\033[0;32m'
YELLOW = '\033[1;33m'
BLUE = '\033[0;34m'
NC = '\033[0m'

# Konfiguracja
PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
DJANGO_PORT = 1971

# Procesy
django_proc = None
vite_proc = None


def cleanup(signum=None, frame=None):
    """Zatrzymuje oba serwery"""
    print(f"\n{YELLOW}Zatrzymywanie serwerów...{NC}")

    for name, proc in [("Vite", vite_proc), ("Django", django_proc)]:
        if proc and proc.poll() is None:
            print(f"{BLUE}Zatrzymuję {name} (PID: {proc.pid})...{NC}")
            proc.terminate()
            try:
                proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                proc.kill()

    print(f"{GREEN}Serwery zatrzymane.{NC}")
    sys.exit(0)


def main():
    global django_proc, vite_proc

    # Obsługa sygnałów
    signal.signal(signal.SIGINT, cleanup)
    signal.signal(signal.SIGTERM, cleanup)

    os.chdir(PROJECT_DIR)

    # Banner
    print(f"{GREEN}")
    print("╔══════════════════════════════════════════════════════════════╗")
    print("║                    CNC TOOLS - Dev Server                    ║")
    print("║                                                              ║")
    print(f"║  Django:  http://0.0.0.0:{DJANGO_PORT}  (dostepny z kazdego IP)     ║")
    print("║  Vite:    http://0.0.0.0:5173 (HMR)                          ║")
    print("║                                                              ║")
    print("║  Uzyj: localhost, 127.0.0.1 lub IP maszyny w przegladarce    ║")
    print("║  Zatrzymanie: Ctrl+C                                         ║")
    print("╚══════════════════════════════════════════════════════════════╝")
    print(f"{NC}")

    # Sprawdź node_modules
    if not os.path.isdir("node_modules"):
        print(f"{YELLOW}Instaluję zależności npm...{NC}")
        subprocess.run(["npm", "install"], check=True)

    # Uruchom Vite
    print(f"{BLUE}Uruchamiam Vite dev server...{NC}")
    vite_proc = subprocess.Popen(["npm", "run", "dev"])

    time.sleep(2)

    # Uruchom Django
    print(f"{BLUE}Uruchamiam Django server...{NC}")
    django_proc = subprocess.Popen([
        sys.executable, "./manage.py", "runserver", f"0.0.0.0:{DJANGO_PORT}"
    ])

    print(f"\n{GREEN}Serwery uruchomione!{NC}")
    print(f"Django PID: {django_proc.pid}")
    print(f"Vite PID: {vite_proc.pid}")
    print(f"\n{YELLOW}Naciśnij Ctrl+C aby zatrzymać...{NC}\n")

    # Czekaj na procesy
    try:
        while True:
            # Sprawdź czy procesy żyją
            if django_proc.poll() is not None or vite_proc.poll() is not None:
                cleanup()
            time.sleep(1)
    except KeyboardInterrupt:
        cleanup()


if __name__ == "__main__":
    main()
