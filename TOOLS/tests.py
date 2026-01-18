# TOOLS/tests.py
"""
================================================================================
                        TESTY APLIKACJI CNCTOOLS
================================================================================

Plik zawiera testy jednostkowe i integracyjne dla aplikacji CNCTOOLS.

--------------------------------------------------------------------------------
                            URUCHAMIANIE TESTÓW
--------------------------------------------------------------------------------

1. WSZYSTKIE TESTY:
   python manage.py test TOOLS.tests

2. TESTY USTAWIEŃ (ustawienia.html):
   python manage.py test TOOLS.tests.UstawieniaTestCase
   python manage.py test TOOLS.tests.UstawieniaViewTestCase

3. TESTY MAGAZYNU (magazyn.html):
   python manage.py test TOOLS.tests.MagazynTestCase
   python manage.py test TOOLS.tests.MagazynViewTestCase

4. POJEDYNCZY TEST:
   python manage.py test TOOLS.tests.MagazynTestCase.test_historia_zwrot

5. Z POZIOMU DJANGO SHELL:
   python manage.py shell
   >>> from TOOLS.tests import run_all_tests, run_ustawienia_tests, run_magazyn_tests
   >>> run_all_tests()       # Wszystkie testy
   >>> run_ustawienia_tests() # Tylko ustawienia
   >>> run_magazyn_tests()    # Tylko magazyn

--------------------------------------------------------------------------------
                            OPCJE URUCHAMIANIA
--------------------------------------------------------------------------------

--verbosity=2    Szczegółowy output (domyślnie w run_* funkcjach)
--keepdb         Zachowaj testową bazę danych między uruchomieniami
--failfast       Zatrzymaj po pierwszym błędzie

Przykład:
   python manage.py test TOOLS.tests --verbosity=2 --failfast

--------------------------------------------------------------------------------
                            STRUKTURA TESTÓW
--------------------------------------------------------------------------------

UstawieniaTestCase:
    - Kategorie (CRUD)
    - Podkategorie (CRUD, walidacja)
    - Lokalizacje (CRUD, unikalność)
    - Maszyny (CRUD)
    - Dostawcy (CRUD)
    - Pracownicy (CRUD, unikalność karty)

MagazynTestCase:
    - Narzędzia magazynowe (CRUD, opakowania)
    - Egzemplarze narzędzi (CRUD, auto-jednostka)
    - Historia użycia (wydanie, zwrot, pracownik zwracający)
    - Liczniki stanów (nowe, używane, w użyciu, komplety)

================================================================================
"""
from django.test import TestCase, Client
from django.contrib.auth.models import User
from rest_framework.test import APITestCase
from rest_framework import status
from .models import (
    Kategoria, Podkategoria, Lokalizacja, Maszyna,
    Dostawca, Pracownik, NarzedzieMagazynowe, EgzemplarzNarzedzia,
    HistoriaUzyciaNarzedzia, FakturaZakupu
)


