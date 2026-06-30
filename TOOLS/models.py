# tools/models.py
from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.utils import timezone


class Kategoria(models.Model):
    # Grupy stanowiskowe widzące tylko narzędzia z przypisanych kategorii.
    # Wartość null = kategoria niedostępna dla stanowisk tokarz/frezer/ślusarz
    # (widzą ją wyłącznie pozostałe role: admin/logistyka/magazyn/kierownik/
    # technologia/brygadzista/produkcja).
    GRUPA_STANOWISKA_CHOICES = [
        ('tokarz', 'tokarz'),
        ('frezer', 'frezer'),
        ('ślusarz', 'ślusarz'),
    ]

    nazwa = models.CharField(max_length=100, unique=True)
    grupa_stanowiska = models.CharField(
        max_length=20,
        choices=GRUPA_STANOWISKA_CHOICES,
        null=True,
        blank=True,
        verbose_name='Grupa stanowiska',
        help_text='Jeśli ustawione, tylko userzy z tej grupy stanowiska zobaczą narzędzia z tej kategorii w widoku Produkcja/Magazyn.',
    )

    class Meta:
        verbose_name_plural = "Kategorie"
        ordering = ['nazwa']

    def __str__(self):
        return self.nazwa


class Podkategoria(models.Model):
    nazwa = models.CharField(max_length=100)
    kategoria = models.ForeignKey(
        Kategoria,
        on_delete=models.CASCADE,
        related_name='podkategorie'
    )

    class Meta:
        verbose_name_plural = "Podkategorie"
        unique_together = ['nazwa', 'kategoria']
        ordering = ['kategoria__nazwa', 'nazwa']

    def __str__(self):
        return f"{self.kategoria.nazwa} / {self.nazwa}"


