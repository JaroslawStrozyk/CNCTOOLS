"""
TOOLS/services.py

Logika biznesowa aplikacji.
Separacja logiki od warstwy HTTP (views) i warstwy danych (models).
"""

from django.db import transaction
from django.utils import timezone
from django.core.exceptions import ValidationError

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
    @transaction.atomic
    def wydaj_egzemplarz(egzemplarz_id, maszyna_id=None, pracownik_id=None):
        """
        Wydaje egzemplarz narzędzia pracownikowi.

        Args:
            egzemplarz_id: ID egzemplarza do wydania
            maszyna_id: ID maszyny (opcjonalne)
            pracownik_id: ID pracownika

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

        # Utwórz wpis historii
        historia = HistoriaUzyciaNarzedzia.objects.create(
            egzemplarz=egzemplarz,
            maszyna_id=maszyna_id,
            pracownik_id=pracownik_id
        )

        return historia

    @staticmethod
    @transaction.atomic
    def zwroc_egzemplarz(historia_id, stan_po_zwrocie):
        """
        Zwraca egzemplarz narzędzia i aktualizuje jego stan.

        Args:
            historia_id: ID wpisu historii użycia
            stan_po_zwrocie: Stan egzemplarza po zwrocie

        Returns:
            HistoriaUzyciaNarzedzia: Zaktualizowany wpis historii

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

        # Aktualizuj wpis historii
        historia.data_zwrotu = timezone.now()
        historia.save()

        # Aktualizuj stan egzemplarza
        egzemplarz = historia.egzemplarz
        egzemplarz.stan = stan_po_zwrocie
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
























































