#!/usr/bin/env python3
"""
CNC Tools - Production Setup (SERWER)
Przygotowuje serwer produkcyjny po skopiowaniu nowej wersji.

WAZNE: Przed skopiowaniem na serwer uruchom na LAPTOPIE:
       ./lap_prod.py

Użycie: ./setup_prod.py
"""
import os
import re
import subprocess
import sys

# Automatyczne wykrywanie i użycie virtualenv
def ensure_virtualenv():
    """Sprawdza czy działa w virtualenv, jeśli nie - re-wykonuje się z właściwym interpreterem"""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)
    venv_python = os.path.join(project_root, "env", "bin", "python3")

    if not os.path.isfile(venv_python):
        print(f"BLAD: Nie znaleziono virtualenv w {venv_python}")
        print(f"Utworz virtualenv: python3 -m venv {os.path.join(project_root, 'env')}")
        sys.exit(1)

    current_python = os.path.realpath(sys.executable)
    expected_python = os.path.realpath(venv_python)

    if current_python != expected_python:
        os.execv(venv_python, [venv_python] + sys.argv)

ensure_virtualenv()

# Kolory ANSI
GREEN = '\033[0;32m'
YELLOW = '\033[1;33m'
BLUE = '\033[0;34m'
RED = '\033[0;31m'
CYAN = '\033[0;36m'
NC = '\033[0m'

PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))


def get_version_from_settings():
    """Pobiera wersję z CNCTOOLS/settings.py"""
    settings_path = os.path.join(PROJECT_DIR, 'CNCTOOLS', 'settings.py')
    try:
        with open(settings_path, 'r', encoding='utf-8') as f:
            content = f.read()
        match = re.search(r"'WERSJA'\s*:\s*'([^']+)'", content)
        if match:
            return match.group(1)
    except Exception:
        pass
    return "nieznana"


def get_cache_name():
    """Pobiera CACHE_NAME z serviceworker.js"""
    sw_path = os.path.join(PROJECT_DIR, 'static_dev', 'serviceworker.js')
    try:
        with open(sw_path, 'r', encoding='utf-8') as f:
            content = f.read()
        match = re.search(r"const CACHE_NAME = '([^']+)';", content)
        if match:
            return match.group(1)
    except Exception:
        pass
    return "nieznany"


def run_command(cmd, description):
    """Uruchamia komendę i wyświetla status"""
    print(f"{BLUE}[*] {description}...{NC}")
    result = subprocess.run(cmd, shell=True, cwd=PROJECT_DIR)
    if result.returncode == 0:
        print(f"{GREEN}[OK] {description}{NC}\n")
        return True
    else:
        print(f"{RED}[BLAD] {description}{NC}\n")
        return False


def main():
    version = get_version_from_settings()
    cache_name = get_cache_name()

    print(f"{CYAN}")
    print("=" * 64)
    print("          CNC TOOLS - Production Setup (SERWER)")
    print("=" * 64)
    print(f"{NC}")
    print(f"{GREEN}Wersja aplikacji: {version}{NC}")
    print(f"{GREEN}Service Worker cache: {cache_name}{NC}")
    print()

    os.chdir(PROJECT_DIR)

    # 1. Sprawdź czy są zbudowane pliki
    dist_dir = os.path.join(PROJECT_DIR, "static_dev", "dist")
    manifest = os.path.join(dist_dir, ".vite", "manifest.json")

    if not os.path.isfile(manifest):
        print(f"{RED}[!] BLAD: Brak zbudowanych plikow w static_dev/dist/{NC}")
        print(f"{YELLOW}    Na LAPTOPIE uruchom: ./lap_prod.py{NC}")
        print(f"{YELLOW}    Nastepnie skopiuj katalog na serwer{NC}")
        sys.exit(1)

    print(f"{GREEN}[OK] Znaleziono zbudowane pliki (manifest.json){NC}\n")

    # 2. Sprawdź datę buildu
    manifest_mtime = os.path.getmtime(manifest)
    from datetime import datetime
    build_date = datetime.fromtimestamp(manifest_mtime).strftime('%Y-%m-%d %H:%M:%S')
    print(f"{BLUE}[i] Data buildu: {build_date}{NC}\n")

    # 3. Zainstaluj/zaktualizuj zależności Python
    run_command(
        f"{sys.executable} -m pip install -r requirements.txt --quiet",
        "Instalacja zaleznosci Python"
    )

    # 4. Usuń stary katalog staticfiles
    staticfiles_dir = os.path.join(PROJECT_DIR, "staticfiles")
    if os.path.isdir(staticfiles_dir):
        print(f"{BLUE}[*] Usuwanie starego katalogu staticfiles...{NC}")
        import shutil
        shutil.rmtree(staticfiles_dir)
        print(f"{GREEN}[OK] Usunieto stary katalog staticfiles{NC}\n")

    # 5. Zbierz pliki statyczne
    run_command(
        f"{sys.executable} manage.py collectstatic --noinput",
        "Zbieranie plikow statycznych (collectstatic)"
    )

    # 6. Migracje bazy danych
    run_command(
        f"{sys.executable} manage.py migrate --noinput",
        "Migracje bazy danych"
    )

    # 7. Podsumowanie
    print(f"{GREEN}")
    print("=" * 64)
    print("              SETUP ZAKONCZONY POMYSLNIE!")
    print("=" * 64)
    print(f"{NC}")
    print(f"{CYAN}Teraz zrestartuj Apache:{NC}")
    print()
    print(f"  {YELLOW}sudo systemctl restart apache2{NC}")
    print()
    print(f"{CYAN}Po restarcie sprawdz aplikacje w przegladarce.{NC}")
    print()
    print(f"{YELLOW}UWAGA: Jesli widzisz stara wersje interfejsu:{NC}")
    print(f"  1. Otworz DevTools (F12)")
    print(f"  2. Application -> Service Workers -> Unregister")
    print(f"  3. Ctrl+Shift+Delete -> Wyczysc cache przegladarki")
    print(f"  4. Odswiez strone (F5)")
    print()
    print(f"{GREEN}Wersja: {version} | Cache: {cache_name}{NC}")
    print()


if __name__ == "__main__":
    main()