class Dostawca(models.Model):
    kod_dostawcy = models.CharField(max_length=50, unique=True)
    nazwa_firmy = models.CharField(max_length=200)
    nip = models.CharField(max_length=20, blank=True, null=True)
    adres = models.TextField(blank=True, null=True)
    telefon = models.CharField(max_length=20, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    generuj_csv = models.BooleanField(
        default=False,
        verbose_name='Generuj plik CSV',
        help_text='Jeśli zaznaczone, do emaila z zamówieniem dla tego dostawcy dołączany jest plik CSV (separator "|").'
    )

    class Meta:
        verbose_name_plural = "Dostawcy"
        ordering = ['nazwa_firmy']

    def __str__(self):
        return f"{self.kod_dostawcy} - {self.nazwa_firmy}"


class NumerKatalogowyDostawcy(models.Model):
    # Mapowanie nasz numer katalogowy ↔ numer katalogowy dostawcy (per dostawca).
    # Wykorzystywane w ostatniej fazie wysyłki zamówienia: tabela HTML + ewentualny załącznik CSV.
    narzedzie = models.ForeignKey(
        'NarzedzieMagazynowe',
        on_delete=models.CASCADE,
        related_name='numery_dostawcow'
    )
    dostawca = models.ForeignKey(
        Dostawca,
        on_delete=models.CASCADE,
        related_name='numery_katalogowe_narzedzi'
    )
    nr_katalogowy_dostawcy = models.CharField(
        max_length=100,
        verbose_name='Nr katalogowy u dostawcy'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Numer katalogowy dostawcy"
        verbose_name_plural = "Numery katalogowe dostawców"
        unique_together = [('narzedzie', 'dostawca')]
        ordering = ['dostawca__nazwa_firmy', 'narzedzie__numer_katalogowy']

    def __str__(self):
        return f"{self.dostawca.nazwa_firmy} → {self.nr_katalogowy_dostawcy}"


class Lokalizacja(models.Model):
    szafa = models.CharField(max_length=50)
    kolumna = models.CharField(max_length=50)
    polka = models.CharField(max_length=50)

    class Meta:
        verbose_name_plural = "Lokalizacje"
        unique_together = ['szafa', 'kolumna', 'polka']
        ordering = ['szafa', 'kolumna', 'polka']

    def __str__(self):
        return f"{self.szafa}/{self.polka}/{self.kolumna}"


class Maszyna(models.Model):
    nazwa = models.CharField(max_length=100, unique=True)

    class Meta:
        verbose_name_plural = "Maszyny"
        ordering = ['nazwa']

    def __str__(self):
        return self.nazwa


class Pracownik(models.Model):
    karta = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        verbose_name='Nr karty'
    )
    nazwisko = models.CharField(max_length=100)
    imie = models.CharField(max_length=100)
    user = models.OneToOneField(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='pracownik',
        verbose_name='Konto użytkownika'
    )
    pobieranie_narzedzi = models.BooleanField(
        default=True,
        verbose_name='Pobieranie narzędzi',
        help_text='Czy pracownik może pobierać narzędzia (pojawia się na listach wyboru)'
    )

    class Meta:
        verbose_name_plural = "Pracownicy"
        ordering = ['nazwisko', 'imie']

    def __str__(self):
        if self.karta:
            return f"{self.nazwisko} {self.imie} ({self.karta})"
        return f"{self.nazwisko} {self.imie}"

    def save(self, *args, **kwargs):
        # Auto-uzupełnienie imie/nazwisko z powiązanego User, gdy puste
        if self.user_id and (not self.nazwisko or not self.imie):
            if not self.nazwisko and self.user.last_name:
                self.nazwisko = self.user.last_name
            if not self.imie and self.user.first_name:
                self.imie = self.user.first_name
        super().save(*args, **kwargs)


class FakturaZakupu(models.Model):
    numer_faktury = models.CharField(max_length=100, unique=True)
    data_wystawienia = models.DateField()
    dostawca = models.ForeignKey(
        Dostawca,
        on_delete=models.PROTECT,
        related_name='faktury'
    )
    plik = models.FileField(upload_to='faktury/', blank=True, null=True)
    rozliczone = models.BooleanField(default=False)

    class Meta:
        verbose_name_plural = "Faktury zakupu"
        ordering = ['-data_wystawienia']

    def __str__(self):
        return f"{self.numer_faktury} ({self.data_wystawienia})"


class NarzedzieMagazynowe(models.Model):
    OPAKOWANIE_CHOICES = [
        ('szt', 'Sztuka'),
        ('kompl', 'Komplet'),
    ]

    podkategoria = models.ForeignKey(
        Podkategoria,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='narzedzia'
    )
    opis = models.TextField()
    numer_katalogowy = models.CharField(max_length=100, blank=True, null=True)
    obraz = models.ImageField(upload_to='narzedzia/', blank=True, null=True)
    stan_minimalny = models.PositiveIntegerField(default=0)
    stan_maksymalny = models.PositiveIntegerField(default=0)
    ostatni_dostawca = models.ForeignKey(
        Dostawca,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='narzedzia_dostarczane'
    )
    domyslna_lokalizacja = models.ForeignKey(
        Lokalizacja,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='narzedzia_domyslne'
    )
    # Jednostka zakupu - jak zamawiamy narzędzie
    opakowanie = models.CharField(
        max_length=10,
        choices=OPAKOWANIE_CHOICES,
        default='szt',
        verbose_name='Jednostka zakupu'
    )
    # Ilość sztuk w komplecie zakupowym
    ilosc_w_opakowaniu = models.PositiveIntegerField(
        default=1,
        verbose_name='Ilość w komplecie'
    )
    # Ręczna kontrola zamówień - generator czyta pole reczne_dodanie zamiast min/max
    reczna_kontrola = models.BooleanField(
        default=False,
        verbose_name='Ręczna kontrola zamówień',
        help_text='Zaznacz, aby generator zamówień używał pola "Ręczne dodanie" zamiast automatycznego wyliczania z limitów min/max.'
    )
    reczne_dodanie = models.PositiveIntegerField(
        default=0,
        verbose_name='Ręczne dodanie',
        help_text='Ilość do zamówienia przy ręcznej kontroli. Po odczycie przez generator pole jest zerowane.'
    )
    # Czy można wydawać pojedyncze sztuki z kompletu
    wydawanie_sztuk = models.BooleanField(
        default=False,
        verbose_name='Możliwość wydawania pojedynczych sztuk',
        help_text='Jeśli zaznaczone, można wydawać pojedyncze sztuki z kompletu. Jeśli nie, tylko całe komplety.'
    )
    # Ostatnia cena jednostkowa — ustawiana ręcznie w modalu Zakupy lub automatycznie
    # propagowana z PozycjaZamowienia.save() (przyciski "Zmień cenę" / "Zapisz" w Zamowienia.vue).
    cena_jednostkowa = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name='Cena jednostkowa',
        help_text='Ostatnia użyta lub ręcznie ustawiona cena jednostkowa.'
    )
    # True: cena propagowana z pozycji zamówienia (PozycjaZamowienia.save()) — wartość
    # wyliczona ma priorytet i (dopóki > 0) nie podlega ręcznej edycji w modalu Zakupy.
    # Ręczna zmiana ceny (gdy dozwolona) zdejmuje flagę w serializerze.
    cena_z_zamowienia = models.BooleanField(
        default=False,
        verbose_name='Cena wyliczona z zamówień',
        help_text='Cena nadpisana automatycznie z pozycji zamówienia.'
    )
    # Narzędzie utworzone w generatorze wraz z zamówieniem — kasowane razem z zamówieniem
    # (tylko jeśli nie ma jeszcze egzemplarzy). Kategorie/podkategorie zostają.
    utworzone_wraz_z_zamowieniem = models.ForeignKey(
        'Zamowienie',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='narzedzia_utworzone_recznie',
        verbose_name='Utworzone wraz z zamówieniem',
        help_text='Jeśli ustawione, narzędzie zostanie skasowane razem z tym zamówieniem (gdy nie ma egzemplarzy).'
    )

    class Meta:
        verbose_name_plural = "Narzędzia magazynowe"
        ordering = ['podkategoria__kategoria__nazwa', 'podkategoria__nazwa', 'opis']

    def clean(self):
        if self.opakowanie == 'kompl' and self.ilosc_w_opakowaniu <= 1:
            raise ValidationError('Dla opakowania "Komplet" ilość w opakowaniu musi być większa niż 1.')

    def __str__(self):
        if self.podkategoria:
            return f"{self.podkategoria} - {self.opis}"
        return self.opis


