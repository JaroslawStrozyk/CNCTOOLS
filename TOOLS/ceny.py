"""
TOOLS/ceny.py

Wybór aktualnej ceny jednostkowej narzędzia: NAJNOWSZY wpis spośród
  - pozycji zamówień (moment = data utworzenia zamówienia, cena > 0),
  - pozycji ofert dostawców (moment = data oferty + godzina wprowadzenia).
Oferta wpisana ręcznie staje się najnowszą ceną; kolejne zamówienia jej nie kasują,
tylko wyprzedzają (aż do następnej oferty).
"""

from .models import NarzedzieMagazynowe, PozycjaOferty, PozycjaZamowienia


def _najnowsze_z_zamowien(narzedzia_ids=None):
    """{narzedzie_id: (moment, cena)} — 1 zapytanie (PostgreSQL DISTINCT ON).
    Remis rozstrzyga domyślne sortowanie PozycjaZamowienia (zamowienie, id)."""
    qs = PozycjaZamowienia.objects.filter(cena_jednostkowa__isnull=False, cena_jednostkowa__gt=0)
    if narzedzia_ids is not None:
        qs = qs.filter(narzedzie_typ_id__in=narzedzia_ids)
    wiersze = qs.order_by(
        'narzedzie_typ_id', '-zamowienie__data_utworzenia', 'zamowienie', 'id'
    ).distinct('narzedzie_typ_id').values_list(
        'narzedzie_typ_id', 'zamowienie__data_utworzenia', 'cena_jednostkowa'
    )
    return {nid: (moment, cena) for nid, moment, cena in wiersze}


def _najnowsze_z_ofert(narzedzia_ids=None):
    """{narzedzie_id: (moment, cena)} — ofert jest niewiele, wybór najnowszej w Pythonie."""
    qs = PozycjaOferty.objects.select_related('oferta')
    if narzedzia_ids is not None:
        qs = qs.filter(narzedzie_typ_id__in=narzedzia_ids)
    wynik = {}
    for poz in qs:
        moment = poz.oferta.moment()
        if poz.narzedzie_typ_id not in wynik or moment >= wynik[poz.narzedzie_typ_id][0]:
            wynik[poz.narzedzie_typ_id] = (moment, poz.cena_jednostkowa)
    return wynik


def najnowsze_ceny(narzedzia_ids=None):
    """{narzedzie_id: cena} — najnowsza cena z zamówień lub ofert (oferta wygrywa remis)."""
    zamowienia = _najnowsze_z_zamowien(narzedzia_ids)
    oferty = _najnowsze_z_ofert(narzedzia_ids)
    wynik = {nid: cena for nid, (_, cena) in zamowienia.items()}
    for nid, (moment, cena) in oferty.items():
        if nid not in zamowienia or moment >= zamowienia[nid][0]:
            wynik[nid] = cena
    return wynik


def odswiez_cene_narzedzia(narzedzie_id):
    """Ustawia NarzedzieMagazynowe.cena_jednostkowa na najnowszą cenę (zamówienia/oferty).
    Brak jakiegokolwiek wpisu → cena narzędzia bez zmian."""
    cena = najnowsze_ceny([narzedzie_id]).get(narzedzie_id)
    if cena is not None:
        NarzedzieMagazynowe.objects.filter(pk=narzedzie_id).update(
            cena_jednostkowa=cena, cena_z_zamowienia=True
        )
