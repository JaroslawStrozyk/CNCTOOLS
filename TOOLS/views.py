# tools/views.py
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from django.shortcuts import get_object_or_404, render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from django.contrib import messages
from django.conf import settings
from django.db.models import Count, F, Q, Sum
from django.db import transaction
from django.utils import timezone
from datetime import datetime
from decimal import Decimal

from .models import (
    Kategoria, Podkategoria, NarzedzieMagazynowe, EgzemplarzNarzedzia,
    Lokalizacja, Maszyna, HistoriaUzyciaNarzedzia, FakturaZakupu,
    Dostawca, Pracownik, Uszkodzenie, Zamowienie, PozycjaZamowienia,
    RealizacjaZamowienia, PozycjaRealizacji,
    ZapotrzebowanieTechnologa, PozycjaZapotrzebowania,
    NumerKatalogowyDostawcy,
)
from django.contrib.auth.models import User
from .serializers import (
    KategoriaSerializer, PodkategoriaSerializer, NarzedzieMagazynoweSerializer,
    EgzemplarzNarzedziaSerializer, LokalizacjaSerializer, MaszynaSerializer,
    HistoriaUzyciaNarzedziaSerializer, FakturaZakupuSerializer,
    DostawcaSerializer, PracownikSerializer, UszkodzenieSerializer,
    ZamowienieSerializer, PozycjaZamowieniaSerializer,
    RealizacjaZamowieniaSerializer, PozycjaRealizacjiSerializer,
    ZapotrzebowanieTechnologaSerializer, PozycjaZapotrzebowaniaSerializer,
    GrupaSerializer, ZespolSerializer,
    NumerKatalogowyDostawcySerializer,
)
from django.contrib.auth.models import Group
from rest_framework.permissions import BasePermission
from .views_inertia import get_user_grupa_stanowiska
from .services import EgzemplarzService, LokalizacjaService
from .logging_service import app_logger, get_user_display_name


# ========== MIXIN LOGOWANIA ==========

class LoggingMixin:
    """
    Mixin dodający logowanie operacji CRUD do ViewSetów.
    Wymaga zdefiniowania atrybutu `log_name` w klasie potomnej.
    """
    log_name = 'Element'  # Domyślna nazwa, nadpisz w potomnej klasie

    def get_log_description(self, instance):
        """Zwraca opis obiektu do logowania. Nadpisz w razie potrzeby."""
        if hasattr(instance, 'nazwa'):
            return instance.nazwa
        elif hasattr(instance, 'opis'):
            return instance.opis
        elif hasattr(instance, '__str__'):
            return str(instance)
        return f'ID: {instance.pk}'

    def perform_create(self, serializer):
        instance = serializer.save()
        user_name = get_user_display_name(self.request.user)
        desc = self.get_log_description(instance)
        app_logger.success(user_name, f"Dodano {self.log_name}: {desc}")

    def perform_update(self, serializer):
        instance = serializer.save()
        user_name = get_user_display_name(self.request.user)
        desc = self.get_log_description(instance)
        app_logger.info(user_name, f"Edytowano {self.log_name}: {desc}")

    def perform_destroy(self, instance):
        user_name = get_user_display_name(self.request.user)
        desc = self.get_log_description(instance)
        instance.delete()
        app_logger.warning(user_name, f"Usunięto {self.log_name}: {desc}")


# ========== WIDOKI HTML ==========

def index_view(request):
    """Strona główna - przekierowanie"""
    if request.user.is_authenticated:
        return redirect('magazyn')
    return redirect('login')


def get_redirect_url_for_user(user):
    """Zwraca URL przekierowania na podstawie grupy użytkownika"""
    if user.groups.filter(name='logistyka').exists():
        return 'zakupy'
    elif user.groups.filter(name='magazyn').exists():
        return 'magazyn'
    # Domyślnie dla admina lub użytkowników bez grupy
    return 'magazyn'


def login_view(request):
    """Panel logowania"""
    from django.conf import settings

    if request.user.is_authenticated:
        return redirect(get_redirect_url_for_user(request.user))

    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                # Sprawdź czy jest parametr next, jeśli nie - przekieruj wg grupy
                next_url = request.GET.get('next')
                if next_url:
                    return redirect(next_url)
                return redirect(get_redirect_url_for_user(user))
        messages.error(request, 'Nieprawidłowa nazwa użytkownika lub hasło.')
    else:
        form = AuthenticationForm()

    # Pobierz informacje o programie z settings.py
    info_program = {}
    if hasattr(settings, 'INFO_PROGRAM') and settings.INFO_PROGRAM:
        info_program = settings.INFO_PROGRAM[0]

    return render(request, 'login.html', {
        'form': form,
        'info_program': info_program
    })


def logout_view(request):
    """Wylogowanie"""
    logout(request)
    return redirect('login')


@login_required
def magazyn_view(request):
    from django.conf import settings

    # Pobierz informacje o programie
    info_program = {}
    if hasattr(settings, 'INFO_PROGRAM') and settings.INFO_PROGRAM:
        info_program = settings.INFO_PROGRAM[0]

    # Sprawdź czy użytkownik należy do grupy logistyka
    is_logistyka = request.user.groups.filter(name='logistyka').exists()

    return render(request, 'magazyn.html', {
        'info_program': info_program,
        'is_logistyka': is_logistyka
    })


@login_required
@login_required
def odpady_view(request):
    return render(request, 'odpady.html')


@login_required
def realizacja_view(request):
    from django.conf import settings
    return render(request, 'realizacja.html', {
        'info_program': settings.INFO_PROGRAM
    })


@login_required
def zakupy_view(request):
    from django.conf import settings

    # Pobierz informacje o programie
    info_program = {}
    if hasattr(settings, 'INFO_PROGRAM') and settings.INFO_PROGRAM:
        info_program = settings.INFO_PROGRAM[0]

    return render(request, 'zakupy.html', {
        'info_program': info_program
    })


@login_required
def faktury_view(request):
    return render(request, 'faktury.html')


@login_required
def ustawienia_view(request):
    return render(request, 'ustawienia.html')


@login_required
def zamowienia_view(request):
    from django.conf import settings

    # Pobierz informacje o programie
    info_program = {}
    if hasattr(settings, 'INFO_PROGRAM') and settings.INFO_PROGRAM:
        info_program = settings.INFO_PROGRAM[0]

    # Sprawdź grupy użytkownika
    is_logistyka = request.user.groups.filter(name='logistyka').exists()
    is_admin = request.user.is_superuser

    # Uprawnienie do generowania zamówień - logistyka lub admin
    can_generate_orders = is_logistyka or is_admin

    return render(request, 'zamowienia.html', {
        'info_program': info_program,
        'is_logistyka': is_logistyka,
        'can_generate_orders': can_generate_orders
    })


@login_required
def generator_view(request):
    return render(request, 'generator.html')


from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.db.models import Count, Q


@api_view(['GET'])
def generator_zamowien_api(request):
    """
    Endpoint zwracający listę narzędzi wymagających zamówienia.
    Zwraca:
    1. Wszystkie pozycje z PozycjaGeneratora (ręcznie dodane lub istniejące)
    2. Automatycznie generuje nowe pozycje dla narzędzi gdzie stan < limit maksymalny
    3. Pozycje z zatwierdzonych zapotrzebowań technologów
    """
    from .models import NarzedzieMagazynowe, EgzemplarzNarzedzia, PozycjaGeneratora, PozycjaZamowienia, PozycjaZapotrzebowania
    from django.db.models import Count, Q

    from django.db.models import F, Sum, Value, Subquery, OuterRef
    from django.db.models.functions import Coalesce

    # Aktualny sposób liczenia zamówień (Ustawienia → Inne):
    #   'standardowa'             — dotychczasowa reguła min/max po stanie całkowitym
    #   'wedlug_nowych_elementow' — reguła PRZEDZIAŁOWA (min/max) po ilości NOWYCH egzemplarzy:
    #       uzupełniamy do stanu MAKSYMALnego, gdy ilość nowych < max (także w przedziale
    #       min–max). stan_minimalny=0 → narzędzie wyłączone z auto-zamawiania; max=0 →
    #       brak celu uzupełnienia → pomijane.
    wedlug_nowych = get_sposob_liczenia_zamowien() == 'wedlug_nowych_elementow'

    # Subquery: ilość nowych (stan='nowe', bez aktualnie wydanych) — liczona jak w Zakupy
    _egzemplarze_wydane = HistoriaUzyciaNarzedzia.objects.filter(
        data_zwrotu__isnull=True
    ).values('egzemplarz_id')

    def _nowe_subquery(outer_field):
        return EgzemplarzNarzedzia.objects.filter(
            narzedzie_typ=OuterRef(outer_field),
            stan='nowe'
        ).exclude(
            id__in=Subquery(_egzemplarze_wydane)
        ).values('narzedzie_typ').annotate(
            total=Sum('ilosc_w_komplecie')
        ).values('total')

    if wedlug_nowych:
        # Czyszczenie zombie (tryb "według nowych elementów"): auto-pozycje, które wg
        # reguły przedziałowej nie są już uzasadnione. MUSI być lustrzane do reguły
        # tworzenia (inaczej pozycje migoczą: delete+recreate, utrata ręcznych edycji).
        # Pozycja uzasadniona ⇔ stan_min>0 AND stan_max>0 AND nowe < stan_max.
        # Usuwamy więc gdy: min=0 (wyłączone) LUB max=0 (brak celu) LUB nowe >= max (pełno).
        zombie_ids = list(
            PozycjaGeneratora.objects.filter(
                zrodlo='auto',
            ).annotate(
                _nowe=Coalesce(Subquery(_nowe_subquery('narzedzie_typ')), Value(0))
            ).filter(
                Q(narzedzie_typ__stan_minimalny__lte=0)
                | Q(narzedzie_typ__stan_maksymalny__lte=0)
                | Q(_nowe__gte=F('narzedzie_typ__stan_maksymalny'))
            ).values_list('id', flat=True)
        )
        if zombie_ids:
            PozycjaGeneratora.objects.filter(id__in=zombie_ids).delete()
    else:
        # Czyszczenie zaszłości po BUG: pozycje 'auto' dla narzędzi z stan_maksymalny=0
        # nie powinny istnieć. Wcześniejsza wersja kodu tworzyła je na podstawie magicznej
        # wartości 10. Usuwamy je przy każdym odświeżeniu, żeby widok generatora się
        # zsynchronizował z regułą "stan_max=0 → nie zamawiaj".
        PozycjaGeneratora.objects.filter(
            zrodlo='auto',
            narzedzie_typ__stan_maksymalny=0
        ).delete()

        # Czyszczenie zombie: auto-pozycje dla narzędzi, których stan już osiągnął lub
        # przekroczył limit maksymalny (np. po dostawie). Bez tego pozycja utworzona
        # kiedyś przy niskim stanie "trzyma się" generatora mimo że zamówienie jest
        # nieuzasadnione (stan aktualny >= stan_maksymalny).
        # Stan liczymy jak Zakupy: SUMA ilosc_w_komplecie (nie liczba egzemplarzy) —
        # inaczej egzemplarz o ilosc_w_komplecie=10 byłby liczony jako 1 szt.
        zombie_ids = list(
            PozycjaGeneratora.objects.filter(
                zrodlo='auto',
                narzedzie_typ__stan_maksymalny__gt=0,
            ).annotate(
                _stan=Coalesce(Sum(
                    'narzedzie_typ__egzemplarze__ilosc_w_komplecie',
                    filter=~Q(narzedzie_typ__egzemplarze__stan='uszkodzone')
                         & ~Q(narzedzie_typ__egzemplarze__stan='uszkodzone_regeneracja'),
                ), 0)
            ).filter(_stan__gte=F('narzedzie_typ__stan_maksymalny')).values_list('id', flat=True)
        )
        if zombie_ids:
            PozycjaGeneratora.objects.filter(id__in=zombie_ids).delete()

    # Najpierw pobierz wszystkie istniejące pozycje z generatora
    istniejace_pozycje = PozycjaGeneratora.objects.select_related(
        'narzedzie_typ',
        'narzedzie_typ__podkategoria',
        'narzedzie_typ__podkategoria__kategoria',
        'dostawca'
    ).all()

    istniejace_narzedzia_ids = set(p.narzedzie_typ.id for p in istniejace_pozycje)

    # Zbiorczy zestaw narzędzi z aktywnymi zamówieniami (1 zapytanie zamiast N)
    aktywne_statusy = ['draft', 'pending_approval', 'verified', 'sent', 'partially_received']
    narzedzia_w_zamowieniach = set(
        PozycjaZamowienia.objects.filter(
            zamowienie__status__in=aktywne_statusy
        ).values_list('narzedzie_typ_id', flat=True).distinct()
    )

    # Zbiorczy słownik ostatnich cen (1 zapytanie zamiast N)
    from django.db.models import Max, Subquery, OuterRef
    ostatnie_ceny_qs = PozycjaZamowienia.objects.filter(
        cena_jednostkowa__isnull=False,
        cena_jednostkowa__gt=0,
    ).values('narzedzie_typ_id').annotate(
        ostatnia_data=Max('zamowienie__data_utworzenia')
    )
    ostatnie_ceny = {}
    for row in ostatnie_ceny_qs:
        poz = PozycjaZamowienia.objects.filter(
            narzedzie_typ_id=row['narzedzie_typ_id'],
            zamowienie__data_utworzenia=row['ostatnia_data'],
            cena_jednostkowa__isnull=False,
            cena_jednostkowa__gt=0,
        ).first()
        if poz:
            ostatnie_ceny[row['narzedzie_typ_id']] = poz.cena_jednostkowa

    # Pobierz narzędzia z annotowanym stanem (egzemplarze bez uszkodzonych).
    # UWAGA: liczymy SUMĘ ilosc_w_komplecie, NIE liczby egzemplarzy — zgodnie z Zakupy.
    # Egzemplarz może reprezentować komplet (np. ilosc_w_komplecie=10), więc
    # Count() zaniżyłby faktyczny stan fizycznych sztuk i prowadził do nieuzasadnionych zamówień.
    narzedzia = NarzedzieMagazynowe.objects.select_related(
        'podkategoria',
        'podkategoria__kategoria',
        'ostatni_dostawca'
    ).annotate(
        stan_aktualny=Coalesce(Sum(
            'egzemplarze__ilosc_w_komplecie',
            filter=~Q(egzemplarze__stan='uszkodzone') & ~Q(egzemplarze__stan='uszkodzone_regeneracja')
        ), 0)
    ).all()

    if wedlug_nowych:
        narzedzia = narzedzia.annotate(
            ilosc_nowych=Coalesce(Subquery(_nowe_subquery('pk')), Value(0))
        )

    # Lista narzędzi z ręczną kontrolą, których pole reczne_dodanie zostało odczytane — do wyzerowania
    reczne_do_wyzerowania = []
    nowe_pozycje = []

    for narzedzie in narzedzia:
        # Pomiń jeśli już jest w PozycjaGeneratora
        if narzedzie.id in istniejace_narzedzia_ids:
            continue

        # Pomiń jeśli jest w aktywnym zamówieniu
        if narzedzie.id in narzedzia_w_zamowieniach:
            continue

        # Cena: ostatnia z zamówień, a gdy brak historii — ustawiona ręcznie w Zakupach
        cena_jednostkowa = ostatnie_ceny.get(narzedzie.id) or narzedzie.cena_jednostkowa or 0

        # --- Ręczna kontrola zamówień ---
        if narzedzie.reczna_kontrola:
            if narzedzie.reczne_dodanie > 0:
                nowe_pozycje.append(PozycjaGeneratora(
                    narzedzie_typ=narzedzie,
                    dostawca=narzedzie.ostatni_dostawca,
                    ilosc_do_zamowienia=narzedzie.reczne_dodanie,
                    cena_jednostkowa=cena_jednostkowa,
                    zrodlo='reczne'
                ))
                reczne_do_wyzerowania.append(narzedzie.id)
            continue

        # --- Automatyczna kontrola ---
        if wedlug_nowych:
            # Tryb "według nowych elementów" — reguła PRZEDZIAŁOWA (min/max po ilości
            # nowych, niewydanych egzemplarzy). Uzupełniamy do stanu MAKSYMALnego, gdy
            # nowych < max (także w przedziale min–max). Cel zawsze = max.
            #   stan_minimalny=0 → narzędzie wyłączone z auto-zamawiania (jak dotąd).
            #   stan_maksymalny=0 → brak celu uzupełnienia → pomijamy.
            if narzedzie.stan_minimalny <= 0 or narzedzie.stan_maksymalny <= 0:
                continue
            ilosc_brakujacych_sztuk = narzedzie.stan_maksymalny - narzedzie.ilosc_nowych
            if ilosc_brakujacych_sztuk <= 0:
                continue
        else:
            # Tryb standardowy (min/max):
            # stan_maksymalny == 0 oznacza "nie zamawiaj automatycznie" — narzędzie pomijane
            stan_maksymalny = narzedzie.stan_maksymalny
            if stan_maksymalny <= 0 or narzedzie.stan_aktualny >= stan_maksymalny:
                continue
            ilosc_brakujacych_sztuk = stan_maksymalny - narzedzie.stan_aktualny

        if narzedzie.opakowanie == 'kompl' and narzedzie.ilosc_w_opakowaniu > 0:
            # Przelicz brakujące sztuki na komplety zakupowe. Zaokrąglamy do NAJBLIŻSZEJ
            # liczby kompletów (połówki w górę), więc zamawiamy kolejny komplet dopiero gdy
            # brakująca ilość jest zbliżona do pełnego opakowania (brak 6/10 → 1 kompl.,
            # brak 4/10 → 0 kompl., brak 15/10 → 2 kompl.).
            # Arytmetyka całkowita (2a+b)//(2b) daje zaokrąglenie połówek w górę bez błędów
            # zmiennoprzecinkowych. UWAGA: Python round() zaokrągla bankowo (round(0.5)=0) —
            # tu niepożądane, dlatego nie używamy round().
            w_opak = narzedzie.ilosc_w_opakowaniu
            komplety = (2 * ilosc_brakujacych_sztuk + w_opak) // (2 * w_opak)
            # Gdy zaokrągliło do 0, a niedobór istnieje (ilosc_brakujacych_sztuk > 0 jest tu
            # zawsze prawdą) — zamów minimum 1 komplet, by stan wrócił powyżej minimum.
            ilosc_do_zamowienia = max(1, komplety)
        else:
            ilosc_do_zamowienia = ilosc_brakujacych_sztuk

        nowe_pozycje.append(PozycjaGeneratora(
            narzedzie_typ=narzedzie,
            dostawca=narzedzie.ostatni_dostawca,
            ilosc_do_zamowienia=ilosc_do_zamowienia,
            cena_jednostkowa=cena_jednostkowa,
            zrodlo='auto'
        ))

    # Bulk create nowych pozycji (1 zapytanie zamiast N)
    if nowe_pozycje:
        PozycjaGeneratora.objects.bulk_create(nowe_pozycje, ignore_conflicts=True)

    # Wyzeruj pole reczne_dodanie dla odczytanych narzędzi z ręczną kontrolą
    if reczne_do_wyzerowania:
        NarzedzieMagazynowe.objects.filter(id__in=reczne_do_wyzerowania).update(reczne_dodanie=0)

    # --- Zapotrzebowania technologów (zatwierdzone, nieprzetworzone) ---
    pozycje_zapotrzebowan = PozycjaZapotrzebowania.objects.filter(
        zapotrzebowanie__status='completed',
        narzedzie_typ__isnull=False,
        w_zamowieniu=False
    ).select_related(
        'narzedzie_typ',
        'narzedzie_typ__ostatni_dostawca',
        'zapotrzebowanie'
    )

    zapotrzebowania_ids = []
    # Śledź zapotrzebowania, których WSZYSTKIE pozycje trafiły do generatora
    zapotrzebowania_do_ordered = set()

    for pz in pozycje_zapotrzebowan:
        narzedzie = pz.narzedzie_typ
        zap_numer = f"ZAM-{pz.zapotrzebowanie.id:04d}"

        # Sprawdź czy narzędzie jest w aktywnym zamówieniu (z cache)
        if narzedzie.id in narzedzia_w_zamowieniach:
            zapotrzebowania_ids.append(pz.id)
            continue

        # Sprawdź czy już jest w generatorze — jeśli tak, zwiększ ilość i dopisz źródło
        try:
            istniejaca = PozycjaGeneratora.objects.get(narzedzie_typ=narzedzie)
            istniejaca.ilosc_do_zamowienia += pz.ilosc
            # Dopisz źródło zapotrzebowania
            if istniejaca.zrodlo != 'zapotrzebowanie':
                istniejaca.zrodlo = 'zapotrzebowanie'
            existing_ids = istniejaca.zrodlo_zapotrzebowanie_ids
            if zap_numer not in existing_ids:
                istniejaca.zrodlo_zapotrzebowanie_ids = (existing_ids + ',' + zap_numer).strip(',')
            istniejaca.save(update_fields=['ilosc_do_zamowienia', 'zrodlo', 'zrodlo_zapotrzebowanie_ids'])
        except PozycjaGeneratora.DoesNotExist:
            # Cena: ostatnia z zamówień, a gdy brak historii — ustawiona ręcznie w Zakupach
            cena_jednostkowa = ostatnie_ceny.get(narzedzie.id) or narzedzie.cena_jednostkowa or 0
            PozycjaGeneratora.objects.create(
                narzedzie_typ=narzedzie,
                dostawca=narzedzie.ostatni_dostawca,
                ilosc_do_zamowienia=pz.ilosc,
                cena_jednostkowa=cena_jednostkowa,
                zrodlo='zapotrzebowanie',
                zrodlo_zapotrzebowanie_ids=zap_numer
            )

        zapotrzebowania_ids.append(pz.id)
        zapotrzebowania_do_ordered.add(pz.zapotrzebowanie.id)

    # Oznacz przetworzone pozycje zapotrzebowań
    if zapotrzebowania_ids:
        PozycjaZapotrzebowania.objects.filter(id__in=zapotrzebowania_ids).update(w_zamowieniu=True)

    # Zmień status zapotrzebowań na 'ordered' tylko gdy WSZYSTKIE pozycje (też bez narzędzia)
    # są przetworzone. Pozycje bez narzędzia (w_zamowieniu=False) utrzymują status 'completed',
    # żeby logistyk mógł je ręcznie przypisać/odrzucić w panelu "nieprzypisane".
    from .models import ZapotrzebowanieTechnologa
    for zap_id in zapotrzebowania_do_ordered:
        zap = ZapotrzebowanieTechnologa.objects.get(id=zap_id)
        if not zap.pozycje.filter(w_zamowieniu=False).exists():
            zap.status = 'ordered'
            zap.save(update_fields=['status'])

    # Teraz pobierz WSZYSTKIE pozycje z generatora (włącznie z nowo utworzonymi)
    wszystkie_pozycje = PozycjaGeneratora.objects.select_related(
        'narzedzie_typ',
        'narzedzie_typ__podkategoria',
        'narzedzie_typ__podkategoria__kategoria',
        'dostawca'
    ).all()

    wynik = []

    for pozycja in wszystkie_pozycje:
        narzedzie = pozycja.narzedzie_typ

        # Pomiń jeśli jest w aktywnym zamówieniu (z cache)
        if narzedzie.id in narzedzia_w_zamowieniach:
            continue

        # Przygotuj dane do wyświetlenia
        element = ''
        if narzedzie.podkategoria:
            element = f"{narzedzie.podkategoria.kategoria.nazwa} / {narzedzie.podkategoria.nazwa} - {narzedzie.opis}"
        else:
            element = narzedzie.opis

        rodzaj = 'szt.'
        if narzedzie.opakowanie == 'kompl':
            rodzaj = f"kompl. ({narzedzie.ilosc_w_opakowaniu} szt.)"

        # Pobierz dostawcę
        dostawca_nazwa = ''
        dostawca_id = None
        if pozycja.dostawca:
            dostawca_nazwa = pozycja.dostawca.nazwa_firmy
            dostawca_id = pozycja.dostawca.id

        # Etykieta źródła
        zrodlo_label = {'auto': 'Auto (stany)', 'reczne': 'Ręczne', 'zapotrzebowanie': 'Zapotrzebowanie'}.get(pozycja.zrodlo, pozycja.zrodlo)
        if pozycja.zrodlo == 'zapotrzebowanie' and pozycja.zrodlo_zapotrzebowanie_ids:
            zrodlo_label = pozycja.zrodlo_zapotrzebowanie_ids

        wynik.append({
            'id': narzedzie.id,
            'dostawca_nazwa': dostawca_nazwa,
            'dostawca_id': dostawca_id,
            'element': element,
            'numer_katalogowy': narzedzie.numer_katalogowy or '',
            'ilosc_do_zamowienia': pozycja.ilosc_do_zamowienia,
            'rodzaj': rodzaj,
            'cena_jednostkowa': float(pozycja.cena_jednostkowa) if pozycja.cena_jednostkowa else 0,
            'zrodlo': pozycja.zrodlo,
            'zrodlo_label': zrodlo_label,
            # Dane do sortowania
            'kategoria': narzedzie.podkategoria.kategoria.nazwa if narzedzie.podkategoria else '',
            'podkategoria': narzedzie.podkategoria.nazwa if narzedzie.podkategoria else '',
            'opis': narzedzie.opis
        })

    # Sortowanie
    wynik.sort(key=lambda x: (x['kategoria'].lower(), x['podkategoria'].lower(), x['opis'].lower()))

    # Pozycje zapotrzebowań BEZ powiązanego narzędzia (do ręcznego przetworzenia).
    # Status 'ordered' też akceptujemy — zaszłości po starym bugu, w którym zapotrzebowanie
    # było przedwcześnie oznaczane jako 'ordered' mimo nieprzypisanych pozycji.
    nieprzypisane = PozycjaZapotrzebowania.objects.filter(
        zapotrzebowanie__status__in=['completed', 'ordered'],
        narzedzie_typ__isnull=True,
        w_zamowieniu=False
    ).select_related('zapotrzebowanie', 'zapotrzebowanie__technolog')

    nieprzypisane_lista = []
    for np_poz in nieprzypisane:
        technolog = np_poz.zapotrzebowanie.technolog
        technolog_nazwa = f"{technolog.first_name} {technolog.last_name}" if technolog else "Nieznany"
        nieprzypisane_lista.append({
            'id': np_poz.id,
            'zapotrzebowanie_numer': f"ZAM-{np_poz.zapotrzebowanie.id:04d}",
            'technolog': technolog_nazwa,
            'specyfikacja': np_poz.specyfikacja or '-',
            'kategoria_nazwa': np_poz.kategoria_nazwa or '-',
            'numer_katalogowy': np_poz.numer_katalogowy or '-',
            'ilosc': np_poz.ilosc,
            'uwagi': np_poz.uwagi or '',
        })

    return Response({
        'pozycje': wynik,
        'nieprzypisane': nieprzypisane_lista
    })


