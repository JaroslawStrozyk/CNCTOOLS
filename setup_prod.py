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

# Stara instalacja (stan przejściowy, ARCHITEKTURA „Serwer”) — tylko ODCZYT: źródło plików serwera
# i wersji Pythona przy pierwszym wdrożeniu w /opt/CNC/CNCTOOLS. Nic w niej nie zmieniamy.
STARA_INSTALACJA = '/opt/CNCTOOLS'


def _python_bazowy():
    """Interpreter dla nowego env: ta sama wersja co stary env Tools (mod_wsgi = jedna wersja Pythona)."""
    cfg = os.path.join(STARA_INSTALACJA, 'env', 'pyvenv.cfg')
    try:
        with open(cfg, encoding='utf-8') as f:
            pola = {k.strip(): v.strip() for k, v in (l.split('=', 1) for l in f.read().splitlines() if '=' in l)}
        wersja = '.'.join(pola.get('version', pola.get('version_info', '')).split('.')[:2])
        kandydat = os.path.join(pola.get('home', ''), f'python{wersja}')
        if wersja and os.path.isfile(kandydat):
            return kandydat
    except OSError:
        pass
    return sys.executable


def _ma_pip(py):
    return subprocess.run([py, '-m', 'pip', '--version'], capture_output=True).returncode == 0


def _utworz_env(interpreter, venv_dir, venv_python):
    import shutil
    if subprocess.run([interpreter, '-m', 'venv', venv_dir]).returncode == 0 and _ma_pip(venv_python):
        return True
    shutil.rmtree(venv_dir, ignore_errors=True)  # niepełny env (bez pip) nie może udawać gotowego
    return False


# Automatyczne wykrywanie i użycie virtualenv
def ensure_virtualenv():
    """Re-exec w ../env. Brak env albo env bez pip → tworzy na miejscu (venv ma ścieżki bezwzględne);
    brak pakietu pythonX.Y-venv a uruchomione jako root → apt-get install i ponowna próba."""
    import shutil
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)
    venv_dir = os.path.join(project_root, "env")
    venv_python = os.path.join(venv_dir, "bin", "python3")

    if os.path.isfile(venv_python) and not _ma_pip(venv_python):
        print(f"Virtualenv {venv_dir} bez pip (niepełny) - tworzę od nowa ...")
        shutil.rmtree(venv_dir, ignore_errors=True)
    if not os.path.isfile(venv_python):
        interpreter = _python_bazowy()
        pakiet = f"{os.path.basename(interpreter)}-venv" if os.path.basename(interpreter).startswith('python3.') \
            else 'python3-venv'
        print(f"Brak virtualenv - tworzę {venv_dir} z {interpreter} ...")
        if not _utworz_env(interpreter, venv_dir, venv_python):
            if os.geteuid() == 0:
                print(f"Instaluję pakiet systemowy {pakiet} (apt-get update && apt-get install -y {pakiet}) ...")
                subprocess.run(['apt-get', 'update'])
                subprocess.run(['apt-get', 'install', '-y', pakiet])
            if not _utworz_env(interpreter, venv_dir, venv_python):
                print(f"BLAD: Nie udało się utworzyć virtualenv z pip w {venv_dir}")
                print(f"Pakiet systemowy: apt-get update && apt install {pakiet} — potem ponownie ./setup_prod.py")
                sys.exit(1)
        print("Virtualenv utworzony - zależności zainstaluje krok pip install.")

    # Porównujemy sys.prefix, nie realpath interpretera - python w venv to dowiązanie
    # do systemowego, więc realpath byłby identyczny i re-exec nigdy by nie nastąpił.
    if os.path.realpath(sys.prefix) != os.path.realpath(venv_dir):
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
# Paczka cnc_wspolne na serwerze (ARCHITEKTURA „Serwer”); nadpisanie: zmienna CNC_WSPOLNE_DIR
CNC_WSPOLNE_DIR = os.environ.get('CNC_WSPOLNE_DIR', '/opt/CNC/CNCWSPOLNE/CNCWSPOLNE')


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


# Pliki serwera. Transfer z laptopa niesie komplet (także laptopowe pass_file.py, app_settings.json, media/, logs/).
# Pierwsze wdrożenie w nowym katalogu (brak znacznika ../.pliki_serwera): wersje laptopowe → *.laptop,
# na ich miejsce kopie ze starej instalacji (tylko odczyt). Kolejne wydania: znacznik jest — nic nie podmieniamy.
PLIKI_SERWERA = ['CNCTOOLS/pass_file.py', 'app_settings.json', 'media', 'logs', 'install/cnctools.crt']
ZNACZNIK = os.path.join(os.path.dirname(PROJECT_DIR), '.pliki_serwera')


