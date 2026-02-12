"""
TOOLS/services.py

Logika biznesowa aplikacji.
Separacja logiki od warstwy HTTP (views) i warstwy danych (models).
"""

from django.db import transaction
from django.utils import timezone
from django.core.exceptions import ValidationError

import re
from .models import (
    EgzemplarzNarzedzia,
    HistoriaUzyciaNarzedzia,
    Uszkodzenie,
    NarzedzieMagazynowe,
    Pracownik,
    Lokalizacja,
)
from .constants import STANY_DOSTEPNE_DO_WYDANIA, STANY_PO_ZWROCIE


# ============================================================================
# SERWIS ZARZĄDZANIA NARZĘDZIAMI
# ============================================================================

class NarzedzieService:
    """
    Serwis zawierający logikę biznesową związaną z narzędziami.
    """

    @staticmethod
    def policz_egzemplarze_narzedzia(narzedzie):
        """
        Oblicza ilości egzemplarzy narzędzia według stanów.

        Args:
            narzedzie: Instancja modelu Narzedzie

        Returns:
            dict: Słownik z ilościami {
                'nowe': int,
                'uzywane': int,
                'w_uzyciu': int,
                'calkowita': int
            }
        """
        egzemplarze = narzedzie.egzemplarze.all()

        return {
            'nowe': egzemplarze.filter(stan='nowe').count(),
            'uzywane': egzemplarze.filter(stan='uzywane').count(),
            'w_uzyciu': HistoriaUzyciaNarzedzia.objects.filter(
                egzemplarz__narzedzie_typ=narzedzie,
                data_zwrotu__isnull=True
            ).count(),
            'calkowita': egzemplarze.count(),
        }


# ============================================================================
# SERWIS ZARZĄDZANIA EGZEMPLARZAMI
# ============================================================================

