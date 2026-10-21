"""
TOOLS/statusy.py

Jedno źródło prawdy o statusach widocznych w aplikacji.

ZASADA: zamówienia są źródłem prawdy. Od chwili, gdy zapotrzebowanie technologa ma
powiązane zamówienia (M2M Zamowienie.zrodlowe_zapotrzebowania), jego status widoczny
w UI/PDF wynika WYŁĄCZNIE ze statusów tych zamówień. Pole
ZapotrzebowanieTechnologa.status opisuje tylko etap sprzed zamówienia
(robocze → wysłane → zatwierdzone) i steruje generatorem — kody w bazie bez zmian.
"""

from django.db.models import OuterRef, Subquery


# Kolejność etapów zamówienia — im dalej, tym bardziej zaawansowane
ETAPY_ZAMOWIENIA = ['draft', 'pending_approval', 'verified', 'sent', 'partially_received', 'completed']

# Statusy zamówienia „w przygotowaniu” (jeszcze nie wysłane do dostawcy)
ZAMOWIENIE_W_PRZYGOTOWANIU = {'draft', 'pending_approval', 'verified'}

# Kody efektywnego statusu zapotrzebowania → etykieta
STATUS_ZAPOTRZEBOWANIA_ETYKIETY = {
    'draft': 'Robocze',
    'submitted': 'Wysłane',
    'approved': 'Zatwierdzone',
    'w_przygotowaniu': 'W zamówieniu – w przygotowaniu',
    'wyslane': 'W zamówieniu – wysłane do dostawcy',
    'czesciowo_odebrane': 'Częściowo odebrane',
    'completed': 'Zrealizowane',
    'cancelled': 'Anulowane',
    'ordered': 'W zamówieniu',  # zapotrzebowanie 'ordered' bez zamówień (zaszłość)
}


def status_efektywny_zapotrzebowania(zap):
    """
    Zwraca kod efektywnego statusu zapotrzebowania (klucz STATUS_ZAPOTRZEBOWANIA_ETYKIETY).

    Bez zamówień: draft / submitted / approved (= 'completed' w bazie) / cancelled.
    Z zamówieniami (źródło prawdy):
      - wszystkie zamówienia 'completed' i nic nie czeka na ponowne zamówienie → 'completed'
      - którekolwiek przyjęte choć częściowo (partially_received/completed) → 'czesciowo_odebrane'
      - wszystkie wysłane do dostawcy → 'wyslane'
      - w pozostałych przypadkach → 'w_przygotowaniu'
    Korzysta z prefetchu `zamowienia` i `pozycje`, jeśli są.
    """
    if zap.status in ('draft', 'submitted', 'cancelled'):
        return zap.status

    statusy = [z.status for z in zap.zamowienia.all()]
    if not statusy:
        return 'approved' if zap.status == 'completed' else zap.status

    # Pozycje z narzędziem, które wróciły do generatora (odpisane, usunięte z zamówienia)
    # — zapotrzebowanie nie jest jeszcze w całości zrealizowane
    czeka_na_zamowienie = any(
        p.narzedzie_typ_id and not p.w_zamowieniu for p in zap.pozycje.all()
    )

    if all(s == 'completed' for s in statusy) and not czeka_na_zamowienie:
        return 'completed'
    if any(s in ('partially_received', 'completed') for s in statusy):
        return 'czesciowo_odebrane'
    if all(s not in ZAMOWIENIE_W_PRZYGOTOWANIU for s in statusy):
        return 'wyslane'
    return 'w_przygotowaniu'


def etykieta_statusu_zapotrzebowania(kod):
    return STATUS_ZAPOTRZEBOWANIA_ETYKIETY.get(kod, kod)


def adnotuj_ostatnie_przyjecie(queryset):
    """
    Adnotacja `_ostatnie_przyjecie` dla zapotrzebowań: data najpóźniej przyjętego
    egzemplarza z powiązanych zamówień (EgzemplarzNarzedzia.data_zakupu) — przybliżenie
    daty realizacji (egzemplarze później usunięte, np. zużyte, nie są liczone).
    """
    from .models import EgzemplarzNarzedzia
    ostatni = EgzemplarzNarzedzia.objects.filter(
        zamowienie__zrodlowe_zapotrzebowania=OuterRef('pk'),
        data_zakupu__isnull=False,
    ).order_by('-data_zakupu').values('data_zakupu')[:1]
    return queryset.annotate(_ostatnie_przyjecie=Subquery(ostatni))
