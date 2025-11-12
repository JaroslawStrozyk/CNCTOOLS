# tools/admin.py
from django.contrib import admin
from .models import (
    Kategoria, Podkategoria, NarzedzieMagazynowe, EgzemplarzNarzedzia,
    Lokalizacja, Maszyna, HistoriaUzyciaNarzedzia, FakturaZakupu,
    Dostawca, Pracownik, Uszkodzenie, Zamowienie, PozycjaZamowienia,
    RealizacjaZamowienia, PozycjaRealizacji
)


@admin.register(Kategoria)
class KategoriaAdmin(admin.ModelAdmin):
    list_display = ['nazwa']
    search_fields = ['nazwa']


class PodkategoriaInline(admin.TabularInline):
    model = Podkategoria
    extra = 1


@admin.register(Podkategoria)
class PodkategoriaAdmin(admin.ModelAdmin):
    list_display = ['nazwa', 'kategoria']
    list_filter = ['kategoria']
    search_fields = ['nazwa', 'kategoria__nazwa']


@admin.register(Dostawca)
class DostawcaAdmin(admin.ModelAdmin):
    list_display = ['kod_dostawcy', 'nazwa_firmy', 'nip', 'email', 'telefon']
    search_fields = ['kod_dostawcy', 'nazwa_firmy', 'nip']
    list_filter = ['nazwa_firmy']


@admin.register(Lokalizacja)
class LokalizacjaAdmin(admin.ModelAdmin):
    list_display = ['szafa', 'kolumna', 'polka']
    list_filter = ['szafa']
    search_fields = ['szafa', 'kolumna', 'polka']
    ordering = ['szafa', 'kolumna', 'polka']


@admin.register(Maszyna)
class MaszynaAdmin(admin.ModelAdmin):
    list_display = ['nazwa']
    search_fields = ['nazwa']


@admin.register(Pracownik)
class PracownikAdmin(admin.ModelAdmin):
    list_display = ['karta', 'nazwisko', 'imie']
    search_fields = ['karta', 'nazwisko', 'imie']
    ordering = ['nazwisko', 'imie']


@admin.register(FakturaZakupu)
class FakturaZakupuAdmin(admin.ModelAdmin):
    list_display = ['numer_faktury', 'data_wystawienia', 'dostawca', 'rozliczone']
    list_filter = ['rozliczone', 'dostawca', 'data_wystawienia']
    search_fields = ['numer_faktury', 'dostawca__nazwa_firmy']
    date_hierarchy = 'data_wystawienia'
    ordering = ['-data_wystawienia']


@admin.register(NarzedzieMagazynowe)
class NarzedzieMagazynoweAdmin(admin.ModelAdmin):
    list_display = ['opis', 'podkategoria', 'numer_katalogowy', 'stan_minimalny', 'stan_maksymalny', 'ostatni_dostawca']
    list_filter = ['podkategoria__kategoria', 'podkategoria', 'ostatni_dostawca']
    search_fields = ['opis', 'numer_katalogowy']
    raw_id_fields = ['podkategoria', 'ostatni_dostawca', 'domyslna_lokalizacja']


@admin.register(EgzemplarzNarzedzia)
class EgzemplarzNarzedziaAdmin(admin.ModelAdmin):
    list_display = ['id', 'narzedzie_typ', 'stan', 'lokalizacja', 'jednostka', 'ilosc_w_komplecie', 'faktura_zakupu', 'data_zakupu']
    list_filter = ['stan', 'jednostka', 'data_zakupu']
    search_fields = ['narzedzie_typ__opis', 'faktura_zakupu__numer_faktury']
    raw_id_fields = ['narzedzie_typ', 'lokalizacja', 'faktura_zakupu']
    date_hierarchy = 'data_zakupu'
    ordering = ['-data_zakupu']


@admin.register(HistoriaUzyciaNarzedzia)
class HistoriaUzyciaNarzedziaAdmin(admin.ModelAdmin):
    list_display = ['egzemplarz', 'pracownik', 'maszyna', 'data_wydania', 'data_zwrotu']
    list_filter = ['data_wydania', 'data_zwrotu', 'maszyna']
    search_fields = ['egzemplarz__narzedzie_typ__opis', 'pracownik__nazwisko', 'pracownik__imie']
    raw_id_fields = ['egzemplarz', 'maszyna', 'pracownik']
    date_hierarchy = 'data_wydania'
    ordering = ['-data_wydania']


@admin.register(Uszkodzenie)
class UszkodzenieAdmin(admin.ModelAdmin):
    list_display = ['egzemplarz', 'data_uszkodzenia', 'pracownik', 'opis_uszkodzenia']
    list_filter = ['data_uszkodzenia']
    search_fields = ['egzemplarz__narzedzie_typ__opis', 'opis_uszkodzenia', 'pracownik__nazwisko']
    raw_id_fields = ['egzemplarz', 'pracownik']
    date_hierarchy = 'data_uszkodzenia'
    ordering = ['-data_uszkodzenia']


class PozycjaZamowieniaInline(admin.TabularInline):
    model = PozycjaZamowienia
    extra = 1
    fields = ['narzedzie_typ', 'ilosc_zamowiona', 'jednostka', 'ilosc_w_komplecie', 'cena_jednostkowa', 'ilosc_dostarczona', 'zrealizowane']
    raw_id_fields = ['narzedzie_typ']


@admin.register(Zamowienie)
class ZamowienieAdmin(admin.ModelAdmin):
    list_display = ['numer', 'dostawca', 'status', 'data_utworzenia', 'data_wyslania']
    list_filter = ['status', 'dostawca', 'data_utworzenia']
    search_fields = ['numer', 'dostawca__nazwa_firmy']
    date_hierarchy = 'data_utworzenia'
    ordering = ['-data_utworzenia']
    inlines = [PozycjaZamowieniaInline]


@admin.register(PozycjaZamowienia)
class PozycjaZamowieniaAdmin(admin.ModelAdmin):
    list_display = ['zamowienie', 'narzedzie_typ', 'ilosc_zamowiona', 'jednostka', 'ilosc_w_komplecie', 'ilosc_dostarczona', 'zrealizowane']
    list_filter = ['jednostka', 'zrealizowane', 'zamowienie__status']
    search_fields = ['zamowienie__numer', 'narzedzie_typ__opis']
    raw_id_fields = ['zamowienie', 'narzedzie_typ']


class PozycjaRealizacjiInline(admin.TabularInline):
    model = PozycjaRealizacji
    extra = 1
    fields = ['pozycja_zamowienia', 'ilosc_przyjeta', 'lokalizacja']
    raw_id_fields = ['pozycja_zamowienia', 'lokalizacja']


@admin.register(RealizacjaZamowienia)
class RealizacjaZamowieniaAdmin(admin.ModelAdmin):
    list_display = ['zamowienie', 'data_realizacji', 'lokalizacja_domyslna']
    list_filter = ['data_realizacji']
    search_fields = ['zamowienie__numer']
    date_hierarchy = 'data_realizacji'
    ordering = ['-data_realizacji']
    raw_id_fields = ['zamowienie', 'lokalizacja_domyslna']
    inlines = [PozycjaRealizacjiInline]


@admin.register(PozycjaRealizacji)
class PozycjaRealizacjiAdmin(admin.ModelAdmin):
    list_display = ['realizacja', 'pozycja_zamowienia', 'ilosc_przyjeta', 'lokalizacja']
    search_fields = ['realizacja__zamowienie__numer', 'pozycja_zamowienia__narzedzie_typ__opis']
    raw_id_fields = ['realizacja', 'pozycja_zamowienia', 'lokalizacja']