class EgzemplarzService:
    """
    Serwis zawierający logikę biznesową związaną z egzemplarzami narzędzi.
    """

    @staticmethod
    def generuj_oznaczenie(narzedzie_typ):
        """
        Generuje oznaczenie w formacie XX-MMRR-NN dla narzędzi z wydawanie_sztuk=True.

        Args:
            narzedzie_typ: Instancja NarzedzieMagazynowe

        Returns:
            str lub None: Wygenerowane oznaczenie lub None jeśli nie dotyczy
        """
        if narzedzie_typ.opakowanie != 'szt' or not narzedzie_typ.podkategoria:
            return None

        # Buduj skrót XX: usuń tekst w nawiasach, weź pierwsze litery słów
        def skrot(nazwa):
            czysta = re.sub(r'\(.*?\)', '', nazwa).strip()
            return ''.join(word[0] for word in czysta.split() if word)

        kategoria_nazwa = narzedzie_typ.podkategoria.kategoria.nazwa
        podkategoria_nazwa = narzedzie_typ.podkategoria.nazwa
        prefix_xx = (skrot(kategoria_nazwa) + skrot(podkategoria_nazwa)).upper()

        # MMRR — miesiąc (2 cyfry) + rok (2 ostatnie cyfry)
        now = timezone.now()
        mm = f"{now.month:02d}"
        rr = f"{now.year % 100:02d}"
        prefix = f"{prefix_xx}-{mm}{rr}"

        # Znajdź max NN wśród istniejących oznaczeń z tym samym prefixem
        pattern = f"{prefix}-"
        istniejace = EgzemplarzNarzedzia.objects.filter(
            oznaczenie__startswith=pattern
        ).values_list('oznaczenie', flat=True)

        max_nn = 0
        for ozn in istniejace:
            try:
                nn = int(ozn.split('-')[-1])
                if nn > max_nn:
                    max_nn = nn
            except (ValueError, IndexError):
                pass

        nowy_nn = max_nn + 1
        return f"{prefix}-{nowy_nn:02d}"

    @staticmethod
    @transaction.atomic
    def wydaj_egzemplarz(egzemplarz_id, maszyna_id=None, pracownik_id=None,
                         czesciowe_wydanie=False, ilosc_sztuk=None, nr_zlecenia=None):
        """
        Wydaje egzemplarz narzędzia pracownikowi.

        Args:
            egzemplarz_id: ID egzemplarza do wydania
            maszyna_id: ID maszyny (opcjonalne)
            pracownik_id: ID pracownika
            czesciowe_wydanie: True jeśli wydajemy tylko część kompletu
            ilosc_sztuk: Ilość sztuk do wydania (tylko przy czesciowe_wydanie=True)

        Returns:
            HistoriaUzyciaNarzedzia: Utworzony wpis historii

        Raises:
            ValidationError: Gdy egzemplarz nie może być wydany
        """
        # Walidacja pracownika
        if not pracownik_id:
            raise ValidationError("Wybierz pracownika wydającego narzędzie.")

        # Pobierz egzemplarz z blokadą
        try:
            egzemplarz = EgzemplarzNarzedzia.objects.select_for_update().get(
                id=egzemplarz_id
            )
        except EgzemplarzNarzedzia.DoesNotExist:
            raise ValidationError("Egzemplarz nie istnieje.")

        # Sprawdź czy pracownik istnieje
        try:
            Pracownik.objects.get(id=pracownik_id)
        except Pracownik.DoesNotExist:
            raise ValidationError("Wybrany pracownik nie istnieje.")

        # Sprawdź stan egzemplarza
        if egzemplarz.stan not in STANY_DOSTEPNE_DO_WYDANIA:
            raise ValidationError(
                "Tego egzemplarza nie można wydać (jest uszkodzony)."
            )

        # Sprawdź czy egzemplarz nie jest już w użyciu
        if HistoriaUzyciaNarzedzia.objects.filter(
                egzemplarz=egzemplarz,
                data_zwrotu__isnull=True
        ).exists():
            raise ValidationError("Ten egzemplarz jest już w użyciu.")

        # Obsługa częściowego wydania (rozbicie kompletu)
        if czesciowe_wydanie:
            if not egzemplarz.narzedzie_typ.wydawanie_sztuk or egzemplarz.ilosc_w_komplecie <= 1:
                raise ValidationError("Częściowe wydanie możliwe tylko dla kompletów z wieloma sztukami.")

            if not ilosc_sztuk or ilosc_sztuk < 1:
                raise ValidationError("Podaj poprawną ilość sztuk do wydania.")

            if ilosc_sztuk > egzemplarz.ilosc_w_komplecie:
                raise ValidationError(
                    f"Ilość sztuk nie może przekraczać {egzemplarz.ilosc_w_komplecie}."
                )

            pozostale_sztuki = egzemplarz.ilosc_w_komplecie - ilosc_sztuk

            # Utwórz nowy egzemplarz dla wydawanych sztuk
            egzemplarz_wydany = EgzemplarzNarzedzia.objects.create(
                narzedzie_typ=egzemplarz.narzedzie_typ,
                stan=egzemplarz.stan,
                lokalizacja=egzemplarz.lokalizacja,
                faktura_zakupu=egzemplarz.faktura_zakupu,
                zamowienie=egzemplarz.zamowienie,
                jednostka='szt',  # Luźne sztuki
                ilosc_w_komplecie=ilosc_sztuk,
                komplet_zrodlowy=egzemplarz
            )

            # Zmodyfikuj oryginalny egzemplarz - pozostałe sztuki
            egzemplarz.ilosc_w_komplecie = pozostale_sztuki
            egzemplarz.save()

            # Utwórz wpis historii dla wydanego egzemplarza
            historia = HistoriaUzyciaNarzedzia.objects.create(
                egzemplarz=egzemplarz_wydany,
                maszyna_id=maszyna_id,
                pracownik_id=pracownik_id,
                nr_zlecenia=nr_zlecenia
            )
        else:
            # Standardowe wydanie całego egzemplarza
            historia = HistoriaUzyciaNarzedzia.objects.create(
                egzemplarz=egzemplarz,
                maszyna_id=maszyna_id,
                pracownik_id=pracownik_id,
                nr_zlecenia=nr_zlecenia
            )

        return historia

    @staticmethod
    @transaction.atomic
    def zwroc_egzemplarz(historia_id, stan_po_zwrocie, czesciowy_zwrot=False, ilosc_sztuk=None):
        """
        Zwraca egzemplarz narzędzia i aktualizuje jego stan.

        Args:
            historia_id: ID wpisu historii użycia
            stan_po_zwrocie: Stan egzemplarza po zwrocie
            czesciowy_zwrot: True jeśli zwracamy tylko część sztuk
            ilosc_sztuk: Ilość sztuk do zwrotu (tylko przy czesciowy_zwrot=True)

        Returns:
            HistoriaUzyciaNarzedzia: Zaktualizowany wpis historii (pełny zwrot)
            lub tuple(HistoriaUzyciaNarzedzia, EgzemplarzNarzedzia): (historia, nowy_egzemplarz) dla częściowego zwrotu

        Raises:
            ValidationError: Gdy zwrot nie może być dokonany
        """
        # Pobierz wpis historii
        try:
            historia = HistoriaUzyciaNarzedzia.objects.select_related('egzemplarz').get(
                id=historia_id
            )
        except HistoriaUzyciaNarzedzia.DoesNotExist:
            raise ValidationError("Wpis historii nie istnieje.")

        # Sprawdź czy nie został już zwrócony
        if historia.data_zwrotu is not None:
            raise ValidationError(
                "Ten wpis historii został już zamknięty (narzędzie zwrócone)."
            )

        # Walidacja stanu po zwrocie
        if stan_po_zwrocie not in STANY_PO_ZWROCIE:
            raise ValidationError("Nieprawidłowy stan po zwrocie.")

        egzemplarz = historia.egzemplarz

        # Obsługa częściowego zwrotu
        if czesciowy_zwrot:
            if not ilosc_sztuk or ilosc_sztuk < 1:
                raise ValidationError("Podaj poprawną ilość sztuk do zwrotu.")

            if ilosc_sztuk >= egzemplarz.ilosc_w_komplecie:
                raise ValidationError(
                    f"Ilość sztuk musi być mniejsza niż {egzemplarz.ilosc_w_komplecie}."
                )

            pozostale_sztuki = egzemplarz.ilosc_w_komplecie - ilosc_sztuk

            # Utwórz nowy egzemplarz dla zwracanych sztuk
            egzemplarz_zwrocony = EgzemplarzNarzedzia.objects.create(
                narzedzie_typ=egzemplarz.narzedzie_typ,
                stan=stan_po_zwrocie,
                lokalizacja=egzemplarz.lokalizacja,
                faktura_zakupu=egzemplarz.faktura_zakupu,
                zamowienie=egzemplarz.zamowienie,
                jednostka='szt',
                ilosc_w_komplecie=ilosc_sztuk
            )

            # Zmniejsz ilość sztuk w oryginalnym egzemplarzu (nadal w użyciu)
            egzemplarz.ilosc_w_komplecie = pozostale_sztuki
            egzemplarz.save()

            # Scalanie zwróconych sztuk z kompletem-źródłem
            if stan_po_zwrocie in ('nowe', 'uzywane') and egzemplarz.komplet_zrodlowy_id:
                try:
                    komplet = EgzemplarzNarzedzia.objects.select_for_update().get(
                        id=egzemplarz.komplet_zrodlowy_id
                    )
                    # Scalaj tylko gdy komplet nie jest w użyciu
                    in_use = HistoriaUzyciaNarzedzia.objects.filter(
                        egzemplarz=komplet, data_zwrotu__isnull=True
                    ).exists()
                    if not in_use and komplet.ilosc_w_komplecie >= 0:
                        komplet.ilosc_w_komplecie += ilosc_sztuk
                        komplet.save()
                        egzemplarz_zwrocony.ilosc_w_komplecie = 0
                        egzemplarz_zwrocony.komplet_zrodlowy = komplet
                        egzemplarz_zwrocony.save()
                except EgzemplarzNarzedzia.DoesNotExist:
                    pass

            # Historia pozostaje otwarta (dla pozostałych sztuk nadal w użyciu)
            return (historia, egzemplarz_zwrocony)

        else:
            # Standardowy pełny zwrot
            historia.data_zwrotu = timezone.now()
            historia.save()

            # Aktualizuj stan egzemplarza
            egzemplarz.stan = stan_po_zwrocie
            egzemplarz.save()

            # Scalanie zwróconych sztuk z kompletem-źródłem
            if (egzemplarz.jednostka == 'szt'
                    and stan_po_zwrocie in ('nowe', 'uzywane')
                    and egzemplarz.komplet_zrodlowy_id):
                try:
                    komplet = EgzemplarzNarzedzia.objects.select_for_update().get(
                        id=egzemplarz.komplet_zrodlowy_id
                    )
                    in_use = HistoriaUzyciaNarzedzia.objects.filter(
                        egzemplarz=komplet, data_zwrotu__isnull=True
                    ).exists()
                    if not in_use and komplet.ilosc_w_komplecie >= 0:
                        komplet.ilosc_w_komplecie += egzemplarz.ilosc_w_komplecie
                        komplet.save()
                        egzemplarz.ilosc_w_komplecie = 0
                        egzemplarz.save()
                except EgzemplarzNarzedzia.DoesNotExist:
                    pass

            # Po zwrocie kompletu — wchłoń jego luźne sztuki z magazynu
            elif (egzemplarz.jednostka == 'kompl'
                    and stan_po_zwrocie in ('nowe', 'uzywane')):
                egz_w_uzyciu_ids = HistoriaUzyciaNarzedzia.objects.filter(
                    data_zwrotu__isnull=True
                ).values_list('egzemplarz_id', flat=True)

                luźne_sztuki = list(
                    EgzemplarzNarzedzia.objects.select_for_update().filter(
                        komplet_zrodlowy=egzemplarz,
                        jednostka='szt',
                        ilosc_w_komplecie__gt=0,
                        stan__in=('nowe', 'uzywane'),
                    ).exclude(
                        id__in=egz_w_uzyciu_ids
                    )
                )

                for piece in luźne_sztuki:
                    egzemplarz.ilosc_w_komplecie += piece.ilosc_w_komplecie
                    piece.ilosc_w_komplecie = 0
                    piece.save()

                if luźne_sztuki:
                    egzemplarz.save()

            return historia

    @staticmethod
    @transaction.atomic
    def usun_egzemplarz_uszkodzony(egzemplarz):
        """
        Usuwa egzemplarz uszkodzony i tworzy wpis w archiwum uszkodzeń.

        Args:
            egzemplarz: Instancja EgzemplarzNarzedzia do usunięcia

        Returns:
            tuple: (czy_utworzono_archiwum: bool, egzemplarz_id: int)
        """
        egzemplarz_id = egzemplarz.id
        utworzono_archiwum = False

        # Tylko uszkodzone egzemplarze są archiwizowane
        if egzemplarz.stan in ['uszkodzone', 'uszkodzone_regeneracja']:
            # Pobierz ostatnią historię użycia
            ostatnia_historia = egzemplarz.historia.select_related(
                'maszyna',
                'pracownik'
            ).order_by('-data_wydania').first()

            # Utwórz wpis w archiwum uszkodzeń
            Uszkodzenie.objects.create(
                egzemplarz=egzemplarz,
                opis_uszkodzenia=f"Egzemplarz ID {egzemplarz_id} - {egzemplarz.narzedzie_typ.opis}",
                pracownik=(
                    ostatnia_historia.pracownik
                    if ostatnia_historia
                    else None
                )
            )
            utworzono_archiwum = True

        # Usuń egzemplarz
        egzemplarz.delete()

        return utworzono_archiwum, egzemplarz_id