@api_view(['PATCH'])
def generator_zamowien_update_api(request, narzedzie_id):
    """
    Endpoint do aktualizacji pozycji w generatorze zamówień.
    Pozwala edytować: dostawca_id, numer_katalogowy, ilosc_do_zamowienia, cena_jednostkowa
    """
    from .models import NarzedzieMagazynowe, Dostawca, PozycjaGeneratora

    try:
        narzedzie = NarzedzieMagazynowe.objects.get(id=narzedzie_id)
    except NarzedzieMagazynowe.DoesNotExist:
        return Response({'error': 'Narzędzie nie istnieje'}, status=404)

    # Pobierz lub utwórz pozycję generatora
    try:
        pozycja = PozycjaGeneratora.objects.get(narzedzie_typ=narzedzie)
    except PozycjaGeneratora.DoesNotExist:
        pozycja = PozycjaGeneratora.objects.create(
            narzedzie_typ=narzedzie,
            dostawca=narzedzie.ostatni_dostawca,
            ilosc_do_zamowienia=0,
            cena_jednostkowa=0
        )

    # Aktualizuj dostawcę
    if 'dostawca_id' in request.data:
        dostawca_id = request.data['dostawca_id']
        if dostawca_id:
            try:
                dostawca = Dostawca.objects.get(id=dostawca_id)
                pozycja.dostawca = dostawca
                # Również zaktualizuj ostatni_dostawca w narzędziu
                narzedzie.ostatni_dostawca = dostawca
                narzedzie.save()
            except Dostawca.DoesNotExist:
                return Response({'error': 'Dostawca nie istnieje'}, status=400)
        else:
            pozycja.dostawca = None

    # Aktualizuj numer katalogowy w narzędziu
    if 'numer_katalogowy' in request.data:
        narzedzie.numer_katalogowy = request.data['numer_katalogowy']
        narzedzie.save()

    # Aktualizuj ilość do zamówienia
    if 'ilosc_do_zamowienia' in request.data:
        pozycja.ilosc_do_zamowienia = request.data['ilosc_do_zamowienia']

    # Aktualizuj cenę jednostkową
    if 'cena_jednostkowa' in request.data:
        cena = request.data['cena_jednostkowa']
        pozycja.cena_jednostkowa = cena if cena is not None else 0

    pozycja.save()

    # Logowanie
    user_name = get_user_display_name(request.user)
    app_logger.info(user_name, f"Edytowano pozycję generatora: {narzedzie.opis}")

    return Response({'success': True, 'message': 'Zaktualizowano pomyślnie'})


@api_view(['DELETE'])
def generator_zamowien_delete_api(request, narzedzie_id):
    """
    Endpoint do usuwania pozycji z generatora.
    Usuwa pozycję z PozycjaGeneratora. Jeśli pozycja pochodziła z zapotrzebowania
    technologa, resetuje flagę w_zamowieniu, aby mogła wrócić przy kolejnym odświeżeniu.
    """
    from .models import NarzedzieMagazynowe, PozycjaGeneratora, PozycjaZapotrzebowania, ZapotrzebowanieTechnologa

    try:
        narzedzie = NarzedzieMagazynowe.objects.get(id=narzedzie_id)
    except NarzedzieMagazynowe.DoesNotExist:
        return Response({'error': 'Narzędzie nie istnieje'}, status=404)

    # Znajdź pozycje generatora i cofnij flagę w_zamowieniu na powiązanych zapotrzebowaniach
    pozycje_generatora = PozycjaGeneratora.objects.filter(narzedzie_typ=narzedzie)
    zapotrzebowania_do_cofniecia = set()

    for pg in pozycje_generatora:
        if pg.zrodlo == 'zapotrzebowanie' and pg.zrodlo_zapotrzebowanie_ids:
            for zn in pg.zrodlo_zapotrzebowanie_ids.split(','):
                zn = zn.strip()
                if zn.startswith('ZAM-'):
                    try:
                        zap_id = int(zn.replace('ZAM-', ''))
                        PozycjaZapotrzebowania.objects.filter(
                            zapotrzebowanie_id=zap_id,
                            narzedzie_typ=narzedzie
                        ).update(w_zamowieniu=False)
                        zapotrzebowania_do_cofniecia.add(zap_id)
                    except ValueError:
                        continue

    pozycje_generatora.delete()

    # Cofnij status 'ordered' → 'completed' dla zapotrzebowań, które znów mają pozycje oczekujące
    for zap_id in zapotrzebowania_do_cofniecia:
        zap = ZapotrzebowanieTechnologa.objects.filter(id=zap_id, status='ordered').first()
        if zap and zap.pozycje.filter(narzedzie_typ__isnull=False, w_zamowieniu=False).exists():
            zap.status = 'completed'
            zap.save(update_fields=['status'])

    # Logowanie
    user_name = get_user_display_name(request.user)
    app_logger.warning(user_name, f"Usunięto z generatora zamówień: {narzedzie.opis}")

    return Response({'success': True, 'message': 'Usunięto z listy zamówień'})


@api_view(['POST'])
def generator_zamowien_przypisz_pozycje_api(request, pozycja_id):
    """
    Przypisuje istniejące narzędzie magazynowe do pozycji zapotrzebowania,
    która została stworzona bez powiązania (np. technolog opisał nowe narzędzie).
    Po przypisaniu pozycja pojawi się automatycznie w generatorze przy kolejnym GET.
    """
    from .models import NarzedzieMagazynowe, PozycjaZapotrzebowania

    narzedzie_id = request.data.get('narzedzie_id')
    if not narzedzie_id:
        return Response({'error': 'Wymagane pole: narzedzie_id'}, status=400)

    try:
        pozycja = PozycjaZapotrzebowania.objects.select_related('zapotrzebowanie').get(id=pozycja_id)
    except PozycjaZapotrzebowania.DoesNotExist:
        return Response({'error': 'Pozycja zapotrzebowania nie istnieje'}, status=404)

    try:
        narzedzie = NarzedzieMagazynowe.objects.get(id=narzedzie_id)
    except NarzedzieMagazynowe.DoesNotExist:
        return Response({'error': 'Narzędzie nie istnieje'}, status=404)

    pozycja.narzedzie_typ = narzedzie
    pozycja.w_zamowieniu = False  # żeby generator podjął ją przy najbliższym odświeżeniu
    pozycja.save(update_fields=['narzedzie_typ', 'w_zamowieniu'])

    user_name = get_user_display_name(request.user)
    app_logger.success(
        user_name,
        f"Przypisano narzędzie '{narzedzie.opis}' do pozycji zapotrzebowania "
        f"ZAM-{pozycja.zapotrzebowanie.id:04d} (specyfikacja: {pozycja.specyfikacja or '-'})"
    )

    return Response({
        'success': True,
        'message': f'Przypisano narzędzie do pozycji. Odśwież generator aby zobaczyć zmianę.'
    })


@api_view(['DELETE'])
def generator_zamowien_odrzuc_pozycje_api(request, pozycja_id):
    """
    Odrzuca nieprzypisaną pozycję zapotrzebowania — oznacza ją jako przetworzoną,
    żeby znikła z panelu nieprzypisanych. Używane gdy logistyk nie chce realizować
    pozycji (np. już mamy, niepotrzebna, błędna specyfikacja).
    """
    from .models import PozycjaZapotrzebowania, ZapotrzebowanieTechnologa

    try:
        pozycja = PozycjaZapotrzebowania.objects.select_related('zapotrzebowanie').get(id=pozycja_id)
    except PozycjaZapotrzebowania.DoesNotExist:
        return Response({'error': 'Pozycja zapotrzebowania nie istnieje'}, status=404)

    spec = pozycja.specyfikacja or '-'
    zap_id = pozycja.zapotrzebowanie.id
    pozycja.w_zamowieniu = True
    pozycja.save(update_fields=['w_zamowieniu'])

    # Jeśli wszystkie pozycje zapotrzebowania zostały przetworzone — oznacz jako 'ordered'
    zap = pozycja.zapotrzebowanie
    if not zap.pozycje.filter(w_zamowieniu=False).exists() and zap.status == 'completed':
        zap.status = 'ordered'
        zap.save(update_fields=['status'])

    user_name = get_user_display_name(request.user)
    app_logger.warning(
        user_name,
        f"Odrzucono pozycję zapotrzebowania ZAM-{zap_id:04d}: {spec}"
    )

    return Response({'success': True, 'message': 'Pozycja została odrzucona'})


@api_view(['POST'])
def generator_zamowien_add_api(request):
    """
    Endpoint do ręcznego dodawania pozycji do generatora zamówień.

    Obsługuje dwa tryby:
    - tryb='istniejace' (domyślny): wybór narzędzia z istniejącej listy
    - tryb='nowe': tworzy nowe narzędzie (z opcjonalnym utworzeniem kategorii/podkategorii)
    """
    from .models import NarzedzieMagazynowe, Dostawca, PozycjaGeneratora, Kategoria, Podkategoria

    tryb = request.data.get('tryb', 'istniejace')
    dostawca_id = request.data.get('dostawca_id')
    ilosc = request.data.get('ilosc_do_zamowienia', 1)
    cena = request.data.get('cena_jednostkowa', 0)

    # Pobierz dostawcę jeśli podano (wspólne dla obu trybów)
    dostawca = None
    if dostawca_id:
        try:
            dostawca = Dostawca.objects.get(id=dostawca_id)
        except Dostawca.DoesNotExist:
            return Response({'error': 'Dostawca nie istnieje'}, status=400)

    if tryb == 'nowe':
        # === TRYB: Nowe narzędzie ===
        kategoria_id = request.data.get('kategoria_id')
        nowa_kategoria_nazwa = (request.data.get('nowa_kategoria_nazwa') or '').strip()
        podkategoria_id = request.data.get('podkategoria_id')
        nowa_podkategoria_nazwa = (request.data.get('nowa_podkategoria_nazwa') or '').strip()
        opis = (request.data.get('opis') or '').strip()
        numer_katalogowy = (request.data.get('numer_katalogowy') or '').strip() or None
        opakowanie = request.data.get('opakowanie', 'szt')
        ilosc_w_opakowaniu = int(request.data.get('ilosc_w_opakowaniu') or 1)
        stan_minimalny = int(request.data.get('stan_minimalny') or 0)
        stan_maksymalny = int(request.data.get('stan_maksymalny') or 0)

        if not opis:
            return Response({'error': 'Podaj opis narzędzia'}, status=400)
        if not kategoria_id and not nowa_kategoria_nazwa:
            return Response({'error': 'Wybierz kategorię lub podaj nazwę nowej'}, status=400)
        if not podkategoria_id and not nowa_podkategoria_nazwa:
            return Response({'error': 'Wybierz podkategorię lub podaj nazwę nowej'}, status=400)
        if opakowanie == 'kompl' and ilosc_w_opakowaniu <= 1:
            return Response({'error': 'Dla opakowania "Komplet" ilość w opakowaniu musi być większa niż 1'}, status=400)

        try:
            with transaction.atomic():
                # Kategoria
                if kategoria_id:
                    try:
                        kategoria = Kategoria.objects.get(id=kategoria_id)
                    except Kategoria.DoesNotExist:
                        return Response({'error': 'Kategoria nie istnieje'}, status=400)
                else:
                    kategoria, _ = Kategoria.objects.get_or_create(nazwa=nowa_kategoria_nazwa)

                # Podkategoria
                if podkategoria_id:
                    try:
                        podkategoria = Podkategoria.objects.get(id=podkategoria_id, kategoria=kategoria)
                    except Podkategoria.DoesNotExist:
                        return Response({'error': 'Podkategoria nie istnieje w wybranej kategorii'}, status=400)
                else:
                    podkategoria, _ = Podkategoria.objects.get_or_create(
                        nazwa=nowa_podkategoria_nazwa,
                        kategoria=kategoria
                    )

                # Narzędzie
                narzedzie = NarzedzieMagazynowe.objects.create(
                    podkategoria=podkategoria,
                    opis=opis,
                    numer_katalogowy=numer_katalogowy,
                    opakowanie=opakowanie,
                    ilosc_w_opakowaniu=ilosc_w_opakowaniu,
                    stan_minimalny=stan_minimalny,
                    stan_maksymalny=stan_maksymalny,
                    ostatni_dostawca=dostawca,
                )

                PozycjaGeneratora.objects.create(
                    narzedzie_typ=narzedzie,
                    dostawca=dostawca,
                    ilosc_do_zamowienia=ilosc,
                    cena_jednostkowa=cena,
                    zrodlo='reczne',
                    utworzone_narzedzie=True,
                )
        except Exception as e:
            return Response({'error': f'Błąd tworzenia narzędzia: {e}'}, status=400)

        user_name = get_user_display_name(request.user)
        app_logger.success(
            user_name,
            f"Utworzono nowe narzędzie i dodano do generatora: {kategoria.nazwa}/{podkategoria.nazwa} - {opis} ({ilosc} szt.)"
        )
        return Response({
            'success': True,
            'message': 'Utworzono narzędzie i dodano do generatora',
            'narzedzie_id': narzedzie.id,
            'kategoria_id': kategoria.id,
            'podkategoria_id': podkategoria.id,
        })

    # === TRYB: Istniejące narzędzie (domyślny) ===
    narzedzie_id = request.data.get('narzedzie_id')
    if not narzedzie_id:
        return Response({'error': 'Wybierz narzędzie'}, status=400)

    try:
        narzedzie = NarzedzieMagazynowe.objects.get(id=narzedzie_id)
    except NarzedzieMagazynowe.DoesNotExist:
        return Response({'error': 'Narzędzie nie istnieje'}, status=404)

    if PozycjaGeneratora.objects.filter(narzedzie_typ=narzedzie).exists():
        return Response({'error': 'To narzędzie jest już w generatorze'}, status=400)

    PozycjaGeneratora.objects.create(
        narzedzie_typ=narzedzie,
        dostawca=dostawca,
        ilosc_do_zamowienia=ilosc,
        cena_jednostkowa=cena,
        zrodlo='reczne'
    )

    user_name = get_user_display_name(request.user)
    app_logger.success(user_name, f"Dodano do generatora zamówień: {narzedzie.opis} ({ilosc} szt.)")

    return Response({'success': True, 'message': 'Dodano pomyślnie'})


