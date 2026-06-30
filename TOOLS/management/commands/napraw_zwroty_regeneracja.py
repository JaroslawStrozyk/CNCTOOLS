"""
Naprawa "duchów" po nieudanych zwrotach narzędzi jako "Zużyte" (uszkodzone_regeneracja).

Tło problemu:
    Generator numeru karty regeneracji sortował numery tekstowo, przez co po
    przekroczeniu 999 zapętlał się na istniejącym numerze → kolizja unique przy
    tworzeniu karty. Akcja zwrotu NIE była atomowa: serwis ustawiał data_zwrotu
    (commit), a dopiero potem padało tworzenie karty. Efekt: egzemplarz pozostawał
    w bazie ze stanem 'uszkodzone_regeneracja' (powinien zostać usunięty), historia
    była zamknięta, a karta uszkodzenia nie powstała. Ponowny zwrot dawał mylące
    "wpis już zamknięty".

    Generator (models.py) i atomowość akcji (views.py) są już naprawione — ta komenda
    sprząta dane sprzed naprawy: DOKAŃCZA nieudane zwroty (tworzy brakującą kartę
    regeneracji i usuwa egzemplarz-ducha), zgodnie z fizyką (narzędzie zostało zużyte).

Użycie:
    python manage.py napraw_zwroty_regeneracja            # podgląd (dry-run), bez zmian
    python manage.py napraw_zwroty_regeneracja --apply     # wykonaj naprawę
"""
from django.core.management.base import BaseCommand
from django.db import transaction

from TOOLS.models import EgzemplarzNarzedzia, HistoriaUzyciaNarzedzia, Uszkodzenie


class Command(BaseCommand):
    help = (
        'Dokańcza nieudane zwroty "Zużyte" (uszkodzone_regeneracja): tworzy brakującą '
        'kartę regeneracji i usuwa egzemplarz-ducha. Domyślnie dry-run; --apply wykonuje.'
    )

    def add_arguments(self, parser):
        parser.add_argument(
            '--apply',
            action='store_true',
            help='Wykonaj naprawę (bez tej flagi tylko podgląd).',
        )

    def handle(self, *args, **options):
        apply = options['apply']

        # Egzemplarze-duchy: po udanym zwrocie regeneracji egzemplarz jest USUWANY,
        # więc każdy egzemplarz z tym stanem to pozostałość po nieudanym zwrocie.
        ghosty = list(
            EgzemplarzNarzedzia.objects.filter(stan='uszkodzone_regeneracja')
            .select_related('narzedzie_typ__podkategoria__kategoria', 'lokalizacja')
        )

        self.stdout.write(self.style.NOTICE(
            f'Znaleziono egzemplarzy-duchów (stan=uszkodzone_regeneracja): {len(ghosty)}'
            + ('' if apply else '   [DRY RUN — bez zmian]')
        ))

        naprawione = 0
        do_recznej = 0

        for egz in ghosty:
            # Powiązana zamknięta historia zwrotu jako regeneracja (pełny zwrot).
            historia = (
                HistoriaUzyciaNarzedzia.objects.filter(
                    egzemplarz=egz,
                    data_zwrotu__isnull=False,
                    stan_po_zwrocie='uszkodzone_regeneracja',
                )
                .select_related('maszyna', 'pracownik')
                .order_by('-data_zwrotu')
                .first()
            )

            nt = egz.narzedzie_typ
            opis = nt.opis if nt else '(brak typu)'

            if historia is None:
                # Np. pozostałość po częściowym zwrocie — brak jednoznacznej historii.
                # Nie fabrykujemy danych karty; zgłaszamy do ręcznej decyzji.
                do_recznej += 1
                self.stdout.write(self.style.WARNING(
                    f'  [RĘCZNIE] egzemplarz #{egz.id} ({opis}) — brak powiązanej '
                    f'zamkniętej historii regeneracji; pomijam.'
                ))
                continue

            if not apply:
                self.stdout.write(
                    f'  [DO NAPRAWY] egzemplarz #{egz.id} ({opis}); '
                    f'historia #{historia.id}; → utworzę kartę regeneracji + usunę egzemplarz'
                )
                continue

            with transaction.atomic():
                narzedzie_opis = nt.opis if nt else ''
                numer_katalogowy = (nt.numer_katalogowy or '') if nt else ''
                kategoria_narzedzia = ''
                if nt and nt.podkategoria:
                    kategoria_narzedzia = f"{nt.podkategoria.kategoria.nazwa} / {nt.podkategoria.nazwa}"
                lokalizacja_opis = ''
                if egz.lokalizacja:
                    lok = egz.lokalizacja
                    lokalizacja_opis = f"{lok.szafa}/{lok.polka}/{lok.kolumna}"

                numer_karty_regen = Uszkodzenie.generuj_numer_karty_regeneracji()
                Uszkodzenie.objects.create(
                    egzemplarz=None,
                    narzedzie_typ=nt,
                    narzedzie_opis=narzedzie_opis,
                    numer_katalogowy=numer_katalogowy,
                    kategoria_narzedzia=kategoria_narzedzia,
                    lokalizacja_opis=lokalizacja_opis,
                    stan='Uszkodzone do regeneracji',
                    maszyna_nazwa=historia.maszyna.nazwa if historia.maszyna else '',
                    pracownik_nazwisko=historia.pracownik.nazwisko if historia.pracownik else '',
                    pracownik_imie=historia.pracownik.imie if historia.pracownik else '',
                    opis_uszkodzenia='Zużyte do regeneracji (naprawa zaległego zwrotu)',
                    pracownik=historia.pracownik,
                    numer_karty=numer_karty_regen,
                )
                egz_id = egz.id
                egz.delete()

            naprawione += 1
            self.stdout.write(self.style.SUCCESS(
                f'  [OK] egzemplarz #{egz_id} ({opis}) → karta {numer_karty_regen}, egzemplarz usunięty'
            ))

        self.stdout.write('')
        if apply:
            self.stdout.write(self.style.SUCCESS(
                f'Naprawiono: {naprawione}; do ręcznej decyzji: {do_recznej}.'
            ))
        else:
            self.stdout.write(self.style.NOTICE(
                f'Podgląd: {len(ghosty) - do_recznej} do naprawy, {do_recznej} do ręcznej decyzji. '
                f'Uruchom z --apply, aby wykonać.'
            ))
