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
from unittest import mock

from django.test import TestCase, Client
from django.db import IntegrityError
from django.utils import timezone
from django.contrib.auth.models import User
from rest_framework.test import APITestCase
from rest_framework import status
from .models import (
    Kategoria, Podkategoria, Lokalizacja, Maszyna,
    Dostawca, Pracownik, NarzedzieMagazynowe, EgzemplarzNarzedzia,
    HistoriaUzyciaNarzedzia, FakturaZakupu, PozycjaGeneratora,
    Zamowienie, PozycjaZamowienia, ZapotrzebowanieTechnologa,
    PozycjaZapotrzebowania, Uszkodzenie
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

    def test_pracownik_karta_reuse_dla_legacy_bez_konta(self):
        """Karta zwolniona do reuse gdy istniejący pracownik nie ma konta usera.

        Unikalność karty wymuszana jest tylko wśród aktywnych kont (user.is_active=True)
        w ZespolSerializer — pracownicy legacy bez user-a nie blokują reuse karty.
        """
        Pracownik.objects.create(karta='12345', nazwisko='Kowalski', imie='Jan')
        data = {'karta': '12345', 'nazwisko': 'Nowak', 'imie': 'Anna'}
        response = self.client.post('/api/pracownicy/', data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Pracownik.objects.filter(karta='12345').count(), 2)


class ZespolKartaTestCase(APITestCase):
    """Testy logiki is_active + reuse karty (ZespolSerializer + login_by_card)."""

    def setUp(self):
        self.admin = User.objects.create_superuser('admin', 'a@a.pl', 'admin123')
        self.client.force_authenticate(user=self.admin)

    def _create_user_with_karta(self, username, karta, is_active=True):
        """Helper: tworzy User + Pracownika z kartą bezpośrednio (omijając ACL)."""
        user = User.objects.create_user(
            username=username, password='pass1234', first_name='Test', last_name=username,
            is_active=is_active,
        )
        Pracownik.objects.create(user=user, imie='Test', nazwisko=username, karta=karta)
        return user

    # ========== ZespolSerializer ==========

    def test_zespol_duplikat_karty_aktywnych_blokowany(self):
        """Próba przypisania karty zajętej przez AKTYWNEGO usera → 400."""
        self._create_user_with_karta('jan', '1111111111', is_active=True)
        payload = {
            'username': 'anna', 'first_name': 'Anna', 'last_name': 'Nowak',
            'password': 'pass1234', 'karta': '1111111111',
            'group_ids': [], 'is_active': True,
        }
        response = self.client.post('/api/zespol/', payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('karta', response.data)

    def test_zespol_duplikat_karty_gdy_stary_nieaktywny_dozwolony(self):
        """Karta zajęta przez NIEAKTYWNEGO usera → nowy aktywny może ją przejąć (201)."""
        self._create_user_with_karta('jan_stary', '2222222222', is_active=False)
        payload = {
            'username': 'jan_nowy', 'first_name': 'Jan', 'last_name': 'Nowy',
            'password': 'pass1234', 'karta': '2222222222',
            'group_ids': [], 'is_active': True,
        }
        response = self.client.post('/api/zespol/', payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Pracownik.objects.filter(karta='2222222222').count(), 2)

    # ========== login_by_card ==========

    def test_login_by_card_nieaktywny_user_404(self):
        """Logowanie kartą przypisaną tylko do nieaktywnego usera → 404."""
        self._create_user_with_karta('zwolniony', '3333333333', is_active=False)
        self.client.logout()
        response = self.client.post(
            '/api/login-card/', {'card_number': '3333333333'}, format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_login_by_card_aktywny_wygrywa_z_nieaktywnym(self):
        """Stary nieaktywny + nowy aktywny z tą samą kartą → loguje aktywnego (200)."""
        self._create_user_with_karta('stary', '4444444444', is_active=False)
        nowy = self._create_user_with_karta('nowy', '4444444444', is_active=True)
        self.client.logout()
        response = self.client.post(
            '/api/login-card/', {'card_number': '4444444444'}, format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.json().get('success'))
        self.assertEqual(response.json()['user']['username'], nowy.username)


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


class GeneratorZamowienTestCase(APITestCase):
    """
    Testy pokrywające trzy bugi generatora zamówień zgłoszone przez grupę Logistyk:

    BUG#1: Generator tworzył pozycje dla narzędzi ze stan_maksymalny=0 (magia 10).
    BUG#2: Po usunięciu pozycji nie wracała przy kolejnym generowaniu.
    BUG#3: Pozycje zapotrzebowań technologa bez powiązanego narzędzia nie dało się
           przypisać/odrzucić z poziomu generatora.
    """

    def setUp(self):
        self.user = User.objects.create_user('logistyk', 'log@test.pl', 'haslo123')
        self.client.force_authenticate(user=self.user)

        # Pin trybu liczenia: testy tej klasy zakładają tryb standardowy — uniezależnienie
        # od wartości 'sposob_liczenia_zamowien' w app_settings.json maszyny deweloperskiej
        patcher = mock.patch('TOOLS.views.get_sposob_liczenia_zamowien', return_value='standardowa')
        patcher.start()
        self.addCleanup(patcher.stop)

        self.kategoria = Kategoria.objects.create(nazwa="Frezy")
        self.podkategoria = Podkategoria.objects.create(
            nazwa="VHM", kategoria=self.kategoria
        )
        self.lokalizacja = Lokalizacja.objects.create(szafa="A", kolumna="01", polka="1")
        self.dostawca = Dostawca.objects.create(
            kod_dostawcy="TEST01", nazwa_firmy="Test Sp. z o.o."
        )

        # Narzędzie A: limit_min=0, limit_max=0 (nic nie zamawiaj automatycznie)
        self.narzedzie_bez_limitow = NarzedzieMagazynowe.objects.create(
            podkategoria=self.podkategoria,
            opis="Frez bez limitów",
            numer_katalogowy="NO-LIMIT",
            opakowanie="szt",
            ilosc_w_opakowaniu=1,
            stan_minimalny=0,
            stan_maksymalny=0,
            ostatni_dostawca=self.dostawca,
        )

        # Narzędzie B: limit_max=20, stan=0 → brakuje 20 szt.
        self.narzedzie_z_limitami = NarzedzieMagazynowe.objects.create(
            podkategoria=self.podkategoria,
            opis="Frez z limitami",
            numer_katalogowy="WITH-LIMIT",
            opakowanie="szt",
            ilosc_w_opakowaniu=1,
            stan_minimalny=5,
            stan_maksymalny=20,
            ostatni_dostawca=self.dostawca,
        )

        # Dla narzędzia B nie tworzymy egzemplarzy → stan_aktualny=0, limit=20

    # ========================================================================
    # BUG #1: stan_maksymalny=0 → narzędzie pomijane
    # ========================================================================

    def test_bug1_narzedzie_bez_limitow_nie_trafia_do_generatora(self):
        """
        REGRESJA BUG#1: narzędzie z limit_max=0 NIE może trafić do generatora.
        Wcześniejszy kod stosował magiczną wartość 10 i generował pozycję.
        """
        response = self.client.get('/api/generator-zamowien/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        pozycje = response.data.get('pozycje', [])
        ids_w_generatorze = [p['id'] for p in pozycje]
        self.assertNotIn(
            self.narzedzie_bez_limitow.id,
            ids_w_generatorze,
            "Narzędzie z stan_maksymalny=0 NIE powinno być w generatorze"
        )

    def test_bug1_narzedzie_z_limitem_trafia_z_prawidlowa_iloscia(self):
        """
        Kontrola: narzędzie z stan_maksymalny=20 i stan=0 ma trafić z iloscia=20.
        """
        response = self.client.get('/api/generator-zamowien/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        pozycje = response.data.get('pozycje', [])
        moja = next((p for p in pozycje if p['id'] == self.narzedzie_z_limitami.id), None)
        self.assertIsNotNone(moja, "Narzędzie z limitem powinno być w generatorze")
        self.assertEqual(moja['ilosc_do_zamowienia'], 20)

    def test_bug1_narzedzie_z_stanem_rownym_limitowi_nie_trafia(self):
        """
        Narzędzie gdzie stan == limit_max nie powinno trafić (granicznie).
        """
        # Dodaj 20 egzemplarzy nowych
        for _ in range(20):
            EgzemplarzNarzedzia.objects.create(
                narzedzie_typ=self.narzedzie_z_limitami,
                stan='nowe',
                lokalizacja=self.lokalizacja
            )

        response = self.client.get('/api/generator-zamowien/')
        pozycje = response.data.get('pozycje', [])
        ids = [p['id'] for p in pozycje]
        self.assertNotIn(self.narzedzie_z_limitami.id, ids)

    # ========================================================================
    # BUG #2: DELETE nie może psuć stan_maksymalny ani blokować powrotu pozycji
    # ========================================================================

    def test_bug2_delete_nie_modyfikuje_stan_maksymalny(self):
        """
        REGRESJA BUG#2: DELETE pozycji z generatora nie może zmieniać stan_maksymalny
        narzędzia (wcześniej ustawiało go = aktualnemu stanowi, co blokowało powrót).
        """
        # Najpierw utwórz pozycję w generatorze
        self.client.get('/api/generator-zamowien/')
        self.assertTrue(
            PozycjaGeneratora.objects.filter(narzedzie_typ=self.narzedzie_z_limitami).exists()
        )

        stan_max_przed = self.narzedzie_z_limitami.stan_maksymalny

        # Usuń z generatora
        response = self.client.delete(
            f'/api/generator-zamowien/{self.narzedzie_z_limitami.id}/delete/'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.narzedzie_z_limitami.refresh_from_db()
        self.assertEqual(
            self.narzedzie_z_limitami.stan_maksymalny,
            stan_max_przed,
            "DELETE nie powinien modyfikować stan_maksymalny"
        )

    def test_bug2_pozycja_wraca_po_usunieciu_i_ponownym_generowaniu(self):
        """
        REGRESJA BUG#2: po DELETE kolejny GET musi ponownie dodać pozycję
        (bo stan_aktualny < stan_maksymalny nadal spełnia warunek).
        """
        # Pierwszy GET → pozycja powstaje
        self.client.get('/api/generator-zamowien/')
        self.assertTrue(
            PozycjaGeneratora.objects.filter(narzedzie_typ=self.narzedzie_z_limitami).exists()
        )

        # DELETE
        self.client.delete(
            f'/api/generator-zamowien/{self.narzedzie_z_limitami.id}/delete/'
        )
        self.assertFalse(
            PozycjaGeneratora.objects.filter(narzedzie_typ=self.narzedzie_z_limitami).exists()
        )

        # Drugi GET → pozycja wraca
        response = self.client.get('/api/generator-zamowien/')
        pozycje = response.data.get('pozycje', [])
        ids = [p['id'] for p in pozycje]
        self.assertIn(
            self.narzedzie_z_limitami.id, ids,
            "Po DELETE pozycja powinna wrócić przy kolejnym GET"
        )

    def test_bug2_delete_resetuje_w_zamowieniu_na_zapotrzebowaniu(self):
        """
        REGRESJA BUG#2: pozycja pochodząca z zapotrzebowania, po usunięciu z generatora,
        musi mieć cofniętą flagę w_zamowieniu, żeby mogła wrócić.
        """
        # Stwórz narzędzie powiązane z zapotrzebowaniem
        narzedzie = NarzedzieMagazynowe.objects.create(
            podkategoria=self.podkategoria,
            opis="Frez zapotrzebowanie",
            opakowanie="szt",
            stan_minimalny=0,
            stan_maksymalny=0,  # celowo 0, żeby TYLKO zapotrzebowanie go napędzało
        )
        zap = ZapotrzebowanieTechnologa.objects.create(
            technolog=self.user, status='completed'
        )
        pozycja_zap = PozycjaZapotrzebowania.objects.create(
            zapotrzebowanie=zap,
            narzedzie_typ=narzedzie,
            ilosc=5,
        )

        # GET generator → wykryje zapotrzebowanie i doda pozycję
        self.client.get('/api/generator-zamowien/')
        self.assertTrue(
            PozycjaGeneratora.objects.filter(narzedzie_typ=narzedzie).exists()
        )
        pozycja_zap.refresh_from_db()
        self.assertTrue(pozycja_zap.w_zamowieniu)

        # DELETE z generatora
        self.client.delete(f'/api/generator-zamowien/{narzedzie.id}/delete/')

        pozycja_zap.refresh_from_db()
        self.assertFalse(
            pozycja_zap.w_zamowieniu,
            "DELETE powinien cofnąć flagę w_zamowieniu na PozycjaZapotrzebowania"
        )

        # Drugi GET → pozycja wraca z zapotrzebowania
        response = self.client.get('/api/generator-zamowien/')
        ids = [p['id'] for p in response.data.get('pozycje', [])]
        self.assertIn(narzedzie.id, ids)

    # ========================================================================
    # Masowe usuwanie pozycji generatora (bulk-delete)
    # ========================================================================

    def _narzedzie_z_limitami(self, opis):
        return NarzedzieMagazynowe.objects.create(
            podkategoria=self.podkategoria, opis=opis, opakowanie="szt",
            ilosc_w_opakowaniu=1, stan_minimalny=5, stan_maksymalny=20,
            ostatni_dostawca=self.dostawca,
        )

    def test_bulk_delete_usuwa_zaznaczone_zostawia_reszte(self):
        n1 = self.narzedzie_z_limitami
        n2 = self._narzedzie_z_limitami("Frez 2")
        n3 = self._narzedzie_z_limitami("Frez 3")  # ma zostać
        self.client.get('/api/generator-zamowien/')  # populate PozycjaGeneratora
        for n in (n1, n2, n3):
            self.assertTrue(PozycjaGeneratora.objects.filter(narzedzie_typ=n).exists())

        resp = self.client.post(
            '/api/generator-zamowien/bulk-delete/',
            {'narzedzie_ids': [n1.id, n2.id]}, format='json'
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data['usunieto'], 2)
        self.assertFalse(PozycjaGeneratora.objects.filter(narzedzie_typ=n1).exists())
        self.assertFalse(PozycjaGeneratora.objects.filter(narzedzie_typ=n2).exists())
        self.assertTrue(PozycjaGeneratora.objects.filter(narzedzie_typ=n3).exists())

    def test_bulk_delete_resetuje_w_zamowieniu(self):
        narzedzie = NarzedzieMagazynowe.objects.create(
            podkategoria=self.podkategoria, opis="Frez zap", opakowanie="szt",
            stan_minimalny=0, stan_maksymalny=0,  # tylko zapotrzebowanie go napędza
        )
        zap = ZapotrzebowanieTechnologa.objects.create(technolog=self.user, status='completed')
        pozycja_zap = PozycjaZapotrzebowania.objects.create(
            zapotrzebowanie=zap, narzedzie_typ=narzedzie, ilosc=5,
        )
        self.client.get('/api/generator-zamowien/')
        pozycja_zap.refresh_from_db()
        self.assertTrue(pozycja_zap.w_zamowieniu)

        resp = self.client.post(
            '/api/generator-zamowien/bulk-delete/',
            {'narzedzie_ids': [narzedzie.id]}, format='json'
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        pozycja_zap.refresh_from_db()
        self.assertFalse(pozycja_zap.w_zamowieniu)

    def test_bulk_delete_pusta_lista_zwraca_400(self):
        resp = self.client.post(
            '/api/generator-zamowien/bulk-delete/', {'narzedzie_ids': []}, format='json'
        )
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    # ========================================================================
    # BUG #3: nieprzypisane pozycje zapotrzebowania — assign/reject
    # ========================================================================

    def _stworz_nieprzypisane_zapotrzebowanie(self, specyfikacja="prowadnice fi 25"):
        """Helper: zapotrzebowanie completed z jedną pozycją bez narzedzie_typ."""
        technolog = User.objects.create_user('zenia', 'z@test.pl', 'pwd')
        zap = ZapotrzebowanieTechnologa.objects.create(
            technolog=technolog, status='completed'
        )
        poz = PozycjaZapotrzebowania.objects.create(
            zapotrzebowanie=zap,
            narzedzie_typ=None,
            specyfikacja=specyfikacja,
            kategoria_nazwa="Prowadnice",
            ilosc=2,
        )
        return zap, poz

    def test_bug3_nieprzypisana_pozycja_pojawia_sie_w_panelu(self):
        """Pozycja zapotrzebowania bez narzedzie_typ trafia do listy nieprzypisanych."""
        _, poz = self._stworz_nieprzypisane_zapotrzebowanie()

        response = self.client.get('/api/generator-zamowien/')
        nieprzypisane = response.data.get('nieprzypisane', [])
        ids = [n['id'] for n in nieprzypisane]
        self.assertIn(poz.id, ids)

    def test_bug3_przypisz_narzedzie_do_pozycji(self):
        """
        REGRESJA BUG#3: endpoint przypisz-pozycje ustawia narzedzie_typ i odblokowuje
        pozycję (w_zamowieniu=False), żeby generator ją podjął.
        """
        _, poz = self._stworz_nieprzypisane_zapotrzebowanie()

        # Utwórz narzędzie do przypisania (z limit_max, aby także potem wystąpiło w generatorze)
        narzedzie = NarzedzieMagazynowe.objects.create(
            podkategoria=self.podkategoria,
            opis="Prowadnica fi 25",
            opakowanie="szt",
            stan_minimalny=0,
            stan_maksymalny=0,
        )

        response = self.client.post(
            f'/api/generator-zamowien/przypisz-pozycje/{poz.id}/',
            {'narzedzie_id': narzedzie.id},
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        poz.refresh_from_db()
        self.assertEqual(poz.narzedzie_typ_id, narzedzie.id)
        self.assertFalse(poz.w_zamowieniu)

        # Po odświeżeniu generatora pozycja powinna się tam pojawić
        response = self.client.get('/api/generator-zamowien/')
        ids = [p['id'] for p in response.data.get('pozycje', [])]
        self.assertIn(narzedzie.id, ids)

        # I już nie powinna być na liście nieprzypisanych
        nieprzypisane_ids = [n['id'] for n in response.data.get('nieprzypisane', [])]
        self.assertNotIn(poz.id, nieprzypisane_ids)

    def test_bug3_przypisz_wymaga_narzedzie_id(self):
        """Bez pola narzedzie_id endpoint ma zwrócić 400."""
        _, poz = self._stworz_nieprzypisane_zapotrzebowanie()
        response = self.client.post(
            f'/api/generator-zamowien/przypisz-pozycje/{poz.id}/',
            {},
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_bug3_odrzuc_nieprzypisana_pozycja(self):
        """
        REGRESJA BUG#3: DELETE /odrzuc-pozycje/ znika pozycję z listy nieprzypisanych
        (flaga w_zamowieniu=True), nie tworząc pozycji w generatorze.
        """
        _, poz = self._stworz_nieprzypisane_zapotrzebowanie()

        response = self.client.delete(
            f'/api/generator-zamowien/odrzuc-pozycje/{poz.id}/'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        poz.refresh_from_db()
        self.assertTrue(poz.w_zamowieniu)

        response = self.client.get('/api/generator-zamowien/')
        nieprzypisane_ids = [n['id'] for n in response.data.get('nieprzypisane', [])]
        self.assertNotIn(poz.id, nieprzypisane_ids)

    def test_bug3_mix_pozycji_z_narzedziem_i_bez_narzedzia(self):
        """
        REGRESJA: zapotrzebowanie zawierające JEDNOCZEŚNIE pozycję z narzędziem
        i pozycję bez narzędzia (np. INNE/INNE spec='TEST'). Po uruchomieniu
        generatora:
          - pozycja z narzędziem idzie do głównej listy,
          - pozycja BEZ narzędzia idzie do panelu nieprzypisane,
          - zapotrzebowanie pozostaje w statusie 'completed' (NIE 'ordered'),
            dopóki logistyk nie rozwiąże pozycji nieprzypisanej.
        """
        technolog = User.objects.create_user('zenia2', 'z2@test.pl', 'pwd')
        zap = ZapotrzebowanieTechnologa.objects.create(
            technolog=technolog, status='completed'
        )
        # Pozycja z narzędziem (już istniejącym w bazie)
        narzedzie = NarzedzieMagazynowe.objects.create(
            podkategoria=self.podkategoria,
            opis="Frez zwykły",
            opakowanie="szt",
            stan_minimalny=0,
            stan_maksymalny=0,
        )
        PozycjaZapotrzebowania.objects.create(
            zapotrzebowanie=zap,
            narzedzie_typ=narzedzie,
            ilosc=3,
        )
        # Pozycja bez narzędzia (nowe narzędzie opisane przez technologa)
        pozycja_bez = PozycjaZapotrzebowania.objects.create(
            zapotrzebowanie=zap,
            narzedzie_typ=None,
            specyfikacja="TEST",
            kategoria_nazwa="INNE",
            podkategoria_nazwa="INNE",
            ilosc=1,
        )

        response = self.client.get('/api/generator-zamowien/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Pozycja z narzędziem — w głównej liście
        ids_glowne = [p['id'] for p in response.data.get('pozycje', [])]
        self.assertIn(narzedzie.id, ids_glowne)

        # Pozycja bez narzędzia — w panelu nieprzypisane
        ids_nieprzypisane = [n['id'] for n in response.data.get('nieprzypisane', [])]
        self.assertIn(pozycja_bez.id, ids_nieprzypisane)

        # Zapotrzebowanie MUSI pozostać 'completed' — pozycja bez narzędzia nadal czeka
        zap.refresh_from_db()
        self.assertEqual(
            zap.status, 'completed',
            "Status zapotrzebowania nie może być 'ordered' dopóki pozycje bez narzędzia czekają"
        )

    def test_bug3_odrzucenie_wszystkich_pozycji_zmienia_status_na_ordered(self):
        """
        Jeśli WSZYSTKIE pozycje zapotrzebowania zostały przetworzone (w_zamowieniu=True),
        status zapotrzebowania ma zmienić się na 'ordered'.
        """
        zap, poz = self._stworz_nieprzypisane_zapotrzebowanie()

        self.client.delete(f'/api/generator-zamowien/odrzuc-pozycje/{poz.id}/')

        zap.refresh_from_db()
        self.assertEqual(zap.status, 'ordered')


class GeneratorWedlugNowychTestCase(APITestCase):
    """
    Testy trybu 'według nowych elementów' (Ustawienia → Inne → Sposób liczenia zamówień).

    Reguła AUTO w tym trybie (PRZEDZIAŁOWA min/max po ilości nowych):
        ilość_nowych = nowe, nieuszkodzone, niewydane (suma ilosc_w_komplecie)
        stan_minimalny=0 → narzędzie wyłączone z auto-zamawiania
        stan_maksymalny=0 → brak celu uzupełnienia → pomiń
        brakuje = stan_maksymalny − ilość_nowych
        brakuje > 0  → pozycja na 'brakuje' (uzupełnienie do MAX, także w przedziale min–max)
        brakuje <= 0 → stan pełny, pomiń
    Wiersze z ręczną kontrolą liczą się jak dotychczas.
    """

    def setUp(self):
        self.user = User.objects.create_user('logistyk2', 'log2@test.pl', 'haslo123')
        self.client.force_authenticate(user=self.user)

        # Wymuszenie trybu "według nowych elementów" niezależnie od app_settings.json
        patcher = mock.patch(
            'TOOLS.views.get_sposob_liczenia_zamowien',
            return_value='wedlug_nowych_elementow'
        )
        self.mock_sposob = patcher.start()
        self.addCleanup(patcher.stop)

        self.kategoria = Kategoria.objects.create(nazwa="Wiertła")
        self.podkategoria = Podkategoria.objects.create(nazwa="HSS", kategoria=self.kategoria)
        self.lokalizacja = Lokalizacja.objects.create(szafa="B", kolumna="02", polka="2")
        self.dostawca = Dostawca.objects.create(kod_dostawcy="TEST02", nazwa_firmy="Test2 Sp. z o.o.")
        self.pracownik = Pracownik.objects.create(karta="11111", nazwisko="Testowy", imie="Jan")

        # Narzędzie AUTO: limit_min=5, limit_max=20
        self.narzedzie = NarzedzieMagazynowe.objects.create(
            podkategoria=self.podkategoria,
            opis="Wiertło 8mm",
            numer_katalogowy="W-8",
            opakowanie="szt",
            ilosc_w_opakowaniu=1,
            stan_minimalny=5,
            stan_maksymalny=20,
            ostatni_dostawca=self.dostawca,
        )

    def _pozycja(self, narzedzie=None):
        """Zwraca pozycję generatora dla narzędzia (lub None)."""
        narzedzie = narzedzie or self.narzedzie
        response = self.client.get('/api/generator-zamowien/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        pozycje = response.data.get('pozycje', [])
        return next((p for p in pozycje if p['id'] == narzedzie.id), None)

    def _dodaj_egzemplarze(self, ile, stan='nowe', ilosc_w_komplecie=1, narzedzie=None):
        narzedzie = narzedzie or self.narzedzie
        return [
            EgzemplarzNarzedzia.objects.create(
                narzedzie_typ=narzedzie,
                stan=stan,
                lokalizacja=self.lokalizacja,
                ilosc_w_komplecie=ilosc_w_komplecie,
            )
            for _ in range(ile)
        ]

    # ========== Reguła przedziałowa: brakuje = max − nowe ==========

    def test_brak_nowych_zamawia_do_limitu_maksymalnego(self):
        """0 nowych, max=20 → pozycja na 20 (uzupełnienie do MAX)."""
        pozycja = self._pozycja()
        self.assertIsNotNone(pozycja)
        self.assertEqual(pozycja['ilosc_do_zamowienia'], 20)
        self.assertEqual(pozycja['zrodlo'], 'auto')

    def test_czesciowy_brak_zamawia_roznice_do_max(self):
        """2 nowe, max=20 → pozycja na 18."""
        self._dodaj_egzemplarze(2)
        pozycja = self._pozycja()
        self.assertIsNotNone(pozycja)
        self.assertEqual(pozycja['ilosc_do_zamowienia'], 18)

    def test_nowych_na_dolnej_granicy_zamawia_do_max(self):
        """5 nowych (= limit_min), max=20 → pozycja na 15 (w przedziale min–max → do max)."""
        self._dodaj_egzemplarze(5)
        pozycja = self._pozycja()
        self.assertIsNotNone(pozycja)
        self.assertEqual(pozycja['ilosc_do_zamowienia'], 15)

    def test_nowych_w_przedziale_zamawia_do_max(self):
        """12 nowych (przedział min–max), max=20 → pozycja na 8."""
        self._dodaj_egzemplarze(12)
        pozycja = self._pozycja()
        self.assertIsNotNone(pozycja)
        self.assertEqual(pozycja['ilosc_do_zamowienia'], 8)

    def test_nowych_tuz_pod_max_zamawia_pojedynczo(self):
        """19 nowych, max=20 → pozycja na 1 (akceptowana konsekwencja reguły max→max)."""
        self._dodaj_egzemplarze(19)
        pozycja = self._pozycja()
        self.assertIsNotNone(pozycja)
        self.assertEqual(pozycja['ilosc_do_zamowienia'], 1)

    def test_nowych_rowne_max_nie_zamawia(self):
        """20 nowych (= max) → różnica 0 → brak pozycji (warunek graniczny, stan pełny)."""
        self._dodaj_egzemplarze(20)
        self.assertIsNone(self._pozycja())

    def test_nowych_powyzej_max_nie_zamawia(self):
        """21 nowych, max=20 → brak pozycji."""
        self._dodaj_egzemplarze(21)
        self.assertIsNone(self._pozycja())

    def test_komplet_liczy_sie_jako_ilosc_w_komplecie(self):
        """1 egzemplarz z ilosc_w_komplecie=20 = 20 nowych szt. (= max) → brak pozycji."""
        self._dodaj_egzemplarze(1, ilosc_w_komplecie=20)
        self.assertIsNone(self._pozycja())

    # ========== Co NIE liczy się jako "nowe" ==========

    def test_uzywane_nie_licza_sie_do_nowych(self):
        """10 używanych, 0 nowych, max=20 → pozycja na 20
        (używane nie wliczają się — liczy się tylko stan nowych)."""
        self._dodaj_egzemplarze(10, stan='uzywane')
        pozycja = self._pozycja()
        self.assertIsNotNone(pozycja)
        self.assertEqual(pozycja['ilosc_do_zamowienia'], 20)

    def test_wydane_nowe_nie_licza_sie(self):
        """5 nowych, ale 3 wydane (aktywne wypożyczenie) → nowych=2 → pozycja na 18."""
        egzemplarze = self._dodaj_egzemplarze(5)
        for egz in egzemplarze[:3]:
            HistoriaUzyciaNarzedzia.objects.create(
                egzemplarz=egz, pracownik=self.pracownik, data_zwrotu=None
            )
        pozycja = self._pozycja()
        self.assertIsNotNone(pozycja)
        self.assertEqual(pozycja['ilosc_do_zamowienia'], 18)

    def test_uszkodzone_nie_licza_sie_do_nowych(self):
        """3 nowe + 4 uszkodzone, max=20 → nowych=3 → pozycja na 17."""
        self._dodaj_egzemplarze(3)
        self._dodaj_egzemplarze(4, stan='uszkodzone')
        pozycja = self._pozycja()
        self.assertIsNotNone(pozycja)
        self.assertEqual(pozycja['ilosc_do_zamowienia'], 17)

    # ========== Limity zero ==========

    def test_stan_minimalny_zero_nie_zamawia(self):
        """limit_min=0 → narzędzie wyłączone z auto-zamawiania → brak pozycji (mimo max=20)."""
        self.narzedzie.stan_minimalny = 0
        self.narzedzie.save()
        self.assertIsNone(self._pozycja())

    def test_stan_maksymalny_zero_blokuje(self):
        """max=0 → brak celu uzupełnienia → brak pozycji (reguła przedziałowa wymaga max>0)."""
        self.narzedzie.stan_maksymalny = 0
        self.narzedzie.save()
        self.assertIsNone(self._pozycja())

    # ========== Opakowania ==========

    def _narzedzie_kompl(self, ilosc_w_opakowaniu=10, stan_max=20, stan_min=1, opis="Płytki"):
        return NarzedzieMagazynowe.objects.create(
            podkategoria=self.podkategoria,
            opis=opis,
            numer_katalogowy=f"PT-{opis}",
            opakowanie="kompl",
            ilosc_w_opakowaniu=ilosc_w_opakowaniu,
            stan_minimalny=stan_min,
            stan_maksymalny=stan_max,
            ostatni_dostawca=self.dostawca,
        )

    def test_komplet_zaokragla_do_najblizszego_w_dol(self):
        """kompl (10 szt.), max=20, 16 nowych → brakuje 4 → round(4/10)=0 → min. 1 komplet."""
        narzedzie = self._narzedzie_kompl()
        self._dodaj_egzemplarze(16, narzedzie=narzedzie)
        pozycja = self._pozycja(narzedzie)
        self.assertIsNotNone(pozycja)
        self.assertEqual(pozycja['ilosc_do_zamowienia'], 1)

    def test_komplet_polowka_zaokragla_w_gore(self):
        """kompl (10 szt.), max=20, 15 nowych → brakuje 5 → 5/10=0,5 → w GÓRĘ → 1 komplet.
        (Python round() dałby bankowo 0 — sprawdzamy, że tak NIE jest.)"""
        narzedzie = self._narzedzie_kompl()
        self._dodaj_egzemplarze(15, narzedzie=narzedzie)
        pozycja = self._pozycja(narzedzie)
        self.assertIsNotNone(pozycja)
        self.assertEqual(pozycja['ilosc_do_zamowienia'], 1)

    def test_komplet_zaokragla_do_najblizszego_w_gore(self):
        """kompl (10 szt.), max=20, 14 nowych → brakuje 6 → round(6/10)=1 komplet."""
        narzedzie = self._narzedzie_kompl()
        self._dodaj_egzemplarze(14, narzedzie=narzedzie)
        pozycja = self._pozycja(narzedzie)
        self.assertIsNotNone(pozycja)
        self.assertEqual(pozycja['ilosc_do_zamowienia'], 1)

    def test_komplet_wiele_opakowan_z_reszta_w_gore(self):
        """kompl (10 szt.), max=20, 5 nowych → brakuje 15 → 15/10=1,5 → 2 komplety."""
        narzedzie = self._narzedzie_kompl()
        self._dodaj_egzemplarze(5, narzedzie=narzedzie)
        pozycja = self._pozycja(narzedzie)
        self.assertIsNotNone(pozycja)
        self.assertEqual(pozycja['ilosc_do_zamowienia'], 2)

    def test_komplet_wiele_opakowan_z_reszta_w_dol(self):
        """kompl (10 szt.), max=20, 6 nowych → brakuje 14 → 14/10=1,4 → 1 komplet."""
        narzedzie = self._narzedzie_kompl()
        self._dodaj_egzemplarze(6, narzedzie=narzedzie)
        pozycja = self._pozycja(narzedzie)
        self.assertIsNotNone(pozycja)
        self.assertEqual(pozycja['ilosc_do_zamowienia'], 1)

    def test_komplet_niedobor_jednej_sztuki_min_jeden_komplet(self):
        """kompl (10 szt.), max=20, 19 nowych → brakuje 1 → round=0 → min. 1 komplet
        (gwarancja powrotu powyżej minimum mimo zaokrąglenia w dół)."""
        narzedzie = self._narzedzie_kompl()
        self._dodaj_egzemplarze(19, narzedzie=narzedzie)
        pozycja = self._pozycja(narzedzie)
        self.assertIsNotNone(pozycja)
        self.assertEqual(pozycja['ilosc_do_zamowienia'], 1)

    # ========== Ręczna kontrola — bez zmian ==========

    def test_reczna_kontrola_liczy_sie_jak_dotychczas(self):
        """reczna_kontrola=True → generator czyta reczne_dodanie, ignoruje limity."""
        self.narzedzie.reczna_kontrola = True
        self.narzedzie.reczne_dodanie = 4
        self.narzedzie.save()
        pozycja = self._pozycja()
        self.assertIsNotNone(pozycja)
        self.assertEqual(pozycja['ilosc_do_zamowienia'], 4)
        self.assertEqual(pozycja['zrodlo'], 'reczne')

    def test_reczna_kontrola_bez_dodania_nie_zamawia(self):
        """reczna_kontrola=True, reczne_dodanie=0 → brak pozycji mimo braku nowych."""
        self.narzedzie.reczna_kontrola = True
        self.narzedzie.reczne_dodanie = 0
        self.narzedzie.save()
        self.assertIsNone(self._pozycja())

    # ========== Czyszczenie zombie ==========

    def test_zombie_pozycja_znika_po_uzupelnieniu_do_max(self):
        """Auto-pozycja utworzona przy braku nowych znika dopiero po dostawie pokrywającej MAX."""
        self.assertIsNotNone(self._pozycja())  # tworzy auto-pozycję (20 szt.)
        self._dodaj_egzemplarze(20)            # dostawa: nowych=20 >= max=20 → pełno
        self.assertIsNone(self._pozycja())
        self.assertFalse(
            PozycjaGeneratora.objects.filter(narzedzie_typ=self.narzedzie).exists()
        )

    def test_zombie_pozycja_zostaje_w_przedziale_min_max(self):
        """Auto-pozycja NIE znika po częściowej dostawie utrzymującej stan w przedziale min–max
        (nowych=12 < max=20 → nadal uzasadniona; bez migotania delete+recreate).
        Ilość pozostaje pierwotna (20) — generator nie przelicza istniejących pozycji."""
        self.assertIsNotNone(self._pozycja())  # tworzy auto-pozycję (20 szt.)
        self._dodaj_egzemplarze(12)            # dostawa: nowych=12, w przedziale min–max
        pozycja = self._pozycja()
        self.assertIsNotNone(pozycja)
        self.assertEqual(pozycja['ilosc_do_zamowienia'], 20)

    # ========== Kontrola regresji trybu standardowego ==========

    def test_tryb_standardowy_liczy_po_staremu(self):
        """Po przełączeniu na 'standardowa': 2 nowe, max=20 → pozycja na 18 (max − stan)."""
        self.mock_sposob.return_value = 'standardowa'
        self._dodaj_egzemplarze(2)
        pozycja = self._pozycja()
        self.assertIsNotNone(pozycja)
        self.assertEqual(pozycja['ilosc_do_zamowienia'], 18)


class SposobLiczeniaZamowienAPITestCase(APITestCase):
    """Testy endpointu /api/ustawienia/sposob-liczenia-zamowien/."""

    def setUp(self):
        self.user = User.objects.create_user(
            'admin1', 'a@test.pl', 'haslo123', first_name='Jan', last_name='Testowy'
        )
        # Widok funkcyjny z @login_required (nie DRF) — wymaga logowania sesyjnego
        self.client.login(username='admin1', password='haslo123')

    def test_get_zwraca_dozwolona_wartosc(self):
        response = self.client.get('/api/ustawienia/sposob-liczenia-zamowien/')
        self.assertEqual(response.status_code, 200)
        self.assertIn(
            response.json()['sposob_liczenia_zamowien'],
            ['standardowa', 'wedlug_nowych_elementow']
        )

    def test_post_nieprawidlowa_wartosc_400(self):
        response = self.client.post(
            '/api/ustawienia/sposob-liczenia-zamowien/',
            {'sposob_liczenia_zamowien': 'bledna_wartosc'},
            format='json'
        )
        self.assertEqual(response.status_code, 400)

    def test_post_zmiana_czysci_auto_pozycje_i_loguje_warning(self):
        """Zmiana trybu usuwa auto-pozycje generatora (ręczne zostają) i loguje WARNING."""
        import tempfile
        from pathlib import Path
        from .models import LogEntry

        kategoria = Kategoria.objects.create(nazwa="Frezy")
        podkategoria = Podkategoria.objects.create(nazwa="VHM", kategoria=kategoria)
        narzedzie_a = NarzedzieMagazynowe.objects.create(
            podkategoria=podkategoria, opis="A", numer_katalogowy="A-1",
            opakowanie="szt", ilosc_w_opakowaniu=1,
        )
        narzedzie_b = NarzedzieMagazynowe.objects.create(
            podkategoria=podkategoria, opis="B", numer_katalogowy="B-1",
            opakowanie="szt", ilosc_w_opakowaniu=1,
        )
        PozycjaGeneratora.objects.create(
            narzedzie_typ=narzedzie_a, ilosc_do_zamowienia=5, zrodlo='auto'
        )
        PozycjaGeneratora.objects.create(
            narzedzie_typ=narzedzie_b, ilosc_do_zamowienia=2, zrodlo='reczne'
        )

        # Tymczasowy BASE_DIR: zapis app_settings.json nie dotyka pliku deweloperskiego
        with tempfile.TemporaryDirectory() as tmp:
            with self.settings(BASE_DIR=Path(tmp), SPOSOB_LICZENIA_ZAMOWIEN='standardowa'):
                response = self.client.post(
                    '/api/ustawienia/sposob-liczenia-zamowien/',
                    {'sposob_liczenia_zamowien': 'wedlug_nowych_elementow'},
                    format='json'
                )
                self.assertEqual(response.status_code, 200)
                self.assertEqual(
                    response.json()['sposob_liczenia_zamowien'], 'wedlug_nowych_elementow'
                )

        self.assertFalse(PozycjaGeneratora.objects.filter(zrodlo='auto').exists())
        self.assertTrue(PozycjaGeneratora.objects.filter(zrodlo='reczne').exists())

        log = LogEntry.objects.filter(operacja__icontains='sposób liczenia zamówień').latest('timestamp')
        self.assertEqual(log.status, 'WARNING')
        self.assertIn('według nowych elementów', log.operacja)


class CenaJednostkowaTestCase(APITestCase):
    """
    Testy priorytetu ceny jednostkowej (Zakupy → modal 'Edytuj typ narzędzia'):
    - cena wyliczona z zamówień (cena_z_zamowienia=True, > 0) — niezmienna,
    - cena ręczna lub zerowa — edytowalna do woli,
    - zamówienie nadpisuje cenę ręczną (priorytet wartości wyliczonej),
    - cena ręczna jest domyślną w generatorze, gdy brak historii zamówień.
    """

    def setUp(self):
        self.user = User.objects.create_user('zakupy', 'zak@test.pl', 'haslo123')
        self.client.force_authenticate(user=self.user)

        self.kategoria = Kategoria.objects.create(nazwa="Frezy")
        self.podkategoria = Podkategoria.objects.create(nazwa="VHM", kategoria=self.kategoria)
        self.dostawca = Dostawca.objects.create(kod_dostawcy="TEST03", nazwa_firmy="Test3 Sp. z o.o.")
        self.narzedzie = NarzedzieMagazynowe.objects.create(
            podkategoria=self.podkategoria,
            opis="Frez D12",
            numer_katalogowy="F12",
            opakowanie="szt",
            ilosc_w_opakowaniu=1,
            stan_minimalny=5,
            stan_maksymalny=20,
            ostatni_dostawca=self.dostawca,
        )

        # Pin trybu liczenia dla wywołań generatora w tych testach
        patcher = mock.patch('TOOLS.views.get_sposob_liczenia_zamowien', return_value='standardowa')
        patcher.start()
        self.addCleanup(patcher.stop)

    def _pozycja_zamowienia(self, cena, status_zam='completed'):
        zamowienie = Zamowienie.objects.create(
            numer=f"ZAM-TEST-{Zamowienie.objects.count() + 1}",
            dostawca=self.dostawca,
            status=status_zam,
        )
        return PozycjaZamowienia.objects.create(
            zamowienie=zamowienie,
            narzedzie_typ=self.narzedzie,
            narzedzie_opis=self.narzedzie.opis,
            ilosc_zamowiona=5,
            cena_jednostkowa=cena,
        )

    # ========== Propagacja z zamówień ==========

    def test_zapis_pozycji_zamowienia_ustawia_cene_i_flage(self):
        self._pozycja_zamowienia('12.50')
        self.narzedzie.refresh_from_db()
        self.assertEqual(float(self.narzedzie.cena_jednostkowa), 12.50)
        self.assertTrue(self.narzedzie.cena_z_zamowienia)

    def test_zamowienie_nadpisuje_cene_reczna(self):
        """Priorytet wartości wyliczonej: zamówienie nadpisuje ręczną cenę i blokuje edycję."""
        self.narzedzie.cena_jednostkowa = 99
        self.narzedzie.save()
        self._pozycja_zamowienia('15.00')
        self.narzedzie.refresh_from_db()
        self.assertEqual(float(self.narzedzie.cena_jednostkowa), 15.00)
        self.assertTrue(self.narzedzie.cena_z_zamowienia)

    # ========== Edycja w modalu (PATCH /api/narzedzia/) ==========

    def test_edycja_zablokowana_gdy_cena_z_zamowienia(self):
        self._pozycja_zamowienia('12.50')
        response = self.client.patch(
            f'/api/narzedzia/{self.narzedzie.id}/', {'cena_jednostkowa': '20.00'}
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.narzedzie.refresh_from_db()
        self.assertEqual(float(self.narzedzie.cena_jednostkowa), 12.50)

    def test_patch_z_ta_sama_cena_przechodzi(self):
        """Modal wysyła PATCH innych pól — niezmieniona cena nie może blokować zapisu."""
        self._pozycja_zamowienia('12.50')
        response = self.client.patch(
            f'/api/narzedzia/{self.narzedzie.id}/',
            {'cena_jednostkowa': '12.50', 'stan_minimalny': 7}
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.narzedzie.refresh_from_db()
        self.assertEqual(self.narzedzie.stan_minimalny, 7)
        self.assertTrue(self.narzedzie.cena_z_zamowienia)

    def test_edycja_dozwolona_gdy_cena_reczna(self):
        """Cena bez flagi (ręczna/brak) — edytowalna do woli."""
        response = self.client.patch(
            f'/api/narzedzia/{self.narzedzie.id}/', {'cena_jednostkowa': '33.00'}
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.narzedzie.refresh_from_db()
        self.assertEqual(float(self.narzedzie.cena_jednostkowa), 33.00)
        self.assertFalse(self.narzedzie.cena_z_zamowienia)

    def test_edycja_dozwolona_gdy_cena_z_zamowienia_zerowa(self):
        """Zerowa cena jest edytowalna nawet z flagą — ręczna zmiana zdejmuje flagę."""
        self._pozycja_zamowienia('0.00')
        self.narzedzie.refresh_from_db()
        self.assertTrue(self.narzedzie.cena_z_zamowienia)

        response = self.client.patch(
            f'/api/narzedzia/{self.narzedzie.id}/', {'cena_jednostkowa': '44.00'}
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.narzedzie.refresh_from_db()
        self.assertEqual(float(self.narzedzie.cena_jednostkowa), 44.00)
        self.assertFalse(self.narzedzie.cena_z_zamowienia)

    # ========== Cena domyślna w generatorze ==========

    def test_generator_uzywa_ceny_recznej_gdy_brak_historii(self):
        """Ręcznie ustawiona cena = domyślna w pozycji generatora (brak zamówień)."""
        self.narzedzie.cena_jednostkowa = 25
        self.narzedzie.save()

        response = self.client.get('/api/generator-zamowien/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        pozycja = next(
            (p for p in response.data.get('pozycje', []) if p['id'] == self.narzedzie.id), None
        )
        self.assertIsNotNone(pozycja)
        self.assertEqual(pozycja['cena_jednostkowa'], 25)

    def test_generator_preferuje_cene_z_zamowien(self):
        """Historia zamówień ma pierwszeństwo przed wartością z pola narzędzia."""
        self._pozycja_zamowienia('18.00')  # status 'completed' — nie blokuje generatora
        self.narzedzie.refresh_from_db()
        # Symulacja rozjazdu: pole narzędzia zmienione wprost w DB (poza propagacją)
        NarzedzieMagazynowe.objects.filter(pk=self.narzedzie.pk).update(cena_jednostkowa=99)

        response = self.client.get('/api/generator-zamowien/')
        pozycja = next(
            (p for p in response.data.get('pozycje', []) if p['id'] == self.narzedzie.id), None
        )
        self.assertIsNotNone(pozycja)
        self.assertEqual(pozycja['cena_jednostkowa'], 18.00)


class EmailZamowieniaTestCase(TestCase):
    """
    Testy treści emaila zamówienia i załącznika CSV (TOOLS/utils.py):
    - skonsolidowana kolumna 'Ilość' (wartość + jednostka),
    - kolumna 'Cena' z ceną jednostkową zamiast 'Jednostka',
    - podsumowanie 'POZYCJI: X; SUMA: Y',
    - CSV: nr_katalogowy|nazwa|ilosc|cena_jedn|suma (kropka dziesiętna, brak ceny → 0.00).
    """

    def setUp(self):
        self.kategoria = Kategoria.objects.create(nazwa="Frezy")
        self.podkategoria = Podkategoria.objects.create(nazwa="VHM", kategoria=self.kategoria)
        self.dostawca = Dostawca.objects.create(
            kod_dostawcy="TEST04", nazwa_firmy="Test4 Sp. z o.o."
        )
        self.narzedzie = NarzedzieMagazynowe.objects.create(
            podkategoria=self.podkategoria,
            opis="Frez D10",
            numer_katalogowy="F10",
            opakowanie="szt",
            ilosc_w_opakowaniu=1,
        )
        self.zamowienie = Zamowienie.objects.create(
            numer="2026/06/01",
            dostawca=self.dostawca,
            email_docelowy="dostawca@test.pl",
        )
        self.poz1 = PozycjaZamowienia.objects.create(
            zamowienie=self.zamowienie,
            narzedzie_typ=self.narzedzie,
            kategoria_nazwa="Frezy",
            podkategoria_nazwa="VHM",
            narzedzie_opis="Frez D10",
            numer_katalogowy="F10",
            ilosc_zamowiona=5,
            jednostka='szt',
            cena_jednostkowa='12.50',
        )
        self.poz2 = PozycjaZamowienia.objects.create(
            zamowienie=self.zamowienie,
            narzedzie_typ=self.narzedzie,
            kategoria_nazwa="Frezy",
            podkategoria_nazwa="VHM",
            narzedzie_opis="Płytki",
            numer_katalogowy="P-1",
            ilosc_zamowiona=2,
            jednostka='kompl',
            ilosc_w_komplecie=10,
            cena_jednostkowa=None,  # brak ceny → 0.00
        )

    def _wyslij_i_przechwyc_html(self):
        from TOOLS import utils
        with mock.patch.object(
            utils, 'send_html_email', return_value={'success': True, 'message': 'OK'}
        ) as mocked:
            utils.send_zamowienie_email(self.zamowienie)
        return mocked.call_args.kwargs['html_content']

    # ========== Email — tabela pozycji ==========

    def test_email_kolumny_ilosc_jednostka(self):
        """Osobne kolumny Ilość i Jednostka (jak w mailu do zatwierdzenia)."""
        html = self._wyslij_i_przechwyc_html()
        self.assertIn('<th style="text-align: center;">Ilość</th>', html)
        self.assertIn('<th style="text-align: center;">Jednostka</th>', html)
        self.assertIn('szt.', html)                 # poz. na sztuki
        self.assertIn('kompl. (10 szt.)', html)     # poz. w komplecie

    def test_email_kolumny_cena_i_wartosc(self):
        html = self._wyslij_i_przechwyc_html()
        self.assertIn('>Cena jedn.<br>', html)  # nagłówek z drugą linią [netto]
        self.assertIn('>Wartość<br>', html)
        self.assertIn('[netto]', html)
        self.assertIn('12,50 zł', html)   # cena za szt. (poz1)
        self.assertIn('62,50 zł', html)   # wartość poz1: 5 × 12,50
        self.assertIn('0,00 zł', html)    # poz2 bez ceny

    def test_email_podsumowanie_pozycje_i_suma(self):
        html = self._wyslij_i_przechwyc_html()
        self.assertNotIn('RAZEM POZYCJI', html)
        self.assertIn('POZYCJI:', html)
        self.assertIn('SUMA:', html)
        # 5 × 12.50 + 2 × 0.00 = 62.50; pozycji: 5 + 2 = 7
        self.assertIn('<strong style="font-size: 1.2em;">7</strong>', html)
        self.assertIn('62,50 zł', html)

    # ========== Załącznik XLSX ==========

    def _wczytaj_xlsx(self, xlsx_bytes):
        import io
        from openpyxl import load_workbook
        wb = load_workbook(io.BytesIO(xlsx_bytes))
        ws = wb.active
        return [list(row) for row in ws.iter_rows(values_only=True)]

    def test_xlsx_naglowek_i_kolumny(self):
        from TOOLS.utils import _build_zamowienie_xlsx
        wiersze = self._wczytaj_xlsx(
            _build_zamowienie_xlsx(list(self.zamowienie.pozycje.all()), {})
        )
        self.assertEqual(wiersze[0], ['nr_katalogowy', 'nazwa', 'ilosc', 'cena_jedn', 'suma'])
        self.assertEqual(wiersze[1], ['F10', 'Frez D10', 5, 12.50, 62.50])
        # Komplet: ilosc rozbita na sztuki (2 kompl. × 10 = 20 szt.); cena za szt.
        self.assertEqual(wiersze[2], ['P-1', 'Płytki', 20, 0.00, 0.00])

    def test_xlsx_mapowanie_nr_dostawcy(self):
        from TOOLS.utils import _build_zamowienie_xlsx
        wiersze = self._wczytaj_xlsx(
            _build_zamowienie_xlsx([self.poz1], {self.narzedzie.id: 'DOST-123'})
        )
        self.assertEqual(wiersze[1], ['DOST-123', 'Frez D10', 5, 12.50, 62.50])

    def test_format_pln(self):
        from TOOLS.utils import _format_pln
        from decimal import Decimal
        self.assertEqual(_format_pln(Decimal('12.50')), '12,50 zł')
        # Separator tysięcy: NBSP ( ) — kwota nie łamie się w HTML emaila
        self.assertEqual(_format_pln(Decimal('1234.56')), '1 234,56 zł')
        self.assertEqual(_format_pln(Decimal('0.00')), '0,00 zł')


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


class KierownikPanelTestCase(APITestCase):
    """Testy dla panelu kierownika: lekkie serializery (optymalizacja) oraz
    eksport PDF listy "Narzędzia w użyciu" z opcjonalnym przedziałem dat."""

    def setUp(self):
        self.user = User.objects.create_user('kier', 'kier@test.pl', 'haslo123')
        self.client.force_authenticate(user=self.user)

        self.kategoria = Kategoria.objects.create(nazwa="Frezy")
        self.podkategoria = Podkategoria.objects.create(nazwa="VHM", kategoria=self.kategoria)
        self.lokalizacja = Lokalizacja.objects.create(szafa="A", kolumna="01", polka="1")
        self.maszyna = Maszyna.objects.create(nazwa="DMU60")
        self.pracownik = Pracownik.objects.create(karta="12345", nazwisko="Kowalski", imie="Jan")
        self.narzedzie = NarzedzieMagazynowe.objects.create(
            podkategoria=self.podkategoria,
            opis="Frez walcowy D10",
            numer_katalogowy="F10-VHM",
            opakowanie="szt",
            ilosc_w_opakowaniu=1,
        )
        self.egzemplarz = EgzemplarzNarzedzia.objects.create(
            narzedzie_typ=self.narzedzie, stan='nowe', lokalizacja=self.lokalizacja
        )
        self.historia = HistoriaUzyciaNarzedzia.objects.create(
            egzemplarz=self.egzemplarz, maszyna=self.maszyna, pracownik=self.pracownik,
            nr_zlecenia='26-0001',
        )

    @staticmethod
    def _as_list(data):
        if isinstance(data, dict) and 'results' in data:
            return data['results']
        return data

    # ---------- Lekkie serializery (optymalizacja ładowania) ----------

    def test_narzedzia_light_pomija_ciezkie_pola(self):
        """?light=true zwraca odchudzony narzędzie z zagnieżdżoną podkategorią,
        ale bez ciężkich relacji (dostawca/lokalizacja)."""
        response = self.client.get('/api/narzedzia/?light=true')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        rec = next(r for r in self._as_list(response.data) if r['id'] == self.narzedzie.id)
        # Kształt oczekiwany przez front Kierownik.vue
        self.assertEqual(rec['podkategoria']['nazwa'], 'VHM')
        self.assertEqual(rec['podkategoria']['kategoria_nazwa'], 'Frezy')
        self.assertIn('calkowita_ilosc', rec)
        # Ciężkie pola pełnego serializera nie powinny być obecne
        self.assertNotIn('ostatni_dostawca', rec)
        self.assertNotIn('domyslna_lokalizacja', rec)

    def test_narzedzia_pelny_zawiera_dostawce(self):
        """Bez ?light pełny serializer wciąż zwraca komplet pól (brak regresji)."""
        response = self.client.get('/api/narzedzia/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        rec = next(r for r in self._as_list(response.data) if r['id'] == self.narzedzie.id)
        self.assertIn('ostatni_dostawca', rec)

    def test_historia_w_uzyciu_light_ksztalt(self):
        """?w_uzyciu=true&light=true zwraca slim historię z zachowanym kształtem."""
        response = self.client.get('/api/historia/?w_uzyciu=true&light=true')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        items = self._as_list(response.data)
        self.assertEqual(len(items), 1)
        rec = items[0]
        self.assertEqual(rec['nr_zlecenia'], '26-0001')
        self.assertEqual(rec['maszyna']['nazwa'], 'DMU60')
        self.assertEqual(rec['pracownik']['nazwisko'], 'Kowalski')
        self.assertEqual(rec['egzemplarz']['narzedzie_typ']['id'], self.narzedzie.id)
        self.assertEqual(
            rec['egzemplarz']['narzedzie_typ']['podkategoria']['kategoria']['nazwa'], 'Frezy'
        )
        # Slim: brak pełnych, ciężkich gałęzi
        self.assertNotIn('pracownik_zwracajacy', rec)

    # ---------- Eksport PDF listy "Narzędzia w użyciu" ----------

    def test_pdf_lista_w_uzyciu_cala(self):
        """Bez dat generuje PDF całej listy w użyciu."""
        response = self.client.post('/api/historia/pdf_lista_w_uzyciu/', {}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response['Content-Type'], 'application/pdf')
        self.assertTrue(response.content.startswith(b'%PDF-'))

    def test_pdf_lista_w_uzyciu_przedzial_dat(self):
        """Przedział dat filtruje po dacie pobrania (data_wydania)."""
        # data_wydania = auto_now_add → nadpisujemy przez update (omija auto_now_add)
        HistoriaUzyciaNarzedzia.objects.filter(pk=self.historia.pk).update(
            data_wydania='2026-03-15T10:00:00+00:00'
        )
        # Zakres obejmujący rekord
        resp_in = self.client.post('/api/historia/pdf_lista_w_uzyciu/',
                                   {'data_od': '2026-03-01', 'data_do': '2026-03-31'}, format='json')
        self.assertEqual(resp_in.status_code, status.HTTP_200_OK)
        self.assertTrue(resp_in.content.startswith(b'%PDF-'))
        # Zakres poza rekordem — wciąż poprawny PDF (pusta lista)
        resp_out = self.client.post('/api/historia/pdf_lista_w_uzyciu/',
                                    {'data_od': '2026-05-01', 'data_do': '2026-05-31'}, format='json')
        self.assertEqual(resp_out.status_code, status.HTTP_200_OK)
        self.assertTrue(resp_out.content.startswith(b'%PDF-'))

    def test_pdf_lista_w_uzyciu_pomija_zwrocone(self):
        """Egzemplarze już zwrócone nie trafiają na listę w użyciu (PDF generuje się mimo to)."""
        # Zwróć jedyny egzemplarz
        HistoriaUzyciaNarzedzia.objects.filter(pk=self.historia.pk).update(
            data_zwrotu='2026-04-01T10:00:00+00:00'
        )
        response = self.client.post('/api/historia/pdf_lista_w_uzyciu/', {}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.content.startswith(b'%PDF-'))


class ZwrotRegeneracjaTestCase(APITestCase):
    """Regresja: zwrot narzędzia jako "Zużyte" (uszkodzone_regeneracja).

    Pokrywa dwa sprzężone błędy naprawione w tej sesji:
      1. Generator numeru karty sortował tekstowo → po przekroczeniu 999 zapętlał
         się na istniejącym numerze (kolizja unique).
      2. Akcja zwrot nie była atomowa → nieudane tworzenie karty zostawiało
         "ducha": historia zamknięta (data_zwrotu), bez karty, egzemplarz nieusunięty.
    """

    def setUp(self):
        self.user = User.objects.create_user('regtest', 'reg@test.pl', 'test123')
        self.client.force_authenticate(user=self.user)

        self.kategoria = Kategoria.objects.create(nazwa="Frezy")
        self.podkategoria = Podkategoria.objects.create(nazwa="VHM", kategoria=self.kategoria)
        self.lokalizacja = Lokalizacja.objects.create(szafa="A", kolumna="01", polka="1")
        self.maszyna = Maszyna.objects.create(nazwa="DMU60")
        self.pracownik = Pracownik.objects.create(karta="12345", nazwisko="Kowalski", imie="Jan")
        self.narzedzie = NarzedzieMagazynowe.objects.create(
            podkategoria=self.podkategoria, opis="Frez D10",
            numer_katalogowy="F10", opakowanie="szt", ilosc_w_opakowaniu=1
        )
        self.rok = timezone.now().year

    def _wydaj(self):
        """Tworzy egzemplarz w użyciu i zwraca (egzemplarz, historia)."""
        egz = EgzemplarzNarzedzia.objects.create(
            narzedzie_typ=self.narzedzie, stan='nowe', lokalizacja=self.lokalizacja
        )
        hist = HistoriaUzyciaNarzedzia.objects.create(
            egzemplarz=egz, maszyna=self.maszyna, pracownik=self.pracownik
        )
        return egz, hist

    def test_generator_regeneracji_numeryczny_po_999(self):
        """Po przekroczeniu 999 generator liczy numerycznie, nie tekstowo."""
        Uszkodzenie.objects.create(numer_karty=f'{self.rok}/999R')
        Uszkodzenie.objects.create(numer_karty=f'{self.rok}/1000R')
        # Sort tekstowy zwróciłby 999R i wygenerował 1000R (kolizja). Numerycznie → 1001R.
        self.assertEqual(
            Uszkodzenie.generuj_numer_karty_regeneracji(), f'{self.rok}/1001R'
        )

    def test_generator_zwykly_numeryczny_po_999(self):
        """Ten sam fix dla zwykłych kart uszkodzeń (bez sufiksu R)."""
        Uszkodzenie.objects.create(numer_karty=f'{self.rok}/999')
        Uszkodzenie.objects.create(numer_karty=f'{self.rok}/1000')
        self.assertEqual(
            Uszkodzenie.generuj_numer_karty(), f'{self.rok}/1001'
        )

    def test_zwrot_regeneracja_tworzy_karte_i_usuwa_egzemplarz(self):
        """Pełny zwrot 'Zużyte' nawet przy liczniku > 1000: 200, karta powstaje, egzemplarz znika."""
        # Dopchnij licznik ponad granicę, która wcześniej blokowała zwroty.
        Uszkodzenie.objects.create(numer_karty=f'{self.rok}/1000R')
        egz, hist = self._wydaj()

        response = self.client.post(
            f'/api/historia/{hist.id}/zwrot/',
            {'stan_po_zwrocie': 'uszkodzone_regeneracja', 'pracownik_zwracajacy_id': self.pracownik.id},
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Udany zwrot regeneracji usuwa egzemplarz; historia kasuje się kaskadowo (CASCADE).
        self.assertFalse(EgzemplarzNarzedzia.objects.filter(id=egz.id).exists())
        self.assertFalse(HistoriaUzyciaNarzedzia.objects.filter(id=hist.id).exists())
        # Powstała nowa karta regeneracji z poprawnym kolejnym numerem
        self.assertTrue(
            Uszkodzenie.objects.filter(numer_karty=f'{self.rok}/1001R').exists()
        )

    def test_zwrot_regeneracja_rollback_przy_bledzie_karty(self):
        """Gdy tworzenie karty padnie, transakcja się wycofuje: brak 'ducha', data_zwrotu pusta, 400."""
        egz, hist = self._wydaj()

        with mock.patch.object(
            Uszkodzenie.objects, 'create', side_effect=IntegrityError('symulacja kolizji')
        ):
            response = self.client.post(
                f'/api/historia/{hist.id}/zwrot/',
                {'stan_po_zwrocie': 'uszkodzone_regeneracja', 'pracownik_zwracajacy_id': self.pracownik.id},
                format='json'
            )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        # Kluczowe: zwrot NIE został utrwalony — ponowna próba jest możliwa
        hist.refresh_from_db()
        self.assertIsNone(hist.data_zwrotu)
        egz.refresh_from_db()
        self.assertTrue(EgzemplarzNarzedzia.objects.filter(id=egz.id).exists())
        self.assertNotEqual(egz.stan, 'uszkodzone_regeneracja')


class WartoscKompletuTestCase(TestCase):
    """
    Wartość pozycji/zamówienia dla narzędzi kupowanych w KOMPLETACH.
    cena_jednostkowa dotyczy pojedynczej sztuki, więc wartość = ilosc × ilosc_w_komplecie × cena.
    Pokrywa: model (oblicz_wartosc/save), agregat zamówienia, XLSX, mail HTML, komendę naprawczą.
    """

    def setUp(self):
        self.kategoria = Kategoria.objects.create(nazwa="Płytki")
        self.podkategoria = Podkategoria.objects.create(nazwa="Tokarskie", kategoria=self.kategoria)
        self.dostawca = Dostawca.objects.create(kod_dostawcy="TESTK", nazwa_firmy="Komplet Sp. z o.o.")
        self.narzedzie = NarzedzieMagazynowe.objects.create(
            podkategoria=self.podkategoria,
            opis="Płytka WNMG",
            numer_katalogowy="WNMG-1",
            opakowanie="kompl",
            ilosc_w_opakowaniu=10,
        )
        self.zamowienie = Zamowienie.objects.create(
            numer="2026/07/K01", dostawca=self.dostawca, email_docelowy="d@test.pl"
        )

    def _poz(self, jednostka='kompl', ilosc=1, w_komplecie=10, cena='30.00'):
        return PozycjaZamowienia.objects.create(
            zamowienie=self.zamowienie,
            narzedzie_typ=self.narzedzie,
            narzedzie_opis="Płytka WNMG",
            numer_katalogowy="WNMG-1",
            ilosc_zamowiona=ilosc,
            jednostka=jednostka,
            ilosc_w_komplecie=w_komplecie,
            cena_jednostkowa=cena,
        )

    # ========== Model ==========

    def test_wartosc_kompletu_mnozona_przez_ilosc_w_komplecie(self):
        """1 kompl. × 10 szt. × 30 zł = 300 zł (a nie 30 zł)."""
        poz = self._poz(ilosc=1, w_komplecie=10, cena='30.00')
        self.assertEqual(float(poz.wartosc_pozycji), 300.00)

    def test_wartosc_sztuki_bez_mnoznika(self):
        """Dla 'szt' mnożnik = 1: 5 × 12 = 60 zł."""
        poz = self._poz(jednostka='szt', ilosc=5, w_komplecie=1, cena='12.00')
        self.assertEqual(float(poz.wartosc_pozycji), 60.00)

    def test_wartosc_wielu_kompletow(self):
        """3 kompl. × 10 szt. × 41.39 zł = 1241.70 zł."""
        poz = self._poz(ilosc=3, w_komplecie=10, cena='41.39')
        self.assertEqual(float(poz.wartosc_pozycji), 1241.70)

    def test_save_zawsze_przelicza_wartosc(self):
        """Nawet gdy podano złe wartosc_pozycji, save() je nadpisuje poprawną."""
        poz = PozycjaZamowienia.objects.create(
            zamowienie=self.zamowienie, narzedzie_typ=self.narzedzie,
            narzedzie_opis="X", ilosc_zamowiona=2, jednostka='kompl',
            ilosc_w_komplecie=10, cena_jednostkowa='30.00',
            wartosc_pozycji=999,  # celowo błędna
        )
        self.assertEqual(float(poz.wartosc_pozycji), 600.00)

    def test_brak_ceny_wartosc_zero(self):
        poz = self._poz(cena=None)
        self.assertEqual(float(poz.wartosc_pozycji), 0.00)

    # ========== Agregat zamówienia ==========

    def test_agregat_wartosci_zamowienia_z_kompletami(self):
        """wartosc_zamowienia = suma wartosc_pozycji (1 kompl×10×30 + 2 szt×15)."""
        from django.db.models import Sum
        self._poz(ilosc=1, w_komplecie=10, cena='30.00')      # 300
        self._poz(jednostka='szt', ilosc=2, w_komplecie=1, cena='15.00')  # 30
        total = self.zamowienie.pozycje.aggregate(s=Sum('wartosc_pozycji'))['s']
        self.assertEqual(float(total), 330.00)

    # ========== XLSX ==========

    def test_xlsx_komplet_suma_pelna(self):
        import io
        from openpyxl import load_workbook
        from TOOLS.utils import _build_zamowienie_xlsx
        self._poz(ilosc=2, w_komplecie=10, cena='30.00')  # 20 szt × 30 = 600
        wb = load_workbook(io.BytesIO(_build_zamowienie_xlsx(list(self.zamowienie.pozycje.all()), {})))
        wiersz = [list(r) for r in wb.active.iter_rows(values_only=True)][1]
        # nr, nazwa, ilosc(szt), cena_jedn, suma
        self.assertEqual(wiersz[2], 20)       # ilość w sztukach
        self.assertEqual(wiersz[3], 30.00)    # cena za sztukę
        self.assertEqual(wiersz[4], 600.00)   # suma pełna

    # ========== Mail HTML (send_zamowienie_email) ==========

    def test_email_suma_uwzglednia_komplety(self):
        from TOOLS import utils
        self._poz(ilosc=2, w_komplecie=10, cena='30.00')  # 600
        with mock.patch.object(utils, 'send_html_email', return_value={'success': True}) as m:
            utils.send_zamowienie_email(self.zamowienie)
        html = m.call_args.kwargs['html_content']
        self.assertIn('600,00 zł', html)          # suma pełna (2 kompl × 10 × 30)
        self.assertIn('kompl. (10 szt.)', html)   # kolumna Jednostka

    # ========== Komenda przelicz_wartosci_zamowien ==========

    def test_komenda_przelicza_zanizone_wartosci(self):
        from django.core.management import call_command
        # Zapisz błędne (zaniżone) wartości bezpośrednio, omijając save()
        poz = self._poz(ilosc=1, w_komplecie=10, cena='30.00')
        PozycjaZamowienia.objects.filter(pk=poz.pk).update(wartosc_pozycji=30)  # zaniżona
        Zamowienie.objects.filter(pk=self.zamowienie.pk).update(wartosc_zamowienia=30)

        call_command('przelicz_wartosci_zamowien', '--apply', verbosity=0)

        poz.refresh_from_db()
        self.zamowienie.refresh_from_db()
        self.assertEqual(float(poz.wartosc_pozycji), 300.00)
        self.assertEqual(float(self.zamowienie.wartosc_zamowienia), 300.00)

    def test_komenda_idempotentna(self):
        from django.core.management import call_command
        self._poz(ilosc=1, w_komplecie=10, cena='30.00')  # już poprawne = 300
        call_command('przelicz_wartosci_zamowien', '--apply', verbosity=0)
        self.zamowienie.refresh_from_db()
        self.assertEqual(float(self.zamowienie.wartosc_zamowienia), 300.00)


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