@api_view(['POST'])
def generator_zamowien_gotowe_api(request):
    """
    Endpoint do tworzenia zamówień z PozycjaGeneratora.
    Grupuje pozycje według dostawcy i tworzy osobne zamówienia.
    Czyści tabelę PozycjaGeneratora po utworzeniu zamówień.
    """
    from .models import PozycjaGeneratora, Zamowienie, PozycjaZamowienia, Dostawca
    from django.utils import timezone
    from django.db import transaction
    from decimal import Decimal

    try:
        with transaction.atomic():
            # Pobierz wszystkie pozycje z generatora
            pozycje_generatora = PozycjaGeneratora.objects.select_related(
                'narzedzie_typ',
                'narzedzie_typ__podkategoria',
                'narzedzie_typ__podkategoria__kategoria',
                'dostawca'
            ).all()

            if not pozycje_generatora.exists():
                return Response({'error': 'Brak pozycji w generatorze'}, status=400)

            # Grupuj według dostawcy; pomiń pozycje z ilością 0 lub ujemną
            from collections import defaultdict
            grouped = defaultdict(list)
            pominiete_zero = 0

            for pozycja in pozycje_generatora:
                if pozycja.ilosc_do_zamowienia <= 0:
                    pominiete_zero += 1
                    continue
                dostawca_id = pozycja.dostawca.id if pozycja.dostawca else None
                grouped[dostawca_id].append(pozycja)

            utworzone_zamowienia = []
            now = timezone.now()
            rok_miesiac = now.strftime('%Y/%m')

            # Dla każdego dostawcy utwórz zamówienie
            for dostawca_id, pozycje in grouped.items():
                if dostawca_id is None:
                    # Pomiń pozycje bez dostawcy
                    continue

                dostawca = Dostawca.objects.get(id=dostawca_id)

                # Generuj numer zamówienia: RRRR/MM/nr_kolejny
                ostatnie_zamowienie = Zamowienie.objects.filter(
                    numer__startswith=rok_miesiac
                ).order_by('-numer').first()

                if ostatnie_zamowienie:
                    try:
                        ostatni_nr = int(ostatnie_zamowienie.numer.split('/')[-1])
                    except (ValueError, IndexError):
                        ostatni_nr = 0
                    nowy_nr = ostatni_nr + 1
                else:
                    nowy_nr = 1

                numer_zamowienia = f"{rok_miesiac}/{nowy_nr:03d}"

                # Oblicz wartość zamówienia
                wartosc_zamowienia = Decimal('0.00')
                for poz in pozycje:
                    cena = poz.cena_jednostkowa if poz.cena_jednostkowa else Decimal('0.00')
                    wartosc_zamowienia += cena * poz.ilosc_do_zamowienia

                # Utwórz zamówienie
                zamowienie = Zamowienie.objects.create(
                    numer=numer_zamowienia,
                    dostawca=dostawca,
                    email_docelowy=dostawca.email or '',
                    data_utworzenia=now,
                    wartosc_zamowienia=wartosc_zamowienia,
                    status='draft'
                )

                # Zbierz ID zapotrzebowań źródłowych z pozycji generatora
                # (format w polu: "ZAM-0001,ZAM-0002" — gdzie liczba = id ZapotrzebowanieTechnologa)
                zapotrzebowania_ids_set = set()
                for pozycja_gen in pozycje:
                    if pozycja_gen.zrodlo == 'zapotrzebowanie' and pozycja_gen.zrodlo_zapotrzebowanie_ids:
                        for token in pozycja_gen.zrodlo_zapotrzebowanie_ids.split(','):
                            token = token.strip()
                            if token.startswith('ZAM-'):
                                try:
                                    zapotrzebowania_ids_set.add(int(token[4:]))
                                except ValueError:
                                    continue
                if zapotrzebowania_ids_set:
                    from .models import ZapotrzebowanieTechnologa
                    istniejace_ids = set(
                        ZapotrzebowanieTechnologa.objects.filter(
                            id__in=zapotrzebowania_ids_set
                        ).values_list('id', flat=True)
                    )
                    if istniejace_ids:
                        zamowienie.zrodlowe_zapotrzebowania.add(*istniejace_ids)

                # Utwórz pozycje zamówienia
                for pozycja_gen in pozycje:
                    narzedzie = pozycja_gen.narzedzie_typ

                    # Spłaszcz dane
                    kategoria_nazwa = ''
                    podkategoria_nazwa = ''
                    if narzedzie.podkategoria:
                        kategoria_nazwa = narzedzie.podkategoria.kategoria.nazwa
                        podkategoria_nazwa = narzedzie.podkategoria.nazwa

                    cena = pozycja_gen.cena_jednostkowa if pozycja_gen.cena_jednostkowa else Decimal('0.00')
                    wartosc_poz = cena * pozycja_gen.ilosc_do_zamowienia

                    PozycjaZamowienia.objects.create(
                        zamowienie=zamowienie,
                        narzedzie_typ=narzedzie,
                        kategoria_nazwa=kategoria_nazwa,
                        podkategoria_nazwa=podkategoria_nazwa,
                        narzedzie_opis=narzedzie.opis,
                        numer_katalogowy=narzedzie.numer_katalogowy or '',
                        ilosc_zamowiona=pozycja_gen.ilosc_do_zamowienia,
                        jednostka=narzedzie.opakowanie,
                        ilosc_w_komplecie=narzedzie.ilosc_w_opakowaniu,
                        cena_jednostkowa=cena,
                        wartosc_pozycji=wartosc_poz
                    )

                    # Jeśli narzędzie zostało utworzone ręcznie razem z tą pozycją —
                    # podepnij FK do zamówienia, by kasowanie zamówienia mogło je usunąć.
                    if pozycja_gen.utworzone_narzedzie and narzedzie.utworzone_wraz_z_zamowieniem_id is None:
                        narzedzie.utworzone_wraz_z_zamowieniem = zamowienie
                        narzedzie.save(update_fields=['utworzone_wraz_z_zamowieniem'])

                utworzone_zamowienia.append({
                    'id': zamowienie.id,
                    'numer': zamowienie.numer,
                    'dostawca': dostawca.nazwa_firmy
                })

            # Jeśli nie powstało żadne zamówienie (wszystkie pozycje bez dostawcy
            # lub ilość=0) — zwróć błąd zamiast mylącego sukcesu.
            if not utworzone_zamowienia:
                return Response({
                    'error': 'Żadna pozycja nie trafiła do zamówienia. Uzupełnij dostawcę lub ilość.'
                }, status=400)

            # Skasuj z generatora TYLKO pozycje, które faktycznie trafiły do zamówień.
            # Pozycje bez dostawcy (grouped[None]) były pominięte powyżej — zostają
            # w generatorze, żeby user mógł uzupełnić dostawcę lub skasować je ręcznie.
            # Pozycje z ilosc=0 również zostają (user widzi i może edytować/usunąć).
            pominiete_count = len(grouped.get(None, []))
            narzedzia_do_zachowania = [
                p.narzedzie_typ_id for p in pozycje_generatora
                if p.ilosc_do_zamowienia <= 0 or p.dostawca is None
            ]
            PozycjaGeneratora.objects.exclude(
                narzedzie_typ_id__in=narzedzia_do_zachowania
            ).delete()

            # Logowanie
            user_name = get_user_display_name(request.user)
            numery = ', '.join([z['numer'] for z in utworzone_zamowienia])
            app_logger.success(user_name, f"Wygenerowano {len(utworzone_zamowienia)} zamówień: {numery}")

            message = f'Utworzono {len(utworzone_zamowienia)} zamówień'
            if pominiete_count > 0:
                message += f'. Pominięto {pominiete_count} pozycji bez dostawcy — pozostają w generatorze do uzupełnienia.'
            if pominiete_zero > 0:
                message += f' Pominięto {pominiete_zero} pozycji z ilością 0 — pozostają w generatorze.'

            return Response({
                'success': True,
                'message': message,
                'zamowienia': utworzone_zamowienia,
                'pominiete_count': pominiete_count,
            })

    except Exception as e:
        return Response({'error': str(e)}, status=500)


@api_view(['POST'])
@login_required
def wyslij_do_zatwierdzenia_api(request):
    """
    Endpoint wysyłający zbiorczy email do szefa z listą zamówień do zatwierdzenia.
    Przyjmuje: { "zamowienie_ids": [1, 2, 3] }
    """
    from .models import Zamowienie
    from .utils import send_approval_email
    from django.utils import timezone

    zamowienie_ids = request.data.get('zamowienie_ids', [])
    if not zamowienie_ids:
        return Response({'error': 'Nie wybrano żadnych zamówień'}, status=400)

    zamowienia = Zamowienie.objects.filter(
        id__in=zamowienie_ids, status='draft'
    ).select_related('dostawca').prefetch_related('pozycje')

    if not zamowienia.exists():
        return Response({'error': 'Brak zamówień w statusie "Wersja robocza"'}, status=400)

    zamowienia_list = list(zamowienia)
    result = send_approval_email(zamowienia_list)

    if result['success']:
        # Zmień status na pending_approval
        zamowienia.update(status='pending_approval')

        user_name = get_user_display_name(request.user)
        numery = ', '.join([z.numer for z in zamowienia_list])
        email_szef = getattr(settings, 'EMAIL_SZEF', '')
        app_logger.success(user_name, f"Wysłano zamówienia do zatwierdzenia: {numery} → {email_szef}")

        return Response({
            'success': True,
            'message': f'Wysłano {len(zamowienia_list)} zamówień do zatwierdzenia.'
        })
    else:
        user_name = get_user_display_name(request.user)
        app_logger.error(user_name, f"Błąd wysyłki zamówień do zatwierdzenia: {result['message']}")
        return Response({'error': result['message']}, status=500)


@api_view(['POST'])
@login_required
def zatwierdz_zamowienia_api(request):
    """
    Endpoint zatwierdzający zamówienia (zmiana statusu pending_approval → verified).
    Przyjmuje: { "zamowienie_ids": [1, 2, 3] }
    """
    from .models import Zamowienie

    zamowienie_ids = request.data.get('zamowienie_ids', [])
    if not zamowienie_ids:
        return Response({'error': 'Nie wybrano żadnych zamówień'}, status=400)

    zamowienia = Zamowienie.objects.filter(
        id__in=zamowienie_ids, status='pending_approval'
    )

    if not zamowienia.exists():
        return Response({'error': 'Brak zamówień oczekujących na zatwierdzenie'}, status=400)

    count = zamowienia.count()
    numery = ', '.join(zamowienia.values_list('numer', flat=True))
    zamowienia.update(status='verified')

    user_name = get_user_display_name(request.user)
    app_logger.success(user_name, f"Zatwierdzono zamówienia: {numery}")

    return Response({
        'success': True,
        'message': f'Zatwierdzono {count} zamówień.'
    })


@api_view(['POST'])
@login_required
def cofnij_do_roboczej_api(request):
    """
    Cofnięcie zamówienia ze statusu pending_approval do draft.
    Przyjmuje: { "zamowienie_id": 1 }
    """
    from .models import Zamowienie

    zamowienie_id = request.data.get('zamowienie_id')
    if not zamowienie_id:
        return Response({'error': 'Brak ID zamówienia'}, status=400)

    try:
        zam = Zamowienie.objects.get(id=zamowienie_id, status='pending_approval')
    except Zamowienie.DoesNotExist:
        return Response({'error': 'Zamówienie nie istnieje lub nie oczekuje na zatwierdzenie'}, status=400)

    zam.status = 'draft'
    zam.save()

    user_name = get_user_display_name(request.user)
    app_logger.info(user_name, f"Cofnięto zamówienie {zam.numer} do wersji roboczej")

    return Response({'success': True, 'message': f'Zamówienie {zam.numer} cofnięte do wersji roboczej.'})


@api_view(['POST'])
@login_required
def zmien_dostawce_api(request):
    """
    Zmienia dostawcę istniejącego zamówienia (z istniejącej listy).
    Dozwolone tylko gdy status ∈ {draft, pending_approval, verified} — czyli zamówienie
    nie jest jeszcze w realizacji. Aktualizuje również email_docelowy na email nowego dostawcy.
    Przyjmuje: { "zamowienie_id": 1, "dostawca_id": 7 }
    """
    from .models import Zamowienie, Dostawca

    zamowienie_id = request.data.get('zamowienie_id')
    dostawca_id = request.data.get('dostawca_id')
    if not zamowienie_id or not dostawca_id:
        return Response({'error': 'Wymagane: zamowienie_id i dostawca_id'}, status=400)

    try:
        zam = Zamowienie.objects.get(id=zamowienie_id)
    except Zamowienie.DoesNotExist:
        return Response({'error': 'Zamówienie nie istnieje'}, status=404)

    if zam.status not in ('draft', 'pending_approval', 'verified'):
        return Response({'error': 'Zmiana dostawcy dozwolona tylko dla zamówień przed wysyłką'}, status=400)

    try:
        nowy_dostawca = Dostawca.objects.get(id=dostawca_id)
    except Dostawca.DoesNotExist:
        return Response({'error': 'Dostawca nie istnieje'}, status=404)

    if zam.dostawca_id == nowy_dostawca.id:
        return Response({'error': 'To już jest bieżący dostawca'}, status=400)

    stary_dostawca_nazwa = zam.dostawca.nazwa_firmy if zam.dostawca else 'brak'
    zam.dostawca = nowy_dostawca
    zam.email_docelowy = nowy_dostawca.email or ''
    zam.save(update_fields=['dostawca', 'email_docelowy'])

    user_name = get_user_display_name(request.user)
    app_logger.info(
        user_name,
        f"Zmieniono dostawcę zam. {zam.numer}: {stary_dostawca_nazwa} → {nowy_dostawca.nazwa_firmy}"
    )

    return Response({
        'success': True,
        'message': f'Dostawca zmieniony na: {nowy_dostawca.nazwa_firmy}',
    })


@api_view(['POST'])
@login_required
def cofnij_do_zatwierdzone_api(request):
    """
    Cofnięcie zamówienia ze statusu 'sent' (wysłane) do 'verified' (zatwierdzone).
    Zastosowanie: dostawca przedłuża realizację, chcemy zmienić dostawcę i wysłać ponownie.
    Blokada, gdy rozpoczęto już realizację (status 'partially_received' lub 'completed').
    Przyjmuje: { "zamowienie_id": 1 }
    """
    from .models import Zamowienie, RealizacjaZamowienia

    zamowienie_id = request.data.get('zamowienie_id')
    if not zamowienie_id:
        return Response({'error': 'Brak ID zamówienia'}, status=400)

    try:
        zam = Zamowienie.objects.get(id=zamowienie_id, status='sent')
    except Zamowienie.DoesNotExist:
        return Response({'error': 'Zamówienie nie istnieje lub nie jest w statusie "Wysłane"'}, status=400)

    # Dodatkowy bezpiecznik — gdyby istniała realizacja, blokuj cofnięcie.
    if RealizacjaZamowienia.objects.filter(zamowienie=zam).exists():
        return Response({'error': 'Nie można cofnąć — istnieje już rozpoczęta realizacja tego zamówienia'}, status=400)

    zam.status = 'verified'
    zam.data_wyslania = None
    zam.save(update_fields=['status', 'data_wyslania'])

    user_name = get_user_display_name(request.user)
    app_logger.info(user_name, f"Cofnięto zamówienie {zam.numer} do statusu 'Zatwierdzone' (było 'Wysłane')")

    return Response({'success': True, 'message': f'Zamówienie {zam.numer} cofnięte do statusu "Zatwierdzone".'})


@api_view(['POST'])
def wyslij_email_zamowienie_api(request, zamowienie_id):
    """
    Endpoint do wysyłki emaila z zamówieniem do dostawcy (+ kopia DW).
    """
    from .models import Zamowienie
    from .utils import send_zamowienie_email
    from django.utils import timezone

    try:
        zamowienie = Zamowienie.objects.select_related('dostawca').prefetch_related('pozycje').get(id=zamowienie_id)
    except Zamowienie.DoesNotExist:
        return Response({'error': 'Zamówienie nie istnieje'}, status=404)

    # Sprawdź czy zamówienie jest zatwierdzone
    if zamowienie.status not in ('verified', 'draft'):
        return Response({'error': 'Zamówienie musi być zatwierdzone przed wysyłką do dostawcy'}, status=400)

    # Sprawdź czy dostawca ma email
    if not zamowienie.email_docelowy:
        return Response({'error': 'Dostawca nie ma przypisanego adresu email'}, status=400)

    # Tryb testowy — podmiana adresu
    is_test = getattr(settings, 'ZAMOWIENIA_TESTOWE', False)
    override_email = None
    if is_test:
        override_email = getattr(settings, 'EMAIL_TEST_ADDRESS', '')
        if not override_email:
            return Response({'error': 'Brak adresu testowego w konfiguracji poczty'}, status=400)

    # Wyślij email
    result = send_zamowienie_email(zamowienie, override_email=override_email)

    if result['success']:
        # Zaktualizuj status i datę wysłania
        zamowienie.status = 'sent'
        zamowienie.data_wyslania = timezone.now()
        zamowienie.save()

        # Logowanie
        user_name = get_user_display_name(request.user)
        dostawca = zamowienie.dostawca.nazwa_firmy if zamowienie.dostawca else 'nieznany'
        target_email = override_email or zamowienie.email_docelowy
        test_info = " [TESTOWO]" if is_test else ""
        app_logger.success(user_name, f"Wysłano email z zamówieniem {zamowienie.numer} do: {dostawca} ({target_email}){test_info}")

        return Response({
            'success': True,
            'message': result['message']
        })
    else:
        # Logowanie błędu
        user_name = get_user_display_name(request.user)
        app_logger.error(user_name, f"Błąd wysyłki email z zamówieniem {zamowienie.numer}: {result['message']}")

        return Response({
            'error': result['message']
        }, status=500)


# ========== EMAIL API ==========

from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from .utils import send_test_email


@login_required
@require_http_methods(["POST"])
def test_email_view(request):
    """Endpoint do testowania wysyłki emaili"""
    result = send_test_email()
    # Logowanie
    user_name = get_user_display_name(request.user)
    if result.get('success'):
        app_logger.info(user_name, "Wysłano testowy email")
    else:
        app_logger.error(user_name, f"Błąd wysyłki testowego emaila: {result.get('message', 'nieznany błąd')}")
    return JsonResponse(result)


@login_required
@require_http_methods(["GET"])
def email_config_view(request):
    """Endpoint zwracający konfigurację email (bez hasła)"""
    from django.conf import settings

    config = {
        'email_host': getattr(settings, 'EMAIL_HOST', ''),
        'email_port': getattr(settings, 'EMAIL_PORT', ''),
        'email_use_ssl': getattr(settings, 'EMAIL_USE_SSL', False),
        'email_use_tls': getattr(settings, 'EMAIL_USE_TLS', False),
        'email_host_user': getattr(settings, 'EMAIL_HOST_USER', ''),
        'default_from_email': getattr(settings, 'DEFAULT_FROM_EMAIL', ''),
        'email_test_address': getattr(settings, 'EMAIL_TEST_ADDRESS', ''),
        'email_dw': getattr(settings, 'EMAIL_DW', ''),
        'email_configured': bool(getattr(settings, 'EMAIL_HOST_USER', '')),
        'zamowienia_testowe': getattr(settings, 'ZAMOWIENIA_TESTOWE', False),
        'imap_host': getattr(settings, 'IMAP_HOST', ''),
        'imap_port': getattr(settings, 'IMAP_PORT', ''),
        'imap_use_ssl': getattr(settings, 'IMAP_USE_SSL', False),
        'imap_sent_folder': getattr(settings, 'IMAP_SENT_FOLDER', ''),
        'imap_configured': bool(getattr(settings, 'IMAP_HOST', '')),
        'email_szef': getattr(settings, 'EMAIL_SZEF', ''),
    }

    return JsonResponse(config)


