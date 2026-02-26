# Instrukcja obsługi systemu CNC Tools
## Stanowisko: Pracownik Produkcji

**Wersja dokumentu:** 1.0
**Data:** Styczeń 2026
**System:** CNC Tools - System zarządzania narzędziami CNC

---

## Spis treści

1. [Wprowadzenie](#1-wprowadzenie)
2. [Logowanie do systemu](#2-logowanie-do-systemu)
3. [Główny ekran - Produkcja](#3-główny-ekran---produkcja)
4. [Przeglądanie katalogu narzędzi](#4-przeglądanie-katalogu-narzędzi)
5. [Moje narzędzia w użyciu](#5-moje-narzędzia-w-użyciu)
6. [Podgląd narzędzi w użyciu](#6-podgląd-narzędzi-w-użyciu)
7. [Wylogowanie](#7-wylogowanie)
8. [Najczęściej zadawane pytania](#8-najczęściej-zadawane-pytania)

---

## 1. Wprowadzenie

System CNC Tools umożliwia pracownikom produkcji monitorowanie narzędzi przypisanych do ich stanowiska. Jako pracownik produkcji masz dostęp do następujących funkcji:

- **Przeglądanie** katalogu dostępnych narzędzi
- **Sprawdzanie** stanów magazynowych narzędzi
- **Podgląd** narzędzi aktualnie wydanych (wszystkich i swoich)
- **Monitorowanie** listy narzędzi przypisanych do Ciebie

**Ważne:** Pobieranie i zwracanie narzędzi odbywa się przez magazyniera. Jako pracownik produkcji możesz jedynie przeglądać informacje o narzędziach.

---

## 2. Logowanie do systemu

### 2.1 Logowanie za pomocą karty zbliżeniowej (zalecane)

1. Na ekranie logowania zobaczysz formularz oraz informację **"przyłóż kartę do czytnika"**
2. Przyłóż swoją kartę zbliżeniową do czytnika RFID
3. System automatycznie odczyta numer karty i zaloguje Cię
4. Zostaniesz przekierowany do głównego ekranu Produkcja

**Wskazówka:** Zielona kropka obok napisu "przyłóż kartę" oznacza, że czytnik kart jest aktywny.

### 2.2 Logowanie tradycyjne (login i hasło)

1. W polu **"Nazwa użytkownika"** wpisz swój login
2. W polu **"Hasło"** wpisz swoje hasło
3. Kliknij przycisk **"Zaloguj"**

---

## 3. Główny ekran - Produkcja

Po zalogowaniu zobaczysz ekran podzielony na dwie główne sekcje:

### 3.1 Pasek nagłówka

W górnej części ekranu znajdują się:

| Element | Opis |
|---------|------|
| **PRODUKCJA** | Nazwa aktualnego modułu (żółty napis) |
| **[Twoje imię i nazwisko]** | Wyświetlane na środku nagłówka |
| **Wyjście** | Przycisk wylogowania (czerwony) |

### 3.2 Panel górny - Lista typów narzędzi

Tabela zawierająca wszystkie typy narzędzi dostępnych w systemie:

| Kolumna | Opis |
|---------|------|
| **Kategoria / Podkategoria** | Klasyfikacja narzędzia (np. Frezy / VHM) |
| **Opis / Specyfikacja** | Szczegółowy opis narzędzia |
| **Nr katalogowy** | Numer katalogowy producenta |
| **Nowe** | Liczba nowych egzemplarzy w magazynie |
| **Używane** | Liczba używanych egzemplarzy dostępnych w magazynie |
| **W użyciu** | Liczba egzemplarzy aktualnie wydanych pracownikom |
| **Razem** | Całkowita liczba egzemplarzy danego typu |

**Wskazówka:** Wartości wyświetlane szarym kolorem (0) oznaczają brak egzemplarzy w danej kategorii.

### 3.3 Panel dolny - Moje narzędzia

Zakładka **"Moje narzędzia w użyciu"** pokazuje narzędzia aktualnie przypisane do Ciebie. Badge z liczbą przy nazwie zakładki informuje o ilości Twoich narzędzi.

---

## 4. Przeglądanie katalogu narzędzi

### 4.1 Wyszukiwanie

1. W polu **"Szukaj..."** (lewy górny róg) wpisz dowolny tekst
2. System przeszuka:
   - Nazwę kategorii i podkategorii
   - Opis narzędzia
   - Numer katalogowy
3. Lista zostanie automatycznie przefiltrowana

**Przykłady:**
- `frez 10` - znajdzie frezy o średnicy 10mm
- `VHM` - znajdzie narzędzia z węglika spiekanego
- `SAND` - znajdzie narzędzia Sandvik (po numerze katalogowym)

### 4.2 Filtrowanie po kategorii

1. Użyj rozwijanego menu **"Wszystkie kategorie"** (prawy górny róg)
2. Wybierz kategorię główną (np. Frezy, Wiertła)
3. Opcjonalnie wybierz podkategorię z drugiego menu
4. Aby wyczyścić filtr, wybierz **"Wszystkie kategorie"**

### 4.3 Wybór narzędzia

1. Kliknij na wybrany wiersz w tabeli
2. Wiersz zostanie podświetlony (brązowe tło)
3. Po prawej stronie dolnego panelu pojawi się obrazek narzędzia

---

## 5. Moje narzędzia w użyciu

### 5.1 Przeglądanie listy

Zakładka **"Moje narzędzia w użyciu"** pokazuje wszystkie narzędzia, które zostały Ci wydane przez magazyniera:

| Kolumna | Opis |
|---------|------|
| **Narzędzie** | Pełna nazwa z kategorią i podkategorią |
| **Maszyna** | Na jakiej maszynie jest używane |
| **Data pobrania** | Kiedy narzędzie zostało Ci wydane |

### 5.2 Obrazek narzędzia

Po prawej stronie tabeli wyświetlany jest obrazek aktualnie wybranego narzędzia z górnej tabeli. Jeśli narzędzie nie ma przypisanego zdjęcia, wyświetlany jest obrazek domyślny.

### 5.3 Brak narzędzi

Jeśli nie masz aktualnie żadnych przypisanych narzędzi, zobaczysz komunikat:
**"Brak narzędzi w użyciu."**

---

## 6. Podgląd narzędzi w użyciu

### 6.1 Sprawdzanie kto używa danego narzędzia

Jeśli w kolumnie **"W użyciu"** widzisz liczbę większą od zera, możesz sprawdzić szczegóły:

1. Kliknij na liczbę w kolumnie **"W użyciu"** (wyświetlona jako przycisk)
2. Otworzy się okno **"Narzędzia w użyciu: [nazwa narzędzia]"**
3. Zobaczysz listę wszystkich wydanych egzemplarzy tego typu

### 6.2 Zawartość okna podglądu

| Kolumna | Opis |
|---------|------|
| **Narzędzie** | Pełna nazwa narzędzia |
| **Maszyna** | Na jakiej maszynie jest używane |
| **Pracownik** | Kto ma przypisane narzędzie |
| **Data pobrania** | Kiedy zostało wydane |

### 6.3 Zamykanie okna

Kliknij przycisk **"X"** w prawym górnym rogu okna lub kliknij poza obszarem okna.

---

## 7. Wylogowanie

### 7.1 Wylogowanie z systemu

1. Kliknij czerwony przycisk **"Wyjście"** w prawym górnym rogu
2. Zostaniesz przekierowany do ekranu logowania

---

## 8. Najczęściej zadawane pytania

### P: Jak pobrać narzędzie z magazynu?

**O:** Jako pracownik produkcji nie możesz samodzielnie pobierać narzędzi. Udaj się do magazyniera, który wyda Ci narzędzie i zarejestruje je w systemie.

---

### P: Jak zwrócić narzędzie?

**O:** Udaj się do magazyniera z narzędziem. Magazynier przyjmie zwrot i zarejestruje go w systemie. Narzędzie zniknie z Twojej listy "Moje narzędzia w użyciu".

---

### P: Dlaczego nie widzę wszystkich narzędzi w "Moje narzędzia w użyciu"?

**O:** W tej zakładce wyświetlane są tylko narzędzia przypisane do Ciebie. Jeśli narzędzie zostało wydane innemu pracownikowi, nie będzie widoczne na Twojej liście.

---

### P: Jak sprawdzić, czy dane narzędzie jest dostępne w magazynie?

**O:** Sprawdź kolumny **"Nowe"** i **"Używane"** w górnej tabeli. Jeśli wartości są większe od zera, narzędzie jest dostępne do pobrania (przez magazyniera).

---

### P: Co oznaczają kolory liczb w tabeli?

**O:**
- **Biały/jasny tekst** - wartość większa od zera
- **Szary tekst** - wartość równa zero (brak egzemplarzy)

---

### P: Karta nie działa przy logowaniu

**O:** Sprawdź czy:
- Widoczna jest zielona kropka przy "przyłóż kartę"
- Karta jest przypisana do Twojego konta w systemie
- Czytnik jest podłączony i działa

W przypadku problemów skontaktuj się z administratorem systemu.

---

### P: Jak znaleźć konkretne narzędzie?

**O:** Użyj pola wyszukiwania "Szukaj..." i wpisz fragment nazwy, numeru katalogowego lub kategorii narzędzia. Lista zostanie automatycznie przefiltrowana.

---

### P: Mogę edytować dane narzędzi?

**O:** Nie. Jako pracownik produkcji masz dostęp tylko do przeglądania informacji. Edycja danych jest dostępna dla magazyniera.

---

### P: Co zrobić jeśli narzędzie jest uszkodzone?

**O:** Zgłoś uszkodzenie magazynierowi podczas zwrotu narzędzia. Magazynier oznaczy narzędzie jako uszkodzone w systemie.

---

## Pomoc techniczna

W przypadku problemów z systemem skontaktuj się z:
- **Magazynierem** - pytania o dostępność narzędzi, wydania i zwroty
- **Administratorem systemu** - problemy z logowaniem, uprawnieniami

---

*Dokument wygenerowany dla systemu CNC Tools v0.93*