# """
# TOOLS/services.py
#
# Logika biznesowa aplikacji.
# Separacja logiki od warstwy HTTP (views) i warstwy danych (models).
# """
#
# from django.db import transaction
# from django.utils import timezone
# from django.core.exceptions import ValidationError
#
# from .models import (
#     EgzemplarzNarzedzia,
#     HistoriaUzyciaNarzedzia,
#     Uszkodzenie,
#     NarzedzieMagazynowe,
#     Pracownik,
#     Lokalizacja,
# )
# from .constants import STANY_DOSTEPNE_DO_WYDANIA, STANY_PO_ZWROCIE
#
#
# # ============================================================================
# # SERWIS ZARZĄDZANIA NARZĘDZIAMI
# # ============================================================================
#
# class NarzedzieService:
#     """
#     Serwis zawierający logikę biznesową związaną z narzędziami.
#     """
#
#     @staticmethod
#     def policz_egzemplarze_narzedzia(narzedzie):
#         """
#         Oblicza ilości egzemplarzy narzędzia według stanów.
#
#         Args:
#             narzedzie: Instancja modelu Narzedzie
#
#         Returns:
#             dict: Słownik z ilościami {
#                 'nowe': int,
#                 'uzywane': int,
#                 'w_uzyciu': int,
#                 'calkowita': int
#             }
#         """
#         egzemplarze = narzedzie.egzemplarze.all()
#
#         return {
#             'nowe': egzemplarze.filter(stan='nowe').count(),
#             'uzywane': egzemplarze.filter(stan='uzywane').count(),
#             'w_uzyciu': HistoriaUzyciaNarzedzia.objects.filter(
#                 egzemplarz__narzedzie_typ=narzedzie,
#                 data_zwrotu__isnull=True
#             ).count(),
#             'calkowita': egzemplarze.count(),
#         }
#
#
# # ============================================================================
# # SERWIS ZARZĄDZANIA EGZEMPLARZAMI
# # ============================================================================
#
# class EgzemplarzService:
#     """
#     Serwis zawierający logikę biznesową związaną z egzemplarzami narzędzi.
#     """
#
#     @staticmethod
#     @transaction.atomic
#     def wydaj_egzemplarz(egzemplarz_id, maszyna_id=None, pracownik_id=None):
#         """
#         Wydaje egzemplarz narzędzia pracownikowi.
#
#         Args:
#             egzemplarz_id: ID egzemplarza do wydania
#             maszyna_id: ID maszyny (opcjonalne)
#             pracownik_id: ID pracownika
#
#         Returns:
#             HistoriaUzyciaNarzedzia: Utworzony wpis historii
#
#         Raises:
#             ValidationError: Gdy egzemplarz nie może być wydany
#         """
#         # Walidacja pracownika
#         if not pracownik_id:
#             raise ValidationError("Wybierz pracownika wydającego narzędzie.")
#
#         # Pobierz egzemplarz z blokadą
#         try:
#             egzemplarz = EgzemplarzNarzedzia.objects.select_for_update().get(
#                 id=egzemplarz_id
#             )
#         except EgzemplarzNarzedzia.DoesNotExist:
#             raise ValidationError("Egzemplarz nie istnieje.")
#
#         # Sprawdź czy pracownik istnieje
#         try:
#             Pracownik.objects.get(id=pracownik_id)
#         except Pracownik.DoesNotExist:
#             raise ValidationError("Wybrany pracownik nie istnieje.")
#
#         # Sprawdź stan egzemplarza
#         if egzemplarz.stan not in STANY_DOSTEPNE_DO_WYDANIA:
#             raise ValidationError(
#                 "Tego egzemplarza nie można wydać (jest uszkodzony)."
#             )
#
#         # Sprawdź czy egzemplarz nie jest już w użyciu
#         if HistoriaUzyciaNarzedzia.objects.filter(
#                 egzemplarz=egzemplarz,
#                 data_zwrotu__isnull=True
#         ).exists():
#             raise ValidationError("Ten egzemplarz jest już w użyciu.")
#
#         # Utwórz wpis historii
#         historia = HistoriaUzyciaNarzedzia.objects.create(
#             egzemplarz=egzemplarz,
#             maszyna_id=maszyna_id,
#             pracownik_id=pracownik_id
#         )
#
#         return historia
#
#     @staticmethod
#     @transaction.atomic
#     def zwroc_egzemplarz(historia_id, stan_po_zwrocie):
#         """
#         Zwraca egzemplarz narzędzia i aktualizuje jego stan.
#
#         Args:
#             historia_id: ID wpisu historii użycia
#             stan_po_zwrocie: Stan egzemplarza po zwrocie
#
#         Returns:
#             HistoriaUzyciaNarzedzia: Zaktualizowany wpis historii
#
#         Raises:
#             ValidationError: Gdy zwrot nie może być dokonany
#         """
#         # Pobierz wpis historii
#         try:
#             historia = HistoriaUzyciaNarzedzia.objects.select_related('egzemplarz').get(
#                 id=historia_id
#             )
#         except HistoriaUzyciaNarzedzia.DoesNotExist:
#             raise ValidationError("Wpis historii nie istnieje.")
#
#         # Sprawdź czy nie został już zwrócony
#         if historia.data_zwrotu is not None:
#             raise ValidationError(
#                 "Ten wpis historii został już zamknięty (narzędzie zwrócone)."
#             )
#
#         # Walidacja stanu po zwrocie
#         if stan_po_zwrocie not in STANY_PO_ZWROCIE:
#             raise ValidationError("Nieprawidłowy stan po zwrocie.")
#
#         # Aktualizuj wpis historii
#         historia.data_zwrotu = timezone.now()
#         historia.save()
#
#         # Aktualizuj stan egzemplarza
#         egzemplarz = historia.egzemplarz
#         egzemplarz.stan = stan_po_zwrocie
#         egzemplarz.save()
#
#         return historia
#
#     @staticmethod
#     @transaction.atomic
#     def usun_egzemplarz_uszkodzony(egzemplarz):
#         """
#         Usuwa egzemplarz uszkodzony i tworzy wpis w archiwum uszkodzeń.
#
#         Args:
#             egzemplarz: Instancja EgzemplarzNarzedzia do usunięcia
#
#         Returns:
#             tuple: (czy_utworzono_archiwum: bool, egzemplarz_id: int)
#         """
#         egzemplarz_id = egzemplarz.id
#         utworzono_archiwum = False
#
#         # Tylko uszkodzone egzemplarze są archiwizowane
#         if egzemplarz.stan == 'uszkodzone':
#             # Pobierz ostatnią historię użycia
#             ostatnia_historia = egzemplarz.historia.select_related(
#                 'maszyna',
#                 'pracownik'
#             ).order_by('-data_wydania').first()
#
#             # Utwórz wpis w archiwum uszkodzeń
#             Uszkodzenie.objects.create(
#                 egzemplarz=egzemplarz,
#                 opis_uszkodzenia=f"Egzemplarz ID {egzemplarz_id} - {egzemplarz.narzedzie_typ.opis}",
#                 pracownik=(
#                     ostatnia_historia.pracownik
#                     if ostatnia_historia
#                     else None
#                 )
#             )
#             utworzono_archiwum = True
#
#         # Usuń egzemplarz
#         egzemplarz.delete()
#
#         return utworzono_archiwum, egzemplarz_id
#
#
# # ============================================================================
# # SERWIS LOKALIZACJI
# # ============================================================================
#
# class LokalizacjaService:
#     """
#     Serwis zawierający logikę biznesową związaną z lokalizacjami.
#     """
#
#     @staticmethod
#     @transaction.atomic
#     def utworz_lokalizacje_seryjnie(szafa, liczba_kolumn, liczba_polek):
#         """
#         Tworzy lokalizacje seryjnie dla danej szafy.
#
#         Args:
#             szafa: Oznaczenie szafy
#             liczba_kolumn: Liczba kolumn do utworzenia
#             liczba_polek: Liczba półek w każdej kolumnie
#
#         Returns:
#             int: Liczba utworzonych lokalizacji
#
#         Raises:
#             ValidationError: Gdy parametry są nieprawidłowe
#         """
#         # Walidacja parametrów
#         try:
#             liczba_kolumn = int(liczba_kolumn)
#             liczba_polek = int(liczba_polek)
#         except (ValueError, TypeError):
#             raise ValidationError(
#                 "Liczba kolumn i półek musi być liczbą całkowitą."
#             )
#
#         if not szafa or liczba_kolumn <= 0 or liczba_polek <= 0:
#             raise ValidationError(
#                 "Wszystkie pola są wymagane i muszą mieć wartości dodatnie."
#             )
#
#         # Generuj lokalizacje
#         nowe_lokalizacje = [
#             Lokalizacja(szafa=szafa, kolumna=str(x), polka=str(y))
#             for x in range(1, liczba_kolumn + 1)
#             for y in range(1, liczba_polek + 1)
#         ]
#
#         # Bulk create z ignore_conflicts (pomija duplikaty)
#         Lokalizacja.objects.bulk_create(nowe_lokalizacje, ignore_conflicts=True)
#
#         return len(nowe_lokalizacje)
#
#