@login_required
@require_http_methods(["POST"])
def toggle_zamowienia_testowe(request):
    """Przełączanie trybu zamówień testowych."""
    from django.conf import settings
    import json

    data = json.loads(request.body)
    value = bool(data.get('zamowienia_testowe', False))
    settings.ZAMOWIENIA_TESTOWE = value

    # Persystencja do pliku
    settings_file = settings.BASE_DIR / 'app_settings.json'
    try:
        with open(settings_file, 'r') as f:
            app_settings = json.loads(f.read())
    except (FileNotFoundError, ValueError):
        app_settings = {}
    app_settings['zamowienia_testowe'] = value
    with open(settings_file, 'w') as f:
        f.write(json.dumps(app_settings, indent=2))

    user_name = get_user_display_name(request.user)
    msg = f"{'Włączono' if value else 'Wyłączono'} tryb zamówień testowych"
    if value:
        app_logger.warning(user_name, msg)
    else:
        app_logger.info(user_name, msg)

    return JsonResponse({'success': True, 'zamowienia_testowe': value})


# Dozwolone wartości ustawienia "Sposób liczenia zamówień" (slug → etykieta do logów/UI)
SPOSOBY_LICZENIA_ZAMOWIEN = {
    'standardowa': 'standardowa',
    'wedlug_nowych_elementow': 'według nowych elementów',
}


def get_sposob_liczenia_zamowien():
    """Aktualna wartość ustawienia "Sposób liczenia zamówień".

    Czytana z app_settings.json przy każdym wywołaniu — wartość w django.conf.settings
    może być nieaktualna przy wielu procesach (np. Apache/mod_wsgi na prod).
    """
    from django.conf import settings
    import json

    try:
        with open(settings.BASE_DIR / 'app_settings.json', 'r') as f:
            value = json.load(f).get('sposob_liczenia_zamowien')
    except (FileNotFoundError, ValueError):
        value = None
    if value not in SPOSOBY_LICZENIA_ZAMOWIEN:
        value = getattr(settings, 'SPOSOB_LICZENIA_ZAMOWIEN', 'standardowa')
        if value not in SPOSOBY_LICZENIA_ZAMOWIEN:
            value = 'standardowa'
    return value


@login_required
@require_http_methods(["GET", "POST"])
def sposob_liczenia_zamowien_view(request):
    """Odczyt (GET) / zmiana (POST) sposobu liczenia zamówień.

    Wartość persystowana w app_settings.json, każda zmiana logowana.
    """
    from django.conf import settings
    import json

    if request.method == 'GET':
        return JsonResponse({
            'sposob_liczenia_zamowien': get_sposob_liczenia_zamowien(),
        })

    data = json.loads(request.body)
    value = data.get('sposob_liczenia_zamowien')
    if value not in SPOSOBY_LICZENIA_ZAMOWIEN:
        return JsonResponse({'success': False, 'error': 'Nieprawidłowa wartość ustawienia.'}, status=400)

    old_value = get_sposob_liczenia_zamowien()
    settings.SPOSOB_LICZENIA_ZAMOWIEN = value

    # Persystencja do pliku
    settings_file = settings.BASE_DIR / 'app_settings.json'
    try:
        with open(settings_file, 'r') as f:
            app_settings = json.loads(f.read())
    except (FileNotFoundError, ValueError):
        app_settings = {}
    app_settings['sposob_liczenia_zamowien'] = value
    with open(settings_file, 'w') as f:
        f.write(json.dumps(app_settings, indent=2))

    if value != old_value:
        # Auto-pozycje generatora wyliczone poprzednią metodą tracą ważność — czyścimy,
        # generator odtworzy je nową metodą przy najbliższym odświeżeniu
        from .models import PozycjaGeneratora
        usuniete, _ = PozycjaGeneratora.objects.filter(zrodlo='auto').delete()

        user_name = get_user_display_name(request.user)
        stara = SPOSOBY_LICZENIA_ZAMOWIEN.get(old_value, old_value)
        nowa = SPOSOBY_LICZENIA_ZAMOWIEN[value]
        app_logger.warning(
            user_name,
            f"Zmieniono sposób liczenia zamówień: '{stara}' → '{nowa}'"
            f" (wyczyszczono auto-pozycje generatora: {usuniete})"
        )

    return JsonResponse({'success': True, 'sposob_liczenia_zamowien': value})


# ========== API VIEWSETS ==========

class StandardResultsSetPagination(PageNumberPagination):
    page_size = 100
    page_size_query_param = 'page_size'
    max_page_size = 1000


class KategoriaViewSet(LoggingMixin, viewsets.ModelViewSet):
    queryset = Kategoria.objects.prefetch_related('podkategorie').all()
    serializer_class = KategoriaSerializer
    log_name = 'kategorię'


class PodkategoriaViewSet(LoggingMixin, viewsets.ModelViewSet):
    queryset = Podkategoria.objects.select_related('kategoria').all()
    serializer_class = PodkategoriaSerializer
    log_name = 'podkategorię'


class DostawcaViewSet(LoggingMixin, viewsets.ModelViewSet):
    queryset = Dostawca.objects.all()
    serializer_class = DostawcaSerializer
    log_name = 'dostawcę'

    def get_log_description(self, instance):
        return instance.nazwa_firmy or instance.kod_dostawcy


class NumerKatalogowyDostawcyViewSet(LoggingMixin, viewsets.ModelViewSet):
    serializer_class = NumerKatalogowyDostawcySerializer
    log_name = 'mapowanie nr katalogowego'

    def get_queryset(self):
        qs = NumerKatalogowyDostawcy.objects.select_related('narzedzie', 'dostawca')
        dostawca_id = self.request.query_params.get('dostawca')
        if dostawca_id:
            qs = qs.filter(dostawca_id=dostawca_id)
        return qs

    def get_log_description(self, instance):
        return f"{instance.dostawca.nazwa_firmy}: {instance.narzedzie.numer_katalogowy or instance.narzedzie_id} → {instance.nr_katalogowy_dostawcy}"


class LokalizacjaViewSet(LoggingMixin, viewsets.ModelViewSet):
    queryset = Lokalizacja.objects.all()
    serializer_class = LokalizacjaSerializer
    log_name = 'lokalizację'

    def get_log_description(self, instance):
        return f"{instance.szafa}/{instance.polka}/{instance.kolumna}"

    @action(detail=False, methods=['post'])
    def dodaj_seryjnie(self, request):
        """Dodaje lokalizacje seryjnie używając serwisu"""
        from django.core.exceptions import ValidationError

        szafa = request.data.get('szafa')
        liczba_kolumn = request.data.get('liczba_kolumn', 1)
        liczba_polek = request.data.get('liczba_polek', 1)

        try:
            liczba_utworzonych = LokalizacjaService.utworz_lokalizacje_seryjnie(
                szafa=szafa,
                liczba_kolumn=liczba_kolumn,
                liczba_polek=liczba_polek
            )
            user_name = get_user_display_name(request.user)
            app_logger.success(user_name, f"Dodano seryjnie {liczba_utworzonych} lokalizacji dla szafy {szafa}")
            return Response(
                {'message': f'Dodano {liczba_utworzonych} lokalizacji dla szafy {szafa}.'},
                status=status.HTTP_201_CREATED
            )
        except ValidationError as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )


class MaszynaViewSet(LoggingMixin, viewsets.ModelViewSet):
    queryset = Maszyna.objects.all()
    serializer_class = MaszynaSerializer
    log_name = 'maszynę'


class PracownikViewSet(LoggingMixin, viewsets.ModelViewSet):
    queryset = Pracownik.objects.select_related('user').all()
    serializer_class = PracownikSerializer
    pagination_class = StandardResultsSetPagination
    log_name = 'pracownika'

    def get_log_description(self, instance):
        return f"{instance.nazwisko} {instance.imie}"

    def get_queryset(self):
        queryset = super().get_queryset()
        # Domyślnie zwracaj tylko pracowników mogących pobierać narzędzia
        # Użyj ?all=true aby pobrać wszystkich (np. dla panelu admina)
        show_all = self.request.query_params.get('all', 'false').lower() == 'true'
        if not show_all:
            queryset = queryset.filter(pobieranie_narzedzi=True).filter(
                Q(user__is_active=True) | Q(user__isnull=True)
            )
        return queryset


class FakturaZakupuViewSet(LoggingMixin, viewsets.ModelViewSet):
    queryset = FakturaZakupu.objects.select_related('dostawca').all()
    serializer_class = FakturaZakupuSerializer
    pagination_class = StandardResultsSetPagination
    log_name = 'fakturę'

    def get_log_description(self, instance):
        return f"{instance.numer_faktury} ({instance.dostawca.nazwa_firmy if instance.dostawca else 'brak dostawcy'})"

    def get_queryset(self):
        queryset = super().get_queryset()
        narzedzie_id = self.request.query_params.get('narzedzie_id', None)

        if narzedzie_id:
            queryset = queryset.filter(
                egzemplarze__narzedzie_typ_id=narzedzie_id
            ).distinct()

        return queryset.order_by('-data_wystawienia')


class NarzedzieMagazynoweViewSet(LoggingMixin, viewsets.ModelViewSet):
    serializer_class = NarzedzieMagazynoweSerializer
    log_name = 'typ narzędzia'

    def get_log_description(self, instance):
        if instance.podkategoria:
            return f"{instance.podkategoria.kategoria.nazwa}/{instance.podkategoria.nazwa} - {instance.opis}"
        return instance.opis

    def get_queryset(self):
        from django.db.models import Value, Subquery, OuterRef
        from django.db.models.functions import Coalesce

        # IDs egzemplarzy aktualnie wydanych (w użyciu)
        egzemplarze_w_uzyciu = HistoriaUzyciaNarzedzia.objects.filter(
            data_zwrotu__isnull=True
        ).values('egzemplarz_id')

        # Subquery dla ilości nowych (stan='nowe') NIE WYDANYCH
        nowe_subquery = EgzemplarzNarzedzia.objects.filter(
            narzedzie_typ=OuterRef('pk'),
            stan='nowe'
        ).exclude(
            id__in=Subquery(egzemplarze_w_uzyciu)
        ).values('narzedzie_typ').annotate(
            total=Sum('ilosc_w_komplecie')
        ).values('total')

        # Subquery dla ilości używanych (stan='uzywane') NIE WYDANYCH
        uzywane_subquery = EgzemplarzNarzedzia.objects.filter(
            narzedzie_typ=OuterRef('pk'),
            stan='uzywane'
        ).exclude(
            id__in=Subquery(egzemplarze_w_uzyciu)
        ).values('narzedzie_typ').annotate(
            total=Sum('ilosc_w_komplecie')
        ).values('total')

        # Subquery dla ilości w użyciu - sumujemy ilosc_w_komplecie egzemplarzy
        # które mają AKTYWNE wypożyczenie (wpis w historii bez daty zwrotu)
        w_uzyciu_subquery = HistoriaUzyciaNarzedzia.objects.filter(
            egzemplarz__narzedzie_typ=OuterRef('pk'),
            data_zwrotu__isnull=True
        ).values('egzemplarz__narzedzie_typ').annotate(
            total=Sum('egzemplarz__ilosc_w_komplecie')
        ).values('total')

        queryset = NarzedzieMagazynowe.objects.select_related(
            'podkategoria__kategoria',
            'ostatni_dostawca',
            'domyslna_lokalizacja'
        ).annotate(
            ilosc_nowych=Coalesce(Subquery(nowe_subquery), Value(0)),
            ilosc_uzywanych_dostepnych=Coalesce(Subquery(uzywane_subquery), Value(0)),
            ilosc_w_uzyciu=Coalesce(Subquery(w_uzyciu_subquery), Value(0)),
        ).annotate(
            calkowita_ilosc=F('ilosc_nowych') + F('ilosc_uzywanych_dostepnych') + F('ilosc_w_uzyciu')
        )

        # Filtr stanowiskowy: tokarz/frezer/ślusarz widzą wyłącznie kategorie z ich grupą.
        # Pozostałe role widzą wszystko. Kategorie bez grupy_stanowiska są niewidoczne
        # dla tych 3 stanowisk (wariant b: jawnie przypisane → widoczne).
        grupa_stanowiska = get_user_grupa_stanowiska(self.request.user)
        if grupa_stanowiska:
            queryset = queryset.filter(podkategoria__kategoria__grupa_stanowiska=grupa_stanowiska)

        return queryset.order_by('podkategoria__kategoria__nazwa', 'podkategoria__nazwa', 'opis')


class NarzedzieMagazynoweProdViewSet(viewsets.ReadOnlyModelViewSet):
    """Lekki, niepaginowany endpoint dla widoku Produkcja — minimum pól, brak pagination."""
    pagination_class = None

    def get_serializer_class(self):
        from .serializers import NarzedzieMagazynoweProdSerializer
        return NarzedzieMagazynoweProdSerializer

    def get_queryset(self):
        from django.db.models import Value, Subquery, OuterRef
        from django.db.models.functions import Coalesce

        egzemplarze_w_uzyciu = HistoriaUzyciaNarzedzia.objects.filter(
            data_zwrotu__isnull=True
        ).values('egzemplarz_id')

        nowe_subquery = EgzemplarzNarzedzia.objects.filter(
            narzedzie_typ=OuterRef('pk'), stan='nowe'
        ).exclude(id__in=Subquery(egzemplarze_w_uzyciu)) \
         .values('narzedzie_typ').annotate(total=Sum('ilosc_w_komplecie')).values('total')

        uzywane_subquery = EgzemplarzNarzedzia.objects.filter(
            narzedzie_typ=OuterRef('pk'), stan='uzywane'
        ).exclude(id__in=Subquery(egzemplarze_w_uzyciu)) \
         .values('narzedzie_typ').annotate(total=Sum('ilosc_w_komplecie')).values('total')

        w_uzyciu_subquery = HistoriaUzyciaNarzedzia.objects.filter(
            egzemplarz__narzedzie_typ=OuterRef('pk'),
            data_zwrotu__isnull=True
        ).values('egzemplarz__narzedzie_typ') \
         .annotate(total=Sum('egzemplarz__ilosc_w_komplecie')).values('total')

        queryset = NarzedzieMagazynowe.objects.select_related(
            'podkategoria__kategoria'
        ).annotate(
            ilosc_nowych=Coalesce(Subquery(nowe_subquery), Value(0)),
            ilosc_uzywanych_dostepnych=Coalesce(Subquery(uzywane_subquery), Value(0)),
            ilosc_w_uzyciu=Coalesce(Subquery(w_uzyciu_subquery), Value(0)),
        ).annotate(
            calkowita_ilosc=F('ilosc_nowych') + F('ilosc_uzywanych_dostepnych') + F('ilosc_w_uzyciu')
        )

        # Filtr stanowiskowy: tokarz/frezer/ślusarz widzą wyłącznie kategorie z ich grupą.
        grupa_stanowiska = get_user_grupa_stanowiska(self.request.user)
        if grupa_stanowiska:
            queryset = queryset.filter(podkategoria__kategoria__grupa_stanowiska=grupa_stanowiska)

        return queryset.order_by('podkategoria__kategoria__nazwa', 'podkategoria__nazwa', 'opis')


class NarzedzieMagazynoweZakupyViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = NarzedzieMagazynoweSerializer

    def get_queryset(self):
        from django.db.models import Value, Subquery, OuterRef
        from django.db.models.functions import Coalesce

        # IDs egzemplarzy aktualnie wydanych (w użyciu)
        egzemplarze_w_uzyciu = HistoriaUzyciaNarzedzia.objects.filter(
            data_zwrotu__isnull=True
        ).values('egzemplarz_id')

        # Subquery dla ilości nowych (stan='nowe') NIE WYDANYCH
        nowe_subquery = EgzemplarzNarzedzia.objects.filter(
            narzedzie_typ=OuterRef('pk'),
            stan='nowe'
        ).exclude(
            id__in=Subquery(egzemplarze_w_uzyciu)
        ).values('narzedzie_typ').annotate(
            total=Sum('ilosc_w_komplecie')
        ).values('total')

        # Subquery dla ilości używanych (stan='uzywane') NIE WYDANYCH
        uzywane_subquery = EgzemplarzNarzedzia.objects.filter(
            narzedzie_typ=OuterRef('pk'),
            stan='uzywane'
        ).exclude(
            id__in=Subquery(egzemplarze_w_uzyciu)
        ).values('narzedzie_typ').annotate(
            total=Sum('ilosc_w_komplecie')
        ).values('total')

        # Subquery dla ilości w użyciu - sumujemy ilosc_w_komplecie egzemplarzy
        # które mają AKTYWNE wypożyczenie (wpis w historii bez daty zwrotu)
        w_uzyciu_subquery = HistoriaUzyciaNarzedzia.objects.filter(
            egzemplarz__narzedzie_typ=OuterRef('pk'),
            data_zwrotu__isnull=True
        ).values('egzemplarz__narzedzie_typ').annotate(
            total=Sum('egzemplarz__ilosc_w_komplecie')
        ).values('total')

        queryset = NarzedzieMagazynowe.objects.select_related(
            'podkategoria__kategoria',
            'ostatni_dostawca',
            'domyslna_lokalizacja'
        ).annotate(
            ilosc_nowych=Coalesce(Subquery(nowe_subquery), Value(0)),
            ilosc_uzywanych_dostepnych=Coalesce(Subquery(uzywane_subquery), Value(0)),
            ilosc_w_uzyciu=Coalesce(Subquery(w_uzyciu_subquery), Value(0)),
        ).annotate(
            calkowita_ilosc=F('ilosc_nowych') + F('ilosc_uzywanych_dostepnych') + F('ilosc_w_uzyciu')
        )
        return queryset.order_by('podkategoria__kategoria__nazwa', 'podkategoria__nazwa', 'opis')


class EgzemplarzNarzedziaViewSet(LoggingMixin, viewsets.ModelViewSet):
    queryset = EgzemplarzNarzedzia.objects.select_related(
        'narzedzie_typ__podkategoria__kategoria',
        'lokalizacja',
        'faktura_zakupu'
    ).all()
    serializer_class = EgzemplarzNarzedziaSerializer
    log_name = 'egzemplarz narzędzia'

    def get_log_description(self, instance):
        return f"{instance.narzedzie_typ.opis} (ID: {instance.id})"

    def get_queryset(self):
        queryset = super().get_queryset()
        narzedzie_typ_id = self.request.query_params.get('narzedzie_typ_id', None)

        if narzedzie_typ_id:
            queryset = queryset.filter(narzedzie_typ_id=narzedzie_typ_id)

        # Ukryj egzemplarze z ilosc_w_komplecie=0 (duchy po scaleniu, istnieją dla historii)
        queryset = queryset.filter(ilosc_w_komplecie__gt=0)

        return queryset.order_by('-data_zakupu')

    @action(detail=True, methods=['get'])
    def etykieta(self, request, pk=None):
        """Generuje etykietę DXF z oznaczeniem egzemplarza.

        Tylko tekst (bez ramki), wysokość 1.6 mm. Jednostki: milimetry.
        """
        import ezdxf
        import io

        egzemplarz = self.get_object()

        if not egzemplarz.oznaczenie:
            return Response(
                {'error': 'Egzemplarz nie ma oznaczenia'},
                status=400
            )

        TEXT_HEIGHT = 1.6  # mm

        doc = ezdxf.new('R2010')
        doc.units = 4  # 4 = millimeters (INSUNITS)
        msp = doc.modelspace()

        msp.add_text(
            egzemplarz.oznaczenie,
            dxfattribs={
                'height': TEXT_HEIGHT,
                'halign': ezdxf.enums.TextHAlign.CENTER,
                'valign': ezdxf.enums.TextVAlign.MIDDLE,
                'insert': (0, 0),
                'align_point': (0, 0),
            }
        )

        buffer = io.StringIO()
        doc.write(buffer)

        from django.http import HttpResponse
        response = HttpResponse(buffer.getvalue().encode('utf-8'), content_type='application/dxf')
        response['Content-Disposition'] = f'attachment; filename="{egzemplarz.oznaczenie}.dxf"'
        return response

    def destroy(self, request, *args, **kwargs):
        """
        Usuwa egzemplarz narzędzia i loguje operację.
        """
        egzemplarz = self.get_object()

        # Loguj usunięcie
        user_name = get_user_display_name(request.user)
        opis = f"{egzemplarz.narzedzie_typ.opis} (ID: {egzemplarz.id}, stan: {egzemplarz.get_stan_display()})"
        app_logger.warning(user_name, f"Usunięto egzemplarz narzędzia: {opis}")

        # Usuń egzemplarz
        egzemplarz.delete()

        return Response(status=status.HTTP_204_NO_CONTENT)


