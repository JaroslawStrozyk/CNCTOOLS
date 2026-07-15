"""
Przeliczenie wartości pozycji i zamówień z uwzględnieniem mnożnika kompletu.

Tło problemu:
    cena_jednostkowa w całym systemie dotyczy pojedynczej SZTUKI. Dla pozycji
    kupowanych w KOMPLETACH ilosc_zamowiona jest liczbą kompletów, więc wartość
    musi być mnożona przez ilosc_w_komplecie:
        wartość = ilosc_zamowiona × (ilosc_w_komplecie jeśli 'kompl' else 1) × cena.
    Wcześniej wartość liczono jako ilosc_zamowiona × cena, przez co pozycje w
    kompletach miały ZANIŻONĄ wartość (np. 1 kompl. 10 szt. × 30 zł = 30 zł
    zamiast 300 zł).

    Model (PozycjaZamowienia.oblicz_wartosc / save) i wszystkie ścieżki liczenia są
    już naprawione — ta komenda przelicza dane historyczne WSZYSTKICH zamówień.
    Idempotentna: ponowne uruchomienie na policzonych danych nic nie zmienia.

    Zapis pomija PozycjaZamowienia.save() (używa .update()), by NIE wywoływać
    propagacji ceny do NarzedzieMagazynowe (to tylko przeliczenie wartości).

Użycie:
    python manage.py przelicz_wartosci_zamowien           # podgląd (dry-run), bez zmian
    python manage.py przelicz_wartosci_zamowien --apply    # zapisz przeliczone wartości
"""
from decimal import Decimal

from django.core.management.base import BaseCommand
from django.db import transaction
from django.db.models import Sum

from TOOLS.models import Zamowienie, PozycjaZamowienia


class Command(BaseCommand):
    help = (
        'Przelicza wartosc_pozycji i wartosc_zamowienia z mnożnikiem kompletu '
        '(cena za sztukę × ilość sztuk). Domyślnie dry-run; --apply zapisuje.'
    )

    def add_arguments(self, parser):
        parser.add_argument(
            '--apply',
            action='store_true',
            help='Zapisz przeliczone wartości (bez tej flagi tylko podgląd).',
        )

    def handle(self, *args, **options):
        apply = options['apply']
        verbose = options.get('verbosity', 1) >= 1

        poz_zmienione = 0
        zam_zmienione = 0

        with transaction.atomic():
            for poz in PozycjaZamowienia.objects.all().iterator():
                nowa = poz.oblicz_wartosc()
                if not isinstance(nowa, Decimal):
                    nowa = Decimal(str(nowa))
                stara = poz.wartosc_pozycji or Decimal('0.00')
                if stara != nowa:
                    poz_zmienione += 1
                    if verbose:
                        self.stdout.write(
                            f"  Pozycja #{poz.id} ({poz.zamowienie.numer}: {poz.narzedzie_opis[:40]}) "
                            f"{poz.ilosc_zamowiona} {poz.jednostka} × {poz.mnoznik_kompletu} × "
                            f"{poz.cena_jednostkowa or 0} zł: {stara} → {nowa} zł"
                        )
                    if apply:
                        # .update() omija save() → bez propagacji ceny do magazynu
                        PozycjaZamowienia.objects.filter(pk=poz.pk).update(wartosc_pozycji=nowa)

            # Przelicz sumy zamówień na podstawie (już zaktualizowanych) wartości pozycji.
            # W dry-run liczymy z bieżących wartosc_pozycji w DB — pokazujemy różnicę,
            # realny zapis nastąpi tylko przy --apply (po aktualizacji pozycji wyżej).
            for zam in Zamowienie.objects.all().iterator():
                if apply:
                    total = zam.pozycje.aggregate(suma=Sum('wartosc_pozycji'))['suma'] or Decimal('0.00')
                else:
                    # symulacja: suma z przeliczonych oblicz_wartosc() pozycji
                    total = sum(
                        (p.oblicz_wartosc() if isinstance(p.oblicz_wartosc(), Decimal)
                         else Decimal(str(p.oblicz_wartosc())))
                        for p in zam.pozycje.all()
                    ) or Decimal('0.00')
                stara = zam.wartosc_zamowienia or Decimal('0.00')
                if stara != total:
                    zam_zmienione += 1
                    if verbose:
                        self.stdout.write(
                            f"  Zamówienie {zam.numer}: {stara} → {total} zł"
                        )
                    if apply:
                        Zamowienie.objects.filter(pk=zam.pk).update(wartosc_zamowienia=total)

            if not apply:
                transaction.set_rollback(True)

        tryb = 'ZAPISANO' if apply else 'DRY-RUN (bez zmian)'
        self.stdout.write(self.style.SUCCESS(
            f"[{tryb}] Pozycje do przeliczenia: {poz_zmienione}, zamówienia: {zam_zmienione}."
        ))
        if not apply and (poz_zmienione or zam_zmienione):
            self.stdout.write("Uruchom z --apply, aby zapisać.")