class EgzemplarzNarzedzia(models.Model):
    STAN_CHOICES = [
        ('nowe', 'Nowe'),
        ('uzywane', 'Używane'),
        ('uszkodzone', 'Uszkodzone'),
        ('uszkodzone_regeneracja', 'Uszkodzone do regeneracji'),
    ]

    JEDNOSTKA_CHOICES = [
        ('szt', 'Sztuka'),
        ('kompl', 'Komplet'),
    ]

    narzedzie_typ = models.ForeignKey(
        NarzedzieMagazynowe,
        on_delete=models.CASCADE,
        related_name='egzemplarze'
    )
    stan = models.CharField(max_length=30, choices=STAN_CHOICES, default='nowe')
    lokalizacja = models.ForeignKey(
        Lokalizacja,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='egzemplarze'
    )
    faktura_zakupu = models.ForeignKey(
        FakturaZakupu,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='egzemplarze'
    )
    zamowienie = models.ForeignKey(
        'Zamowienie',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='egzemplarze'
    )
    data_zakupu = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    data_modyfikacji = models.DateTimeField(auto_now=True)
    oznaczenie = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name='Oznaczenie'
    )
    jednostka = models.CharField(
        max_length=10,
        choices=JEDNOSTKA_CHOICES,
        default='szt'
    )
    ilosc_w_komplecie = models.PositiveIntegerField(default=1)
    komplet_zrodlowy = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='wydane_sztuki',
        help_text='Komplet, z którego wydano te sztuki'
    )
    nowy_wpis = models.BooleanField(
        default=False,
        verbose_name='Nowy wpis',
        help_text='Egzemplarz z auto-wygenerowanym oznaczeniem oczekujący na pobranie etykiety'
    )

    class Meta:
        verbose_name_plural = "Egzemplarze narzędzi"
        ordering = ['-data_zakupu']

    def __str__(self):
        return f"{self.narzedzie_typ} - {self.stan} ({self.id})"