class UstawieniaTestCase(APITestCase):
    """Testy dla funkcjonalności Ustawień"""

    def setUp(self):
        """Przygotowanie danych testowych"""
        self.user = User.objects.create_user('test', 'test@test.pl', 'test123')
        self.client.force_authenticate(user=self.user)

        # Dane testowe
        self.kategoria = Kategoria.objects.create(nazwa="Frezy")
        self.dostawca = Dostawca.objects.create(
            kod_dostawcy="TEST01",
            nazwa_firmy="Test Sp. z o.o.",
            nip="1234567890"
        )

    # ========== TESTY KATEGORII ==========

    def test_kategoria_create(self):
        """Test dodawania kategorii"""
        data = {'nazwa': 'Wiertła'}
        response = self.client.post('/api/kategorie/', data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Kategoria.objects.count(), 2)

    def test_kategoria_list(self):
        """Test listowania kategorii"""
        response = self.client.get('/api/kategorie/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_kategoria_update(self):
        """Test edycji kategorii"""
        data = {'nazwa': 'Frezy CNC'}
        response = self.client.put(f'/api/kategorie/{self.kategoria.id}/', data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.kategoria.refresh_from_db()
        self.assertEqual(self.kategoria.nazwa, 'Frezy CNC')

    def test_kategoria_delete(self):
        """Test usuwania kategorii"""
        response = self.client.delete(f'/api/kategorie/{self.kategoria.id}/')
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Kategoria.objects.count(), 0)

    # ========== TESTY PODKATEGORII ==========

    def test_podkategoria_create(self):
        """Test dodawania podkategorii"""
        data = {
            'nazwa': 'VHM',
            'kategoria_id': self.kategoria.id
        }
        response = self.client.post('/api/podkategorie/', data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Podkategoria.objects.count(), 1)

        podkat = Podkategoria.objects.first()
        self.assertEqual(podkat.nazwa, 'VHM')
        self.assertEqual(podkat.kategoria, self.kategoria)

    def test_podkategoria_bez_kategorii(self):
        """Test dodawania podkategorii bez kategorii - powinno się nie udać"""
        data = {'nazwa': 'VHM'}
        response = self.client.post('/api/podkategorie/', data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_podkategoria_list(self):
        """Test listowania podkategorii"""
        Podkategoria.objects.create(nazwa='VHM', kategoria=self.kategoria)
        response = self.client.get('/api/podkategorie/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    # ========== TESTY LOKALIZACJI ==========

    def test_lokalizacja_create(self):
        """Test dodawania lokalizacji"""
        data = {
            'szafa': 'A',
            'kolumna': '01',
            'polka': '1'
        }
        response = self.client.post('/api/lokalizacje/', data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Lokalizacja.objects.count(), 1)

    def test_lokalizacja_unique(self):
        """Test unikalności lokalizacji"""
        Lokalizacja.objects.create(szafa='A', kolumna='01', polka='1')
        data = {'szafa': 'A', 'kolumna': '01', 'polka': '1'}
        response = self.client.post('/api/lokalizacje/', data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    # ========== TESTY MASZYN ==========

    def test_maszyna_create(self):
        """Test dodawania maszyny"""
        data = {'nazwa': 'DMU60'}
        response = self.client.post('/api/maszyny/', data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Maszyna.objects.count(), 1)

    # ========== TESTY DOSTAWCÓW ==========

    def test_dostawca_create(self):
        """Test dodawania dostawcy"""
        data = {
            'kod_dostawcy': 'SUPP01',
            'nazwa_firmy': 'Supplier Sp. z o.o.',
            'nip': '9876543210',
            'email': 'test@supplier.pl'
        }
        response = self.client.post('/api/dostawcy/', data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Dostawca.objects.count(), 2)

    def test_dostawca_update(self):
        """Test edycji dostawcy"""
        data = {
            'kod_dostawcy': 'TEST01',
            'nazwa_firmy': 'Test UPDATED',
            'nip': '1234567890'
        }
        response = self.client.put(f'/api/dostawcy/{self.dostawca.id}/', data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.dostawca.refresh_from_db()
        self.assertEqual(self.dostawca.nazwa_firmy, 'Test UPDATED')

    # ========== TESTY PRACOWNIKÓW ==========

    def test_pracownik_create(self):
        """Test dodawania pracownika"""
        data = {
            'karta': '12345',
            'nazwisko': 'Kowalski',
            'imie': 'Jan'
        }
        response = self.client.post('/api/pracownicy/', data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Pracownik.objects.count(), 1)

    def test_pracownik_unique_karta(self):
        """Test unikalności karty pracownika"""
        Pracownik.objects.create(karta='12345', nazwisko='Kowalski', imie='Jan')
        data = {'karta': '12345', 'nazwisko': 'Nowak', 'imie': 'Anna'}
        response = self.client.post('/api/pracownicy/', data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class UstawieniaViewTestCase(TestCase):
    """Testy dla widoku HTML ustawień"""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user('test', 'test@test.pl', 'test123')
        self.client.login(username='test', password='test123')

    def test_ustawienia_view_get(self):
        """Test dostępu do strony ustawień"""
        response = self.client.get('/ustawienia/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Ustawienia')


class MagazynTestCase(APITestCase):
    """Testy dla funkcjonalności Magazynu"""

    def setUp(self):
        """Przygotowanie danych testowych"""
        self.user = User.objects.create_user('test', 'test@test.pl', 'test123')
        self.client.force_authenticate(user=self.user)

        # Dane testowe
        self.kategoria = Kategoria.objects.create(nazwa="Frezy")
        self.podkategoria = Podkategoria.objects.create(
            nazwa="VHM",
            kategoria=self.kategoria
        )
        self.lokalizacja = Lokalizacja.objects.create(
            szafa="A",
            kolumna="01",
            polka="1"
        )
        self.maszyna = Maszyna.objects.create(nazwa="DMU60")
        self.pracownik = Pracownik.objects.create(
            karta="12345",
            nazwisko="Kowalski",
            imie="Jan"
        )
        self.pracownik2 = Pracownik.objects.create(
            karta="67890",
            nazwisko="Nowak",
            imie="Anna"
        )
        self.dostawca = Dostawca.objects.create(
            kod_dostawcy="TEST01",
            nazwa_firmy="Test Sp. z o.o."
        )
        self.narzedzie = NarzedzieMagazynowe.objects.create(
            podkategoria=self.podkategoria,
            opis="Frezwalcowy D10",
            numer_katalogowy="F10-VHM",
            opakowanie="szt",
            ilosc_w_opakowaniu=1
        )

    # ========== TESTY NARZĘDZI MAGAZYNOWYCH ==========

    def test_narzedzie_create(self):
        """Test dodawania narzędzia magazynowego"""
        data = {
            'podkategoria_id': self.podkategoria.id,
            'opis': 'Wiertło D5',
            'numer_katalogowy': 'W5-VHM',
            'opakowanie': 'szt',
            'ilosc_w_opakowaniu': 1,
            'stan_minimalny': 5,
            'stan_maksymalny': 20
        }
        response = self.client.post('/api/narzedzia/', data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(NarzedzieMagazynowe.objects.count(), 2)

    def test_narzedzie_list(self):
        """Test listowania narzędzi"""
        response = self.client.get('/api/narzedzia/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_narzedzie_update(self):
        """Test edycji narzędzia"""
        data = {
            'podkategoria_id': self.podkategoria.id,
            'opis': 'Frez walcowy D10 UPDATED',
            'numer_katalogowy': 'F10-VHM-NEW',
            'opakowanie': 'szt',
            'ilosc_w_opakowaniu': 1
        }
        response = self.client.put(f'/api/narzedzia/{self.narzedzie.id}/', data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.narzedzie.refresh_from_db()
        self.assertEqual(self.narzedzie.opis, 'Frez walcowy D10 UPDATED')

    def test_narzedzie_komplet(self):
        """Test dodawania narzędzia w opakowaniu komplet"""
        data = {
            'podkategoria_id': self.podkategoria.id,
            'opis': 'Płytki skrawające',
            'opakowanie': 'kompl',
            'ilosc_w_opakowaniu': 10
        }
        response = self.client.post('/api/narzedzia/', data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        narzedzie = NarzedzieMagazynowe.objects.get(opis='Płytki skrawające')
        self.assertEqual(narzedzie.opakowanie, 'kompl')
        self.assertEqual(narzedzie.ilosc_w_opakowaniu, 10)

    # ========== TESTY EGZEMPLARZY NARZĘDZI ==========

    def test_egzemplarz_create(self):
        """Test dodawania egzemplarza narzędzia"""
        data = {
            'narzedzie_typ_id': self.narzedzie.id,
            'stan': 'nowe',
            'lokalizacja_id': self.lokalizacja.id
        }
        response = self.client.post('/api/egzemplarze/', data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(EgzemplarzNarzedzia.objects.count(), 1)

    def test_egzemplarz_auto_jednostka(self):
        """Test automatycznego ustawienia jednostki na podstawie typu narzędzia"""
        data = {
            'narzedzie_typ_id': self.narzedzie.id,
            'stan': 'nowe'
        }
        response = self.client.post('/api/egzemplarze/', data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        egzemplarz = EgzemplarzNarzedzia.objects.first()
        self.assertEqual(egzemplarz.jednostka, self.narzedzie.opakowanie)
        self.assertEqual(egzemplarz.ilosc_w_komplecie, self.narzedzie.ilosc_w_opakowaniu)

    def test_egzemplarz_update_stan(self):
        """Test zmiany stanu egzemplarza"""
        egzemplarz = EgzemplarzNarzedzia.objects.create(
            narzedzie_typ=self.narzedzie,
            stan='nowe',
            lokalizacja=self.lokalizacja
        )
        data = {
            'narzedzie_typ_id': self.narzedzie.id,
            'stan': 'uzywane',
            'lokalizacja_id': self.lokalizacja.id
        }
        response = self.client.patch(f'/api/egzemplarze/{egzemplarz.id}/', data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        egzemplarz.refresh_from_db()
        self.assertEqual(egzemplarz.stan, 'uzywane')

    # ========== TESTY HISTORII UŻYCIA ==========

    def test_historia_wydanie(self):
        """Test wydania narzędzia pracownikowi"""
        egzemplarz = EgzemplarzNarzedzia.objects.create(
            narzedzie_typ=self.narzedzie,
            stan='nowe',
            lokalizacja=self.lokalizacja
        )
        data = {
            'egzemplarz_id': egzemplarz.id,
            'maszyna_id': self.maszyna.id,
            'pracownik_id': self.pracownik.id
        }
        response = self.client.post('/api/historia/wydanie/', data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(HistoriaUzyciaNarzedzia.objects.count(), 1)

        historia = HistoriaUzyciaNarzedzia.objects.first()
        self.assertEqual(historia.egzemplarz, egzemplarz)
        self.assertEqual(historia.pracownik, self.pracownik)
        self.assertIsNone(historia.data_zwrotu)

    def test_historia_zwrot(self):
        """Test zwrotu narzędzia"""
        egzemplarz = EgzemplarzNarzedzia.objects.create(
            narzedzie_typ=self.narzedzie,
            stan='nowe',
            lokalizacja=self.lokalizacja
        )
        historia = HistoriaUzyciaNarzedzia.objects.create(
            egzemplarz=egzemplarz,
            maszyna=self.maszyna,
            pracownik=self.pracownik
        )

        data = {
            'stan_po_zwrocie': 'uzywane',
            'pracownik_zwracajacy_id': self.pracownik.id
        }
        response = self.client.post(f'/api/historia/{historia.id}/zwrot/', data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        historia.refresh_from_db()
        self.assertIsNotNone(historia.data_zwrotu)
        self.assertEqual(historia.pracownik_zwracajacy, self.pracownik)

        egzemplarz.refresh_from_db()
        self.assertEqual(egzemplarz.stan, 'uzywane')

    def test_historia_zwrot_inny_pracownik(self):
        """Test zwrotu narzędzia przez innego pracownika"""
        egzemplarz = EgzemplarzNarzedzia.objects.create(
            narzedzie_typ=self.narzedzie,
            stan='nowe',
            lokalizacja=self.lokalizacja
        )
        historia = HistoriaUzyciaNarzedzia.objects.create(
            egzemplarz=egzemplarz,
            maszyna=self.maszyna,
            pracownik=self.pracownik  # Pobiera pracownik1
        )

        data = {
            'stan_po_zwrocie': 'uzywane',
            'pracownik_zwracajacy_id': self.pracownik2.id  # Zwraca pracownik2
        }
        response = self.client.post(f'/api/historia/{historia.id}/zwrot/', data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        historia.refresh_from_db()
        self.assertEqual(historia.pracownik, self.pracownik)  # Pobierający
        self.assertEqual(historia.pracownik_zwracajacy, self.pracownik2)  # Zwracający

    def test_historia_zwrot_uszkodzone(self):
        """Test zwrotu narzędzia w stanie uszkodzonym"""
        egzemplarz = EgzemplarzNarzedzia.objects.create(
            narzedzie_typ=self.narzedzie,
            stan='nowe',
            lokalizacja=self.lokalizacja
        )
        historia = HistoriaUzyciaNarzedzia.objects.create(
            egzemplarz=egzemplarz,
            maszyna=self.maszyna,
            pracownik=self.pracownik
        )

        data = {
            'stan_po_zwrocie': 'uszkodzone',
            'pracownik_zwracajacy_id': self.pracownik.id
        }
        response = self.client.post(f'/api/historia/{historia.id}/zwrot/', data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        egzemplarz.refresh_from_db()
        self.assertEqual(egzemplarz.stan, 'uszkodzone')

    def test_historia_w_uzyciu_list(self):
        """Test listowania narzędzi w użyciu"""
        egzemplarz = EgzemplarzNarzedzia.objects.create(
            narzedzie_typ=self.narzedzie,
            stan='nowe',
            lokalizacja=self.lokalizacja
        )
        HistoriaUzyciaNarzedzia.objects.create(
            egzemplarz=egzemplarz,
            maszyna=self.maszyna,
            pracownik=self.pracownik
        )

        response = self.client.get('/api/historia/?w_uzyciu=true')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Obsługa z paginacją lub bez
        if isinstance(response.data, dict) and 'results' in response.data:
            self.assertEqual(len(response.data['results']), 1)
        else:
            self.assertEqual(len(response.data), 1)

    # ========== TESTY LICZNIKÓW STANÓW ==========

    def test_licznik_nowe(self):
        """Test licznika narzędzi nowych"""
        # Dodaj 3 egzemplarze nowe (sztuki)
        for i in range(3):
            EgzemplarzNarzedzia.objects.create(
                narzedzie_typ=self.narzedzie,
                stan='nowe',
                lokalizacja=self.lokalizacja
            )

        response = self.client.get(f'/api/narzedzia/{self.narzedzie.id}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['ilosc_nowych'], 3)

    def test_licznik_komplety(self):
        """Test licznika dla narzędzi w kompletach"""
        # Narzędzie w kompletach po 10 szt
        narzedzie_kompl = NarzedzieMagazynowe.objects.create(
            podkategoria=self.podkategoria,
            opis="Płytki",
            opakowanie='kompl',
            ilosc_w_opakowaniu=10
        )

        # Dodaj 2 komplety nowe (2x10=20 szt) - przez API aby automatycznie ustawić ilosc_w_komplecie
        for i in range(2):
            data = {
                'narzedzie_typ_id': narzedzie_kompl.id,
                'stan': 'nowe'
            }
            self.client.post('/api/egzemplarze/', data)

        response = self.client.get(f'/api/narzedzia/{narzedzie_kompl.id}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['ilosc_nowych'], 20)  # 2 komplety x 10 szt

    def test_licznik_w_uzyciu(self):
        """Test licznika narzędzi w użyciu"""
        egzemplarz = EgzemplarzNarzedzia.objects.create(
            narzedzie_typ=self.narzedzie,
            stan='nowe',
            lokalizacja=self.lokalizacja
        )
        HistoriaUzyciaNarzedzia.objects.create(
            egzemplarz=egzemplarz,
            maszyna=self.maszyna,
            pracownik=self.pracownik
        )

        response = self.client.get(f'/api/narzedzia/{self.narzedzie.id}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['ilosc_w_uzyciu'], 1)


class MagazynViewTestCase(TestCase):
    """Testy dla widoku HTML magazynu"""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user('test', 'test@test.pl', 'test123')
        self.client.login(username='test', password='test123')

    def test_magazyn_view_get(self):
        """Test dostępu do strony magazynu"""
        response = self.client.get('/magazyn/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Magazyn')


# ========== RUNNER ==========

def run_ustawienia_tests():
    """Funkcja do ręcznego uruchomienia testów"""
    from django.test.utils import get_runner
    from django.conf import settings

    TestRunner = get_runner(settings)
    test_runner = TestRunner(verbosity=2, interactive=False, keepdb=True)

    failures = test_runner.run_tests(['TOOLS.tests.UstawieniaTestCase'])

    if failures:
        print(f"\n❌ {failures} testów nie przeszło!")
    else:
        print("\n✅ Wszystkie testy przeszły pomyślnie!")

    return failures


def run_magazyn_tests():
    """Funkcja do ręcznego uruchomienia testów magazynu"""
    from django.test.utils import get_runner
    from django.conf import settings

    TestRunner = get_runner(settings)
    test_runner = TestRunner(verbosity=2, interactive=False, keepdb=True)

    failures = test_runner.run_tests(['TOOLS.tests.MagazynTestCase'])

    if failures:
        print(f"\n❌ {failures} testów nie przeszło!")
    else:
        print("\n✅ Wszystkie testy magazynu przeszły pomyślnie!")

    return failures


def run_all_tests():
    """Funkcja do uruchomienia wszystkich testów"""
    from django.test.utils import get_runner
    from django.conf import settings

    TestRunner = get_runner(settings)
    test_runner = TestRunner(verbosity=2, interactive=False, keepdb=True)

    failures = test_runner.run_tests(['TOOLS.tests'])

    if failures:
        print(f"\n❌ {failures} testów nie przeszło!")
    else:
        print("\n✅ Wszystkie testy przeszły pomyślnie!")

    return failures