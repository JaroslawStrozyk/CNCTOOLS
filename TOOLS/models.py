# tools/models.py
from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError


class Kategoria(models.Model):
    nazwa = models.CharField(max_length=100, unique=True)

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

    class Meta:
        verbose_name_plural = "Dostawcy"
        ordering = ['nazwa_firmy']

    def __str__(self):
        return f"{self.kod_dostawcy} - {self.nazwa_firmy}"


class Lokalizacja(models.Model):
    szafa = models.CharField(max_length=50)
    kolumna = models.CharField(max_length=50)
    polka = models.CharField(max_length=50)

    class Meta:
        verbose_name_plural = "Lokalizacje"
        unique_together = ['szafa', 'kolumna', 'polka']
        ordering = ['szafa', 'kolumna', 'polka']

    def __str__(self):
        return f"{self.szafa}/{self.kolumna}/{self.polka}"


class Maszyna(models.Model):
    nazwa = models.CharField(max_length=100, unique=True)

    class Meta:
        verbose_name_plural = "Maszyny"
        ordering = ['nazwa']

    def __str__(self):
        return self.nazwa


class Pracownik(models.Model):
    karta = models.CharField(max_length=50, unique=True)
    nazwisko = models.CharField(max_length=100)
    imie = models.CharField(max_length=100)

    class Meta:
        verbose_name_plural = "Pracownicy"
        ordering = ['nazwisko', 'imie']

    def __str__(self):
        return f"{self.nazwisko} {self.imie} ({self.karta})"


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
    stan_minimalny = models.PositiveIntegerField(default=5)
    stan_maksymalny = models.PositiveIntegerField(default=20)
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
    opakowanie = models.CharField(
        max_length=10,
        choices=OPAKOWANIE_CHOICES,
        default='szt'
    )
    ilosc_w_opakowaniu = models.PositiveIntegerField(default=1)

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
    jednostka = models.CharField(
        max_length=10,
        choices=JEDNOSTKA_CHOICES,
        default='szt'
    )
    ilosc_w_komplecie = models.PositiveIntegerField(default=1)

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
    data_wydania = models.DateTimeField(auto_now_add=True)
    data_zwrotu = models.DateTimeField(null=True, blank=True)
    uwagi = models.TextField(blank=True)

    class Meta:
        verbose_name_plural = "Historia użycia narzędzi"
        ordering = ['-data_wydania']

    def __str__(self):
        return f"{self.egzemplarz} -> {self.pracownik} ({self.data_wydania})"


class Uszkodzenie(models.Model):
    egzemplarz = models.ForeignKey(
        EgzemplarzNarzedzia,
        on_delete=models.CASCADE,
        related_name='uszkodzenia',
        null=True,
        blank=True
    )
    data_uszkodzenia = models.DateTimeField(auto_now_add=True)
    opis_uszkodzenia = models.TextField(null=True)
    pracownik = models.ForeignKey(
        Pracownik,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='zgloszone_uszkodzenia'
    )

    class Meta:
        verbose_name_plural = "Uszkodzenia"
        ordering = ['-data_uszkodzenia']

    def __str__(self):
        return f"Uszkodzenie: {self.egzemplarz} - {self.data_uszkodzenia}"


class Zamowienie(models.Model):
    STATUS_CHOICES = [
        ('draft', 'Wersja robocza'),
        ('verified', 'Zweryfikowane'),
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
    data_utworzenia = models.DateTimeField(auto_now_add=True)
    data_wyslania = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    uwagi = models.TextField(blank=True)

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
    ilosc_zamowiona = models.PositiveIntegerField()
    jednostka = models.CharField(max_length=10, choices=JEDNOSTKA_CHOICES, default='szt')
    ilosc_w_komplecie = models.PositiveIntegerField(default=1)
    cena_jednostkowa = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True
    )
    ilosc_dostarczona = models.PositiveIntegerField(default=0)
    zrealizowane = models.BooleanField(default=False)

    class Meta:
        verbose_name_plural = "Pozycje zamówień"
        ordering = ['zamowienie', 'id']

    def __str__(self):
        return f"{self.zamowienie.numer} - {self.narzedzie_typ.opis} x{self.ilosc_zamowiona}"


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

    class Meta:
        verbose_name_plural = "Pozycje realizacji"
        ordering = ['realizacja', 'id']

    def __str__(self):
        return f"{self.realizacja} - {self.pozycja_zamowienia.narzedzie_typ.opis} x{self.ilosc_przyjeta}"