# ============================================================================
# SERWIS LOKALIZACJI
# ============================================================================

class LokalizacjaService:
    """
    Serwis zawierający logikę biznesową związaną z lokalizacjami.
    """

    @staticmethod
    @transaction.atomic
    def utworz_lokalizacje_seryjnie(szafa, liczba_kolumn, liczba_polek):
        """
        Tworzy lokalizacje seryjnie dla danej szafy.

        Args:
            szafa: Oznaczenie szafy
            liczba_kolumn: Liczba kolumn do utworzenia
            liczba_polek: Liczba półek w każdej kolumnie

        Returns:
            int: Liczba utworzonych lokalizacji

        Raises:
            ValidationError: Gdy parametry są nieprawidłowe
        """
        # Walidacja parametrów
        try:
            liczba_kolumn = int(liczba_kolumn)
            liczba_polek = int(liczba_polek)
        except (ValueError, TypeError):
            raise ValidationError(
                "Liczba kolumn i półek musi być liczbą całkowitą."
            )

        if not szafa or liczba_kolumn <= 0 or liczba_polek <= 0:
            raise ValidationError(
                "Wszystkie pola są wymagane i muszą mieć wartości dodatnie."
            )

        # Generuj lokalizacje
        nowe_lokalizacje = [
            Lokalizacja(szafa=szafa, kolumna=str(x), polka=str(y))
            for x in range(1, liczba_kolumn + 1)
            for y in range(1, liczba_polek + 1)
        ]

        # Bulk create z ignore_conflicts (pomija duplikaty)
        Lokalizacja.objects.bulk_create(nowe_lokalizacje, ignore_conflicts=True)

        return len(nowe_lokalizacje)


