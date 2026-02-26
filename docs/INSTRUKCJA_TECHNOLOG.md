# Instrukcja obsługi systemu CNC Tools
## Stanowisko: Technolog

**Wersja dokumentu:** 1.0
**Data:** Styczeń 2026
**System:** CNC Tools - System zarządzania narzędziami CNC

---

## Spis treści

1. [Wprowadzenie](#1-wprowadzenie)
2. [Logowanie do systemu](#2-logowanie-do-systemu)
3. [Główny ekran - Technolog](#3-główny-ekran---technolog)
4. [Przeglądanie katalogu narzędzi](#4-przeglądanie-katalogu-narzędzi)
5. [Tworzenie zapotrzebowania](#5-tworzenie-zapotrzebowania)
6. [Zarządzanie koszykiem zamówienia](#6-zarządzanie-koszykiem-zamówienia)
7. [Podgląd i drukowanie PDF](#7-podgląd-i-drukowanie-pdf)
8. [Wysyłanie zapotrzebowania](#8-wysyłanie-zapotrzebowania)
9. [Wylogowanie](#9-wylogowanie)
10. [Najczęściej zadawane pytania](#10-najczęściej-zadawane-pytania)

---

## 1. Wprowadzenie

System CNC Tools umożliwia technologom składanie zapotrzebowań na narzędzia bezpośrednio do magazynu. Jako technolog masz dostęp do następujących funkcji:

- **Przeglądanie** katalogu dostępnych narzędzi
- **Składanie zapotrzebowań** na narzędzia
- **Podgląd i drukowanie** dokumentów PDF z zapotrzebowaniem
- **Wysyłanie** zapotrzebowań do magazynu

---

## 2. Logowanie do systemu

### 2.1 Logowanie za pomocą karty zbliżeniowej (zalecane)

1. Na ekranie logowania zobaczysz formularz oraz informację **"przyłóż kartę do czytnika"**
2. Przyłóż swoją kartę zbliżeniową do czytnika RFID
3. System automatycznie odczyta numer karty i zaloguje Cię
4. Zostaniesz przekierowany do głównego ekranu Technologa

**Wskazówka:** Zielona kropka obok napisu "przyłóż kartę" oznacza, że czytnik kart jest aktywny.

### 2.2 Logowanie tradycyjne (login i hasło)

1. W polu **"Nazwa użytkownika"** wpisz swój login
2. W polu **"Hasło"** wpisz swoje hasło
3. Kliknij przycisk **"Zaloguj"**

---

## 3. Główny ekran - Technolog

Po zalogowaniu zobaczysz ekran podzielony na następujące sekcje:

### 3.1 Pasek nagłówka

W górnej części ekranu znajdują się:

| Element | Opis |
|---------|------|
| **TECHNOLOG** | Nazwa aktualnego modułu |
| **Zamówienie** | Otwiera koszyk z aktualnym zapotrzebowaniem |
| **[Twoje imię]** | Menu użytkownika (wylogowanie, o programie) |

Przy przycisku **Zamówienie** widoczna jest liczba pozycji w koszyku (np. "Zamówienie (3)").

### 3.2 Panel główny - Katalog narzędzi

Tabela zawierająca wszystkie dostępne typy narzędzi:

| Kolumna | Opis |
|---------|------|
| **Kategoria / Podkategoria** | Klasyfikacja narzędzia |
| **Opis / Specyfikacja** | Szczegółowy opis narzędzia |
| **Nr katalogowy** | Numer katalogowy producenta |
| **Magazyn** | Ilość dostępna w magazynie |
| **Akcje** | Przyciski do dodawania do zamówienia |

---

## 4. Przeglądanie katalogu narzędzi

### 4.1 Wyszukiwanie

1. W polu **"Szukaj narzędzia..."** wpisz dowolny tekst
2. System przeszuka:
   - Nazwę kategorii i podkategorii
   - Opis narzędzia
   - Numer katalogowy
3. Lista zostanie automatycznie przefiltrowana

**Przykłady:**
- `frez 10` - znajdzie frezy o średnicy 10mm
- `VHM` - znajdzie narzędzia z węglika spiekanego
- `SAND` - znajdzie narzędzia Sandvik

### 4.2 Filtrowanie po kategorii

1. Użyj rozwijanego menu **kategorii** w prawym górnym rogu
2. Wybierz kategorię główną (np. Frezy, Wiertła)
3. Opcjonalnie wybierz podkategorię
4. Aby wyczyścić filtr, wybierz **"Wszystkie"**

### 4.3 Podgląd narzędzia

1. Kliknij ikonę **oka** przy wybranym narzędziu
2. Otworzy się okno z:
   - Zdjęciem narzędzia
   - Pełną specyfikacją
   - Numerem katalogowym

---

## 5. Tworzenie zapotrzebowania

### 5.1 Szybkie dodawanie do koszyka

1. Znajdź narzędzie w katalogu
2. Kliknij przycisk **"+"** (zielony) przy narzędziu
3. Narzędzie zostanie dodane do koszyka z domyślną ilością 1
4. Licznik przy przycisku **Zamówienie** zwiększy się

### 5.2 Dodawanie z pełnym formularzem

1. Kliknij przycisk **"Dodaj"** przy wybranym narzędziu
2. W oknie dialogowym wypełnij:

| Pole | Opis | Wymagane |
|------|------|----------|
| **Nr klienta** | Numer klienta/projektu | Nie |
| **Nr zlecenia** | Numer zlecenia produkcyjnego | Nie |
| **Kategoria** | Automatycznie wypełnione | - |
| **Podkategoria** | Automatycznie wypełnione | - |
| **Specyfikacja** | Opis narzędzia (można edytować) | Tak |
| **Nr katalogowy** | Numer producenta | Nie |
| **Ilość** | Liczba sztuk do zamówienia | Tak |
| **Uwagi** | Dodatkowe informacje | Nie |

3. Kliknij **"Dodaj do zamówienia"**

---

## 6. Zarządzanie koszykiem zamówienia

### 6.1 Otwieranie koszyka

Kliknij przycisk **"Zamówienie"** w nagłówku strony.

### 6.2 Zawartość okna zamówienia

W górnej części okna wyświetlane są:
- **Nr zamówienia** - automatycznie nadany numer (np. ZAM-0003)
- **Dział** - Twój dział (np. TECHNOLOGIA)
- **Imię i Nazwisko** - Twoje dane

### 6.3 Lista pozycji

Tabela zawiera wszystkie dodane narzędzia:

| Kolumna | Opis |
|---------|------|
| **Nr klienta** | Numer klienta/projektu |
| **Nr zlecenia** | Numer zlecenia |
| **Kategoria** | Kategoria narzędzia |
| **Podkategoria** | Podkategoria |
| **Specyfikacja** | Opis narzędzia |
| **Nr kat.** | Numer katalogowy |
| **Ilość** | Zamawiana ilość |
| **Akcje** | Edycja i usuwanie |

### 6.4 Edycja pozycji

1. Kliknij ikonę **ołówka** przy pozycji
2. Zmień dane w formularzu
3. Kliknij **"Zapisz zmiany"**

### 6.5 Usuwanie pozycji

1. Kliknij ikonę **kosza** przy pozycji
2. Potwierdź usunięcie w oknie dialogowym

### 6.6 Podsumowanie

Na dole okna widoczna jest **łączna liczba pozycji** w zamówieniu.

---

## 7. Podgląd i drukowanie PDF

### 7.1 Generowanie podglądu

1. W oknie zamówienia kliknij przycisk **"PDF"**
2. System wygeneruje dokument PDF
3. Otworzy się okno z podglądem dokumentu

### 7.2 Zawartość dokumentu PDF

Dokument **"KARTA ZAPOTRZEBOWANIA"** zawiera:

- **Nagłówek** z logo firmy
- **Dane dokumentu**: numer, data utworzenia, dział, technolog, status
- **Tabelę pozycji** ze wszystkimi narzędziami
- **Sekcję podpisów**: Sporządził, Zatwierdził, Przyjął
- **Stopkę** z datą i wersją dokumentu

### 7.3 Drukowanie

1. W oknie podglądu PDF użyj przycisków w górnej części:
   - **Ikona drukarki** - drukowanie
   - **Ikona pobierania** - zapisanie pliku PDF
2. Kliknij **"Zamknij"** aby zamknąć podgląd

---

## 8. Wysyłanie zapotrzebowania

### 8.1 Wysyłanie do magazynu

1. W oknie zamówienia kliknij przycisk **"Wyślij"**
2. Pojawi się okno potwierdzenia z informacją:
   - Numer zamówienia
   - Liczba pozycji
   - Ostrzeżenie, że po wysłaniu nie można edytować
3. Kliknij **"Wyślij"** aby potwierdzić

### 8.2 Potwierdzenie wysłania

Po pomyślnym wysłaniu:
1. Zobaczysz komunikat **"Zapotrzebowanie zostało wysłane!"**
2. Okno zamówienia zostanie zamknięte
3. Koszyk zostanie automatycznie wyczyszczony
4. Utworzony zostanie nowy, pusty koszyk

### 8.3 Co dzieje się po wysłaniu?

- Zapotrzebowanie trafia do **magazyniera**
- Magazynier widzi je w zakładce **"Zapotrzebowania"**
- Po skompletowaniu magazynier oznacza je jako **zrealizowane**
- Możesz wydrukować PDF przed lub po wysłaniu

---

## 9. Wylogowanie

### 9.1 Wylogowanie z systemu

1. Kliknij na swoje imię i nazwisko w prawym górnym rogu
2. Z menu wybierz **"Wyjście"**
3. Zostaniesz przekierowany do ekranu logowania

**Uwaga:** Niezapisane zmiany w koszyku pozostaną zachowane do następnego logowania.

---

## 10. Najczęściej zadawane pytania

### P: Jak sprawdzić, ile narzędzi jest dostępnych w magazynie?

**O:** W kolumnie "Magazyn" wyświetlana jest aktualna liczba dostępnych egzemplarzy danego typu narzędzia.

---

### P: Czy mogę edytować wysłane zapotrzebowanie?

**O:** Nie. Po wysłaniu zapotrzebowania nie można go edytować. Jeśli potrzebujesz zmian, skontaktuj się z magazynierem.

---

### P: Co oznacza numer ZAM-XXXX?

**O:** To unikalny numer Twojego zapotrzebowania. Używaj go w komunikacji z magazynem. Numer nadawany jest automatycznie.

---

### P: Czy muszę wypełniać wszystkie pola?

**O:** Nie. Obowiązkowe są tylko:
- Specyfikacja (opis narzędzia)
- Ilość

Pozostałe pola (nr klienta, nr zlecenia, uwagi) są opcjonalne, ale pomagają w organizacji pracy.

---

### P: Jak długo zapotrzebowanie czeka na realizację?

**O:** To zależy od dostępności narzędzi i obciążenia magazynu. Po wysłaniu zapotrzebowania magazynier widzi je natychmiast.

---

### P: Czy mogę zamówić narzędzie, którego nie ma w katalogu?

**O:** System pozwala zamawiać tylko narzędzia z katalogu. Jeśli potrzebujesz narzędzia spoza katalogu, zgłoś to do magazyniera lub działu zakupów.

---

### P: Jak wydrukować zapotrzebowanie?

**O:**
1. Otwórz okno "Zamówienie"
2. Kliknij przycisk "PDF"
3. W oknie podglądu użyj ikony drukarki lub pobierz plik

---

### P: Co się stanie, jeśli zamknę przeglądarkę bez wysłania?

**O:** Twój koszyk (zapotrzebowanie w statusie "robocze") zostanie zachowany. Po ponownym zalogowaniu zobaczysz swoje niezakończone zamówienie.

---

## Pomoc techniczna

W przypadku problemów z systemem skontaktuj się z:
- **Administratorem systemu** - problemy z logowaniem, uprawnieniami
- **Magazynierem** - pytania o dostępność narzędzi, status zapotrzebowania

---

*Dokument wygenerowany dla systemu CNC Tools v0.93*