def pliki_serwera():
    stary = os.path.join(STARA_INSTALACJA, 'CNCTOOLS')
    pierwsze = not os.path.exists(ZNACZNIK) and os.path.isdir(stary) \
        and os.path.realpath(stary) != os.path.realpath(PROJECT_DIR)
    if pierwsze:
        print(f"{BLUE}[*] Pierwsze wdrożenie w {os.path.dirname(PROJECT_DIR)}: pliki serwera z {stary}{NC}")
        for wzgl in PLIKI_SERWERA:
            zrodlo, cel = os.path.join(stary, wzgl), os.path.join(PROJECT_DIR, wzgl)
            if not os.path.exists(zrodlo):
                print(f"{YELLOW}[i] {wzgl}: brak w starej instalacji — zostaje wersja z transferu{NC}")
                continue
            if os.path.lexists(cel):
                odlozony = cel + '.laptop'
                subprocess.run(['rm', '-rf', odlozony])
                os.rename(cel, odlozony)
            os.makedirs(os.path.dirname(cel), exist_ok=True)
            # cp -a: właściciel i prawa jak w starej instalacji (Apache pisze do media/, logs/)
            if subprocess.run(['cp', '-a', zrodlo, cel]).returncode != 0:
                print(f"{RED}[!] BLAD: kopia {zrodlo} → {cel}{NC}")
                sys.exit(1)
            print(f"{GREEN}[OK] {wzgl} ← {zrodlo} (laptopowa: {wzgl}.laptop){NC}")
        with open(ZNACZNIK, 'w', encoding='utf-8') as f:
            f.write(f'Pliki serwera skopiowane z {stary} przez setup_prod.py; wersje z laptopa: *.laptop\n')
        print()
    if not os.path.isfile(os.path.join(PROJECT_DIR, 'CNCTOOLS', 'pass_file.py')):
        print(f"{RED}[!] BLAD: brak CNCTOOLS/pass_file.py{NC}")
        sys.exit(1)


def apache_wskazuje():
    """Czy vhost Apache serwuje Tools z tego katalogu (informacja na koniec — konfiguracji nie zmieniamy)."""
    try:
        with open('/etc/apache2/sites-available/000-default.conf', encoding='utf-8') as f:
            return os.path.dirname(PROJECT_DIR) + '/' in f.read()
    except OSError:
        return None


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

    # 0. Pliki serwera (pass_file.py, app_settings.json, media/, logs/, certyfikat)
    pliki_serwera()

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

    # 3b. Paczka wspólna systemu CNC (token Portalu) — CNC-Wspolne/KONTRAKTY.md
    if os.path.isfile(os.path.join(CNC_WSPOLNE_DIR, "pyproject.toml")):
        if not run_command(
            f"{sys.executable} -m pip install --quiet --upgrade {CNC_WSPOLNE_DIR}",
            f"Instalacja cnc_wspolne z {CNC_WSPOLNE_DIR}"
        ):
            sys.exit(1)
    else:
        print(f"{RED}[!] BLAD: Brak paczki cnc_wspolne w {CNC_WSPOLNE_DIR}{NC}")
        print(f"{YELLOW}    Skopiuj zawartosc CNC-Wspolne/cnc_wspolne (pyproject + pakiet) do tego katalogu{NC}")
        sys.exit(1)

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

    # 7. Naprawa danych: dokonczenie zaleglych zwrotow "Zuzyte" (uszkodzone_regeneracja)
    #    sprzed naprawy generatora numeru karty. Tworzy brakujace karty regeneracji
    #    i usuwa egzemplarze-duchy. IDEMPOTENTNE - bez duchow nic nie robi (Naprawiono: 0).
    run_command(
        f"{sys.executable} manage.py napraw_zwroty_regeneracja --apply",
        "Naprawa zaleglych zwrotow 'Zuzyte' (duchy egzemplarzy)"
    )

    # 7b. Naprawa danych: przeliczenie wartosci pozycji/zamowien z mnoznikiem kompletu.
    #     Cena jednostkowa dotyczy pojedynczej sztuki - dla kompletow wartosc byla zanizona
    #     (brak mnozenia przez ilosc sztuk w komplecie). IDEMPOTENTNE.
    run_command(
        f"{sys.executable} manage.py przelicz_wartosci_zamowien --apply",
        "Przeliczenie wartosci zamowien (mnoznik kompletu)"
    )

    # 7c. PODGLAD (dry-run) osieroconych pozycji zapotrzebowan technologow: pozycje
    #     oznaczone "w zamowieniu", ktorych zamowienie usunieto przed 1.18.0g. NIC nie zmienia.
    #     Naprawa RECZNIE po przejrzeniu listy z logistyka (pozycje wroca do generatora):
    #       python manage.py napraw_zapotrzebowania_osierocone --apply
    run_command(
        f"{sys.executable} manage.py napraw_zapotrzebowania_osierocone",
        "Podglad osieroconych pozycji zapotrzebowan (bez zmian)"
    )

    # 8. Podsumowanie
    print(f"{GREEN}")
    print("=" * 64)
    print("              SETUP ZAKONCZONY POMYSLNIE!")
    print("=" * 64)
    print(f"{NC}")
    print(f"{YELLOW}Osierocone pozycje zapotrzebowan (krok 7c) - jesli lista nie jest pusta,{NC}")
    print(f"{YELLOW}po uzgodnieniu z logistyka: python manage.py napraw_zapotrzebowania_osierocone --apply{NC}")
    print()
    if apache_wskazuje() is False:
        stary, nowy = STARA_INSTALACJA + '/', os.path.dirname(PROJECT_DIR) + '/'
        print(f"{CYAN}Apache serwuje jeszcze Tools ze starej ścieżki — przepięcie na {nowy} (rollback: kopia pliku):{NC}")
        print()
        print(f"  {YELLOW}cp -a /etc/apache2/sites-available/000-default.conf /root/000-default.conf.$(date +%Y%m%d_%H%M){NC}")
        print(f"  {YELLOW}sed -i 's#{stary}#{nowy}#g' /etc/apache2/sites-available/000-default.conf{NC}")
        print(f"  {YELLOW}apache2ctl configtest && systemctl restart apache2{NC}")
    else:
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