class HistoriaUzyciaNarzedzia(models.Model):
    egzemplarz = models.ForeignKey(
        EgzemplarzNarzedzia,
        on_delete=models.CASCADE,
        related_name='historia'
    )
    maszyna = models.ForeignKey(
        Maszyna,
        on_delete=models.SET_NULL,
        null=True,
        related_name='historia_uzycia'
    )
    pracownik = models.ForeignKey(
        Pracownik,
        on_delete=models.SET_NULL,
        null=True,
        related_name='historia_uzycia'
    )
    pracownik_zwracajacy = models.ForeignKey(
        Pracownik,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='historia_zwrotow',
        verbose_name='Pracownik zwracający'
    )
    data_wydania = models.DateTimeField(auto_now_add=True)
    data_zwrotu = models.DateTimeField(null=True, blank=True)
    uwagi = models.TextField(blank=True)
    nr_zlecenia = models.CharField(max_length=100, blank=True, null=True, verbose_name='Nr zlecenia')
    stan_po_zwrocie = models.CharField(max_length=30, blank=True, null=True)

    class Meta:
        verbose_name_plural = "Historia użycia narzędzi"
        ordering = ['-data_wydania']

    def __str__(self):
        return f"{self.egzemplarz} -> {self.pracownik} ({self.data_wydania})"


class Uszkodzenie(models.Model):
    egzemplarz = models.ForeignKey(
        EgzemplarzNarzedzia,
        on_delete=models.SET_NULL,
        related_name='uszkodzenia',
        null=True,
        blank=True
    )
    # Pola do przechowania danych usuniętego egzemplarza
    narzedzie_typ = models.ForeignKey(
        NarzedzieMagazynowe,
        on_delete=models.CASCADE,
        related_name='uszkodzenia_narzedzi',
        null=True,
        blank=True
    )
    narzedzie_opis = models.CharField(max_length=500, blank=True)
    numer_katalogowy = models.CharField(max_length=200, blank=True)
    kategoria_narzedzia = models.CharField(max_length=300, blank=True)
    lokalizacja_opis = models.CharField(max_length=200, blank=True)
    stan = models.CharField(max_length=50, blank=True)
    maszyna_nazwa = models.CharField(max_length=200, blank=True)
    pracownik_nazwisko = models.CharField(max_length=100, blank=True)
    pracownik_imie = models.CharField(max_length=100, blank=True)

    data_uszkodzenia = models.DateTimeField(auto_now_add=True)
    opis_uszkodzenia = models.TextField(null=True, blank=True)
    pracownik = models.ForeignKey(
        Pracownik,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='zgloszone_uszkodzenia'
    )
    # Pola karty uszkodzenia
    numer_karty = models.CharField(max_length=15, unique=True, blank=True, null=True)
    przyczyna_uszkodzenia = models.TextField(blank=True)
    stracony_czas = models.IntegerField(null=True, blank=True)  # wartość w minutach
    typ_zglaszajacego = models.CharField(max_length=20, blank=True)  # 'pobierajacy' lub 'zwracajacy'
    nazwisko_zglaszajacego = models.CharField(max_length=200, blank=True)

    class Meta:
        verbose_name_plural = "Uszkodzenia"
        ordering = ['-data_uszkodzenia']

    @classmethod
    def generuj_numer_karty(cls):
        """Generuje unikalny numer karty uszkodzenia w formacie ROK/NNN"""
        rok = timezone.now().year
        # UWAGA: maksimum liczone NUMERYCZNIE, nie przez order_by('-numer_karty').
        # Sort tekstowy myli się po przekroczeniu 999 ('999' > '1000' jako string),
        # przez co generator zapętlał się na istniejącym numerze → kolizja unique.
        ostatni_numer = 0
        numery = cls.objects.filter(
            numer_karty__startswith=f'{rok}/'
        ).exclude(
            numer_karty__endswith='R'
        ).values_list('numer_karty', flat=True)
        for nr in numery:
            try:
                n = int(nr.split('/')[1])
            except (ValueError, IndexError):
                continue
            if n > ostatni_numer:
                ostatni_numer = n
        return f'{rok}/{ostatni_numer + 1:03d}'

    @classmethod
    def generuj_numer_karty_regeneracji(cls):
        """Generuje unikalny numer karty regeneracji w formacie ROK/NNNR"""
        rok = timezone.now().year
        # UWAGA: maksimum liczone NUMERYCZNIE (patrz komentarz w generuj_numer_karty).
        ostatni_numer = 0
        numery = cls.objects.filter(
            numer_karty__startswith=f'{rok}/',
            numer_karty__endswith='R'
        ).values_list('numer_karty', flat=True)
        for nr in numery:
            try:
                n = int(nr.split('/')[1].rstrip('R'))
            except (ValueError, IndexError):
                continue
            if n > ostatni_numer:
                ostatni_numer = n
        return f'{rok}/{ostatni_numer + 1:03d}R'

    def __str__(self):
        if self.egzemplarz:
            return f"Uszkodzenie: {self.egzemplarz} - {self.data_uszkodzenia}"
        return f"Uszkodzenie: {self.narzedzie_opis} - {self.data_uszkodzenia}"


