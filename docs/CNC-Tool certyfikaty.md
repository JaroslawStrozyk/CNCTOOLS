# CNC-Tools - Instalacja certyfikatu SSL

**Wersja:** 1.0
**Data:** Styczeń 2026

---

## Spis treści

1. [Wprowadzenie](#1-wprowadzenie)
2. [Pobranie certyfikatu](#2-pobranie-certyfikatu)
3. [Windows](#3-windows)
   - [Chrome / Edge](#31-chrome--edge-windows)
   - [Firefox](#32-firefox-windows)
4. [Linux](#4-linux)
   - [Chrome / Chromium](#41-chrome--chromium-linux)
   - [Firefox](#42-firefox-linux)
   - [Edge](#43-edge-linux)
5. [macOS](#5-macos)
   - [Chrome / Edge](#51-chrome--edge-macos)
   - [Firefox](#52-firefox-macos)
6. [Weryfikacja instalacji](#6-weryfikacja-instalacji)
7. [Rozwiązywanie problemów](#7-rozwiązywanie-problemów)

---

## 1. Wprowadzenie

Aplikacja CNC-Tools używa certyfikatu SSL do bezpiecznego połączenia HTTPS. Ponieważ certyfikat jest self-signed (samopodpisany), przeglądarki domyślnie wyświetlają ostrzeżenie "Niezabezpieczona".

Aby usunąć to ostrzeżenie i umożliwić poprawne działanie trybu PWA (aplikacja na pulpicie), należy zainstalować certyfikat jako zaufany na każdym komputerze klienckim.

**Adres serwera:** `https://192.168.1.226`

---

## 2. Pobranie certyfikatu

### Metoda 1: Przez przeglądarkę

1. Otwórz w przeglądarce: `https://192.168.1.226/static/cnctools.crt`
2. Zapisz plik na dysku (np. w folderze Pobrane)

### Metoda 2: Z serwera (dla administratorów)

Certyfikat znajduje się na serwerze w lokalizacji:
```
/etc/apache2/ssl/cnctools/server.crt
```

---

## 3. Windows

### 3.1 Chrome / Edge (Windows)

Chrome i Edge na Windows używają systemowego magazynu certyfikatów Windows.

**Kroki:**

1. Znajdź pobrany plik `cnctools.crt`
2. Kliknij prawym przyciskiem myszy na plik
3. Wybierz **"Zainstaluj certyfikat"**
4. Wybierz **"Komputer lokalny"** (wymaga uprawnień administratora)
5. Kliknij **Dalej**
6. Wybierz **"Umieść wszystkie certyfikaty w następującym magazynie"**
7. Kliknij **Przeglądaj**
8. Wybierz **"Zaufane główne urzędy certyfikacji"**
9. Kliknij **OK**, potem **Dalej**, potem **Zakończ**
10. Potwierdź ostrzeżenie bezpieczeństwa klikając **Tak**
11. **Zamknij i otwórz ponownie przeglądarkę**

**Alternatywnie przez wiersz poleceń (jako Administrator):**

```cmd
certutil -addstore -f "ROOT" C:\sciezka\do\cnctools.crt
```

---

### 3.2 Firefox (Windows)

Firefox używa własnego magazynu certyfikatów.

**Kroki:**

1. Otwórz Firefox
2. Kliknij menu (trzy kreski) → **Ustawienia**
3. W wyszukiwarce wpisz: `certyfikaty`
4. Kliknij **Wyświetl certyfikaty...**
5. Przejdź do zakładki **Urzędy certyfikacji**
6. Kliknij **Importuj...**
7. Wybierz plik `cnctools.crt`
8. Zaznacz opcję **"Zaufaj temu CA przy identyfikowaniu witryn"**
9. Kliknij **OK**
10. **Zamknij i otwórz ponownie Firefox**

---

## 4. Linux

### 4.1 Chrome / Chromium (Linux)

Chrome na Linuxie używa bazy NSS.

**Wymagania:**
```bash
sudo apt install libnss3-tools
```

**Instalacja certyfikatu:**

```bash
# Utwórz katalog bazy jeśli nie istnieje
mkdir -p ~/.pki/nssdb

# Zainicjuj bazę jeśli jest nowa
certutil -d sql:$HOME/.pki/nssdb -N --empty-password

# Dodaj certyfikat
certutil -d sql:$HOME/.pki/nssdb -A -t "C,," -n "CNCTOOLS" -i ~/Pobrane/cnctools.crt
```

**Sprawdzenie:**
```bash
certutil -d sql:$HOME/.pki/nssdb -L
```

**WAŻNE:** Wykonuj komendy jako zwykły użytkownik, nie jako root!

Po instalacji **zamknij całkowicie Chrome** i otwórz ponownie.

**Usunięcie certyfikatu (jeśli potrzebne):**
```bash
certutil -d sql:$HOME/.pki/nssdb -D -n "CNCTOOLS"
```

---

### 4.2 Firefox (Linux)

Firefox używa własnego magazynu certyfikatów (tak samo jak na Windows).

**Kroki:**

1. Otwórz Firefox
2. Kliknij menu (trzy kreski) → **Ustawienia**
3. Przejdź do: **Prywatność i bezpieczeństwo**
4. Przewiń do sekcji **Certyfikaty**
5. Kliknij **Wyświetl certyfikaty...**
6. Przejdź do zakładki **Urzędy certyfikacji**
7. Kliknij **Importuj...**
8. Wybierz plik `cnctools.crt`
9. Zaznacz **"Zaufaj temu CA przy identyfikowaniu witryn"**
10. Kliknij **OK**
11. **Zamknij i otwórz ponownie Firefox**

**Alternatywnie przez terminal:**

```bash
# Znajdź profil Firefox
FIREFOX_PROFILE=$(find ~/.mozilla/firefox -name "*.default-release" -type d | head -1)

# Dodaj certyfikat
certutil -d sql:$FIREFOX_PROFILE -A -t "C,," -n "CNCTOOLS" -i ~/Pobrane/cnctools.crt
```

---

### 4.3 Edge (Linux)

Edge na Linuxie używa tej samej bazy NSS co Chrome.

Wykonaj te same kroki co dla [Chrome / Chromium (Linux)](#41-chrome--chromium-linux).

---

## 5. macOS

### 5.1 Chrome / Edge (macOS)

Chrome i Edge na macOS używają systemowego Pęku kluczy (Keychain).

**Metoda graficzna:**

1. Znajdź pobrany plik `cnctools.crt`
2. Kliknij dwukrotnie na plik
3. Otworzy się **Dostęp do pęku kluczy** (Keychain Access)
4. Wybierz pęk kluczy **System** lub **login**
5. Certyfikat zostanie dodany
6. Znajdź certyfikat na liście (szukaj "192.168.1.226" lub "CNCTOOLS")
7. Kliknij dwukrotnie na certyfikat
8. Rozwiń sekcję **Zaufanie**
9. Przy opcji **"Używając tego certyfikatu"** wybierz **"Zawsze ufaj"**
10. Zamknij okno i podaj hasło administratora
11. **Zamknij i otwórz ponownie przeglądarkę**

**Metoda przez terminal:**

```bash
# Dodaj certyfikat do pęku kluczy systemowego
sudo security add-trusted-cert -d -r trustRoot -k /Library/Keychains/System.keychain ~/Downloads/cnctools.crt
```

---

### 5.2 Firefox (macOS)

Firefox na macOS używa własnego magazynu (nie systemowego Keychain).

**Kroki:**

1. Otwórz Firefox
2. Kliknij menu → **Preferencje** (lub **Ustawienia**)
3. Przejdź do: **Prywatność i bezpieczeństwo**
4. Przewiń do sekcji **Certyfikaty**
5. Kliknij **Wyświetl certyfikaty...**
6. Przejdź do zakładki **Urzędy certyfikacji**
7. Kliknij **Importuj...**
8. Wybierz plik `cnctools.crt`
9. Zaznacz **"Zaufaj temu CA przy identyfikowaniu witryn"**
10. Kliknij **OK**
11. **Zamknij i otwórz ponownie Firefox**

---

## 6. Weryfikacja instalacji

Po zainstalowaniu certyfikatu i restarcie przeglądarki:

1. Otwórz `https://192.168.1.226`
2. Sprawdź czy:
   - **Nie ma** ostrzeżenia "Niezabezpieczona" / "Not Secure"
   - Przy adresie widać **kłódkę** (może być szara lub z wykrzyknikiem informacyjnym)
   - Kliknięcie na kłódkę pokazuje informację o certyfikacie

**Test PWA:**
1. Na stronie CNC-Tools kliknij ikonę instalacji (w pasku adresu lub menu)
2. Zainstaluj aplikację
3. Otwórz zainstalowaną aplikację
4. Sprawdź czy **nie ma paska adresu** z napisem "Niezabezpieczona"

---

## 7. Rozwiązywanie problemów

### Problem: "SEC_ERROR_BAD_DATABASE" na Linux

**Przyczyna:** Komenda wykonana jako root lub baza NSS nie istnieje.

**Rozwiązanie:**
```bash
# Upewnij się że NIE jesteś rootem
whoami  # powinno pokazać twój login, nie "root"

# Utwórz bazę
mkdir -p ~/.pki/nssdb
certutil -d sql:$HOME/.pki/nssdb -N --empty-password

# Dodaj certyfikat ponownie
certutil -d sql:$HOME/.pki/nssdb -A -t "C,," -n "CNCTOOLS" -i ~/Pobrane/cnctools.crt
```

---

### Problem: Certyfikat dodany, ale nadal jest ostrzeżenie

**Rozwiązanie:**
1. Zamknij **całkowicie** przeglądarkę (sprawdź czy nie działa w tle)
2. Na Linux: `pkill chrome` lub `pkill firefox`
3. Otwórz przeglądarkę ponownie
4. Wyczyść cache przeglądarki (Ctrl+Shift+Delete)
5. Odśwież stronę (Ctrl+F5)

---

### Problem: Nie mogę znaleźć pliku certyfikatu

**Rozwiązanie:**
Pobierz certyfikat bezpośrednio z serwera:
```
https://192.168.1.226/static/cnctools.crt
```

---

### Problem: "Certyfikat nie jest zaufany" mimo instalacji

**Możliwe przyczyny:**
1. Certyfikat dodany do złego magazynu (np. "Osobiste" zamiast "Zaufane główne urzędy certyfikacji")
2. Przeglądarka nie została zrestartowana
3. Na Linux: komenda wykonana jako root (certyfikat trafił do /root/.pki zamiast /home/user/.pki)

---

### Problem: Brak uprawnień do instalacji (Windows)

**Rozwiązanie:**
1. Kliknij prawym na plik .crt
2. Wybierz "Uruchom jako administrator"
3. Lub poproś administratora IT o instalację

---

## Szybka ściągawka

| System | Przeglądarka | Metoda |
|--------|--------------|--------|
| Windows | Chrome / Edge | Kliknij .crt → Zainstaluj → Zaufane główne urzędy certyfikacji |
| Windows | Firefox | Ustawienia → Certyfikaty → Importuj |
| Linux | Chrome / Edge | `certutil -d sql:$HOME/.pki/nssdb -A -t "C,," -n "CNCTOOLS" -i cert.crt` |
| Linux | Firefox | Ustawienia → Prywatność → Certyfikaty → Importuj |
| macOS | Chrome / Edge | Kliknij .crt → Keychain → Zawsze ufaj |
| macOS | Firefox | Preferencje → Prywatność → Certyfikaty → Importuj |

---

## Kontakt

W przypadku problemów z instalacją certyfikatu skontaktuj się z administratorem systemu CNC-Tools.

---

*Dokument dla systemu CNC-Tools*
*© 2025 - Wszystkie prawa zastrzeżone*
