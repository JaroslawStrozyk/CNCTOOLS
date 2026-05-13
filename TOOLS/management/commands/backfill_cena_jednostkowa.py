"""
Backfill pola NarzedzieMagazynowe.cena_jednostkowa z najnowszych pozycji zamówień.

Uruchamiać RAZ po migracji 0048_narzedzie_cena_jednostkowa na bazie produkcyjnej.
Komenda jest idempotentna — można uruchamiać wielokrotnie (nadpisuje ostatnią ceną).

Użycie:
    python manage.py backfill_cena_jednostkowa
    python manage.py backfill_cena_jednostkowa --dry-run    # tylko podgląd, bez zmian
"""
from django.core.management.base import BaseCommand
from TOOLS.models import NarzedzieMagazynowe, PozycjaZamowienia


class Command(BaseCommand):
    help = (
        'Backfill cena_jednostkowa w NarzedzieMagazynowe z najnowszej pozycji zamówienia. '
        'Uruchomić raz po migracji 0048.'
    )

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Tylko podgląd — bez zapisu do bazy.',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        total = NarzedzieMagazynowe.objects.count()
        updated = 0
        skipped = 0

        self.stdout.write(self.style.NOTICE(
            f'Backfill cena_jednostkowa — {total} narzędzi w bazie'
            + (' [DRY RUN]' if dry_run else '')
        ))

        for narzedzie in NarzedzieMagazynowe.objects.all().iterator():
            poz = (
                PozycjaZamowienia.objects
                .filter(narzedzie_typ=narzedzie, cena_jednostkowa__isnull=False)
                .order_by('-zamowienie__data_utworzenia', '-id')
                .first()
            )
            if poz is None or poz.cena_jednostkowa is None:
                skipped += 1
                continue

            if narzedzie.cena_jednostkowa == poz.cena_jednostkowa:
                # Już aktualne — nie nadpisuj
                skipped += 1
                continue

            if not dry_run:
                narzedzie.cena_jednostkowa = poz.cena_jednostkowa
                narzedzie.save(update_fields=['cena_jednostkowa'])
            updated += 1

        self.stdout.write(self.style.SUCCESS(
            f'Gotowe. Zaktualizowano: {updated} / {total} (pominięto: {skipped})'
            + (' [DRY RUN — żadne dane nie zostały zapisane]' if dry_run else '')
        ))
