# tools/admin.py
from django.contrib import admin, messages
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User, Group
from django.shortcuts import redirect
from django.urls import path
from django.core.management import call_command
from io import StringIO
from .models import (
    Kategoria, Podkategoria, NarzedzieMagazynowe, EgzemplarzNarzedzia,
    Lokalizacja, Maszyna, HistoriaUzyciaNarzedzia, FakturaZakupu,
    Dostawca, Pracownik, Uszkodzenie, Zamowienie, PozycjaZamowienia,
    RealizacjaZamowienia, PozycjaRealizacji
)


# Inline dla Pracownika w panelu User
class PracownikInline(admin.StackedInline):
    model = Pracownik
    can_delete = False
    verbose_name = 'Dane pracownika'
    verbose_name_plural = 'Dane pracownika'
    fields = ['karta', 'pobieranie_narzedzi']


# Rozszerzony UserAdmin z inline Pracownik
class UserAdmin(BaseUserAdmin):
    inlines = [PracownikInline]
    list_display = ['username', 'email', 'first_name', 'last_name', 'get_grupy', 'get_karta', 'get_pobieranie', 'is_staff']
    search_fields = ['username', 'email', 'first_name', 'last_name']

    @admin.display(description='Grupy')
    def get_grupy(self, obj):
        grupy = obj.groups.all()
        if grupy:
            return ', '.join([g.name for g in grupy])
        return '-'

    @admin.display(description='Nr karty')
    def get_karta(self, obj):
        if hasattr(obj, 'pracownik') and obj.pracownik:
            return obj.pracownik.karta
        return '-'

    @admin.display(description='Pobieranie', boolean=True)
    def get_pobieranie(self, obj):
        if hasattr(obj, 'pracownik') and obj.pracownik:
            return obj.pracownik.pobieranie_narzedzi
        return None

    def save_formset(self, request, form, formset, change):
        """Synchronizuje first_name/last_name z User do imie/nazwisko w Pracownik"""
        instances = formset.save(commit=False)
        for instance in instances:
            if isinstance(instance, Pracownik):
                # Kopiuj dane z User do Pracownik
                user = form.instance
                instance.imie = user.first_name or ''
                instance.nazwisko = user.last_name or ''
                instance.save()
        formset.save_m2m()


# Przerejestrowujemy User z nowym UserAdmin
admin.site.unregister(User)
admin.site.register(User, UserAdmin)


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
    list_display = ['karta', 'nazwisko', 'imie', 'user', 'pobieranie_narzedzi']
    search_fields = ['karta', 'nazwisko', 'imie', 'user__username']
    list_filter = ['pobieranie_narzedzi', 'user__is_active']
    list_editable = ['pobieranie_narzedzi']
    ordering = ['nazwisko', 'imie']
    autocomplete_fields = ['user']
    actions = ['sync_selected_to_user', 'sync_selected_from_user']
    change_list_template = 'admin/TOOLS/pracownik/change_list.html'

    @admin.action(description='Synchronizuj zaznaczonych → User (Pracownik nadpisuje User)')
    def sync_selected_to_user(self, request, queryset):
        """Synchronizuje zaznaczonych Pracowników do User (tworzy User jeśli brak)"""
        utworzono = 0
        zsynchronizowano = 0
        dodano_grupe = 0

        # Pobierz grupę "produkcja"
        grupa_produkcja = Group.objects.filter(name='produkcja').first()

        for pracownik in queryset:
            if pracownik.user is None:
                # Utwórz nowego User
                username = self._generate_username(pracownik.imie, pracownik.nazwisko)
                user = User.objects.create_user(
                    username=username,
                    password='cnctools!',
                    first_name=pracownik.imie,
                    last_name=pracownik.nazwisko,
                    is_active=True,
                )
                # Przypisz grupę "produkcja"
                if grupa_produkcja:
                    user.groups.add(grupa_produkcja)
                pracownik.user = user
                pracownik.save(update_fields=['user'])
                utworzono += 1
            else:
                # Synchronizuj Pracownik → User
                user = pracownik.user
                changed = False
                if user.first_name != pracownik.imie or user.last_name != pracownik.nazwisko:
                    user.first_name = pracownik.imie
                    user.last_name = pracownik.nazwisko
                    user.save()
                    changed = True
                # Dodaj grupę "produkcja" jeśli User nie ma żadnej grupy
                if not user.groups.exists() and grupa_produkcja:
                    user.groups.add(grupa_produkcja)
                    dodano_grupe += 1
                    changed = True
                if changed:
                    zsynchronizowano += 1

        msg = []
        if utworzono:
            msg.append(f'Utworzono {utworzono} nowych kont User (z grupą produkcja)')
        if zsynchronizowano:
            msg.append(f'Zsynchronizowano {zsynchronizowano} rekordów')
        if dodano_grupe:
            msg.append(f'Dodano grupę produkcja: {dodano_grupe}')
        if not msg:
            msg.append('Brak zmian')

        self.message_user(request, '. '.join(msg), messages.SUCCESS)

    @admin.action(description='Synchronizuj zaznaczonych ← User (User nadpisuje Pracownik)')
    def sync_selected_from_user(self, request, queryset):
        """Synchronizuje zaznaczonych Pracowników z User (User nadpisuje Pracownika)"""
        zsynchronizowano = 0
        pominięto = 0

        for pracownik in queryset:
            if pracownik.user is None:
                pominięto += 1
                continue

            user = pracownik.user
            if pracownik.imie != user.first_name or pracownik.nazwisko != user.last_name:
                pracownik.imie = user.first_name
                pracownik.nazwisko = user.last_name
                pracownik.save()
                zsynchronizowano += 1

        msg = []
        if zsynchronizowano:
            msg.append(f'Zsynchronizowano {zsynchronizowano} rekordów')
        if pominięto:
            msg.append(f'Pominięto {pominięto} (brak powiązanego User)')
        if not msg:
            msg.append('Brak zmian')

        self.message_user(request, '. '.join(msg), messages.SUCCESS)

    def _generate_username(self, imie, nazwisko):
        """Generuje unikalny username w formacie imie.nazwisko"""
        import unicodedata

        def normalize(text):
            nfkd = unicodedata.normalize('NFKD', text.lower())
            ascii_text = ''.join(c for c in nfkd if not unicodedata.combining(c))
            ascii_text = ascii_text.replace('ł', 'l')
            return ''.join(c for c in ascii_text if c.isalnum())

        base_username = f"{normalize(imie)}.{normalize(nazwisko)}"
        username = base_username
        counter = 2
        while User.objects.filter(username=username).exists():
            username = f"{base_username}{counter}"
            counter += 1
        return username

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('sync-all/', self.admin_site.admin_view(self.sync_all_view), name='pracownik_sync_all'),
        ]
        return custom_urls + urls

    def sync_all_view(self, request):
        """Widok do synchronizacji WSZYSTKICH Pracowników"""
        out = StringIO()
        call_command('sync_pracownicy', stdout=out)
        output = out.getvalue()

        # Zlicz wyniki z output
        lines = output.split('\n')
        for line in lines:
            if 'Utworzono' in line or 'Zsynchronizowano' in line or 'Bez zmian' in line or 'Błędy' in line:
                self.message_user(request, line.strip(), messages.INFO)

        self.message_user(request, 'Synchronizacja zakończona!', messages.SUCCESS)
        return redirect('admin:TOOLS_pracownik_changelist')


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