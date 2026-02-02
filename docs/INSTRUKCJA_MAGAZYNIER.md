# Instrukcja obsługi systemu CNC Tools
## Stanowisko: Magazynier

**Wersja dokumentu:** 1.0
**Data:** Styczeń 2026
**System:** CNC Tools - System zarządzania narzędziami CNC

---

## Spis treści

1. [Wprowadzenie](#1-wprowadzenie)
2. [Logowanie do systemu](#2-logowanie-do-systemu)
3. [Główny ekran - Magazyn](#3-główny-ekran---magazyn)
4. [Wyszukiwanie i filtrowanie narzędzi](#4-wyszukiwanie-i-filtrowanie-narzędzi)
5. [Przeglądanie szczegółów narzędzia](#5-przeglądanie-szczegółów-narzędzia)
6. [Wydawanie narzędzi (Pobieranie)](#6-wydawanie-narzędzi-pobieranie)
7. [Przyjmowanie zwrotów](#7-przyjmowanie-zwrotów)
8. [Zarządzanie typami narzędzi](#8-zarządzanie-typami-narzędzi)
9. [Zarządzanie egzemplarzami](#9-zarządzanie-egzemplarzami)
10. [Narzędzia aktualnie w użyciu](#10-narzędzia-aktualnie-w-użyciu)
11. [Moduł Zwroty - Uszkodzone narzędzia](#11-moduł-zwroty---uszkodzone-narzędzia)
12. [Ustawienia systemu](#12-ustawienia-systemu)
13. [Zamówienia](#13-zamówienia)
14. [Wylogowanie](#14-wylogowanie)
15. [Najczęściej zadawane pytania](#15-najczęściej-zadawane-pytania)

---

## 1. Wprowadzenie

System CNC Tools służy do kompleksowego zarządzania narzędziami w zakładzie produkcyjnym. Jako magazynier masz dostęp do następujących funkcji:

- **Przeglądanie** stanu magazynu narzędzi
- **Wydawanie** narzędzi pracownikom produkcji
- **Przyjmowanie zwrotów** narzędzi
- **Dodawanie** nowych typów narzędzi i ich egzemplarzy
- **Edycja** danych narzędzi
- **Przeglądanie** historii użycia narzędzi
- **Monitorowanie** uszkodzonych narzędzi
- **Konfiguracja** podstawowych ustawień systemu

---

## 2. Logowanie do systemu

### 2.1 Logowanie za pomocą karty zbliżeniowej (zalecane)

1. Na ekranie logowania zobaczysz formularz oraz informację **"przyłóż kartę do czytnika"**
2. Przyłóż swoją kartę zbliżeniową do czytnika RFID
3. System automatycznie odczyta numer karty i zaloguje Cię
4. Jeśli karta jest poprawnie przypisana do Twojego konta, zobaczysz komunikat **"Witaj, [Twoje imię]!"** i zostaniesz przekierowany do głównego ekranu

**Wskazówka:** Zielona kropka obok napisu "przyłóż kartę" oznacza, że czytnik kart jest aktywny i gotowy do użycia.

### 2.2 Logowanie tradycyjne (login i hasło)

1. W polu **"Nazwa użytkownika"** wpisz swój login
2. W polu **"Hasło"** wpisz swoje hasło
3. Kliknij przycisk **"Zaloguj"**

**Uwaga:** W przypadku problemów z logowaniem skontaktuj się z administratorem systemu.

---

## 3. Główny ekran - Magazyn

Po zalogowaniu zostaniesz przekierowany do głównego ekranu **MAGAZYN**. Ekran podzielony jest na następujące sekcje:

### 3.1 Pasek nagłówka

W górnej części ekranu znajdują się:

| Element | Opis |
|---------|------|
| **MAGAZYN** | Nazwa aktualnego modułu |
| **Ustawienia** | Przejście do konfiguracji systemu |
| **Zwroty** | Przegląd uszkodzonych narzędzi |
| **Zamówienia** | Lista zamówień narzędzi |
| **Zakupy** | Dostępne tylko dla logistyki |
| **[Twoje imię]** | Menu użytkownika (wylogowanie, o programie) |

### 3.2 Panel górny - Lista typów narzędzi

Główna tabela zawierająca wszystkie typy narzędzi w magazynie z kolumnami:

| Kolumna | Opis |
|---------|------|
| **Kategoria / Podkategoria** | Klasyfikacja narzędzia (np. Frezy / HSS) |
| **Opis / Specyfikacja** | Szczegółowy opis narzędzia |
| **Nr katalogowy** | Numer katalogowy producenta |
| **Nowe** | Liczba nowych egzemplarzy dostępnych w magazynie |
| **Używane** | Liczba używanych egzemplarzy dostępnych w magazynie |
| **W użyciu** | Liczba egzemplarzy aktualnie wydanych pracownikom |
| **Razem** | Całkowita liczba egzemplarzy danego typu |

### 3.3 Panel dolny - Zakładki szczegółów

Po wybraniu narzędzia z tabeli pojawiają się trzy zakładki:

1. **Szczegóły** - lista egzemplarzy wybranego narzędzia z obrazkiem
2. **Historia użycia** - pełna historia wydań i zwrotów
3. **Narzędzia aktualnie w użyciu** - wszystkie wydane narzędzia (wszystkich typów)

---

## 4. Wyszukiwanie i filtrowanie narzędzi

### 4.1 Wyszukiwarka tekstowa

1. W lewym górnym rogu panelu z listą narzędzi znajduje się pole **"Szukaj..."**
2. Wpisz dowolny tekst do wyszukania
3. System przeszuka:
   - Nazwę kategorii
   - Nazwę podkategorii
   - Opis narzędzia
   - Numer katalogowy
4. Lista narzędzi zostanie automatycznie przefiltrowana

**Przykłady wyszukiwania:**
- `HSS` - znajdzie wszystkie frezy HSS
- `10mm` - znajdzie narzędzia o średnicy 10mm
- `SAND` - znajdzie narzędzia od producenta Sandvik (po numerze katalogowym)

### 4.2 Filtrowanie po kategorii

1. W prawym górnym rogu panelu znajdują się dwa rozwijane menu:
   - **Kategoria główna** (np. Frezy, Wiertła, Płytki)
   - **Podkategoria** (np. HSS, VHM, Węglik)
2. Wybierz kategorię główną - lista podkategorii zostanie zaktualizowana
3. Opcjonalnie wybierz podkategorię dla bardziej szczegółowego filtrowania
4. Aby wyczyścić filtr, wybierz **"Wszystkie kategorie"**

---

## 5. Przeglądanie szczegółów narzędzia

### 5.1 Wybór narzędzia

1. Kliknij na wybrany wiersz w tabeli narzędzi
2. Wiersz zostanie podświetlony
3. W dolnym panelu pojawią się szczegóły

### 5.2 Zakładka "Szczegóły"

Zawiera:

**Tabela egzemplarzy** z kolumnami:
| Kolumna | Opis |
|---------|------|
| **Lokalizacja** | Miejsce przechowywania (Szafa/Kolumna/Półka) |
| **Data** | Data ostatniej modyfikacji |
| **Opakowanie** | Typ: Sztuka lub Komplet (X szt.) |
| **Stan** | Nowe / Używane / Uszkodzone |
| **Akcja** | Przycisk pobierania (dla dostępnych egzemplarzy) |

**Obrazek narzędzia** - wyświetlany po prawej stronie

**Stany techniczne egzemplarzy:**
- 🟢 **Nowe** - egzemplarz nieużywany
- 🔵 **Używane** - egzemplarz w dobrym stanie po użyciu
- 🔴 **Uszkodzone** - egzemplarz uszkodzony, do utylizacji
- 🟠 **Uszkodzone do regeneracji** - egzemplarz do naprawy/ostrzenia

### 5.3 Zakładka "Historia użycia"

Pokazuje pełną historię danego narzędzia:

| Kolumna | Opis |
|---------|------|
| **Pracownik** | Kto pobrał narzędzie |
| **Maszyna** | Na jakiej maszynie było używane |
| **Data pobrania** | Kiedy zostało wydane |
| **Data zwrotu** | Kiedy zostało zwrócone (lub "W użyciu") |
| **Zwrócił** | Kto dokonał zwrotu |
| **Uwagi** | Dodatkowe informacje |

---

## 6. Wydawanie narzędzi (Pobieranie)

### 6.1 Wydanie całego egzemplarza

1. Wybierz typ narzędzia z górnej tabeli
2. W zakładce **"Szczegóły"** znajdź egzemplarz do wydania
3. Kliknij niebieski przycisk **pobierania** (ikona strzałki w dół) przy wybranym egzemplarzu
4. W oknie modalnym **"Pobierz egzemplarz"**:
   - Sprawdź nazwę narzędzia
   - Wybierz **maszynę** z listy rozwijanej
   - Wybierz **pracownika** z listy rozwijanej
5. Kliknij **"Pobierz"**

**Uwaga:** Przycisk pobierania jest nieaktywny (szary) jeśli egzemplarz jest już w użyciu.

### 6.2 Wydanie części kompletu

Jeśli narzędzie jest w formie kompletu (np. zestaw 10 płytek), możesz wydać tylko część:

1. Kliknij przycisk pobierania przy egzemplarzu typu "Komplet"
2. W oknie modalnym pojawi się dodatkowa opcja **"Typ wydania"**:
   - **Cały komplet** - wydaj wszystkie sztuki
   - **Wybrane sztuki** - wydaj tylko część
3. Przy wyborze **"Wybrane sztuki"**:
   - Wprowadź liczbę sztuk do wydania
   - System pokaże ile zostanie w magazynie
4. Kliknij **"Pobierz"**

**Działanie systemu:** Przy częściowym wydaniu system automatycznie:
- Tworzy nowy egzemplarz dla wydanych sztuk
- Zmniejsza ilość w oryginalnym egzemplarzu
- Oba egzemplarze są oznaczone jako "sztuki" (nie "komplet")

---

## 7. Przyjmowanie zwrotów

### 7.1 Zwrot z zakładki "Narzędzia aktualnie w użyciu"

1. Przejdź do zakładki **"Narzędzia aktualnie w użyciu"** (trzecia zakładka)
2. Znajdź narzędzie do zwrotu (możesz użyć wyszukiwarki lub filtra po maszynie)
3. Kliknij zielony przycisk **"Zwróć"** (ikona strzałki wstecz)
4. W oknie modalnym **"Zwrot narzędzia"**:
   - Sprawdź informacje o narzędziu
   - Wybierz lub potwierdź **pracownika zwracającego**
   - Wybierz **stan techniczny** po zwrocie:
     - **Dobrym (jako używane)** - narzędzie nadaje się do dalszego użytku
     - **Uszkodzonym** - narzędzie do utylizacji
     - **Zużytym do regeneracji** - narzędzie do naprawy/ostrzenia
5. Kliknij **"Potwierdź zwrot"**

### 7.2 Zwrot częściowy

Jeśli pracownik zwraca tylko część wydanych sztuk:

1. W oknie zwrotu pojawi się opcja **"Ile zwracasz?"**:
   - **Całość** - zwrot wszystkich wydanych sztuk
   - **Tylko część** - zwrot częściowy
2. Przy wyborze **"Tylko część"**:
   - Wprowadź liczbę zwracanych sztuk
   - System pokaże ile pozostanie w użyciu
3. Wybierz stan techniczny zwracanych sztuk
4. Kliknij **"Potwierdź zwrot"**

**Działanie systemu:** Przy częściowym zwrocie:
- Tworzony jest nowy egzemplarz dla zwróconych sztuk (trafia do magazynu)
- Reszta pozostaje w użyciu u pracownika
- Historia użycia pozostaje otwarta dla pozostałych sztuk

---

## 8. Zarządzanie typami narzędzi

### 8.1 Dodawanie nowego typu narzędzia

1. W tabeli narzędzi kliknij zielony przycisk **"+"** w nagłówku ostatniej kolumny
2. W oknie **"Dodaj nowy typ narzędzia"** wypełnij:

| Pole | Opis | Wymagane |
|------|------|----------|
| **Kategoria / Podkategoria** | Wybierz z listy lub pozostaw "Brak" | Nie |
| **Opis / Specyfikacja** | Szczegółowy opis narzędzia | Tak |
| **Numer katalogowy** | Numer producenta | Nie |
| **Domyślna lokalizacja** | Gdzie przechowywać | Nie |
| **Opakowanie** | Sztuka lub Komplet | Tak |
| **Ilość w opakowaniu** | Dla kompletu - ile sztuk | Tak |
| **Obraz narzędzia** | Zdjęcie (opcjonalne) | Nie |

3. Kliknij **"Dodaj"**

**Uwaga dotycząca kompletów:**
- Przy wyborze "Komplet" ilość w opakowaniu musi być większa niż 1
- Przykład: Komplet płytek = 10 szt.

### 8.2 Edycja typu narzędzia

1. W tabeli narzędzi kliknij szary przycisk **edycji** (ikona ołówka) przy wybranym narzędziu
2. Zmodyfikuj potrzebne pola
3. Kliknij **"Zapisz"**

---

## 9. Zarządzanie egzemplarzami

### 9.1 Dodawanie nowego egzemplarza

1. Wybierz typ narzędzia z tabeli
2. W zakładce **"Szczegóły"** kliknij zielony przycisk **"+"** w nagłówku tabeli egzemplarzy
3. W oknie **"Dodaj nowy egzemplarz"** wypełnij:

| Pole | Opis |
|------|------|
| **Typ Narzędzia** | Automatycznie wypełnione |
| **Stan Techniczny** | Nowe / Używane / Uszkodzone |
| **Lokalizacja** | Wybierz z listy (Szafa/Kolumna/Półka) |
| **Typ dodawania** | Dla kompletów: Pełny komplet / Luźne sztuki |
| **Ilość sztuk** | Dla luźnych sztuk - ile sztuk dodajesz |
| **Zamówienie** | Opcjonalnie powiąż z zamówieniem |
| **Ilość** | Ile egzemplarzy dodać (dla kompletów: ile kompletów) |

4. Kliknij **"Zapisz"**

**Dodawanie luźnych sztuk:**
Jeśli masz pozostałość z kompletu (np. 3 luźne płytki z zestawu 10):
1. Wybierz **"Luźne sztuki"** w polu "Typ dodawania"
2. Wprowadź liczbę sztuk (np. 3)
3. Egzemplarz zostanie utworzony jako "3 szt." (nie jako komplet)

### 9.2 Edycja egzemplarza

1. W tabeli egzemplarzy kliknij szary przycisk **edycji** przy wybranym egzemplarzu
2. Możesz zmienić:
   - Stan techniczny
   - Lokalizację
3. Kliknij **"Zapisz"**

### 9.3 Usuwanie egzemplarza

1. W tabeli egzemplarzy kliknij czerwony przycisk **usuwania** (ikona kosza)
2. System wyświetli okno potwierdzenia z odpowiednim komunikatem
3. Potwierdź operację klikając **"Tak, usuń"**

**Zachowanie systemu w zależności od stanu egzemplarza:**

| Stan egzemplarza | Działanie systemu |
|------------------|-------------------|
| **Nowe** | Egzemplarz jest trwale usuwany z bazy danych |
| **Używane** | Egzemplarz jest trwale usuwany z bazy danych |
| **Uszkodzone** | Egzemplarz jest przenoszony do modułu **Zwroty** (zakładka "Uszkodzone elementy") |
| **Uszkodzone do regeneracji** | Egzemplarz jest przenoszony do modułu **Zwroty** (zakładka "Uszkodzone do regeneracji") |

**Dlaczego uszkodzone trafiają do Zwrotów?**
- Umożliwia to prowadzenie ewidencji uszkodzonych narzędzi
- Pozwala śledzić, które narzędzia wymagają regeneracji
- Zachowuje historię dla celów statystycznych i analizy zużycia

**Ograniczenia:**
- Nie można usunąć egzemplarza, który jest aktualnie w użyciu (przypisany do pracownika)
- Przed usunięciem upewnij się, że egzemplarz został zwrócony

---

## 10. Narzędzia aktualnie w użyciu

### 10.1 Przeglądanie listy

Trzecia zakładka **"Narzędzia aktualnie w użyciu"** pokazuje wszystkie wydane narzędzia:

| Kolumna | Opis |
|---------|------|
| **Narzędzie** | Pełna nazwa z kategorią |
| **Maszyna** | Gdzie jest używane |
| **Pracownik** | Kto ma narzędzie |
| **Data pobrania** | Kiedy zostało wydane |
| **Akcje** | Przycisk zwrotu |

Liczba w badge przy nazwie zakładki pokazuje ilość narzędzi w użyciu.

### 10.2 Wyszukiwanie i filtrowanie

- **Pole wyszukiwania** - wyszukuje po nazwie narzędzia i nazwisku pracownika
- **Filtr po maszynie** - pokazuje tylko narzędzia używane na wybranej maszynie

---

## 11. Moduł Zwroty - Uszkodzone narzędzia

### 11.1 Dostęp do modułu

Kliknij przycisk **"Zwroty"** w pasku nagłówka.

### 11.2 Zawartość modułu

Moduł zawiera dwie zakładki:

**Zakładka "Uszkodzone elementy":**
- Lista narzędzi oznaczonych jako uszkodzone (do utylizacji)
- Zawiera informacje o ostatniej maszynie, użytkowniku, dacie uszkodzenia

**Zakładka "Uszkodzone do regeneracji":**
- Lista narzędzi wymagających naprawy/ostrzenia
- Te narzędzia można po regeneracji przywrócić do użytku

### 11.3 Informacje w tabeli

| Kolumna | Opis |
|---------|------|
| **Data uszkodzenia** | Kiedy zgłoszono uszkodzenie |
| **Ostatnia maszyna** | Gdzie narzędzie było używane |
| **Ostatni użytkownik** | Kto używał przed uszkodzeniem |
| **Narzędzie** | Pełna nazwa |
| **Nr kat.** | Numer katalogowy |
| **Ostatnia lokalizacja** | Gdzie było przechowywane |
| **Opis uszkodzenia** | Szczegóły problemu |

---

## 12. Ustawienia systemu

### 12.1 Dostęp do ustawień

Kliknij przycisk **"Ustawienia"** w pasku nagłówka.

### 12.2 Zakładka "Kategorie"

Zarządzanie strukturą kategorii narzędzi:

**Kategorie główne** (lewa strona):
- Dodawanie nowej kategorii: przycisk "Dodaj"
- Edycja: przycisk ołówka
- Usuwanie: przycisk kosza

**Podkategorie** (prawa strona):
- Wybierz kategorię główną, aby zobaczyć jej podkategorie
- Dodawanie/edycja/usuwanie analogicznie

### 12.3 Zakładka "Maszyny"

Lista maszyn CNC dostępnych w systemie:
- Dodawanie nowej maszyny
- Edycja nazwy
- Usuwanie (jeśli maszyna nie ma powiązanych wydań)

### 12.4 Zakładka "Lokalizacje"

Zarządzanie miejscami przechowywania narzędzi:

**Struktura lokalizacji:**
- Szafa (np. "SZAFA-01", "REGAŁ-A")
- Półka (numer półki)
- Pozycja/Kolumna (numer miejsca na półce)

**Dodawanie seryjne:**
1. Kliknij **"Dodaj seryjnie"**
2. Podaj nazwę szafy
3. Określ liczbę półek (oś Y)
4. Określ liczbę pozycji na półce (oś X)
5. System utworzy wszystkie kombinacje automatycznie

**Przykład:** Szafa "A" z 5 półkami i 10 pozycjami utworzy 50 lokalizacji (A/1/1, A/1/2, ... A/5/10)

### 12.5 Zakładka "Dostawcy"

Lista dostawców narzędzi z danymi kontaktowymi:
- Kod dostawcy (identyfikator)
- Nazwa firmy
- NIP
- Adres
- Telefon
- Email

### 12.6 Zakładka "Poczta"

Informacje o konfiguracji poczty email (tylko podgląd):
- Serwer SMTP
- Konto email
- Status konfiguracji
- Możliwość wysłania testowego emaila

---

## 13. Zamówienia

### 13.1 Dostęp do modułu

Kliknij przycisk **"Zamówienia"** w pasku nagłówka.

### 13.2 Przeglądanie zamówień

Lista zamówień zawiera:
- Numer zamówienia
- Dostawca
- Data utworzenia
- Status (Wersja robocza / Wysłane / Zrealizowane)
- Wartość

**Uwaga:** Szczegółowe zarządzanie zamówieniami dostępne jest dla działu logistyki.

---

## 14. Wylogowanie

### 14.1 Sposób wylogowania

1. Kliknij na swoje imię i nazwisko w prawym górnym rogu
2. Z rozwiniętego menu wybierz **"Wyjście"**
3. Zostaniesz przekierowany do ekranu logowania

### 14.2 Informacje o programie

1. Kliknij na swoje imię i nazwisko
2. Wybierz **"O programie"**
3. Zobaczysz informacje o wersji systemu i danych kontaktowych

---

## 15. Najczęściej zadawane pytania

### P: Nie mogę wydać narzędzia - przycisk jest nieaktywny
**O:** Sprawdź czy:
- Egzemplarz nie jest już w użyciu (szary przycisk oznacza wydane narzędzie)
- Egzemplarz nie jest uszkodzony (uszkodzone nie mogą być wydawane)

### P: Jak dodać narzędzie, które przyszło luzem (nie w komplecie)?
**O:** Przy dodawaniu egzemplarza wybierz "Luźne sztuki" zamiast "Pełny komplet" i podaj faktyczną liczbę sztuk.

### P: Pracownik chce zwrócić tylko część wydanych płytek
**O:** Przy zwrocie wybierz opcję "Tylko część" i wprowadź liczbę zwracanych sztuk. Reszta pozostanie przypisana do pracownika.

### P: Jak oznaczyć uszkodzone narzędzie?
**O:** Przy przyjmowaniu zwrotu wybierz stan "Uszkodzonym" lub "Zużytym do regeneracji". Narzędzie trafi do modułu Zwroty.

### P: Nie widzę przycisku "Zakupy"
**O:** Przycisk jest widoczny tylko dla użytkowników z uprawnieniami logistyki. Skontaktuj się z administratorem, jeśli potrzebujesz dostępu.

### P: Jak szybko znaleźć wszystkie narzędzia na konkretnej maszynie?
**O:** W zakładce "Narzędzia aktualnie w użyciu" użyj filtra "Filtruj po maszynie".

### P: Karta nie działa przy logowaniu
**O:** Sprawdź czy:
- Widoczna jest zielona kropka przy "przyłóż kartę"
- Karta jest przypisana do Twojego konta w systemie
- Czytnik jest podłączony i działa

### P: Jak zmienić lokalizację egzemplarza?
**O:** Kliknij przycisk edycji przy egzemplarzu i zmień lokalizację z listy rozwijanej.

### P: Dlaczego usunięty uszkodzony egzemplarz pojawił się w module Zwroty?
**O:** To celowe działanie systemu. Egzemplarze oznaczone jako "Uszkodzone" lub "Uszkodzone do regeneracji" nie są trwale usuwane - trafiają do modułu Zwroty w celu prowadzenia ewidencji. Tylko egzemplarze w stanie "Nowe" i "Używane" są usuwane na stałe.

### P: Jak całkowicie usunąć uszkodzony egzemplarz?
**O:** Uszkodzone egzemplarze są archiwizowane w module Zwroty i nie można ich całkowicie usunąć z poziomu aplikacji. To zabezpieczenie pozwala zachować pełną historię narzędzi dla celów analitycznych.

---

## Kontakt z pomocą techniczną

W przypadku problemów technicznych lub pytań dotyczących systemu skontaktuj się z:

- **Administrator systemu** - problemy z kontem, uprawnieniami
- **Wsparcie IT** - problemy techniczne, awarie

---

*Dokument dla systemu CNC Tools* *© 2025 - Wszystkie prawa zastrzeżone*
