# CNC Tools - Schemat Bazy Danych

**Wersja aplikacji:** 1.00.0g
**Baza danych:** PostgreSQL
**Framework:** Django 4.2
**Aplikacja:** TOOLS
**Data generacji:** 2026-02-24

---

## Spis treści

1. [Kategoria](#1-kategoria)
2. [Podkategoria](#2-podkategoria)
3. [Dostawca](#3-dostawca)
4. [Lokalizacja](#4-lokalizacja)
5. [Maszyna](#5-maszyna)
6. [Pracownik](#6-pracownik)
7. [FakturaZakupu](#7-fakturazakupu)
8. [NarzedzieMagazynowe](#8-narzedziemagazynowe)
9. [EgzemplarzNarzedzia](#9-egzemplarznarzedzia)
10. [HistoriaUzyciaNarzedzia](#10-historiauzycianarzeadzia)
11. [Uszkodzenie](#11-uszkodzenie)
12. [Zamowienie](#12-zamowienie)
13. [PozycjaZamowienia](#13-pozycjazamowienia)
14. [RealizacjaZamowienia](#14-realizacjazamowienia)
15. [PozycjaRealizacji](#15-pozycjarealizacji)
16. [PozycjaGeneratora](#16-pozycjageneratora)
17. [ZapotrzebowanieTechnologa](#17-zapotrzebowanietechnologa)
18. [PozycjaZapotrzebowania](#18-pozycjazapotrzebowania)
19. [LogEntry](#19-logentry)

---

## Diagram relacji (uproszczony)

```
Kategoria ──1:N──► Podkategoria ──1:N──► NarzedzieMagazynowe
                                              │
                    Dostawca ──1:N─────────────┤ (ostatni_dostawca)
                    Lokalizacja ──1:N──────────┤ (domyslna_lokalizacja)
                                              │
                                         1:N  ▼
                                    EgzemplarzNarzedzia
                                         │    │
                      Lokalizacja ───────┘    │
                      FakturaZakupu ──────────┤
                      Zamowienie ─────────────┤
                      self (komplet) ─────────┘
                                              │
                                         1:N  ▼
                                  HistoriaUzyciaNarzedzia
                                         │    │
                      Maszyna ───────────┘    │
                      Pracownik (wydanie) ────┤
                      Pracownik (zwrot) ──────┘

Dostawca ──1:N──► Zamowienie ──1:N──► PozycjaZamowienia
                       │                     │
                  1:N  ▼                1:N  ▼
            RealizacjaZamowienia    PozycjaRealizacji
                       │                │    │
            Lokalizacja ───────────────┘    │
            FakturaZakupu ──────────────────┘

NarzedzieMagazynowe ──1:1──► PozycjaGeneratora
Dostawca ─────────────1:N──► PozycjaGeneratora

User ──1:N──► ZapotrzebowanieTechnologa ──1:N──► PozycjaZapotrzebowania
                                                        │
                              NarzedzieMagazynowe ──────┘

NarzedzieMagazynowe ──1:N──► Uszkodzenie
EgzemplarzNarzedzia ──1:N──► Uszkodzenie
Pracownik ────────────1:N──► Uszkodzenie

Pracownik ──1:1──► User (Django auth)
```

---

## Tabele

### 1. Kategoria
**Opis:** Główne kategorie narzędzi

| Pole | Typ | Ograniczenia | Opis |
|------|-----|-------------|------|
| id | BigAutoField | PK, auto | Klucz główny |
| nazwa | CharField(100) | UNIQUE, NOT NULL | Nazwa kategorii |

**Meta:** ordering = ['nazwa']

---

### 2. Podkategoria
**Opis:** Podkategorie w ramach kategorii

| Pole | Typ | Ograniczenia | Opis |
|------|-----|-------------|------|
| id | BigAutoField | PK, auto | Klucz główny |
| nazwa | CharField(100) | NOT NULL | Nazwa podkategorii |
| kategoria | ForeignKey → Kategoria | CASCADE, NOT NULL | Kategoria nadrzędna |

**Meta:** unique_together = [('nazwa', 'kategoria')], ordering = ['kategoria__nazwa', 'nazwa']

---

### 3. Dostawca
**Opis:** Dostawcy narzędzi

| Pole | Typ | Ograniczenia | Opis |
|------|-----|-------------|------|
| id | BigAutoField | PK, auto | Klucz główny |
| kod_dostawcy | CharField(50) | UNIQUE, NOT NULL | Kod dostawcy |
| nazwa_firmy | CharField(200) | NOT NULL | Nazwa firmy |
| nip | CharField(20) | NULL, BLANK | NIP |
| adres | TextField | NULL, BLANK | Adres |
| telefon | CharField(20) | NULL, BLANK | Telefon |
| email | EmailField | NULL, BLANK | Email |

**Meta:** ordering = ['nazwa_firmy']

---

### 4. Lokalizacja
**Opis:** Lokalizacja magazynowa (szafa/kolumna/półka)

| Pole | Typ | Ograniczenia | Opis |
|------|-----|-------------|------|
| id | BigAutoField | PK, auto | Klucz główny |
| szafa | CharField(50) | NOT NULL | Szafa/regał |
| kolumna | CharField(50) | NOT NULL | Kolumna |
| polka | CharField(50) | NOT NULL | Półka |

**Meta:** unique_together = [('szafa', 'kolumna', 'polka')], ordering = ['szafa', 'kolumna', 'polka']

---

### 5. Maszyna
**Opis:** Maszyny CNC

| Pole | Typ | Ograniczenia | Opis |
|------|-----|-------------|------|
| id | BigAutoField | PK, auto | Klucz główny |
| nazwa | CharField(100) | UNIQUE, NOT NULL | Nazwa maszyny |

**Meta:** ordering = ['nazwa']

---

### 6. Pracownik
**Opis:** Pracownicy

| Pole | Typ | Ograniczenia | Opis |
|------|-----|-------------|------|
| id | BigAutoField | PK, auto | Klucz główny |
| karta | CharField(50) | UNIQUE, NULL, BLANK | Numer karty pracownika |
| nazwisko | CharField(100) | NOT NULL | Nazwisko |
| imie | CharField(100) | NOT NULL | Imię |
| user | OneToOneField → User | SET_NULL, NULL, BLANK | Konto Django |
| pobieranie_narzedzi | BooleanField | default=True | Czy może pobierać narzędzia |

**Meta:** ordering = ['nazwisko', 'imie']

---

### 7. FakturaZakupu
**Opis:** Faktury zakupu

| Pole | Typ | Ograniczenia | Opis |
|------|-----|-------------|------|
| id | BigAutoField | PK, auto | Klucz główny |
| numer_faktury | CharField(100) | UNIQUE, NOT NULL | Numer faktury |
| data_wystawienia | DateField | NOT NULL | Data wystawienia |
| dostawca | ForeignKey → Dostawca | PROTECT, NOT NULL | Dostawca |
| plik | FileField | NULL, BLANK, upload='faktury/' | Plik faktury |
| rozliczone | BooleanField | default=False | Czy rozliczona |

**Meta:** ordering = ['-data_wystawienia']

---

### 8. NarzedzieMagazynowe
**Opis:** Typy narzędzi w magazynie (kartoteka)

| Pole | Typ | Ograniczenia | Opis |
|------|-----|-------------|------|
| id | BigAutoField | PK, auto | Klucz główny |
| podkategoria | ForeignKey → Podkategoria | SET_NULL, NULL, BLANK | Podkategoria |
| opis | TextField | NOT NULL | Opis / specyfikacja |
| numer_katalogowy | CharField(100) | NULL, BLANK | Numer katalogowy |
| obraz | ImageField | NULL, BLANK, upload='narzedzia/' | Zdjęcie narzędzia |
| stan_minimalny | PositiveIntegerField | default=0 | Stan minimalny |
| stan_maksymalny | PositiveIntegerField | default=0 | Stan maksymalny |
| ostatni_dostawca | ForeignKey → Dostawca | SET_NULL, NULL, BLANK | Ostatni dostawca |
| domyslna_lokalizacja | ForeignKey → Lokalizacja | SET_NULL, NULL, BLANK | Domyślna lokalizacja |
| opakowanie | CharField(10) | choices: szt/kompl, default='szt' | Jednostka zakupu |
| ilosc_w_opakowaniu | PositiveIntegerField | default=1 | Ilość sztuk w opakowaniu |
| wydawanie_sztuk | BooleanField | default=False | Wydawanie pojedynczych sztuk |

**Meta:** ordering = ['podkategoria__kategoria__nazwa', 'podkategoria__nazwa', 'opis']

---

### 9. EgzemplarzNarzedzia
**Opis:** Pojedyncze egzemplarze narzędzi (stan magazynowy)

| Pole | Typ | Ograniczenia | Opis |
|------|-----|-------------|------|
| id | BigAutoField | PK, auto | Klucz główny |
| narzedzie_typ | ForeignKey → NarzedzieMagazynowe | CASCADE, NOT NULL | Typ narzędzia |
| stan | CharField(30) | choices: nowe/uzywane/uszkodzone/uszkodzone_regeneracja, default='nowe' | Stan egzemplarza |
| lokalizacja | ForeignKey → Lokalizacja | SET_NULL, NULL, BLANK | Aktualna lokalizacja |
| faktura_zakupu | ForeignKey → FakturaZakupu | SET_NULL, NULL, BLANK | Faktura zakupu |
| zamowienie | ForeignKey → Zamowienie | SET_NULL, NULL, BLANK | Zamówienie źródłowe |
| data_zakupu | DateTimeField | auto_now_add, NULL, BLANK | Data przyjęcia |
| data_modyfikacji | DateTimeField | auto_now | Data ostatniej modyfikacji |
| oznaczenie | CharField(100) | NULL, BLANK | Oznaczenie/etykieta |
| jednostka | CharField(10) | choices: szt/kompl, default='szt' | Jednostka |
| ilosc_w_komplecie | PositiveIntegerField | default=1 | Ilość w komplecie |
| komplet_zrodlowy | ForeignKey → self | SET_NULL, NULL, BLANK | Komplet źródłowy (self-ref) |
| nowy_wpis | BooleanField | default=False | Oczekuje na wydruk etykiety |

**Meta:** ordering = ['-data_zakupu']

---

### 10. HistoriaUzyciaNarzedzia
**Opis:** Historia wydań i zwrotów narzędzi

| Pole | Typ | Ograniczenia | Opis |
|------|-----|-------------|------|
| id | BigAutoField | PK, auto | Klucz główny |
| egzemplarz | ForeignKey → EgzemplarzNarzedzia | CASCADE, NOT NULL | Egzemplarz |
| maszyna | ForeignKey → Maszyna | SET_NULL, NULL | Maszyna |
| pracownik | ForeignKey → Pracownik | SET_NULL, NULL | Pracownik pobierający |
| pracownik_zwracajacy | ForeignKey → Pracownik | SET_NULL, NULL, BLANK | Pracownik zwracający |
| data_wydania | DateTimeField | auto_now_add, NOT NULL | Data wydania |
| data_zwrotu | DateTimeField | NULL, BLANK | Data zwrotu |
| uwagi | TextField | BLANK | Uwagi |
| nr_zlecenia | CharField(100) | NULL, BLANK | Nr zlecenia produkcyjnego |
| stan_po_zwrocie | CharField(30) | NULL, BLANK | Stan po zwrocie |

**Meta:** ordering = ['-data_wydania']

---

### 11. Uszkodzenie
**Opis:** Karty uszkodzeń narzędzi

| Pole | Typ | Ograniczenia | Opis |
|------|-----|-------------|------|
| id | BigAutoField | PK, auto | Klucz główny |
| egzemplarz | ForeignKey → EgzemplarzNarzedzia | SET_NULL, NULL, BLANK | Egzemplarz |
| narzedzie_typ | ForeignKey → NarzedzieMagazynowe | CASCADE, NULL, BLANK | Typ narzędzia |
| narzedzie_opis | CharField(500) | BLANK | Opis narzędzia (snapshot) |
| numer_katalogowy | CharField(200) | BLANK | Nr katalogowy (snapshot) |
| kategoria_narzedzia | CharField(300) | BLANK | Kategoria (snapshot) |
| lokalizacja_opis | CharField(200) | BLANK | Lokalizacja (snapshot) |
| stan | CharField(50) | BLANK | Stan (snapshot) |
| maszyna_nazwa | CharField(200) | BLANK | Maszyna (snapshot) |
| pracownik_nazwisko | CharField(100) | BLANK | Nazwisko pracownika |
| pracownik_imie | CharField(100) | BLANK | Imię pracownika |
| data_uszkodzenia | DateTimeField | auto_now_add | Data uszkodzenia |
| opis_uszkodzenia | TextField | NULL, BLANK | Opis uszkodzenia |
| pracownik | ForeignKey → Pracownik | SET_NULL, NULL, BLANK | Zgłaszający |
| numer_karty | CharField(15) | UNIQUE, NULL, BLANK | Nr karty (RRRR/NNN lub RRRR/NNNR) |
| przyczyna_uszkodzenia | TextField | BLANK | Przyczyna |
| stracony_czas | CharField(100) | BLANK | Stracony czas |
| typ_zglaszajacego | CharField(20) | BLANK | Typ: pobierajacy/zwracajacy |
| nazwisko_zglaszajacego | CharField(200) | BLANK | Nazwisko zgłaszającego |

**Meta:** ordering = ['-data_uszkodzenia']

---

### 12. Zamowienie
**Opis:** Zamówienia zakupu narzędzi

| Pole | Typ | Ograniczenia | Opis |
|------|-----|-------------|------|
| id | BigAutoField | PK, auto | Klucz główny |
| numer | CharField(50) | UNIQUE, NOT NULL | Numer zamówienia |
| dostawca | ForeignKey → Dostawca | PROTECT, NOT NULL | Dostawca |
| email_docelowy | EmailField | NULL, BLANK | Email dostawcy (snapshot) |
| data_utworzenia | DateTimeField | auto_now_add | Data utworzenia |
| data_wyslania | DateTimeField | NULL, BLANK | Data wysłania |
| wartosc_zamowienia | DecimalField(12,2) | default=0 | Wartość zamówienia |
| status | CharField(20) | choices: draft/verified/sent/partially_received/completed, default='draft' | Status |
| uwagi | TextField | BLANK | Uwagi |

**Meta:** ordering = ['-data_utworzenia']

---

### 13. PozycjaZamowienia
**Opis:** Pozycje (linie) zamówień

| Pole | Typ | Ograniczenia | Opis |
|------|-----|-------------|------|
| id | BigAutoField | PK, auto | Klucz główny |
| zamowienie | ForeignKey → Zamowienie | CASCADE, NOT NULL | Zamówienie |
| narzedzie_typ | ForeignKey → NarzedzieMagazynowe | PROTECT, NOT NULL | Typ narzędzia |
| kategoria_nazwa | CharField(200) | BLANK | Kategoria (snapshot) |
| podkategoria_nazwa | CharField(200) | BLANK | Podkategoria (snapshot) |
| narzedzie_opis | TextField | BLANK | Opis narzędzia (snapshot) |
| numer_katalogowy | CharField(100) | BLANK | Nr katalogowy (snapshot) |
| ilosc_zamowiona | PositiveIntegerField | NOT NULL | Ilość zamówiona |
| jednostka | CharField(10) | choices: szt/kompl, default='szt' | Jednostka |
| ilosc_w_komplecie | PositiveIntegerField | default=1 | Ilość w komplecie |
| cena_jednostkowa | DecimalField(10,2) | NULL, BLANK | Cena jednostkowa |
| wartosc_pozycji | DecimalField(12,2) | default=0 | Wartość pozycji |
| ilosc_dostarczona | PositiveIntegerField | default=0 | Ilość dostarczona |
| zrealizowane | BooleanField | default=False | Czy zrealizowana |

**Meta:** ordering = ['zamowienie', 'id']

---

### 14. RealizacjaZamowienia
**Opis:** Realizacje (przyjęcia) zamówień

| Pole | Typ | Ograniczenia | Opis |
|------|-----|-------------|------|
| id | BigAutoField | PK, auto | Klucz główny |
| zamowienie | ForeignKey → Zamowienie | CASCADE, NOT NULL | Zamówienie |
| data_realizacji | DateTimeField | auto_now_add | Data realizacji |
| lokalizacja_domyslna | ForeignKey → Lokalizacja | SET_NULL, NULL, BLANK | Domyślna lokalizacja |
| uwagi | TextField | BLANK | Uwagi |

**Meta:** ordering = ['-data_realizacji']

---

### 15. PozycjaRealizacji
**Opis:** Pozycje realizacji zamówień

| Pole | Typ | Ograniczenia | Opis |
|------|-----|-------------|------|
| id | BigAutoField | PK, auto | Klucz główny |
| realizacja | ForeignKey → RealizacjaZamowienia | CASCADE, NOT NULL | Realizacja |
| pozycja_zamowienia | ForeignKey → PozycjaZamowienia | CASCADE, NOT NULL | Pozycja zamówienia |
| ilosc_przyjeta | PositiveIntegerField | NOT NULL | Ilość przyjęta |
| lokalizacja | ForeignKey → Lokalizacja | SET_NULL, NULL | Lokalizacja docelowa |
| faktura_zakupu | ForeignKey → FakturaZakupu | SET_NULL, NULL, BLANK | Faktura zakupu |
| cena_jednostkowa | DecimalField(10,2) | NULL, BLANK | Cena rzeczywista |

**Meta:** ordering = ['realizacja', 'id']

---

### 16. PozycjaGeneratora
**Opis:** Pozycje generatora zamówień (tymczasowe)

| Pole | Typ | Ograniczenia | Opis |
|------|-----|-------------|------|
| id | BigAutoField | PK, auto | Klucz główny |
| narzedzie_typ | OneToOneField → NarzedzieMagazynowe | CASCADE, UNIQUE | Typ narzędzia |
| dostawca | ForeignKey → Dostawca | SET_NULL, NULL, BLANK | Dostawca |
| cena_jednostkowa | DecimalField(10,2) | default=0 | Cena jednostkowa PLN |
| ilosc_do_zamowienia | PositiveIntegerField | default=0 | Ilość do zamówienia |
| data_utworzenia | DateTimeField | auto_now_add | Data utworzenia |
| data_modyfikacji | DateTimeField | auto_now | Data modyfikacji |

**Meta:** ordering = ['narzedzie_typ__podkategoria__kategoria__nazwa', 'narzedzie_typ__opis']

---

### 17. ZapotrzebowanieTechnologa
**Opis:** Zapotrzebowania technologów na narzędzia

| Pole | Typ | Ograniczenia | Opis |
|------|-----|-------------|------|
| id | BigAutoField | PK, auto | Klucz główny |
| technolog | ForeignKey → User | SET_NULL, NULL | Technolog zgłaszający |
| data_utworzenia | DateTimeField | auto_now_add | Data utworzenia |
| data_wyslania | DateTimeField | NULL, BLANK | Data wysłania |
| data_realizacji | DateTimeField | NULL, BLANK | Data realizacji |
| zrealizowany_przez | ForeignKey → User | SET_NULL, NULL, BLANK | Zrealizowane przez |
| status | CharField(20) | choices: draft/submitted/completed/cancelled, default='draft' | Status |
| uwagi | TextField | BLANK | Uwagi |

**Meta:** ordering = ['-data_utworzenia']

---

### 18. PozycjaZapotrzebowania
**Opis:** Pozycje zapotrzebowań technologów

| Pole | Typ | Ograniczenia | Opis |
|------|-----|-------------|------|
| id | BigAutoField | PK, auto | Klucz główny |
| zapotrzebowanie | ForeignKey → ZapotrzebowanieTechnologa | CASCADE, NOT NULL | Zapotrzebowanie |
| narzedzie_typ | ForeignKey → NarzedzieMagazynowe | SET_NULL, NULL, BLANK | Typ narzędzia |
| kategoria_nazwa | CharField(200) | BLANK | Kategoria (snapshot) |
| podkategoria_nazwa | CharField(200) | BLANK | Podkategoria (snapshot) |
| specyfikacja | TextField | BLANK | Specyfikacja |
| numer_katalogowy | CharField(100) | BLANK | Nr katalogowy |
| nr_klienta | CharField(100) | BLANK | Nr klienta |
| nr_zlecenia | CharField(100) | BLANK | Nr zlecenia |
| ilosc | PositiveIntegerField | default=1 | Ilość |
| uwagi | TextField | BLANK | Uwagi |
| data_dodania | DateTimeField | auto_now_add | Data dodania |

**Meta:** ordering = ['data_dodania']

---

### 19. LogEntry
**Opis:** Logi operacji użytkowników

| Pole | Typ | Ograniczenia | Opis |
|------|-----|-------------|------|
| id | BigAutoField | PK, auto | Klucz główny |
| timestamp | DateTimeField | auto_now_add, db_index | Znacznik czasu |
| status | CharField(10) | choices: INFO/SUCCESS/WARNING/ERROR, default='INFO' | Poziom |
| osoba | CharField(200) | default='-' | Użytkownik |
| operacja | TextField | NOT NULL | Opis operacji |

**Meta:** ordering = ['-timestamp'], indexes = [Index('-timestamp')]

---

## Podsumowanie statystyczne

| Metryka | Wartość |
|---------|---------|
| Liczba modeli | 19 |
| Relacje ForeignKey | 31 |
| Relacje OneToOneField | 2 |
| Ograniczenia UNIQUE | 7 |
| unique_together | 2 |
| Zachowanie CASCADE | 12 relacji |
| Zachowanie SET_NULL | 19 relacji |
| Zachowanie PROTECT | 2 relacji |

## Wzorce projektowe

- **Pola snapshot:** Wiele modeli (PozycjaZamowienia, Uszkodzenie, PozycjaZapotrzebowania) przechowuje kopie danych (np. kategoria_nazwa, narzedzie_opis) z momentu transakcji
- **Self-referential FK:** EgzemplarzNarzedzia → komplet_zrodlowy (wydawanie sztuk z kompletu)
- **Hierarchia kategorii:** Kategoria → Podkategoria → NarzedzieMagazynowe
- **Śledzenie historii:** HistoriaUzyciaNarzedzia rejestruje wydania/zwroty z timestampami
- **Statusy workflow:** Zamowienie (draft → verified → sent → partially_received → completed), ZapotrzebowanieTechnologa (draft → submitted → completed/cancelled)