class Zamowienie(models.Model):
    STATUS_CHOICES = [
        ('draft', 'Wersja robocza'),
        ('pending_approval', 'Oczekuje na zatwierdzenie'),
        ('verified', 'Zatwierdzone'),
        ('sent', 'Wysłane'),
        ('partially_received', 'Częściowo odebrane'),
        ('completed', 'Zrealizowane'),
    ]

    numer = models.CharField(max_length=50, unique=True)
    dostawca = models.ForeignKey(
        Dostawca,
        on_delete=models.PROTECT,
        related_name='zamowienia'
    )
    email_docelowy = models.EmailField(blank=True, null=True,
                                       help_text="Email dostawcy w momencie tworzenia zamówienia")
    data_utworzenia = models.DateTimeField(auto_now_add=True)
    data_wyslania = models.DateTimeField(null=True, blank=True)
    wartosc_zamowienia = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        help_text="Łączna wartość zamówienia"
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    uwagi = models.TextField(blank=True)
    nr_oferty_dostawcy = models.CharField(
        max_length=100,
        blank=True,
        default='',
        help_text="Nr oferty dostawcy, na podstawie której składane jest zamówienie (widoczny tylko dla logistyki)"
    )
    zrodlowe_zapotrzebowania = models.ManyToManyField(
        'ZapotrzebowanieTechnologa',
        blank=True,
        related_name='zamowienia',
        help_text="Zapotrzebowania technologów, z których pochodzi to zamówienie"
    )

    class Meta:
        verbose_name_plural = "Zamówienia"
        ordering = ['-data_utworzenia']

    def __str__(self):
        return f"{self.numer} - {self.dostawca.nazwa_firmy} ({self.status})"


class PozycjaZamowienia(models.Model):
    JEDNOSTKA_CHOICES = [
        ('szt', 'Sztuka'),
        ('kompl', 'Komplet'),
    ]

    zamowienie = models.ForeignKey(
        Zamowienie,
        on_delete=models.CASCADE,
        related_name='pozycje'
    )
    narzedzie_typ = models.ForeignKey(
        NarzedzieMagazynowe,
        on_delete=models.PROTECT,
        related_name='pozycje_zamowien'
    )
    # Spłaszczone dane z generatora (snapshot w momencie tworzenia)
    kategoria_nazwa = models.CharField(max_length=200, blank=True)
    podkategoria_nazwa = models.CharField(max_length=200, blank=True)
    narzedzie_opis = models.TextField(blank=True)
    numer_katalogowy = models.CharField(max_length=100, blank=True)

    ilosc_zamowiona = models.PositiveIntegerField()
    jednostka = models.CharField(max_length=10, choices=JEDNOSTKA_CHOICES, default='szt')
    ilosc_w_komplecie = models.PositiveIntegerField(default=1)
    cena_jednostkowa = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True
    )
    wartosc_pozycji = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        help_text="Wartość pozycji = ilość * cena jednostkowa"
    )
    ilosc_dostarczona = models.PositiveIntegerField(default=0)
    zrealizowane = models.BooleanField(default=False)

    class Meta:
        verbose_name_plural = "Pozycje zamówień"
        ordering = ['zamowienie', 'id']

    def __str__(self):
        return f"{self.zamowienie.numer} - {self.narzedzie_opis} x{self.ilosc_zamowiona}"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        if self.cena_jednostkowa is not None and self.narzedzie_typ_id:
            NarzedzieMagazynowe.objects.filter(pk=self.narzedzie_typ_id).update(
                cena_jednostkowa=self.cena_jednostkowa,
                cena_z_zamowienia=True
            )


