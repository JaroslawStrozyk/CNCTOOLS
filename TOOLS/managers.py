"""
TOOLS/managers.py

Custom Managers i QuerySets dla modeli.
Przeniesienie logiki zapytań z modeli do dedykowanych managerów.
"""

from django.db import models
from django.db.models import Count, Q


# ============================================================================
# NARZEDZIE MANAGER
# ============================================================================

class NarzedzieQuerySet(models.QuerySet):
    """
    Custom QuerySet dla modelu Narzedzie.
    Zawiera metody do filtrowania i agregacji danych o narzędziach.
    """

    def z_pelna_kategoria(self):
        """
        Optymalizuje zapytanie poprzez prefetch powiązań z kategoriami.
        """
        return self.select_related(
            'dostawca',
            'podkategoria__kategoria'
        )

    def ponizej_limitu(self):
        """
        Zwraca narzędzia, których całkowita ilość jest poniżej limitu minimalnego.
        """
        return self.annotate(
            total_count=Count('egzemplarze')
        ).filter(
            total_count__lt=models.F('limit_minimalny')
        )


class NarzedzieManager(models.Manager):
    """
    Manager dla modelu Narzedzie.
    """

    def get_queryset(self):
        return NarzedzieQuerySet(self.model, using=self._db)

    def z_pelna_kategoria(self):
        return self.get_queryset().z_pelna_kategoria()

    def ponizej_limitu(self):
        return self.get_queryset().ponizej_limitu()


# ============================================================================
# EGZEMPLARZ NARZEDZIA MANAGER
# ============================================================================

class EgzemplarzNarzedziaQuerySet(models.QuerySet):
    """
    Custom QuerySet dla modelu EgzemplarzNarzedzia.
    """

    def z_pelna_relacja(self):
        """
        Optymalizuje zapytanie poprzez prefetch wszystkich powiązań.
        """
        return self.select_related(
            'lokalizacja',
            'faktura_zakupu',
            'narzedzie_typ__podkategoria__kategoria'
        )

    def nowe(self):
        """Zwraca tylko nowe egzemplarze."""
        return self.filter(stan='nowe')

    def uzywane(self):
        """Zwraca tylko używane egzemplarze."""
        return self.filter(stan='uzywane')

    def uszkodzone(self):
        """Zwraca tylko uszkodzone egzemplarze."""
        return self.filter(stan='uszkodzone')

    def dostepne_do_wydania(self):
        """Zwraca egzemplarze dostępne do wydania (nowe lub używane)."""
        return self.filter(stan__in=['nowe', 'uzywane'])


class EgzemplarzNarzedziaManager(models.Manager):
    """
    Manager dla modelu EgzemplarzNarzedzia.
    """

    def get_queryset(self):
        return EgzemplarzNarzedziaQuerySet(self.model, using=self._db)

    def z_pelna_relacja(self):
        return self.get_queryset().z_pelna_relacja()

    def nowe(self):
        return self.get_queryset().nowe()

    def uzywane(self):
        return self.get_queryset().uzywane()

    def uszkodzone(self):
        return self.get_queryset().uszkodzone()

    def dostepne_do_wydania(self):
        return self.get_queryset().dostepne_do_wydania()


# ============================================================================
# HISTORIA UŻYCIA MANAGER
# ============================================================================

class HistoriaUzyciaQuerySet(models.QuerySet):
    """
    Custom QuerySet dla modelu HistoriaUzycia.
    """

    def z_pelna_relacja(self):
        """
        Optymalizuje zapytanie poprzez prefetch wszystkich powiązań.
        """
        return self.select_related(
            'maszyna',
            'pracownik',
            'egzemplarz__narzedzie_typ__podkategoria__kategoria',
            'egzemplarz__lokalizacja'
        )

    def w_uzyciu(self):
        """
        Zwraca tylko wpisy bez daty zwrotu (narzędzia aktualnie w użyciu).
        """
        return self.filter(data_zwrotu__isnull=True)

    def zwrocone(self):
        """
        Zwraca tylko wpisy z datą zwrotu (narzędzia już zwrócone).
        """
        return self.filter(data_zwrotu__isnull=False)

    def dla_narzedzia(self, narzedzie_id):
        """
        Filtruje historię dla konkretnego typu narzędzia.
        """
        return self.filter(egzemplarz__narzedzie_typ_id=narzedzie_id)


class HistoriaUzyciaManager(models.Manager):
    """
    Manager dla modelu HistoriaUzycia.
    """

    def get_queryset(self):
        return HistoriaUzyciaQuerySet(self.model, using=self._db)

    def z_pelna_relacja(self):
        return self.get_queryset().z_pelna_relacja()

    def w_uzyciu(self):
        return self.get_queryset().w_uzyciu()

    def zwrocone(self):
        return self.get_queryset().zwrocone()

    def dla_narzedzia(self, narzedzie_id):
        return self.get_queryset().dla_narzedzia(narzedzie_id)


# ============================================================================
# FAKTURA MANAGER
# ============================================================================

class FakturaQuerySet(models.QuerySet):
    """
    Custom QuerySet dla modelu Faktura.
    """

    def nierozliczone(self):
        """Zwraca tylko nierozliczone faktury."""
        return self.filter(rozliczone=False)

    def rozliczone(self):
        """Zwraca tylko rozliczone faktury."""
        return self.filter(rozliczone=True)


class FakturaManager(models.Manager):
    """
    Manager dla modelu Faktura.
    """

    def get_queryset(self):
        return FakturaQuerySet(self.model, using=self._db)

    def nierozliczone(self):
        return self.get_queryset().nierozliczone()

    def rozliczone(self):
        return self.get_queryset().rozliczone()