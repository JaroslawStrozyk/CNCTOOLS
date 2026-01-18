# Instrukcja wdrożenia CNC Tools na serwer produkcyjny

**Środowisko docelowe:** Debian 11 / Apache2 / SSL
**Adres serwera:** https://192.168.1.226

---

## Wymagania wstępne

### Na serwerze (jednorazowa konfiguracja):
- Debian 11 z Apache2 i mod_wsgi
- Python 3.9+ z virtualenv
- PostgreSQL (baza danych)
- Certyfikat SSL skonfigurowany w Apache2

### Na laptopie (środowisko deweloperskie):
- Node.js 18+ z npm
- Python 3.9+ z virtualenv

---

## Procedura wdrożenia

### Krok 1: Przygotowanie na LAPTOPIE

Po zakończeniu modyfikacji i testów (`./run.py`), wykonaj build produkcyjny:

```bash
cd /opt/PROJEKTY/CNC-Tools/CNCTOOLS
./lap_prod.py
```

Skrypt automatycznie:
- Aktualizuje `CACHE_NAME` w Service Worker (na podstawie wersji z `settings.py`)
- Wykonuje `npm run build`
- Generuje zoptymalizowane pliki JS/CSS w `static_dev/dist/`

**Oczekiwany wynik:**
```
================================================================
              BUILD ZAKONCZONY POMYSLNIE!
================================================================

Wersja: X.XX.Xg
Cache:  cnctools-X.XX.Xg
```

---

### Krok 2: Kopiowanie na serwer

Skopiuj cały katalog CNCTOOLS na serwer:

```bash
scp -r /opt/PROJEKTY/CNC-Tools/CNCTOOLS user@192.168.1.226:/tmp/
```

Lub przez rsync (szybsze przy aktualizacjach):

```bash
rsync -avz --exclude='node_modules' --exclude='__pycache__' \
    /opt/PROJEKTY/CNC-Tools/CNCTOOLS/ \
    user@192.168.1.226:/tmp/CNCTOOLS/
```

---

### Krok 3: Podmiana projektu na SERWERZE

Zaloguj się na serwer:

```bash
ssh user@192.168.1.226
```

Podmień stary katalog na nowy:

```bash
# Usuń starą wersję (zachowaj backup jeśli potrzebny)
sudo rm -rf /sciezka/do/CNCTOOLS

# Skopiuj nową wersję
sudo cp -r /tmp/CNCTOOLS /sciezka/do/

# Ustaw właściciela (dopasuj do konfiguracji Apache)
sudo chown -R www-data:www-data /sciezka/do/CNCTOOLS
```

---

### Krok 4: Setup produkcyjny na SERWERZE

```bash
cd /sciezka/do/CNCTOOLS
./setup_prod.py
```

Skrypt automatycznie:
- Sprawdza obecność zbudowanych plików
- Instaluje zależności Python (`pip install -r requirements.txt`)
- Usuwa stary katalog `staticfiles/`
- Zbiera pliki statyczne (`collectstatic`)
- Wykonuje migracje bazy danych (`migrate`)

**Oczekiwany wynik:**
```
================================================================
              SETUP ZAKONCZONY POMYSLNIE!
================================================================

Wersja: X.XX.Xg | Cache: cnctools-X.XX.Xg
```

---

### Krok 5: Restart Apache

```bash
sudo systemctl restart apache2
```

Sprawdź status:

```bash
sudo systemctl status apache2
```

---

### Krok 6: Weryfikacja w przeglądarce

Otwórz w przeglądarce:

```
https://192.168.1.226
```

**Sprawdź:**
- Wersja w "O programie" zgadza się z wdrożoną
- Interfejs wygląda poprawnie (nowe zmiany są widoczne)
- Logowanie działa
- Funkcjonalności działają prawidłowo

---

## Rozwiązywanie problemów

### Problem: Stary interfejs mimo aktualizacji

**Przyczyna:** Przeglądarka używa starego cache Service Worker.

**Rozwiązanie:**
1. Otwórz DevTools (F12)
2. Przejdź do: `Application` → `Service Workers`
3. Kliknij `Unregister` przy aktywnym SW
4. Wyczyść cache: `Ctrl+Shift+Delete` → zaznacz "Cached images and files"
5. Odśwież stronę: `F5` lub `Ctrl+R`

### Problem: Błąd 500 / Internal Server Error

**Sprawdź logi Apache:**
```bash
sudo tail -50 /var/log/apache2/error.log
```

**Sprawdź logi Django:**
```bash
cd /sciezka/do/CNCTOOLS
./run_prod.py
# Sprawdź output w terminalu
```

### Problem: Brak plików statycznych (404)

**Sprawdź czy collectstatic się wykonał:**
```bash
ls -la /sciezka/do/CNCTOOLS/staticfiles/
```

**Wykonaj ponownie:**
```bash
cd /sciezka/do/CNCTOOLS
python manage.py collectstatic --noinput
```

### Problem: Błąd "Brak zbudowanych plików"

**Przyczyna:** Nie wykonano `./lap_prod.py` na laptopie przed kopiowaniem.

**Rozwiązanie:** Wróć do Kroku 1 i wykonaj build na laptopie.

---

## Szybka ściągawka

```bash
# === LAPTOP ===
cd /opt/PROJEKTY/CNC-Tools/CNCTOOLS
./lap_prod.py
scp -r /opt/PROJEKTY/CNC-Tools/CNCTOOLS user@192.168.1.226:/tmp/

# === SERWER ===
ssh user@192.168.1.226
sudo rm -rf /sciezka/do/CNCTOOLS
sudo cp -r /tmp/CNCTOOLS /sciezka/do/
sudo chown -R www-data:www-data /sciezka/do/CNCTOOLS
cd /sciezka/do/CNCTOOLS
./setup_prod.py
sudo systemctl restart apache2

# === PRZEGLĄDARKA ===
# https://192.168.1.226
```

---

## Struktura plików produkcyjnych

```
CNCTOOLS/
├── lap_prod.py          # Skrypt buildu (LAPTOP)
├── setup_prod.py        # Skrypt setup (SERWER)
├── run_prod.py          # Serwer testowy (SERWER)
├── static_dev/
│   ├── dist/            # Zbudowane pliki Vite
│   │   ├── main-*.js    # Aplikacja JS (zhashowana nazwa)
│   │   ├── main-*.css   # Style CSS (zhashowana nazwa)
│   │   └── .vite/
│   │       └── manifest.json
│   └── serviceworker.js # Service Worker z CACHE_NAME
├── staticfiles/         # Zebrane pliki (po collectstatic)
└── CNCTOOLS/
    └── settings.py      # Konfiguracja z wersją
```

---

**Autor:** Jarosław Stróżyk / EDATABIT
**Ostatnia aktualizacja:** 2026-01-14