class HistoriaUzyciaNarzedziaViewSet(viewsets.ModelViewSet):
    queryset = HistoriaUzyciaNarzedzia.objects.select_related(
        'egzemplarz__narzedzie_typ__podkategoria__kategoria',
        'maszyna',
        'pracownik__user',
        'pracownik_zwracajacy__user'
    ).all()
    serializer_class = HistoriaUzyciaNarzedziaSerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        narzedzie_id = self.request.query_params.get('narzedzie_id', None)
        w_uzyciu = self.request.query_params.get('w_uzyciu', None)

        if narzedzie_id:
            queryset = queryset.filter(egzemplarz__narzedzie_typ_id=narzedzie_id)

        if w_uzyciu and w_uzyciu.lower() == 'true':
            queryset = queryset.filter(data_zwrotu__isnull=True)

        return queryset.order_by('-data_wydania')

    @action(detail=False, methods=['post'])
    def wydanie(self, request):
        """Wydaje narzędzie pracownikowi używając serwisu"""
        from django.core.exceptions import ValidationError

        egzemplarz_id = request.data.get('egzemplarz_id')
        maszyna_id = request.data.get('maszyna_id')
        pracownik_id = request.data.get('pracownik_id')
        czesciowe_wydanie = request.data.get('czesciowe_wydanie', False)
        ilosc_sztuk = request.data.get('ilosc_sztuk')
        nr_zlecenia = request.data.get('nr_zlecenia')

        try:
            historia = EgzemplarzService.wydaj_egzemplarz(
                egzemplarz_id=egzemplarz_id,
                maszyna_id=maszyna_id,
                pracownik_id=pracownik_id,
                czesciowe_wydanie=czesciowe_wydanie,
                ilosc_sztuk=ilosc_sztuk,
                nr_zlecenia=nr_zlecenia
            )
            # Logowanie wydania
            user_name = get_user_display_name(request.user)
            narzedzie_opis = historia.egzemplarz.narzedzie_typ.opis
            pracownik_info = f"{historia.pracownik.nazwisko} {historia.pracownik.imie}" if historia.pracownik else "nieznany"
            maszyna_info = historia.maszyna.nazwa if historia.maszyna else "brak"
            app_logger.success(user_name, f"Wydano narzędzie: {narzedzie_opis} → pracownik: {pracownik_info}, maszyna: {maszyna_info}")

            serializer = self.get_serializer(historia)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        except ValidationError as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=True, methods=['post'])
    def zwrot(self, request, pk=None):
        """Zwraca narzędzie używając serwisu"""
        from django.core.exceptions import ValidationError

        historia = self.get_object()
        stan_po_zwrocie = request.data.get('stan_po_zwrocie', 'uzywane')
        pracownik_zwracajacy_id = request.data.get('pracownik_zwracajacy_id')
        czesciowy_zwrot = request.data.get('czesciowy_zwrot', False)
        ilosc_sztuk = request.data.get('ilosc_sztuk')
        karta_uszkodzenia = request.data.get('karta_uszkodzenia')  # Dane karty uszkodzenia

        try:
            result = EgzemplarzService.zwroc_egzemplarz(
                historia_id=historia.id,
                stan_po_zwrocie=stan_po_zwrocie,
                czesciowy_zwrot=czesciowy_zwrot,
                ilosc_sztuk=ilosc_sztuk
            )

            # result może być historia (pełny zwrot) lub tuple (historia_updated, egzemplarz_zwrocony) dla częściowego
            if isinstance(result, tuple):
                historia_updated, egzemplarz_zwrocony = result
                # Przy częściowym zwrocie, historia pozostaje otwarta
                # egzemplarz_zwrocony to nowy egzemplarz ze zwróconymi sztukami
            else:
                historia_updated = result
                egzemplarz_zwrocony = historia_updated.egzemplarz

            # Zapisz pracownika zwracającego
            if pracownik_zwracajacy_id:
                try:
                    pracownik_zwracajacy = Pracownik.objects.get(id=pracownik_zwracajacy_id)
                    historia_updated.pracownik_zwracajacy = pracownik_zwracajacy
                    historia_updated.save()
                except Pracownik.DoesNotExist:
                    pass

            # Zapisz stan po zwrocie w historii
            historia_updated.stan_po_zwrocie = stan_po_zwrocie
            historia_updated.save()

            # Zapisz opis narzędzia do logowania (przed ewentualnym usunięciem egzemplarza)
            narzedzie_opis_do_logu = historia.egzemplarz.narzedzie_typ.opis if historia.egzemplarz and historia.egzemplarz.narzedzie_typ else 'nieznane'

            # Jeśli uszkodzone lub uszkodzone_regeneracja, utwórz wpis w tabeli uszkodzeń
            if stan_po_zwrocie in ['uszkodzone', 'uszkodzone_regeneracja']:
                # Przygotuj dane do zapisu w uszkodzeniu (snapshot przed usunięciem egzemplarza)
                narzedzie_typ = egzemplarz_zwrocony.narzedzie_typ
                narzedzie_opis = narzedzie_typ.opis if narzedzie_typ else ''
                numer_katalogowy = (narzedzie_typ.numer_katalogowy or '') if narzedzie_typ else ''
                kategoria_narzedzia = ''
                if narzedzie_typ and narzedzie_typ.podkategoria:
                    kategoria_narzedzia = f"{narzedzie_typ.podkategoria.kategoria.nazwa} / {narzedzie_typ.podkategoria.nazwa}"
                lokalizacja_opis = ''
                if egzemplarz_zwrocony.lokalizacja:
                    lok = egzemplarz_zwrocony.lokalizacja
                    lokalizacja_opis = f"{lok.szafa}/{lok.polka}/{lok.kolumna}"
                maszyna_nazwa = historia.maszyna.nazwa if historia.maszyna else ''
                pracownik_nazwisko = historia.pracownik.nazwisko if historia.pracownik else ''
                pracownik_imie = historia.pracownik.imie if historia.pracownik else ''
                stan = egzemplarz_zwrocony.get_stan_display() if hasattr(egzemplarz_zwrocony, 'get_stan_display') else egzemplarz_zwrocony.stan

                if stan_po_zwrocie == 'uszkodzone' and karta_uszkodzenia:
                    # Uszkodzone z kartą uszkodzenia - generuj numer karty i zapisz pełne dane
                    numer_karty = Uszkodzenie.generuj_numer_karty()
                    uszkodzenie = Uszkodzenie.objects.create(
                        egzemplarz=None,  # Egzemplarz zostanie usunięty
                        narzedzie_typ=narzedzie_typ,
                        narzedzie_opis=narzedzie_opis,
                        numer_katalogowy=numer_katalogowy,
                        kategoria_narzedzia=kategoria_narzedzia,
                        lokalizacja_opis=lokalizacja_opis,
                        stan=stan,
                        maszyna_nazwa=maszyna_nazwa,
                        pracownik_nazwisko=pracownik_nazwisko,
                        pracownik_imie=pracownik_imie,
                        opis_uszkodzenia=karta_uszkodzenia.get('uwagi', ''),
                        pracownik=historia.pracownik,
                        numer_karty=numer_karty,
                        przyczyna_uszkodzenia=karta_uszkodzenia.get('przyczyna_uszkodzenia', ''),
                        stracony_czas=karta_uszkodzenia.get('stracony_czas', ''),
                        typ_zglaszajacego=karta_uszkodzenia.get('typ_zglaszajacego', ''),
                        nazwisko_zglaszajacego=karta_uszkodzenia.get('nazwisko_zglaszajacego', '')
                    )
                    # Usuń egzemplarz
                    egzemplarz_zwrocony.delete()
                elif stan_po_zwrocie == 'uszkodzone_regeneracja':
                    # Uszkodzone do regeneracji - z kartą w formacie RRRR/XXXR
                    numer_karty_regen = Uszkodzenie.generuj_numer_karty_regeneracji()
                    Uszkodzenie.objects.create(
                        egzemplarz=None,  # Egzemplarz zostanie usunięty
                        narzedzie_typ=narzedzie_typ,
                        narzedzie_opis=narzedzie_opis,
                        numer_katalogowy=numer_katalogowy,
                        kategoria_narzedzia=kategoria_narzedzia,
                        lokalizacja_opis=lokalizacja_opis,
                        stan='Uszkodzone do regeneracji',
                        maszyna_nazwa=maszyna_nazwa,
                        pracownik_nazwisko=pracownik_nazwisko,
                        pracownik_imie=pracownik_imie,
                        opis_uszkodzenia=request.data.get('uwagi', 'Zużyte do regeneracji'),
                        pracownik=historia.pracownik,
                        numer_karty=numer_karty_regen
                    )
                    # Usuń egzemplarz
                    egzemplarz_zwrocony.delete()
                else:
                    # Fallback - uszkodzone bez karty (stary tryb)
                    opis_domyslny = 'Uszkodzenie podczas użycia'
                    Uszkodzenie.objects.create(
                        egzemplarz=egzemplarz_zwrocony,
                        opis_uszkodzenia=request.data.get('uwagi', opis_domyslny),
                        pracownik=historia.pracownik
                    )

            # Logowanie zwrotu
            user_name = get_user_display_name(request.user)
            stan_map = {'nowe': 'nowe', 'uzywane': 'używane', 'uszkodzone': 'uszkodzone', 'uszkodzone_regeneracja': 'do regeneracji'}
            stan_tekst = stan_map.get(stan_po_zwrocie, stan_po_zwrocie)
            if stan_po_zwrocie in ['uszkodzone', 'uszkodzone_regeneracja']:
                app_logger.warning(user_name, f"Zwrócono narzędzie jako {stan_tekst}: {narzedzie_opis_do_logu}")
            else:
                app_logger.success(user_name, f"Zwrócono narzędzie ({stan_tekst}): {narzedzie_opis_do_logu}")

            serializer = self.get_serializer(historia_updated)
            return Response(serializer.data)
        except ValidationError as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )


class UszkodzenieViewSet(LoggingMixin, viewsets.ModelViewSet):
    queryset = Uszkodzenie.objects.select_related(
        'egzemplarz__narzedzie_typ__podkategoria__kategoria',
        'pracownik'
    ).all()
    serializer_class = UszkodzenieSerializer
    log_name = 'uszkodzenie'

    def get_log_description(self, instance):
        narzedzie = instance.narzedzie_opis or (instance.egzemplarz.narzedzie_typ.opis if instance.egzemplarz else 'nieznane')
        return f"{narzedzie} (ID: {instance.id})"

    def get_queryset(self):
        return super().get_queryset().order_by('-data_uszkodzenia')

    @action(detail=False, methods=['get'])
    def nastepny_numer_karty(self, request):
        """Zwraca następny numer karty uszkodzenia"""
        numer = Uszkodzenie.generuj_numer_karty()
        return Response({'numer_karty': numer})

    @action(detail=True, methods=['get'])
    def pdf(self, request, pk=None):
        """
        Generuje PDF karty uszkodzenia (WeasyPrint + HTML template).
        """
        import os
        from django.http import HttpResponse
        from django.template.loader import render_to_string
        from django.conf import settings
        from weasyprint import HTML

        uszkodzenie = self.get_object()

        # Ścieżka do logo
        logo_path = os.path.join(settings.BASE_DIR, 'static_dev', 'images', 'logo-cnc.png')

        # Przygotowanie danych zgłaszającego
        zglaszajacy = uszkodzenie.nazwisko_zglaszajacego
        if not zglaszajacy and uszkodzenie.pracownik_nazwisko:
            zglaszajacy = f"{uszkodzenie.pracownik_nazwisko} {uszkodzenie.pracownik_imie}".strip()

        # Dane narzędzia
        kategoria = uszkodzenie.kategoria_narzedzia
        narzedzie = uszkodzenie.narzedzie_opis
        numer_katalogowy = uszkodzenie.numer_katalogowy

        # Jeśli nie ma snapshotów, próbuj pobrać z egzemplarza
        if uszkodzenie.egzemplarz:
            egz = uszkodzenie.egzemplarz
            if egz.narzedzie_typ:
                if not narzedzie:
                    narzedzie = egz.narzedzie_typ.opis
                if not numer_katalogowy:
                    numer_katalogowy = egz.narzedzie_typ.numer_katalogowy
                if not kategoria and egz.narzedzie_typ.podkategoria:
                    kategoria = f"{egz.narzedzie_typ.podkategoria.kategoria.nazwa} / {egz.narzedzie_typ.podkategoria.nazwa}"

        context = {
            'numer_karty': uszkodzenie.numer_karty or '-',
            'data_uszkodzenia': uszkodzenie.data_uszkodzenia.strftime('%Y-%m-%d %H:%M'),
            'maszyna': uszkodzenie.maszyna_nazwa,
            'zglaszajacy': zglaszajacy,
            'kategoria': kategoria,
            'narzedzie': narzedzie,
            'numer_katalogowy': numer_katalogowy,
            'przyczyna': uszkodzenie.przyczyna_uszkodzenia,
            'stracony_czas': uszkodzenie.stracony_czas,
            'uwagi': uszkodzenie.opis_uszkodzenia,
            'logo_path': f'file://{logo_path}',
            'data_wydruku': getattr(settings, 'PDF_USZKODZENIE_DATA', ''),
            'wersja_dokumentu': getattr(settings, 'PDF_USZKODZENIE_WERSJA', 1),
        }

        # Renderowanie HTML
        html_string = render_to_string('pdf/karta_uszkodzenia.html', context)

        # Generowanie PDF
        pdf_file = HTML(string=html_string, base_url=str(settings.BASE_DIR)).write_pdf()

        filename = f"Karta_uszkodzenia_{uszkodzenie.numer_karty or uszkodzenie.id}.pdf".replace('/', '-')
        response = HttpResponse(pdf_file, content_type='application/pdf')
        response['Content-Disposition'] = f'inline; filename="{filename}"'
        return response

    @action(detail=False, methods=['post'])
    def pdf_lista(self, request):
        """
        Generuje zbiorczy PDF z listą uszkodzeń.
        Przyjmuje listę ID uszkodzeń w body: {"ids": [1, 2, 3], "typ": "uszkodzone"|"regeneracja"}
        """
        import os
        from django.http import HttpResponse
        from django.template.loader import render_to_string
        from weasyprint import HTML

        ids = request.data.get('ids', [])
        typ = request.data.get('typ', 'uszkodzone')

        if not ids:
            return Response({'error': 'Brak ID uszkodzeń'}, status=status.HTTP_400_BAD_REQUEST)

        uszkodzenia = Uszkodzenie.objects.filter(id__in=ids).order_by('-data_uszkodzenia')

        logo_path = os.path.join(settings.BASE_DIR, 'static_dev', 'images', 'logo-cnc.png')

        # Ustawienia zależne od typu
        if typ == 'regeneracja':
            typ_raportu = 'Do regeneracji'
            tytul_dokumentu = 'LISTA NARZĘDZI DO REGENERACJI'
            filename_prefix = 'Lista_do_regeneracji'
        else:
            typ_raportu = 'Uszkodzenia'
            tytul_dokumentu = 'LISTA USZKODZONYCH NARZĘDZI'
            filename_prefix = 'Lista_uszkodzen'

        # Przygotuj dane do szablonu
        lista = []
        for u in uszkodzenia:
            zglaszajacy = u.nazwisko_zglaszajacego
            if not zglaszajacy and u.pracownik_nazwisko:
                zglaszajacy = f"{u.pracownik_nazwisko} {u.pracownik_imie}".strip()

            lista.append({
                'numer_karty': u.numer_karty or '-',
                'data_uszkodzenia': u.data_uszkodzenia.strftime('%Y-%m-%d %H:%M'),
                'maszyna': u.maszyna_nazwa or '-',
                'zglaszajacy': zglaszajacy or '-',
                'kategoria': u.kategoria_narzedzia or '-',
                'narzedzie': u.narzedzie_opis or '-',
                'numer_katalogowy': u.numer_katalogowy or '-',
                'przyczyna': u.przyczyna_uszkodzenia or '-',
                'stracony_czas': u.stracony_czas or '-',
                'uwagi': u.opis_uszkodzenia or '-',
            })

        context = {
            'uszkodzenia': lista,
            'liczba': len(lista),
            'typ_raportu': typ_raportu,
            'tytul_dokumentu': tytul_dokumentu,
            'data_wydruku': datetime.now().strftime('%Y-%m-%d %H:%M'),
            'logo_path': f'file://{logo_path}',
            'wersja_dokumentu': getattr(settings, 'PDF_LISTA_USZKODZEN_WERSJA', 1),
        }

        # Renderowanie HTML
        html_string = render_to_string('pdf/lista_uszkodzen.html', context)

        # Generowanie PDF
        pdf_file = HTML(string=html_string, base_url=str(settings.BASE_DIR)).write_pdf()

        today = datetime.now().strftime('%Y-%m-%d')
        response = HttpResponse(pdf_file, content_type='application/pdf')
        response['Content-Disposition'] = f'inline; filename="{filename_prefix}_{today}.pdf"'
        return response


def _propaguj_status_zapotrzebowan(zamowienie):
    """
    Po zmianie statusu zamówienia na completed/partially_received propaguje
    status do powiązanych ZapotrzebowanieTechnologa:
    - jeśli WSZYSTKIE zamówienia powiązane z danym zapotrzebowaniem mają
      status='completed' → ustaw status zapotrzebowania na 'completed'.
    """
    from django.utils import timezone as _tz
    powiazane = zamowienie.zrodlowe_zapotrzebowania.all()
    for zap in powiazane:
        wszystkie = zap.zamowienia.all()
        if wszystkie.exists() and all(z.status == 'completed' for z in wszystkie):
            if zap.status != 'completed':
                zap.status = 'completed'
                if not zap.data_realizacji:
                    zap.data_realizacji = _tz.now()
                zap.save(update_fields=['status', 'data_realizacji'])


