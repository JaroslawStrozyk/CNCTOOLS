"""
Naprawa zapotrzebowań technologów "osieroconych" po usunięciu zamówienia/pozycji.

Tło problemu:
    Do wersji 1.18.0g usunięcie zamówienia (lub pozycji zamówienia) nie cofało flagi
    PozycjaZapotrzebowania.w_zamowieniu. Pozycja zapotrzebowania zostawała oznaczona
    jako "w zamówieniu", choć żadne zamówienie jej nie zawierało: generator jej nie
    widział, a zapotrzebowanie wisiało jako "W zamówieniu" bez końca.
    Od 1.18.0g usuwanie zwraca pozycje do generatora (views._zwroc_pozycje_zapotrzebowan)
    — ta komenda sprząta dane sprzed poprawki.

Pozycja jest osierocona, gdy (wszystkie warunki):
    - ma narzędzie i w_zamowieniu=True, zapotrzebowanie w statusie 'ordered'/'completed',
    - żadne zamówienie powiązane z zapotrzebowaniem (M2M) nie zawiera tego narzędzia,
    - narzędzia nie ma w generatorze (PozycjaGeneratora z dowolnego źródła),
    - ZABEZPIECZENIE (dane sprzed powiązań M2M — migracja 0046 — oraz pozycje oznaczone,
      bo towar był już „w drodze”): nie istnieje zamówienie z tym narzędziem, które mogło
      pozycję pokryć — utworzone od dnia zatwierdzenia, nadal aktywne albo przyjmowane
      od dnia zatwierdzenia. W razie wątpliwości pozycja NIE jest ruszana.
Naprawa: w_zamowieniu=False (pozycja wraca do generatora), zapotrzebowanie 'ordered'
z pozycjami oczekującymi → 'completed' (zatwierdzone). IDEMPOTENTNE.

Użycie:
    python manage.py napraw_zapotrzebowania_osierocone            # podgląd (dry-run), bez zmian
    python manage.py napraw_zapotrzebowania_osierocone --apply     # wykonaj naprawę
"""
from django.core.management.base import BaseCommand
from django.db import transaction

from TOOLS.models import (
    PozycjaGeneratora, PozycjaZamowienia, PozycjaZapotrzebowania, ZapotrzebowanieTechnologa,
)


class Command(BaseCommand):
    help = (
        'Zwraca do generatora pozycje zapotrzebowań, których zamówienie usunięto '
        '(osierocone w_zamowieniu=True). Domyślnie dry-run; --apply wykonuje.'
    )

    def add_arguments(self, parser):
        parser.add_argument(
            '--apply',
            action='store_true',
            help='Wykonaj naprawę (bez tej flagi tylko podgląd).',
        )

    def _osierocona(self, poz):
        zap = poz.zapotrzebowanie
        nid = poz.narzedzie_typ_id

        # Zamówienie powiązane (M2M) z tym narzędziem — pozycja ma swoje zamówienie
        if PozycjaZamowienia.objects.filter(
            zamowienie__zrodlowe_zapotrzebowania=zap, narzedzie_typ_id=nid
        ).exists():
            return False

        # Narzędzie jest w generatorze (z dowolnego źródła) — nie ruszamy
        if PozycjaGeneratora.objects.filter(narzedzie_typ_id=nid).exists():
            return False

        # Zamówienie z tym narzędziem, które mogło pokryć pozycję bez zapisanego powiązania:
        #  - utworzone od dnia zatwierdzenia (dane sprzed M2M, migracja 0046),
        #  - nadal aktywne (towar „w drodze” — generator oznacza wtedy pozycję bez nowego zamówienia),
        #  - przyjmowane od dnia zatwierdzenia (było w drodze w chwili zatwierdzenia).
        od = (zap.data_realizacji or zap.data_wyslania or zap.data_utworzenia).date()
        zamowienia = PozycjaZamowienia.objects.filter(narzedzie_typ_id=nid)
        if (
            zamowienia.filter(zamowienie__data_utworzenia__date__gte=od).exists()
            or zamowienia.exclude(zamowienie__status='completed').exists()
            or zamowienia.filter(zamowienie__realizacje__data_realizacji__date__gte=od).exists()
            or zamowienia.filter(
                zamowienie__egzemplarze__narzedzie_typ_id=nid,
                zamowienie__egzemplarze__data_zakupu__date__gte=od,
            ).exists()
        ):
            return False

        return True

    def handle(self, *args, **options):
        apply = options['apply']

        kandydaci = PozycjaZapotrzebowania.objects.filter(
            w_zamowieniu=True,
            narzedzie_typ__isnull=False,
            zapotrzebowanie__status__in=['ordered', 'completed'],
        ).select_related('zapotrzebowanie', 'narzedzie_typ')

        osierocone = [p for p in kandydaci if self._osierocona(p)]

        self.stdout.write(self.style.NOTICE(
            f'Sprawdzono pozycji zapotrzebowań "w zamówieniu": {kandydaci.count()}, '
            f'osieroconych: {len(osierocone)}'
            + ('' if apply else '   [DRY RUN — bez zmian]')
        ))
        for p in osierocone:
            self.stdout.write(
                f'  ZAM-{p.zapotrzebowanie_id:04d} [{p.zapotrzebowanie.status}]  '
                f'{p.narzedzie_typ.opis} ({p.ilosc} szt.)'
            )

        if not apply or not osierocone:
            if not apply and osierocone:
                self.stdout.write(self.style.WARNING('Uruchom z --apply, aby naprawić.'))
            return

        with transaction.atomic():
            PozycjaZapotrzebowania.objects.filter(id__in=[p.id for p in osierocone]).update(w_zamowieniu=False)
            cofniete = 0
            for zap in ZapotrzebowanieTechnologa.objects.filter(
                id__in={p.zapotrzebowanie_id for p in osierocone}, status='ordered'
            ):
                if zap.pozycje.filter(w_zamowieniu=False, narzedzie_typ__isnull=False).exists():
                    zap.status = 'completed'
                    zap.save(update_fields=['status'])
                    cofniete += 1

        self.stdout.write(self.style.SUCCESS(
            f'Naprawiono: {len(osierocone)} pozycji wróciło do generatora, '
            f'{cofniete} zapotrzebowań cofnięto do „Zatwierdzone”.'
        ))