class RealizacjaZamowienia(models.Model):
    zamowienie = models.ForeignKey(
        Zamowienie,
        on_delete=models.CASCADE,
        related_name='realizacje'
    )
    data_realizacji = models.DateTimeField(auto_now_add=True)
    lokalizacja_domyslna = models.ForeignKey(
        Lokalizacja,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='realizacje_zamowien'
    )
    uwagi = models.TextField(blank=True)

    class Meta:
        verbose_name_plural = "Realizacje zamówień"
        ordering = ['-data_realizacji']

    def __str__(self):
        return f"Realizacja {self.zamowienie.numer} - {self.data_realizacji}"


class PozycjaRealizacji(models.Model):
    realizacja = models.ForeignKey(
        RealizacjaZamowienia,
        on_delete=models.CASCADE,
        related_name='pozycje'
    )
    pozycja_zamowienia = models.ForeignKey(
        PozycjaZamowienia,
        on_delete=models.CASCADE,
        related_name='realizacje_pozycji'
    )
    ilosc_przyjeta = models.PositiveIntegerField()
    lokalizacja = models.ForeignKey(
        Lokalizacja,
        on_delete=models.SET_NULL,
        null=True,
        related_name='pozycje_realizacji'
    )
    faktura_zakupu = models.ForeignKey(
        'FakturaZakupu',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='pozycje_realizacji',
        help_text="Faktura zakupu dla tej pozycji (uzupełniane przez Logistyka)"
    )
    cena_jednostkowa = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Rzeczywista cena jednostkowa z faktury (uzupełniane przez Logistyka)"
    )

    class Meta:
        verbose_name_plural = "Pozycje realizacji"
        ordering = ['realizacja', 'id']

    def __str__(self):
        return f"{self.realizacja} - {self.pozycja_zamowienia.narzedzie_typ.opis} x{self.ilosc_przyjeta}"


class PozycjaGeneratora(models.Model):
    """
    Model tymczasowy przechowujący pozycje z generatora zamówień.
    Zawiera edytowalne pola: dostawca, cena jednostkowa, ilość.
    """
    narzedzie_typ = models.OneToOneField(
        NarzedzieMagazynowe,
        on_delete=models.CASCADE,
        related_name='pozycja_generatora',
        unique=True
    )
    dostawca = models.ForeignKey(
        Dostawca,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='pozycje_generatora'
    )
    cena_jednostkowa = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        help_text="Cena jednostkowa w PLN"
    )
    ilosc_do_zamowienia = models.PositiveIntegerField(
        default=0,
        help_text="Obliczona lub ręcznie edytowana ilość"
    )
    zrodlo = models.CharField(
        max_length=50,
        default='auto',
        help_text="Źródło pozycji: auto, reczne, zapotrzebowanie"
    )
    utworzone_narzedzie = models.BooleanField(
        default=False,
        help_text="True = narzędzie zostało utworzone ręcznie razem z tą pozycją (przy generowaniu zamówienia zostanie podpięte przez utworzone_wraz_z_zamowieniem)."
    )
    zrodlo_zapotrzebowanie_ids = models.CharField(
        max_length=200,
        blank=True,
        help_text="ID zapotrzebowań (ZAM-XXXX) — jeśli źródło=zapotrzebowanie"
    )
    data_utworzenia = models.DateTimeField(auto_now_add=True)
    data_modyfikacji = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = "Pozycje generatora zamówień"
        ordering = ['narzedzie_typ__podkategoria__kategoria__nazwa', 'narzedzie_typ__opis']

    def __str__(self):
        return f"Generator: {self.narzedzie_typ.opis} - {self.ilosc_do_zamowienia} szt."