class ZamowienieViewSet(LoggingMixin, viewsets.ModelViewSet):
    queryset = Zamowienie.objects.select_related('dostawca').prefetch_related('pozycje').all()
    serializer_class = ZamowienieSerializer
    log_name = 'zamówienie'

    def get_log_description(self, instance):
        dostawca = instance.dostawca.nazwa_firmy if instance.dostawca else 'brak dostawcy'
        return f"{instance.numer} ({dostawca})"

    def get_queryset(self):
        queryset = super().get_queryset()
        narzedzie_id = self.request.query_params.get('narzedzie_id', None)
        if narzedzie_id:
            # Pobierz ID zamówień które mają pozycję z danym narzędziem
            from .models import PozycjaZamowienia
            zamowienie_ids = PozycjaZamowienia.objects.filter(
                narzedzie_typ_id=narzedzie_id
            ).values_list('zamowienie_id', flat=True).distinct()
            queryset = queryset.filter(id__in=zamowienie_ids)
        return queryset.order_by('-data_utworzenia')

    def _strip_logistyka_only_fields(self, serializer):
        # Pole nr_oferty_dostawcy może edytować tylko grupa 'logistyka'.
        user = self.request.user
        if not user.groups.filter(name='logistyka').exists():
            serializer.validated_data.pop('nr_oferty_dostawcy', None)

    def perform_create(self, serializer):
        self._strip_logistyka_only_fields(serializer)
        super().perform_create(serializer)

    def perform_update(self, serializer):
        self._strip_logistyka_only_fields(serializer)
        super().perform_update(serializer)

    def perform_destroy(self, instance):
        """
        Przy kasowaniu zamówienia usuń również narzędzia utworzone ręcznie razem z tym
        zamówieniem (tryb "Nowe narzędzie" w generatorze) — ale tylko te bez egzemplarzy
        (czyli dostawa nie została jeszcze przyjęta). Kategorie/podkategorie zostają.
        """
        # Zbierz ręcznie utworzone narzędzia przypisane do tego zamówienia.
        # Pomiń te, które mają egzemplarze (fizyczne sztuki w magazynie).
        narzedzia_do_usuniecia = list(
            instance.narzedzia_utworzone_recznie
                    .annotate(liczba_egz=Count('egzemplarze'))
                    .filter(liczba_egz=0)
        )
        nazwy = [n.opis for n in narzedzia_do_usuniecia]

        # Najpierw usuń zamówienie (kaskadowo znikną PozycjaZamowienia wskazujące na te narzędzia).
        super().perform_destroy(instance)

        # Potem usuń same narzędzia.
        for n in narzedzia_do_usuniecia:
            try:
                n.delete()
            except Exception:
                # Jeśli coś jeszcze trzyma narzędzie (np. historia) — zostaw, nie wywalaj całej operacji.
                pass

        if nazwy:
            user_name = get_user_display_name(self.request.user)
            app_logger.info(
                user_name,
                f"Przy usuwaniu zam. {instance.numer} skasowano {len(nazwy)} ręcznie utworzone narzędzie(a): {', '.join(nazwy)}"
            )

    @action(detail=False, methods=['post'])
    def generuj_automatyczne(self, request):
        """Generuje zamówienia dla narzędzi poniżej limitu"""
        pass

    @action(detail=True, methods=['post'])
    def wyslij_email(self, request, pk=None):
        """Wysyła zamówienie mailem do dostawcy"""
        pass

    @action(detail=True, methods=['post'])
    def rozpocznij_realizacje(self, request, pk=None):
        """Tworzy realizację do zaznaczania przychodzących pozycji"""
        from .models import RealizacjaZamowienia, PozycjaRealizacji

        try:
            zamowienie = self.get_object()

            # Sprawdź czy realizacja już istnieje
            if RealizacjaZamowienia.objects.filter(zamowienie=zamowienie).exists():
                return Response(
                    {'error': 'Realizacja dla tego zamówienia już istnieje'},
                    status=400
                )

            # Utwórz realizację
            realizacja = RealizacjaZamowienia.objects.create(
                zamowienie=zamowienie
            )

            # Skopiuj pozycje zamówienia do pozycji realizacji
            for pozycja_zam in zamowienie.pozycje.all():
                PozycjaRealizacji.objects.create(
                    realizacja=realizacja,
                    pozycja_zamowienia=pozycja_zam,
                    lokalizacja=pozycja_zam.narzedzie_typ.domyslna_lokalizacja,
                    ilosc_przyjeta=0,
                    faktura_zakupu=None,
                    cena_jednostkowa=pozycja_zam.cena_jednostkowa
                )

            # Logowanie
            user_name = get_user_display_name(request.user)
            dostawca = zamowienie.dostawca.nazwa_firmy if zamowienie.dostawca else 'brak'
            app_logger.info(user_name, f"Rozpoczęto realizację zamówienia: {zamowienie.numer} ({dostawca})")

            return Response({
                'success': True,
                'message': 'Realizacja utworzona pomyślnie',
                'realizacja_id': realizacja.id
            })

        except Exception as e:
            return Response(
                {'error': str(e)},
                status=500
            )

    @action(detail=True, methods=['get'])
    def stan_realizacji(self, request, pk=None):
        """Zwraca stan realizacji zamówienia — ile zamówiono, ile przyjęto, ile pozostało."""
        zamowienie = self.get_object()
        realizacja = RealizacjaZamowienia.objects.filter(zamowienie=zamowienie).first()

        pozycje = []
        for poz_zam in zamowienie.pozycje.select_related('narzedzie_typ__domyslna_lokalizacja').all():
            ilosc_przyjeta = 0
            lokalizacja_data = None

            if realizacja:
                poz_real = PozycjaRealizacji.objects.filter(
                    realizacja=realizacja, pozycja_zamowienia=poz_zam
                ).select_related('lokalizacja').first()
                if poz_real:
                    ilosc_przyjeta = poz_real.ilosc_przyjeta or 0
                    if poz_real.lokalizacja:
                        lokalizacja_data = {
                            'id': poz_real.lokalizacja.id,
                            'szafa': poz_real.lokalizacja.szafa,
                            'polka': poz_real.lokalizacja.polka,
                            'kolumna': poz_real.lokalizacja.kolumna,
                        }

            if not lokalizacja_data and poz_zam.narzedzie_typ and poz_zam.narzedzie_typ.domyslna_lokalizacja:
                lok = poz_zam.narzedzie_typ.domyslna_lokalizacja
                lokalizacja_data = {
                    'id': lok.id,
                    'szafa': lok.szafa,
                    'polka': lok.polka,
                    'kolumna': lok.kolumna,
                }

            ilosc_pozostala = max(0, poz_zam.ilosc_zamowiona - ilosc_przyjeta)

            pozycje.append({
                'pozycja_zamowienia_id': poz_zam.id,
                'narzedzie_opis': poz_zam.narzedzie_opis,
                'numer_katalogowy': poz_zam.numer_katalogowy,
                'kategoria_nazwa': poz_zam.kategoria_nazwa,
                'jednostka': poz_zam.jednostka,
                'ilosc_w_komplecie': poz_zam.ilosc_w_komplecie,
                'ilosc_zamowiona': poz_zam.ilosc_zamowiona,
                'ilosc_przyjeta': ilosc_przyjeta,
                'ilosc_pozostala': ilosc_pozostala,
                'cena_jednostkowa': float(poz_zam.cena_jednostkowa) if poz_zam.cena_jednostkowa else 0,
                'lokalizacja': lokalizacja_data,
            })

        return Response({
            'has_realizacja': realizacja is not None,
            'realizacja_id': realizacja.id if realizacja else None,
            'pozycje': pozycje,
        })

    @action(detail=True, methods=['post'])
    def przelicz_status(self, request, pk=None):
        """Ponownie wylicza status zamówienia z aktualnego stanu pozycji i realizacji.
        Bezpieczna operacja: nie rusza pozycji, realizacji ani egzemplarzy —
        zmienia wyłącznie pole `status`. Działa tylko dla 'sent' / 'partially_received'."""
        zamowienie = self.get_object()

        if zamowienie.status not in ('sent', 'partially_received'):
            return Response({
                'success': False,
                'error': f'Przeliczenie dozwolone tylko dla zamówień w statusie "Wysłane" lub "Częściowo odebrane" (bieżący: {zamowienie.status})'
            }, status=400)

        realizacja = RealizacjaZamowienia.objects.filter(zamowienie=zamowienie).first()
        pozostale_pozycje = list(PozycjaZamowienia.objects.filter(zamowienie=zamowienie))

        if not pozostale_pozycje:
            return Response({'success': False, 'error': 'Zamówienie nie zawiera pozycji'}, status=400)

        wszystkie = True
        any_received = False
        for poz_zam in pozostale_pozycje:
            ilosc_przyjeta = 0
            if realizacja:
                poz_real = realizacja.pozycje.filter(pozycja_zamowienia=poz_zam).first()
                if poz_real:
                    ilosc_przyjeta = poz_real.ilosc_przyjeta or 0
            if ilosc_przyjeta > 0:
                any_received = True
            if ilosc_przyjeta < poz_zam.ilosc_zamowiona:
                wszystkie = False

        if wszystkie:
            new_status = 'completed'
        elif any_received:
            new_status = 'partially_received'
        else:
            new_status = 'sent'

        old_status = zamowienie.status
        if old_status == new_status:
            return Response({
                'success': True,
                'changed': False,
                'status': new_status,
                'message': f'Status nie wymaga zmiany (nadal: {new_status}).'
            })

        zamowienie.status = new_status
        zamowienie.save(update_fields=['status'])
        _propaguj_status_zapotrzebowan(zamowienie)

        user_name = get_user_display_name(request.user)
        app_logger.info(
            user_name,
            f"Przeliczono status zamówienia {zamowienie.numer}: {old_status} → {new_status}"
        )

        return Response({
            'success': True,
            'changed': True,
            'old_status': old_status,
            'status': new_status,
            'message': f'Status zaktualizowany: {old_status} → {new_status}.'
        })

    @action(detail=True, methods=['post'])
    def realizuj(self, request, pk=None):
        """Realizacja zamówienia — częściowa lub pełna. Tworzy egzemplarze w magazynie.
        Obsługuje także odpisanie pozycji (skasowanie z zamówienia) — niezrealizowane
        pozycje wracają do puli generatora."""
        from .models import PozycjaZapotrzebowania, ZapotrzebowanieTechnologa
        try:
            zamowienie = self.get_object()
            pozycje_dane = request.data.get('pozycje', [])
            pozycje_do_odpisania = request.data.get('pozycje_do_odpisania', []) or []

            if not pozycje_dane and not pozycje_do_odpisania:
                return Response({'error': 'Brak pozycji do przyjęcia lub odpisania'}, status=400)

            with transaction.atomic():
                # Utwórz lub pobierz realizację
                realizacja, created = RealizacjaZamowienia.objects.get_or_create(
                    zamowienie=zamowienie
                )

                if created:
                    for poz_zam in zamowienie.pozycje.select_related('narzedzie_typ__domyslna_lokalizacja').all():
                        lok = poz_zam.narzedzie_typ.domyslna_lokalizacja if poz_zam.narzedzie_typ else None
                        PozycjaRealizacji.objects.create(
                            realizacja=realizacja,
                            pozycja_zamowienia=poz_zam,
                            lokalizacja=lok,
                            ilosc_przyjeta=0,
                            cena_jednostkowa=poz_zam.cena_jednostkowa
                        )

                utworzone_egzemplarze = []

                for poz_data in pozycje_dane:
                    pozycja_zam_id = poz_data.get('pozycja_zamowienia_id')
                    ilosc = int(poz_data.get('ilosc_przyjeta', 0))

                    if ilosc <= 0:
                        continue

                    poz_zam = PozycjaZamowienia.objects.select_related(
                        'narzedzie_typ__domyslna_lokalizacja'
                    ).get(id=pozycja_zam_id)

                    poz_real = PozycjaRealizacji.objects.select_related('lokalizacja').get(
                        realizacja=realizacja,
                        pozycja_zamowienia=poz_zam
                    )

                    # Akumuluj ilość (nie nadpisuj)
                    poz_real.ilosc_przyjeta = (poz_real.ilosc_przyjeta or 0) + ilosc
                    poz_real.save(update_fields=['ilosc_przyjeta'])

                    # Oznacz pozycję zamówienia jako zrealizowaną jeśli pełna ilość
                    if poz_real.ilosc_przyjeta >= poz_zam.ilosc_zamowiona:
                        poz_zam.zrealizowane = True
                        poz_zam.ilosc_dostarczona = poz_real.ilosc_przyjeta
                        poz_zam.save(update_fields=['zrealizowane', 'ilosc_dostarczona'])

                    # Utwórz egzemplarze w magazynie
                    narzedzie_typ = poz_zam.narzedzie_typ
                    lokalizacja = poz_real.lokalizacja or (narzedzie_typ.domyslna_lokalizacja if narzedzie_typ else None)

                    for i in range(ilosc):
                        egz = EgzemplarzNarzedzia.objects.create(
                            narzedzie_typ=narzedzie_typ,
                            lokalizacja=lokalizacja,
                            stan='nowe',
                            jednostka=poz_zam.jednostka,
                            ilosc_w_komplecie=poz_zam.ilosc_w_komplecie,
                            zamowienie=zamowienie,
                        )

                        # Auto-generowanie oznaczenia
                        if narzedzie_typ and narzedzie_typ.opakowanie == 'szt' and not egz.oznaczenie:
                            oznaczenie = EgzemplarzService.generuj_oznaczenie(narzedzie_typ)
                            if oznaczenie:
                                egz.oznaczenie = oznaczenie
                                egz.nowy_wpis = True
                                egz.save(update_fields=['oznaczenie', 'nowy_wpis'])

                        lok_str = (
                            f"{lokalizacja.szafa}/{lokalizacja.polka}/{lokalizacja.kolumna}"
                            if lokalizacja else 'Brak'
                        )
                        utworzone_egzemplarze.append({
                            'narzedzie': narzedzie_typ.opis if narzedzie_typ else poz_zam.narzedzie_opis,
                            'lokalizacja': lok_str,
                            'ilosc': poz_zam.ilosc_w_komplecie or 1,
                        })

                # Odpisz (skasuj) wskazane pozycje — wracają do puli generatora
                odpisane_opisy = []
                zapotrzebowania_do_sprawdzenia = set()
                if pozycje_do_odpisania:
                    zrodlowe_zap_ids = list(zamowienie.zrodlowe_zapotrzebowania.values_list('id', flat=True))
                    for pz_id in pozycje_do_odpisania:
                        try:
                            poz_zam = PozycjaZamowienia.objects.select_related('narzedzie_typ').get(
                                id=pz_id, zamowienie=zamowienie
                            )
                        except PozycjaZamowienia.DoesNotExist:
                            continue

                        # Cofnij flagę w_zamowieniu na powiązanych pozycjach zapotrzebowań,
                        # żeby generator mógł je ponownie wykryć.
                        if poz_zam.narzedzie_typ and zrodlowe_zap_ids:
                            PozycjaZapotrzebowania.objects.filter(
                                zapotrzebowanie_id__in=zrodlowe_zap_ids,
                                narzedzie_typ=poz_zam.narzedzie_typ,
                                w_zamowieniu=True,
                            ).update(w_zamowieniu=False)
                            zapotrzebowania_do_sprawdzenia.update(zrodlowe_zap_ids)

                        odpisane_opisy.append(poz_zam.narzedzie_opis)
                        poz_zam.delete()

                    # Cofnij status zapotrzebowań z 'ordered' na 'completed' jeśli mają
                    # teraz pozycje oczekujące na przeniesienie do generatora.
                    for zap_id in zapotrzebowania_do_sprawdzenia:
                        zap = ZapotrzebowanieTechnologa.objects.filter(
                            id=zap_id, status='ordered'
                        ).first()
                        if zap and zap.pozycje.filter(w_zamowieniu=False, narzedzie_typ__isnull=False).exists():
                            zap.status = 'completed'
                            zap.save(update_fields=['status'])

                    # Przelicz wartość zamówienia po kasowaniu pozycji
                    from django.db.models import Sum, F
                    total = zamowienie.pozycje.aggregate(
                        suma=Sum(F('ilosc_zamowiona') * F('cena_jednostkowa'))
                    )['suma'] or 0
                    zamowienie.wartosc_zamowienia = total
                    zamowienie.save(update_fields=['wartosc_zamowienia'])

                # Sprawdź czy wszystkie pozycje w pełni zrealizowane.
                # UWAGA: NIE używamy `zamowienie.pozycje.all()` — self.get_object() ma
                # prefetch_related('pozycje'), więc ten manager zwraca cache sprzed
                # odpisywania. Idziemy bezpośrednio po PozycjaZamowienia.
                pozostale_pozycje = list(
                    PozycjaZamowienia.objects.filter(zamowienie=zamowienie)
                )
                wszystkie = True
                for poz_zam in pozostale_pozycje:
                    poz_real = realizacja.pozycje.filter(pozycja_zamowienia=poz_zam).first()
                    if not poz_real or poz_real.ilosc_przyjeta < poz_zam.ilosc_zamowiona:
                        wszystkie = False
                        break

                zamowienie.status = 'completed' if wszystkie else 'partially_received'
                zamowienie.save(update_fields=['status'])
                _propaguj_status_zapotrzebowan(zamowienie)

                # Logowanie
                user_name = get_user_display_name(request.user)
                dostawca = zamowienie.dostawca.nazwa_firmy if zamowienie.dostawca else 'brak'
                status_tekst = 'zrealizowane w całości' if wszystkie else 'częściowo zrealizowane'
                app_logger.success(
                    user_name,
                    f"Przyjęto {len(utworzone_egzemplarze)} szt. z zamówienia "
                    f"{zamowienie.numer} ({dostawca}) - {status_tekst}"
                )
                if odpisane_opisy:
                    app_logger.warning(
                        user_name,
                        f"Odpisano {len(odpisane_opisy)} pozycji z zamówienia "
                        f"{zamowienie.numer} ({dostawca}): {', '.join(odpisane_opisy)}"
                    )

            msg = f'Przyjęto {len(utworzone_egzemplarze)} pozycji do magazynu'
            if odpisane_opisy:
                msg += f'. Odpisano {len(odpisane_opisy)} pozycji (wrócą do generatora).'

            return Response({
                'success': True,
                'message': msg,
                'utworzone_egzemplarze': utworzone_egzemplarze,
                'odpisane_count': len(odpisane_opisy),
                'status_zamowienia': zamowienie.status,
            })

        except Exception as e:
            return Response({'error': str(e)}, status=500)


class PozycjaZamowieniaViewSet(LoggingMixin, viewsets.ModelViewSet):
    queryset = PozycjaZamowienia.objects.select_related(
        'zamowienie',
        'narzedzie_typ__podkategoria__kategoria'
    ).all()
    serializer_class = PozycjaZamowieniaSerializer
    log_name = 'pozycję zamówienia'

    def get_log_description(self, instance):
        return f"{instance.narzedzie_opis} (zam. {instance.zamowienie.numer})"

    def get_queryset(self):
        queryset = super().get_queryset()
        zamowienie_id = self.request.query_params.get('zamowienie_id', None)
        if zamowienie_id:
            queryset = queryset.filter(zamowienie_id=zamowienie_id)
        return queryset

    def _przelicz_wartosc_zamowienia(self, zamowienie):
        from django.db.models import Sum, F
        total = zamowienie.pozycje.aggregate(
            suma=Sum(F('ilosc_zamowiona') * F('cena_jednostkowa'))
        )['suma'] or 0
        zamowienie.wartosc_zamowienia = total
        zamowienie.save(update_fields=['wartosc_zamowienia'])

    def perform_update(self, serializer):
        instance = serializer.save()
        instance.wartosc_pozycji = instance.ilosc_zamowiona * (instance.cena_jednostkowa or 0)
        instance.save(update_fields=['wartosc_pozycji'])
        self._przelicz_wartosc_zamowienia(instance.zamowienie)
        user_name = get_user_display_name(self.request.user)
        app_logger.info(
            user_name,
            f"Edytowano pozycję zamówienia {instance.zamowienie.numer}: "
            f"{instance.narzedzie_opis} (ilość: {instance.ilosc_zamowiona}, cena: {instance.cena_jednostkowa})"
        )

    def perform_destroy(self, instance):
        zamowienie = instance.zamowienie
        super().perform_destroy(instance)  # LoggingMixin loguje usunięcie
        self._przelicz_wartosc_zamowienia(zamowienie)


class RealizacjaZamowieniaViewSet(LoggingMixin, viewsets.ModelViewSet):
    queryset = RealizacjaZamowienia.objects.select_related(
        'zamowienie__dostawca',
        'lokalizacja_domyslna'
    ).prefetch_related('pozycje').all()
    serializer_class = RealizacjaZamowieniaSerializer
    log_name = 'realizację zamówienia'

    def get_log_description(self, instance):
        return f"zam. {instance.zamowienie.numer}"

    @action(detail=True, methods=['post'])
    def zatwierdz(self, request, pk=None):
        """Tworzy egzemplarze, loguje, aktualizuje status"""
        from .models import EgzemplarzNarzedzia, HistoriaUzyciaNarzedzia
        from decimal import Decimal

        try:
            realizacja = self.get_object()
            pozycje_dane = request.data.get('pozycje', [])

            if not pozycje_dane:
                return Response(
                    {'error': 'Brak danych pozycji do przyjęcia'},
                    status=400
                )

            utworzone_egzemplarze = []

            with transaction.atomic():
                for poz_data in pozycje_dane:
                    pozycja_id = poz_data.get('id')
                    ilosc_przyjeta = int(poz_data.get('ilosc_przyjeta', 0))

                    if ilosc_przyjeta <= 0:
                        continue

                    pozycja = PozycjaRealizacji.objects.get(id=pozycja_id)
                    pozycja.ilosc_przyjeta = ilosc_przyjeta
                    pozycja.save()

                    # Utwórz egzemplarze
                    narzedzie_typ = pozycja.pozycja_zamowienia.narzedzie_typ
                    lokalizacja = pozycja.lokalizacja or narzedzie_typ.domyslna_lokalizacja

                    for i in range(ilosc_przyjeta):
                        egzemplarz = EgzemplarzNarzedzia.objects.create(
                            narzedzie_typ=narzedzie_typ,
                            lokalizacja=lokalizacja,
                            stan='nowe',
                            jednostka=pozycja.pozycja_zamowienia.jednostka,
                            ilosc_w_komplecie=pozycja.pozycja_zamowienia.ilosc_w_komplecie,
                            faktura_zakupu=pozycja.faktura_zakupu
                        )

                        # Auto-generowanie oznaczenia dla narzędzi kupowanych na sztuki
                        if narzedzie_typ.opakowanie == 'szt' and not egzemplarz.oznaczenie:
                            oznaczenie = EgzemplarzService.generuj_oznaczenie(narzedzie_typ)
                            if oznaczenie:
                                egzemplarz.oznaczenie = oznaczenie
                                egzemplarz.nowy_wpis = True
                                egzemplarz.save(update_fields=['oznaczenie', 'nowy_wpis'])

                        utworzone_egzemplarze.append({
                            'narzedzie': narzedzie_typ.opis,
                            'lokalizacja': f"{lokalizacja.szafa}/{lokalizacja.polka}/{lokalizacja.kolumna}" if lokalizacja else 'Brak',
                            'ilosc': egzemplarz.ilosc_w_komplecie
                        })

                # Sprawdź czy wszystkie pozycje zrealizowane
                zamowienie = realizacja.zamowienie
                wszystkie_zrealizowane = True

                for poz_zam in zamowienie.pozycje.all():
                    poz_real = realizacja.pozycje.filter(pozycja_zamowienia=poz_zam).first()
                    if not poz_real or poz_real.ilosc_przyjeta < poz_zam.ilosc_zamowiona:
                        wszystkie_zrealizowane = False
                        break

                # Aktualizuj status zamówienia
                if wszystkie_zrealizowane:
                    zamowienie.status = 'completed'
                else:
                    zamowienie.status = 'partially_received'
                zamowienie.save()
                _propaguj_status_zapotrzebowan(zamowienie)

                # Logowanie
                user_name = get_user_display_name(request.user)
                ilosc_przyjeta = len(utworzone_egzemplarze)
                dostawca = zamowienie.dostawca.nazwa_firmy if zamowienie.dostawca else 'brak'
                status_tekst = 'zrealizowane w całości' if wszystkie_zrealizowane else 'częściowo zrealizowane'
                app_logger.success(user_name, f"Przyjęto {ilosc_przyjeta} szt. z zamówienia {zamowienie.numer} ({dostawca}) - {status_tekst}")

            return Response({
                'success': True,
                'message': 'Przyjęcie zatwierdzone',
                'utworzone_egzemplarze': utworzone_egzemplarze,
                'status_zamowienia': zamowienie.status
            })

        except Exception as e:
            return Response(
                {'error': str(e)},
                status=500
            )


