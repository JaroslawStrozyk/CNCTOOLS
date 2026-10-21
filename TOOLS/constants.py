"""
TOOLS/constants.py

Stałe i enumeracje używane w całym module TOOLS.
Centralizacja wartości ułatwia zarządzanie i modyfikację.
"""

from django.db import models


# ============================================================================
# STANY EGZEMPLARZY NARZĘDZI
# ============================================================================

class StanEgzemplarza(models.TextChoices):
    """
    Możliwe stany egzemplarza narzędzia w magazynie.
    """
    NOWE = 'nowe', 'Nowe'
    UZYWANE = 'uzywane', 'Używane'
    USZKODZONE = 'uszkodzone', 'Uszkodzone'
    USZKODZONE_REGENERACJA = 'uszkodzone_regeneracja', 'Uszkodzone do regeneracji'


# ============================================================================
# FILTRY I WALIDACJA
# ============================================================================

# Stany umożliwiające wydanie narzędzia pracownikowi
STANY_DOSTEPNE_DO_WYDANIA = [
    StanEgzemplarza.NOWE,
    StanEgzemplarza.UZYWANE,
]

# Stany możliwe po zwrocie narzędzia JEDNORAZOWEGO (paczki): nieużyte wracają, reszta zużyta
STANY_PO_ZWROCIE_JEDNORAZOWE = [
    StanEgzemplarza.NOWE,
    StanEgzemplarza.USZKODZONE_REGENERACJA,
]

# Stan zapisywany w Uszkodzenie dla zużytej paczki narzędzia jednorazowego (zakładka w Zwrotach)
STAN_ZUZYTE_JEDNORAZOWE = 'Zużyte – jednorazowe'

# Stany możliwe po zwrocie narzędzia
STANY_PO_ZWROCIE = [
    StanEgzemplarza.NOWE,
    StanEgzemplarza.UZYWANE,
    StanEgzemplarza.USZKODZONE,
    StanEgzemplarza.USZKODZONE_REGENERACJA,
]