class ZapotrzebowanieTechnologa(models.Model):
    """
    Model przechowujący zapotrzebowania technologów na narzędzia.
    Każde zapotrzebowanie może mieć wiele pozycji (narzędzi do zamówienia).
    """
    STATUS_CHOICES = [
        ('draft', 'Robocze'),
        ('submitted', 'Wysłane'),
        ('completed', 'Zrealizowane'),
        ('ordered', 'W zamówieniu'),
        ('cancelled', 'Anulowane'),
    ]

    technolog = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='zapotrzebowania'
    )
    data_utworzenia = models.DateTimeField(auto_now_add=True)
    data_wyslania = models.DateTimeField(null=True, blank=True)
    data_realizacji = models.DateTimeField(null=True, blank=True)
    zrealizowany_przez = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='zrealizowane_zapotrzebowania'
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    uwagi = models.TextField(blank=True)

    class Meta:
        verbose_name = "Zapotrzebowanie technologa"
        verbose_name_plural = "Zapotrzebowania technologów"
        ordering = ['-data_utworzenia']

    def __str__(self):
        technolog_nazwa = self.technolog.username if self.technolog else 'Nieznany'
        return f"ZAP-{self.id} ({technolog_nazwa}) - {self.get_status_display()}"


class LogEntry(models.Model):
    """
    Model przechowujący logi operacji użytkowników.
    Logi z dzisiaj są bieżące, starsze archiwizowane do plików.
    """
    STATUS_CHOICES = [
        ('INFO', 'Info'),
        ('SUCCESS', 'Sukces'),
        ('WARNING', 'Ostrzeżenie'),
        ('ERROR', 'Błąd'),
    ]

    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='INFO')
    osoba = models.CharField(max_length=200, default='-')
    operacja = models.TextField()

    class Meta:
        verbose_name = "Wpis logu"
        verbose_name_plural = "Wpisy logów"
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['-timestamp']),
        ]

    def __str__(self):
        return f"[{self.timestamp}] {self.status} - {self.osoba}: {self.operacja[:50]}"


class PozycjaZapotrzebowania(models.Model):
    """
    Pozycja w zapotrzebowaniu technologa.
    Przechowuje snapshot danych narzędzia oraz pola specyficzne dla technologa.
    """
    zapotrzebowanie = models.ForeignKey(
        ZapotrzebowanieTechnologa,
        related_name='pozycje',
        on_delete=models.CASCADE
    )
    narzedzie_typ = models.ForeignKey(
        NarzedzieMagazynowe,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='pozycje_zapotrzebowan'
    )

    # Snapshot danych (wypełniane automatycznie lub ręcznie)
    kategoria_nazwa = models.CharField(max_length=200, blank=True)
    podkategoria_nazwa = models.CharField(max_length=200, blank=True)
    specyfikacja = models.TextField(blank=True)
    numer_katalogowy = models.CharField(max_length=100, blank=True)

    # Rodzaj: sztuki czy komplety. Dla pozycji z magazynu = snapshot opakowania narzędzia
    # (tylko do odczytu w karcie), dla pozycji ręcznych = wybór technologa (domyślnie szt).
    opakowanie = models.CharField(
        max_length=20,
        choices=NarzedzieMagazynowe.OPAKOWANIE_CHOICES,
        default='szt',
    )

    # Pola technologa
    nr_klienta = models.CharField(max_length=100, blank=True)
    nr_zlecenia = models.CharField(max_length=100, blank=True)
    ilosc = models.PositiveIntegerField(default=1)
    uwagi = models.TextField(blank=True)

    data_dodania = models.DateTimeField(auto_now_add=True)
    w_zamowieniu = models.BooleanField(default=False, help_text="Czy pozycja trafiła do generatora zamówień")

    class Meta:
        verbose_name = "Pozycja zapotrzebowania"
        verbose_name_plural = "Pozycje zapotrzebowań"
        ordering = ['data_dodania']

    def __str__(self):
        narzedzie = self.specyfikacja or (self.narzedzie_typ.opis if self.narzedzie_typ else 'Brak')
        return f"{self.zapotrzebowanie} - {narzedzie} x{self.ilosc}"