class PozycjaRealizacjiViewSet(LoggingMixin, viewsets.ModelViewSet):
    queryset = PozycjaRealizacji.objects.select_related(
        'realizacja',
        'pozycja_zamowienia__narzedzie_typ',
        'lokalizacja'
    ).all()
    serializer_class = PozycjaRealizacjiSerializer
    log_name = 'pozycję realizacji'

    def get_queryset(self):
        queryset = super().get_queryset()
        realizacja_id = self.request.query_params.get('realizacja_id', None)
        if realizacja_id:
            queryset = queryset.filter(realizacja_id=realizacja_id)
        return queryset


class ZapotrzebowanieTechnologaViewSet(LoggingMixin, viewsets.ModelViewSet):
    """
    ViewSet dla zapotrzebowań technologów.
    Zawiera akcje customowe: moj_koszyk, wyslij, pdf.
    """
    queryset = ZapotrzebowanieTechnologa.objects.select_related('technolog').prefetch_related('pozycje').all()
    serializer_class = ZapotrzebowanieTechnologaSerializer
    log_name = 'zapotrzebowanie'

    def get_log_description(self, instance):
        technolog = f"{instance.technolog.first_name} {instance.technolog.last_name}" if instance.technolog else 'nieznany'
        return f"ID: {instance.id} ({technolog})"

    def get_queryset(self):
        """Filtrowanie - technolog widzi swoje, magazynier/logistyk/kierownik widzi wysłane i zatwierdzone + własne (drafty)"""
        queryset = super().get_queryset()
        if self.request.user.is_authenticated and not self.request.user.is_superuser:
            magazyn_groups = {'magazyn', 'logistyka', 'kierownik', 'administrator'}
            user_groups = set(self.request.user.groups.values_list('name', flat=True))
            if user_groups & magazyn_groups:
                queryset = queryset.filter(
                    Q(status__in=['submitted', 'completed', 'ordered']) | Q(technolog=self.request.user)
                )
            else:
                queryset = queryset.filter(technolog=self.request.user)
        return queryset.order_by('-data_utworzenia')

    def perform_create(self, serializer):
        """Automatycznie przypisz technologa przy tworzeniu"""
        instance = serializer.save(technolog=self.request.user)
        user_name = get_user_display_name(self.request.user)
        app_logger.success(
            user_name,
            f"Utworzono zapotrzebowanie ZAM-{instance.id:04d} (status: {instance.status})"
        )

    @action(detail=False, methods=['get'])
    def moj_koszyk(self, request):
        """
        Zwraca aktywny koszyk (draft) użytkownika lub tworzy nowy.
        """
        koszyk = ZapotrzebowanieTechnologa.objects.filter(
            technolog=request.user,
            status='draft'
        ).first()

        if not koszyk:
            koszyk = ZapotrzebowanieTechnologa.objects.create(
                technolog=request.user,
                status='draft'
            )

        serializer = self.get_serializer(koszyk)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def wyslij(self, request, pk=None):
        """
        Zmienia status na 'submitted', ustawia datę wysłania.
        """
        zapotrzebowanie = self.get_object()

        if zapotrzebowanie.status != 'draft':
            return Response(
                {'error': 'Tylko zapotrzebowanie w statusie roboczym może być wysłane'},
                status=status.HTTP_400_BAD_REQUEST
            )

        if not zapotrzebowanie.pozycje.exists():
            return Response(
                {'error': 'Nie można wysłać pustego zapotrzebowania'},
                status=status.HTTP_400_BAD_REQUEST
            )

        zapotrzebowanie.status = 'submitted'
        zapotrzebowanie.data_wyslania = timezone.now()
        zapotrzebowanie.save()

        # Logowanie
        user_name = get_user_display_name(request.user)
        ilosc_pozycji = zapotrzebowanie.pozycje.count()
        app_logger.success(user_name, f"Wysłano zapotrzebowanie (ID: {zapotrzebowanie.id}, {ilosc_pozycji} pozycji)")

        serializer = self.get_serializer(zapotrzebowanie)
        return Response({
            'success': True,
            'message': 'Zapotrzebowanie zostało wysłane',
            'data': serializer.data
        })

    @action(detail=False, methods=['get'])
    def historia(self, request):
        """
        Zwraca historię zapotrzebowań (nie-draft) z ostatnich 6 miesięcy.
        Parametry:
        - all=true: pokaż zapotrzebowania wszystkich technologów
        - all=false (domyślnie): tylko własne zapotrzebowania
        """
        from datetime import timedelta

        # Sprawdź czy użytkownik jest zalogowany
        if not request.user.is_authenticated:
            return Response([])

        # Oblicz datę 6 miesięcy wstecz
        data_od = timezone.now() - timedelta(days=180)

        # Bazowe zapytanie - tylko nie-draft i z ostatnich 6 miesięcy
        queryset = ZapotrzebowanieTechnologa.objects.exclude(
            status='draft'
        ).filter(
            data_utworzenia__gte=data_od
        ).select_related('technolog').prefetch_related('pozycje')

        # Filtrowanie - własne lub wszystkie
        show_all = request.query_params.get('all', 'false').lower() == 'true'
        if not show_all:
            queryset = queryset.filter(technolog=request.user)

        # Sortowanie od najnowszych
        queryset = queryset.order_by('-data_wyslania', '-data_utworzenia')

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def lista_dla_magazynu(self, request):
        """
        Zwraca wysłane i zatwierdzone zapotrzebowania dla magazyniera.
        Sortowanie od najnowszych.
        """
        zapotrzebowania = ZapotrzebowanieTechnologa.objects.filter(
            status__in=['submitted', 'completed', 'ordered']
        ).select_related('technolog', 'zrealizowany_przez').prefetch_related('pozycje').order_by('-data_wyslania')

        serializer = self.get_serializer(zapotrzebowania, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def zrealizuj(self, request, pk=None):
        """
        Zatwierdza zapotrzebowanie — zmienia status na 'completed'.
        Pozycje będą widoczne dla generatora zamówień.
        """
        zapotrzebowanie = self.get_object()

        if zapotrzebowanie.status != 'submitted':
            return Response(
                {'error': 'Tylko wysłane zapotrzebowanie może być zatwierdzone'},
                status=status.HTTP_400_BAD_REQUEST
            )

        zapotrzebowanie.status = 'completed'
        zapotrzebowanie.data_realizacji = timezone.now()
        if request.user.is_authenticated:
            zapotrzebowanie.zrealizowany_przez = request.user
        zapotrzebowanie.save()

        # Logowanie
        user_name = get_user_display_name(request.user)
        technolog = f"{zapotrzebowanie.technolog.first_name} {zapotrzebowanie.technolog.last_name}" if zapotrzebowanie.technolog else 'nieznany'
        pozycje_count = zapotrzebowanie.pozycje.count()
        app_logger.success(user_name, f"Zatwierdzono zapotrzebowanie ZAM-{zapotrzebowanie.id:04d} od: {technolog} ({pozycje_count} poz.)")

        serializer = self.get_serializer(zapotrzebowanie)
        return Response({
            'success': True,
            'message': f'Zapotrzebowanie zatwierdzone ({pozycje_count} pozycji gotowych do zamówienia).',
            'data': serializer.data
        })

    @action(detail=True, methods=['post'])
    def cofnij(self, request, pk=None):
        """
        Cofa zatwierdzenie — zmienia status z 'completed' z powrotem na 'submitted'.
        """
        zapotrzebowanie = self.get_object()

        if zapotrzebowanie.status not in ('completed', 'ordered'):
            return Response(
                {'error': 'Tylko zatwierdzone lub zamówione zapotrzebowanie może być cofnięte'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Resetuj flagę w_zamowieniu na pozycjach
        if zapotrzebowanie.status == 'ordered':
            zapotrzebowanie.pozycje.filter(w_zamowieniu=True).update(w_zamowieniu=False)

        zapotrzebowanie.status = 'submitted'
        zapotrzebowanie.data_realizacji = None
        zapotrzebowanie.zrealizowany_przez = None
        zapotrzebowanie.save()

        # Logowanie
        user_name = get_user_display_name(request.user)
        app_logger.warning(user_name, f"Cofnięto zatwierdzenie zapotrzebowania ZAM-{zapotrzebowanie.id:04d}")

        serializer = self.get_serializer(zapotrzebowanie)
        return Response({
            'success': True,
            'message': 'Zatwierdzenie zapotrzebowania zostało cofnięte.',
            'data': serializer.data
        })

    @action(detail=True, methods=['get'])
    def pdf(self, request, pk=None):
        """
        Generuje PDF z pozycjami zapotrzebowania (WeasyPrint + HTML template).
        """
        import os
        from datetime import datetime
        from django.http import HttpResponse
        from django.template.loader import render_to_string
        from django.conf import settings
        from weasyprint import HTML

        zapotrzebowanie = self.get_object()

        # Dane do szablonu
        technolog_nazwa = f"{zapotrzebowanie.technolog.first_name} {zapotrzebowanie.technolog.last_name}" if zapotrzebowanie.technolog else "Nieznany"
        numer = f"ZAM-{zapotrzebowanie.id:04d}"

        # Pobierz grupę użytkownika (dział)
        dzial = "---"
        if zapotrzebowanie.technolog:
            groups = zapotrzebowanie.technolog.groups.all()
            if groups.exists():
                dzial = groups.first().name

        # Mapowanie statusów na polskie nazwy
        status_display = {
            'draft': 'Robocze',
            'submitted': 'Wysłane',
            'completed': 'Zrealizowane',
            'cancelled': 'Anulowane',
        }.get(zapotrzebowanie.status, zapotrzebowanie.status)

        # Ścieżka do logo (absolutna dla WeasyPrint)
        logo_path = os.path.join(settings.BASE_DIR, 'static_dev', 'images', 'logo-cnc.png')

        context = {
            'numer': numer,
            'data_utworzenia': zapotrzebowanie.data_utworzenia.strftime('%Y-%m-%d'),
            'data_wydruku': getattr(settings, 'PDF_ZAPOTRZEBOWANIE_DATA', ''),
            'wersja_dokumentu': getattr(settings, 'PDF_ZAPOTRZEBOWANIE_WERSJA', 1),
            'technolog': technolog_nazwa,
            'dzial': dzial,
            'status': status_display,
            'uwagi': zapotrzebowanie.uwagi,
            'pozycje': zapotrzebowanie.pozycje.all(),
            'logo_path': f'file://{logo_path}',
        }

        # Renderowanie HTML
        html_string = render_to_string('pdf/zapotrzebowanie.html', context)

        # Generowanie PDF
        pdf_file = HTML(string=html_string, base_url=str(settings.BASE_DIR)).write_pdf()

        response = HttpResponse(pdf_file, content_type='application/pdf')
        response['Content-Disposition'] = f'inline; filename="{numer}.pdf"'
        return response


class PozycjaZapotrzebowaniaViewSet(LoggingMixin, viewsets.ModelViewSet):
    """
    ViewSet dla pozycji zapotrzebowań.
    CRUD dla pozycji koszyka.
    """
    queryset = PozycjaZapotrzebowania.objects.select_related(
        'zapotrzebowanie',
        'narzedzie_typ__podkategoria__kategoria'
    ).all()
    serializer_class = PozycjaZapotrzebowaniaSerializer
    log_name = 'pozycję koszyka'

    def get_log_description(self, instance):
        return instance.specyfikacja or str(instance.id)

    def get_queryset(self):
        """Filtrowanie pozycji zapotrzebowań.
        Technolog widzi tylko swoje, magazynier/logistyk widzi wysłane + własne (drafty)."""
        queryset = super().get_queryset()
        user = self.request.user

        if not user.is_superuser:
            user_groups = set(user.groups.values_list('name', flat=True))
            magazyn_groups = {'magazyn', 'logistyka', 'kierownik', 'administrator'}
            if user_groups & magazyn_groups:
                queryset = queryset.filter(
                    Q(zapotrzebowanie__status='submitted') | Q(zapotrzebowanie__technolog=user)
                )
            else:
                queryset = queryset.filter(zapotrzebowanie__technolog=user)

        zapotrzebowanie_id = self.request.query_params.get('zapotrzebowanie_id', None)
        if zapotrzebowanie_id:
            queryset = queryset.filter(zapotrzebowanie_id=zapotrzebowanie_id)

        return queryset.order_by('data_dodania')

    def perform_create(self, serializer):
        """
        Przy tworzeniu pozycji automatycznie wypełnia snapshot danych
        jeśli podano narzedzie_typ.
        """
        narzedzie_typ = serializer.validated_data.get('narzedzie_typ')
        extra_data = {}

        if narzedzie_typ:
            extra_data['specyfikacja'] = narzedzie_typ.opis
            extra_data['numer_katalogowy'] = narzedzie_typ.numer_katalogowy or ''
            if narzedzie_typ.podkategoria:
                extra_data['kategoria_nazwa'] = narzedzie_typ.podkategoria.kategoria.nazwa
                extra_data['podkategoria_nazwa'] = narzedzie_typ.podkategoria.nazwa

        instance = serializer.save(**extra_data)
        # Logowanie
        user_name = get_user_display_name(self.request.user)
        app_logger.success(user_name, f"Dodano {self.log_name}: {self.get_log_description(instance)}")


# ========== LOGI API ==========

from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.contrib.admin.views.decorators import staff_member_required


@login_required
@require_http_methods(["GET"])
def logi_biezace_view(request):
    """
    Zwraca logi z dzisiaj.
    Dostępne tylko dla administratorów.
    """
    if not request.user.groups.filter(name='administrator').exists():
        return JsonResponse({'error': 'Brak uprawnień'}, status=403)

    logs = app_logger.get_recent_logs()
    return JsonResponse(logs, safe=False)


@login_required
@require_http_methods(["GET"])
def logi_pliki_view(request):
    """
    Zwraca listę plików logów archiwalnych.
    Dostępne tylko dla administratorów.
    """
    if not request.user.groups.filter(name='administrator').exists():
        return JsonResponse({'error': 'Brak uprawnień'}, status=403)

    files = app_logger.get_log_files()
    return JsonResponse(files, safe=False)


@login_required
@require_http_methods(["GET"])
def logi_plik_content_view(request, filename):
    """
    Zwraca zawartość konkretnego pliku logu jako listę logów.
    Dostępne tylko dla administratorów.
    """
    if not request.user.groups.filter(name='administrator').exists():
        return JsonResponse({'error': 'Brak uprawnień'}, status=403)

    logs = app_logger.get_file_content(filename)
    return JsonResponse(logs, safe=False)


@login_required
@require_http_methods(["GET"])
def logi_pdf_biezace_view(request):
    """
    Generuje PDF z logami bieżącymi (dzisiejszymi).
    Dostępne tylko dla administratorów.
    """
    import os
    from datetime import datetime
    from django.http import HttpResponse
    from django.template.loader import render_to_string
    from django.conf import settings
    from weasyprint import HTML

    if not request.user.groups.filter(name='administrator').exists():
        return JsonResponse({'error': 'Brak uprawnień'}, status=403)

    # Parametr filtra statusu
    status_filter = request.GET.get('status', None)

    # Pobierz logi
    logs = app_logger.get_recent_logs()

    # Filtrowanie po statusie
    if status_filter:
        logs = [log for log in logs if log['status'] == status_filter]

    # Przygotuj dane do szablonu
    today = datetime.now().strftime('%Y-%m-%d')
    logo_path = os.path.join(settings.BASE_DIR, 'static_dev', 'images', 'logo-cnc.png')

    # Przekształć logi do formatu dla szablonu
    logi_formatted = []
    for log in logs:
        timestamp = datetime.fromisoformat(log['timestamp'].replace('+00:00', ''))
        logi_formatted.append({
            'data': timestamp.strftime('%Y-%m-%d'),
            'godzina': timestamp.strftime('%H:%M:%S'),
            'status': log['status'],
            'osoba': log['osoba'],
            'operacja': log['operacja']
        })

    context = {
        'typ_logow': 'Bieżące',
        'data_logu': today,
        'filtr_statusu': status_filter or 'Wszystkie',
        'logi': logi_formatted,
        'data_wydruku': getattr(settings, 'PDF_LOGI_DATA', datetime.now().strftime('%Y-%m-%d')),
        'wersja_dokumentu': getattr(settings, 'PDF_LOGI_WERSJA', 1),
        'logo_path': f'file://{logo_path}',
    }

    # Renderowanie HTML
    html_string = render_to_string('pdf/logi.html', context)

    # Generowanie PDF
    pdf_file = HTML(string=html_string, base_url=str(settings.BASE_DIR)).write_pdf()

    response = HttpResponse(pdf_file, content_type='application/pdf')
    filename = f'logi_biezace_{today}.pdf'
    response['Content-Disposition'] = f'inline; filename="{filename}"'
    return response


@login_required
@require_http_methods(["GET"])
def logi_pdf_archiwum_view(request, filename):
    """
    Generuje PDF z logami z pliku archiwalnego.
    Dostępne tylko dla administratorów.
    """
    import os
    from datetime import datetime
    from django.http import HttpResponse
    from django.template.loader import render_to_string
    from django.conf import settings
    from weasyprint import HTML

    if not request.user.groups.filter(name='administrator').exists():
        return JsonResponse({'error': 'Brak uprawnień'}, status=403)

    # Parametr filtra statusu
    status_filter = request.GET.get('status', None)

    # Pobierz logi z pliku
    logs = app_logger.get_file_content(filename)

    # Filtrowanie po statusie
    if status_filter:
        logs = [log for log in logs if log['status'] == status_filter]

    # Przygotuj dane do szablonu
    data_logu = filename.replace('.log', '')
    logo_path = os.path.join(settings.BASE_DIR, 'static_dev', 'images', 'logo-cnc.png')

    # Przekształć logi do formatu dla szablonu
    logi_formatted = []
    for log in logs:
        try:
            timestamp = datetime.fromisoformat(log['timestamp'].replace('+00:00', ''))
            logi_formatted.append({
                'data': timestamp.strftime('%Y-%m-%d'),
                'godzina': timestamp.strftime('%H:%M:%S'),
                'status': log['status'],
                'osoba': log['osoba'],
                'operacja': log['operacja']
            })
        except (ValueError, KeyError):
            continue

    context = {
        'typ_logow': 'Archiwum',
        'data_logu': data_logu,
        'filtr_statusu': status_filter or 'Wszystkie',
        'logi': logi_formatted,
        'data_wydruku': getattr(settings, 'PDF_LOGI_DATA', datetime.now().strftime('%Y-%m-%d')),
        'wersja_dokumentu': getattr(settings, 'PDF_LOGI_WERSJA', 1),
        'logo_path': f'file://{logo_path}',
    }

    # Renderowanie HTML
    html_string = render_to_string('pdf/logi.html', context)

    # Generowanie PDF
    pdf_file = HTML(string=html_string, base_url=str(settings.BASE_DIR)).write_pdf()

    response = HttpResponse(pdf_file, content_type='application/pdf')
    pdf_filename = f'logi_{data_logu}.pdf'
    response['Content-Disposition'] = f'inline; filename="{pdf_filename}"'
    return response


# ========== WZORY DOKUMENTÓW (puste szablony do ISO) ==========

@login_required
@require_http_methods(["GET"])
def dokument_wzor_view(request, typ):
    """
    Generuje pusty wzór dokumentu PDF dla dokumentacji ISO.
    Dostępne typy: zapotrzebowanie, uszkodzenie, logi
    """
    import os
    from django.http import HttpResponse
    from django.template.loader import render_to_string
    from weasyprint import HTML

    logo_path = os.path.join(settings.BASE_DIR, 'static_dev', 'images', 'logo-cnc.png')

    is_print = request.GET.get('print') == '1'

    if typ == 'zapotrzebowanie':
        if is_print:
            pozycje = [{'nr_klienta': '', 'nr_zlecenia': '', 'kategoria_nazwa': '', 'podkategoria_nazwa': '',
                        'specyfikacja': '', 'numer_katalogowy': '', 'ilosc': '', 'uwagi': '', 'lp': i}
                       for i in range(1, 21)]
        else:
            pozycje = [
                {'nr_klienta': '', 'nr_zlecenia': '', 'kategoria_nazwa': '', 'podkategoria_nazwa': '',
                 'specyfikacja': '', 'numer_katalogowy': '', 'ilosc': '', 'uwagi': ''},
            ]
        context = {
            'numer': 'ZAM-XXXX',
            'data_utworzenia': 'RRRR-MM-DD',
            'data_wydruku': getattr(settings, 'PDF_ZAPOTRZEBOWANIE_DATA', ''),
            'wersja_dokumentu': getattr(settings, 'PDF_ZAPOTRZEBOWANIE_WERSJA', 1),
            'technolog': '..................',
            'dzial': '..................',
            'status': 'WZÓR',
            'uwagi': '',
            'pozycje': pozycje,
            'logo_path': f'file://{logo_path}',
            'is_print': is_print,
        }
        template = 'pdf/zapotrzebowanie.html'
        filename = 'Wzor_Karta_zapotrzebowania.pdf'

    elif typ == 'uszkodzenie':
        context = {
            'numer_karty': 'RRRR/XXX',
            'data_uszkodzenia': 'RRRR-MM-DD GG-MM',
            'maszyna': '..................',
            'zglaszajacy': '..................',
            'kategoria': '..................',
            'narzedzie': '..................',
            'numer_katalogowy': '..................',
            'przyczyna': '',
            'stracony_czas': '',
            'uwagi': '',
            'logo_path': f'file://{logo_path}',
            'data_wydruku': getattr(settings, 'PDF_USZKODZENIE_DATA', ''),
            'wersja_dokumentu': getattr(settings, 'PDF_USZKODZENIE_WERSJA', 1),
            'is_print': is_print,
        }
        template = 'pdf/karta_uszkodzenia.html'
        filename = 'Wzor_Karta_uszkodzenia.pdf'

    elif typ == 'logi':
        context = {
            'typ_logow': 'WZÓR',
            'data_logu': 'RRRR-MM-DD',
            'filtr_statusu': 'Wszystkie',
            'logi': [
                {'timestamp': 'RRRR-MM-DD HH:MM:SS', 'status': 'INFO', 'osoba': '...............', 'operacja': '...............'},
                {'timestamp': 'RRRR-MM-DD HH:MM:SS', 'status': 'SUCCESS', 'osoba': '...............', 'operacja': '...............'},
                {'timestamp': 'RRRR-MM-DD HH:MM:SS', 'status': 'WARNING', 'osoba': '...............', 'operacja': '...............'},
                {'timestamp': 'RRRR-MM-DD HH:MM:SS', 'status': 'ERROR', 'osoba': '...............', 'operacja': '...............'},
            ],
            'data_wydruku': getattr(settings, 'PDF_LOGI_DATA', ''),
            'wersja_dokumentu': getattr(settings, 'PDF_LOGI_WERSJA', 1),
            'logo_path': f'file://{logo_path}',
        }
        template = 'pdf/logi.html'
        filename = 'Wzor_Raport_logow.pdf'

    elif typ == 'lista_uszkodzen':
        if is_print:
            uszkodzenia = [{'numer_karty': '', 'data_uszkodzenia': '', 'maszyna': '',
                            'zglaszajacy': '', 'kategoria': '', 'narzedzie': '',
                            'przyczyna': '', 'stracony_czas': ''} for _ in range(20)]
        else:
            uszkodzenia = [
                {'numer_karty': 'RRRR/XXX', 'data_uszkodzenia': 'RRRR-MM-DD', 'maszyna': '........',
                 'zglaszajacy': '............', 'kategoria': '........', 'narzedzie': '............',
                 'przyczyna': '...............', 'stracony_czas': '...'},
            ]
        context = {
            'data_wydruku': getattr(settings, 'PDF_LISTA_USZKODZEN_DATA', ''),
            'wersja_dokumentu': getattr(settings, 'PDF_LISTA_USZKODZEN_WERSJA', 1),
            'liczba': 'X',
            'uszkodzenia': uszkodzenia,
            'logo_path': f'file://{logo_path}',
            'is_print': is_print,
        }
        template = 'pdf/lista_uszkodzen.html'
        filename = 'Wzor_Lista_uszkodzen.pdf'

    elif typ == 'inwentura':
        context = {
            'data_wydruku': getattr(settings, 'PDF_INWENTURA_DATA', ''),
            'godzina_wydruku': 'GG:MM',
            'wersja_dokumentu': getattr(settings, 'PDF_INWENTURA_WERSJA', 1),
            'liczba_pozycji': 'X',
            'narzedzia': [
                {'lp': '1', 'kategoria': '..................', 'opis': '..................',
                 'numer_katalogowy': '..................', 'lokalizacja': '........', 'razem': '...'},
                {'lp': '2', 'kategoria': '..................', 'opis': '..................',
                 'numer_katalogowy': '..................', 'lokalizacja': '........', 'razem': '...'},
                {'lp': '3', 'kategoria': '..................', 'opis': '..................',
                 'numer_katalogowy': '..................', 'lokalizacja': '........', 'razem': '...'},
            ],
            'logo_path': f'file://{logo_path}',
        }
        template = 'pdf/inwentura.html'
        filename = 'Wzor_Inwentura_startowa.pdf'

    else:
        return HttpResponse('Nieznany typ dokumentu', status=400)

    # Renderowanie HTML
    html_string = render_to_string(template, context)

    # Generowanie PDF
    pdf_file = HTML(string=html_string, base_url=str(settings.BASE_DIR)).write_pdf()

    response = HttpResponse(pdf_file, content_type='application/pdf')
    response['Content-Disposition'] = f'inline; filename="{filename}"'
    return response


# ========== EKSPORT INWENTURY ==========

@login_required
def inwentura_pdf_view(request):
    """
    Generuje PDF ze stanem magazynowym do przeprowadzenia inwentury.
    Zawiera wszystkie narzędzia z ilościami i lokalizacjami.
    """
    import os
    from django.http import HttpResponse
    from django.template.loader import render_to_string
    from weasyprint import HTML

    logo_path = os.path.join(settings.BASE_DIR, 'static_dev', 'images', 'logo-cnc.png')
    today = datetime.now()

    # Pobierz wszystkie typy narzędzi z egzemplarzami
    narzedzia = NarzedzieMagazynowe.objects.prefetch_related(
        'egzemplarze__lokalizacja',
        'podkategoria__kategoria'
    ).order_by('podkategoria__kategoria__nazwa', 'podkategoria__nazwa', 'opis')

    # Przygotuj dane do inwentury
    inwentura_data = []
    lp = 0

    for narzedzie in narzedzia:
        # Grupuj egzemplarze po lokalizacji i stanie
        egzemplarze = narzedzie.egzemplarze.filter(
            stan__in=['nowe', 'uzywane']
        ).order_by('lokalizacja__szafa', 'lokalizacja__polka', 'lokalizacja__kolumna', 'stan')

        # Sprawdź też ile jest w użyciu
        w_uzyciu = HistoriaUzyciaNarzedzia.objects.filter(
            egzemplarz__narzedzie_typ=narzedzie,
            data_zwrotu__isnull=True
        ).count()

        # Zlicz egzemplarze wg stanu
        nowe_count = egzemplarze.filter(stan='nowe').count()
        uzywane_count = egzemplarze.filter(stan='uzywane').count()
        razem = nowe_count + uzywane_count + w_uzyciu

        if razem == 0:
            continue  # Pomiń narzędzia bez egzemplarzy

        lp += 1

        # Kategoria/Podkategoria
        if narzedzie.podkategoria:
            kategoria = f"{narzedzie.podkategoria.kategoria.nazwa} / {narzedzie.podkategoria.nazwa}"
        else:
            kategoria = "Brak kategorii"

        # Lokalizacje (unikalne)
        lokalizacje = set()
        for egz in egzemplarze:
            if egz.lokalizacja:
                lokalizacje.add(f"{egz.lokalizacja.szafa}/{egz.lokalizacja.polka}/{egz.lokalizacja.kolumna}")

        inwentura_data.append({
            'lp': lp,
            'kategoria': kategoria,
            'opis': narzedzie.opis,
            'numer_katalogowy': narzedzie.numer_katalogowy or '-',
            'lokalizacja': ', '.join(sorted(lokalizacje)) if lokalizacje else '-',
            'razem': razem,
        })

    context = {
        'data_wydruku': today.strftime('%Y-%m-%d'),
        'godzina_wydruku': today.strftime('%H:%M'),
        'narzedzia': inwentura_data,
        'liczba_pozycji': len(inwentura_data),
        'logo_path': f'file://{logo_path}',
        'wersja_dokumentu': getattr(settings, 'PDF_INWENTURA_WERSJA', 1),
    }

    html_string = render_to_string('pdf/inwentura.html', context)
    pdf_file = HTML(string=html_string, base_url=str(settings.BASE_DIR)).write_pdf()

    filename = f'Inwentura_{today.strftime("%Y-%m-%d")}.pdf'
    response = HttpResponse(pdf_file, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    return response


@login_required
def inwentura_xls_view(request):
    """
    Generuje plik Excel ze stanem magazynowym do przeprowadzenia inwentury.
    Profesjonalny styl, gotowy do wydruku A4 landscape.
    """
    from django.http import HttpResponse
    import openpyxl
    from openpyxl.styles import Font, Alignment, Border, Side, PatternFill
    from openpyxl.utils import get_column_letter

    today = datetime.now()

    # Utwórz nowy workbook
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Inwentura"

    # Ustawienia strony - A4 landscape
    ws.page_setup.orientation = 'landscape'
    ws.page_setup.paperSize = ws.PAPERSIZE_A4
    ws.page_setup.fitToPage = True
    ws.page_setup.fitToWidth = 1
    ws.page_setup.fitToHeight = 0
    ws.print_options.horizontalCentered = True
    ws.page_margins.left = 0.4
    ws.page_margins.right = 0.4
    ws.page_margins.top = 0.5
    ws.page_margins.bottom = 0.5

    # Style - zielony motyw (spójny z PDF)
    green_color = "198754"
    green_light = "d4edda"
    title_font = Font(bold=True, size=14, color="FFFFFF")
    title_fill = PatternFill(start_color=green_color, end_color=green_color, fill_type="solid")
    header_font = Font(bold=True, size=10, color="FFFFFF")
    header_fill = PatternFill(start_color=green_color, end_color=green_color, fill_type="solid")
    info_fill = PatternFill(start_color=green_light, end_color=green_light, fill_type="solid")
    info_font = Font(size=10, italic=True, color="155724")
    data_font = Font(size=9)
    data_font_bold = Font(size=9, bold=True)
    alt_fill = PatternFill(start_color="f8f9fa", end_color="f8f9fa", fill_type="solid")
    thin_border = Border(
        left=Side(style='thin', color='dee2e6'),
        right=Side(style='thin', color='dee2e6'),
        top=Side(style='thin', color='dee2e6'),
        bottom=Side(style='thin', color='dee2e6')
    )
    center_align = Alignment(horizontal='center', vertical='center')
    left_align = Alignment(horizontal='left', vertical='center', wrap_text=False)
    right_align = Alignment(horizontal='right', vertical='center')

    # Nagłówek dokumentu (wiersz 1)
    ws.merge_cells('A1:H1')
    ws['A1'] = f'INWENTURA MAGAZYNU NARZĘDZI'
    ws['A1'].font = title_font
    ws['A1'].fill = title_fill
    ws['A1'].alignment = center_align
    ws.row_dimensions[1].height = 25

    # Info wiersz (wiersz 2)
    ws.merge_cells('A2:H2')
    ws['A2'] = f'Stan na dzień: {today.strftime("%Y-%m-%d")} godz. {today.strftime("%H:%M")} | Liczba pozycji: {{POZYCJE}}'
    ws['A2'].fill = info_fill
    ws['A2'].font = info_font
    ws['A2'].font = Font(size=10, italic=True)
    ws['A2'].alignment = center_align
    ws.row_dimensions[2].height = 18

    # Nagłówki kolumn (wiersz 3)
    # Szerokości kolumn zoptymalizowane dla A4 landscape (~277mm - marginesy = ~250mm użyteczne)
    headers = ['Lp.', 'Kategoria', 'Opis / Specyfikacja', 'Nr katalogowy', 'Lokalizacja', 'Stan', 'Stan fakt.', 'Uwagi']
    col_widths = [5, 32, 50, 18, 20, 8, 12, 40]

    for col_idx, (header, width) in enumerate(zip(headers, col_widths), 1):
        cell = ws.cell(row=3, column=col_idx, value=header)
        cell.font = header_font
        cell.fill = header_fill
        cell.border = thin_border
        cell.alignment = center_align
        ws.column_dimensions[get_column_letter(col_idx)].width = width

    ws.row_dimensions[3].height = 20

    # Pobierz dane
    narzedzia = NarzedzieMagazynowe.objects.prefetch_related(
        'egzemplarze__lokalizacja',
        'podkategoria__kategoria'
    ).order_by('podkategoria__kategoria__nazwa', 'podkategoria__nazwa', 'opis')

    row_idx = 4
    lp = 0

    for narzedzie in narzedzia:
        egzemplarze = narzedzie.egzemplarze.filter(stan__in=['nowe', 'uzywane'])

        w_uzyciu = HistoriaUzyciaNarzedzia.objects.filter(
            egzemplarz__narzedzie_typ=narzedzie,
            data_zwrotu__isnull=True
        ).count()

        nowe_count = egzemplarze.filter(stan='nowe').count()
        uzywane_count = egzemplarze.filter(stan='uzywane').count()
        razem = nowe_count + uzywane_count + w_uzyciu

        if razem == 0:
            continue

        lp += 1

        if narzedzie.podkategoria:
            kategoria = f"{narzedzie.podkategoria.kategoria.nazwa} / {narzedzie.podkategoria.nazwa}"
        else:
            kategoria = "Brak kategorii"

        lokalizacje = set()
        for egz in egzemplarze:
            if egz.lokalizacja:
                lokalizacje.add(f"{egz.lokalizacja.szafa}/{egz.lokalizacja.polka}/{egz.lokalizacja.kolumna}")

        row_data = [
            lp,
            kategoria,
            narzedzie.opis,
            narzedzie.numer_katalogowy or '-',
            ', '.join(sorted(lokalizacje)) if lokalizacje else '-',
            razem,
            '',  # Stan faktyczny - puste
            '',  # Uwagi - puste
        ]

        # Alternatywne tło dla parzystych wierszy
        use_alt_fill = (lp % 2 == 0)

        for col_idx, value in enumerate(row_data, 1):
            cell = ws.cell(row=row_idx, column=col_idx, value=value)
            cell.border = thin_border
            cell.font = data_font_bold if col_idx == 6 else data_font

            if col_idx in [1, 6, 7]:
                cell.alignment = center_align
            else:
                cell.alignment = left_align

            if use_alt_fill:
                cell.fill = alt_fill

        ws.row_dimensions[row_idx].height = 16
        row_idx += 1

    # Aktualizuj liczbę pozycji w wierszu info
    ws['A2'] = f'Stan na dzień: {today.strftime("%Y-%m-%d")} godz. {today.strftime("%H:%M")} | Liczba pozycji: {lp}'

    # Pusta linia
    row_idx += 1

    # Podsumowanie
    ws.merge_cells(f'A{row_idx}:C{row_idx}')
    ws[f'A{row_idx}'] = f'Razem pozycji do sprawdzenia: {lp}'
    ws[f'A{row_idx}'].font = Font(bold=True, size=10)
    row_idx += 1

    ws.merge_cells(f'A{row_idx}:C{row_idx}')
    ws[f'A{row_idx}'] = f'Data wydruku: {today.strftime("%Y-%m-%d %H:%M")}'
    ws[f'A{row_idx}'].font = Font(size=9)
    row_idx += 2

    # Podpisy
    ws.merge_cells(f'A{row_idx}:D{row_idx}')
    ws[f'A{row_idx}'] = 'Podpis osoby przeprowadzającej inwenturę: _______________________________'
    ws[f'A{row_idx}'].font = Font(size=9)
    row_idx += 1

    ws.merge_cells(f'A{row_idx}:D{row_idx}')
    ws[f'A{row_idx}'] = 'Podpis osoby odpowiedzialnej za magazyn: _______________________________'
    ws[f'A{row_idx}'].font = Font(size=9)

    # Stopka drukowania
    ws.oddFooter.center.text = "Strona &P z &N"
    ws.oddFooter.center.size = 9
    ws.oddHeader.left.text = "CNC Tools - Inwentura magazynu"
    ws.oddHeader.left.size = 8
    ws.oddHeader.right.text = today.strftime("%Y-%m-%d")
    ws.oddHeader.right.size = 8

    # Powtarzanie nagłówków na każdej stronie
    ws.print_title_rows = '1:3'

    # Zwróć plik
    response = HttpResponse(
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    filename = f'Inwentura_{today.strftime("%Y-%m-%d")}.xlsx'
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    wb.save(response)
    return response

# ============================================================================
# Zarządzanie użytkownikami (zakładka "Użytkownicy" w Ustawieniach)
# Dostęp: administrator + logistyka. Magazyn/inni: 403.
# ============================================================================

class IsAdminOrLogistyka(BasePermission):
    """Tylko grupa administrator lub logistyka (lub superuser)."""

    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        if request.user.is_superuser:
            return True
        return request.user.groups.filter(name__in=["administrator", "logistyka"]).exists()


class GrupaViewSet(viewsets.ReadOnlyModelViewSet):
    """Lista grup Django dla dropdownu w modalu Użytkownicy."""
    queryset = Group.objects.all().order_by("name")
    serializer_class = GrupaSerializer
    permission_classes = [IsAdminOrLogistyka]
    pagination_class = None


class ZespolViewSet(LoggingMixin, viewsets.ModelViewSet):
    """CRUD na User + Pracownik. Tylko is_staff=False (admini niewidoczni)."""
    serializer_class = ZespolSerializer
    permission_classes = [IsAdminOrLogistyka]
    pagination_class = None
    log_name = "użytkownika"

    def get_log_description(self, instance):
        full = f"{instance.first_name} {instance.last_name}".strip()
        return full or instance.username

    def get_queryset(self):
        return (
            User.objects.filter(is_staff=False)
            .select_related("pracownik")
            .prefetch_related("groups")
            .order_by("last_name", "first_name", "username")
        )

    def perform_destroy(self, instance):
        # OneToOne Pracownik.user = SET_NULL → kasujemy Pracownika ręcznie
        # (FK z HistoriaUzyciaNarzedzia/Uszkodzenie na Pracownika mogą zablokować — wtedy 500)
        with transaction.atomic():
            pracownik = getattr(instance, "pracownik", None)
            if pracownik is not None:
                pracownik.delete()
            instance.delete()
