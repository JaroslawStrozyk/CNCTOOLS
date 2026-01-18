#!/usr/bin/env python3
"""
CNC Tools - Laptop Production Build
Przygotowuje projekt do wdrozenia na serwer produkcyjny.

Uruchom PRZED skopiowaniem na serwer!

Użycie: ./lap_prod.py
"""
import os
import re
import subprocess
import sys

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

    with open(settings_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Szukaj 'WERSJA': 'X.Y.Z'
    match = re.search(r"'WERSJA'\s*:\s*'([^']+)'", content)
    if match:
        return match.group(1)
    return None


def update_serviceworker_cache(version):
    """Aktualizuje CACHE_NAME w serviceworker.js"""
    sw_path = os.path.join(PROJECT_DIR, 'static_dev', 'serviceworker.js')

    if not os.path.isfile(sw_path):
        print(f"{YELLOW}[!] Brak pliku serviceworker.js - pomijam{NC}")
        return False

    with open(sw_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Zamień CACHE_NAME na nową wersję
    new_content = re.sub(
        r"const CACHE_NAME = 'cnctools-[^']*';",
        f"const CACHE_NAME = 'cnctools-{version}';",
        content
    )

    if new_content != content:
        with open(sw_path, 'w', encoding='utf-8') as f:
            f.write(new_content)
        return True
    return False


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


def check_npm():
    """Sprawdza czy npm jest dostępny"""
    result = subprocess.run(['npm', '--version'], capture_output=True)
    return result.returncode == 0


def main():
    print(f"{CYAN}")
    print("=" * 64)
    print("         CNC TOOLS - Laptop Production Build")
    print("=" * 64)
    print(f"{NC}")

    os.chdir(PROJECT_DIR)

    # 1. Sprawdź npm
    if not check_npm():
        print(f"{RED}[!] BLAD: npm nie jest zainstalowany!{NC}")
        print(f"{YELLOW}    Zainstaluj Node.js: https://nodejs.org/{NC}")
        sys.exit(1)

    # 2. Pobierz wersję
    version = get_version_from_settings()
    if not version:
        print(f"{RED}[!] BLAD: Nie mozna odczytac wersji z settings.py{NC}")
        sys.exit(1)

    print(f"{GREEN}[i] Wersja aplikacji: {version}{NC}\n")

    # 3. Aktualizuj CACHE_NAME w Service Worker
    print(f"{BLUE}[*] Aktualizacja Service Worker cache...{NC}")
    if update_serviceworker_cache(version):
        print(f"{GREEN}[OK] CACHE_NAME zaktualizowany do: cnctools-{version}{NC}\n")
    else:
        print(f"{YELLOW}[i] CACHE_NAME juz aktualny{NC}\n")

    # 4. Sprawdź node_modules
    node_modules = os.path.join(PROJECT_DIR, 'node_modules')
    if not os.path.isdir(node_modules):
        print(f"{YELLOW}[!] Brak node_modules - instaluje zaleznosci...{NC}")
        if not run_command('npm install', 'Instalacja zaleznosci npm'):
            sys.exit(1)

    # 5. Build Vite
    if not run_command('npm run build', 'Budowanie frontendu (Vite)'):
        print(f"{RED}[!] Build nie powiodl sie!{NC}")
        sys.exit(1)

    # 6. Sprawdź wynik
    manifest = os.path.join(PROJECT_DIR, 'static_dev', 'dist', '.vite', 'manifest.json')
    if not os.path.isfile(manifest):
        print(f"{RED}[!] BLAD: Brak manifest.json po buildzie!{NC}")
        sys.exit(1)

    # 7. Podsumowanie
    print(f"{GREEN}")
    print("=" * 64)
    print("              BUILD ZAKONCZONY POMYSLNIE!")
    print("=" * 64)
    print(f"{NC}")
    print(f"{CYAN}Teraz skopiuj katalog CNCTOOLS na serwer:{NC}")
    print()
    print(f"  {YELLOW}scp -r /opt/PROJEKTY/CNC-Tools/CNCTOOLS user@serwer:/tmp/{NC}")
    print()
    print(f"{CYAN}Na serwerze wykonaj:{NC}")
    print()
    print(f"  {YELLOW}cd /sciezka/do/CNCTOOLS{NC}")
    print(f"  {YELLOW}./setup_prod.py{NC}")
    print(f"  {YELLOW}sudo systemctl restart apache2{NC}")
    print()
    print(f"{GREEN}Wersja: {version}{NC}")
    print(f"{GREEN}Cache:  cnctools-{version}{NC}")
    print()


if __name__ == "__main__":
    main()
