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
from django.db.models import Count, Q, Sum
from django.db import transaction
from django.utils import timezone
from datetime import datetime
from decimal import Decimal

from .models import (
    Kategoria, Podkategoria, NarzedzieMagazynowe, EgzemplarzNarzedzia,
    Lokalizacja, Maszyna, HistoriaUzyciaNarzedzia, FakturaZakupu,
    Dostawca, Pracownik, Uszkodzenie, Zamowienie, PozycjaZamowienia,
    RealizacjaZamowienia, PozycjaRealizacji,
    ZapotrzebowanieTechnologa, PozycjaZapotrzebowania
)
from django.contrib.auth.models import User
from .serializers import (
    KategoriaSerializer, PodkategoriaSerializer, NarzedzieMagazynoweSerializer,
    EgzemplarzNarzedziaSerializer, LokalizacjaSerializer, MaszynaSerializer,
    HistoriaUzyciaNarzedziaSerializer, FakturaZakupuSerializer,
    DostawcaSerializer, PracownikSerializer, UszkodzenieSerializer,
    ZamowienieSerializer, PozycjaZamowieniaSerializer,
    RealizacjaZamowieniaSerializer, PozycjaRealizacjiSerializer,
    ZapotrzebowanieTechnologaSerializer, PozycjaZapotrzebowaniaSerializer
)
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
    """
    from .models import NarzedzieMagazynowe, EgzemplarzNarzedzia, PozycjaGeneratora, PozycjaZamowienia

    # Najpierw pobierz wszystkie istniejące pozycje z generatora
    istniejace_pozycje = PozycjaGeneratora.objects.select_related(
        'narzedzie_typ',
        'narzedzie_typ__podkategoria',
        'narzedzie_typ__podkategoria__kategoria',
        'dostawca'
    ).all()

    istniejace_narzedzia_ids = set(p.narzedzie_typ.id for p in istniejace_pozycje)

    # Teraz sprawdź czy są narzędzia wymagające zamówienia (nie uwzględnione w PozycjaGeneratora)
    narzedzia = NarzedzieMagazynowe.objects.select_related(
        'podkategoria',
        'podkategoria__kategoria',
        'ostatni_dostawca'
    ).prefetch_related('egzemplarze').all()

    for narzedzie in narzedzia:
        # Pomiń jeśli już jest w PozycjaGeneratora
        if narzedzie.id in istniejace_narzedzia_ids:
            continue

        # Sprawdź czy narzędzie jest w aktywnym (niezrealizowanym) zamówieniu
        # Aktywne = status nie jest 'completed'
        ma_aktywne_zamowienie = PozycjaZamowienia.objects.filter(
            narzedzie_typ=narzedzie,
            zamowienie__status__in=['draft', 'verified', 'sent', 'partially_received']
        ).exists()

        # Pomiń jeśli jest w aktywnym zamówieniu
        if ma_aktywne_zamowienie:
            continue

        # Oblicz aktualny stan
        calkowita_ilosc = narzedzie.egzemplarze.exclude(
            stan='uszkodzone'
        ).exclude(
            stan='uszkodzone_regeneracja'
        ).count()

        stan_maksymalny = narzedzie.stan_maksymalny if narzedzie.stan_maksymalny else 10

        # Sprawdź czy wymaga zamówienia
        if calkowita_ilosc < stan_maksymalny:
            ilosc_brakujacych_sztuk = stan_maksymalny - calkowita_ilosc

            # Przelicz na komplety jeśli potrzeba
            if narzedzie.opakowanie == 'kompl' and narzedzie.ilosc_w_opakowaniu > 0:
                import math
                ilosc_do_zamowienia = math.ceil(ilosc_brakujacych_sztuk / narzedzie.ilosc_w_opakowaniu)
            else:
                ilosc_do_zamowienia = ilosc_brakujacych_sztuk

            # Pobierz cenę z ostatniej pozycji zamówienia
            cena_jednostkowa = 0
            if narzedzie.ostatni_dostawca:
                ostatnia_pozycja = PozycjaZamowienia.objects.filter(
                    narzedzie_typ=narzedzie,
                    zamowienie__dostawca=narzedzie.ostatni_dostawca,
                    cena_jednostkowa__isnull=False
                ).order_by('-zamowienie__data_utworzenia').first()

                if ostatnia_pozycja and ostatnia_pozycja.cena_jednostkowa:
                    cena_jednostkowa = ostatnia_pozycja.cena_jednostkowa

            # Utwórz pozycję generatora
            PozycjaGeneratora.objects.create(
                narzedzie_typ=narzedzie,
                dostawca=narzedzie.ostatni_dostawca,
                ilosc_do_zamowienia=ilosc_do_zamowienia,
                cena_jednostkowa=cena_jednostkowa
            )

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

        # Sprawdź czy narzędzie jest w aktywnym (niezrealizowanym) zamówieniu
        # Pomijamy tylko jeśli jest w zamówieniu - pozycje w generatorze pozostają do czasu zrealizowania
        ma_aktywne_zamowienie = PozycjaZamowienia.objects.filter(
            narzedzie_typ=narzedzie,
            zamowienie__status__in=['draft', 'verified', 'sent', 'partially_received']
        ).exists()

        # Pomiń jeśli jest w aktywnym zamówieniu
        if ma_aktywne_zamowienie:
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

        wynik.append({
            'id': narzedzie.id,
            'dostawca_nazwa': dostawca_nazwa,
            'dostawca_id': dostawca_id,
            'element': element,
            'numer_katalogowy': narzedzie.numer_katalogowy or '',
            'ilosc_do_zamowienia': pozycja.ilosc_do_zamowienia,
            'rodzaj': rodzaj,
            'cena_jednostkowa': float(pozycja.cena_jednostkowa) if pozycja.cena_jednostkowa else 0,
            # Dane do sortowania
            'kategoria': narzedzie.podkategoria.kategoria.nazwa if narzedzie.podkategoria else '',
            'podkategoria': narzedzie.podkategoria.nazwa if narzedzie.podkategoria else '',
            'opis': narzedzie.opis
        })

    # Sortowanie
    wynik.sort(key=lambda x: (x['kategoria'].lower(), x['podkategoria'].lower(), x['opis'].lower()))

    return Response(wynik)


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
    Usuwa pozycję z PozycjaGeneratora i ustawia stan_maksymalny = calkowita_ilosc
    """
    from .models import NarzedzieMagazynowe, PozycjaGeneratora

    try:
        narzedzie = NarzedzieMagazynowe.objects.get(id=narzedzie_id)
    except NarzedzieMagazynowe.DoesNotExist:
        return Response({'error': 'Narzędzie nie istnieje'}, status=404)

    # Usuń pozycję generatora
    PozycjaGeneratora.objects.filter(narzedzie_typ=narzedzie).delete()

    # Ustaw stan_maksymalny równy aktualnemu stanowi
    calkowita_ilosc = narzedzie.egzemplarze.exclude(
        stan='uszkodzone'
    ).exclude(
        stan='uszkodzone_regeneracja'
    ).count()

    narzedzie.stan_maksymalny = calkowita_ilosc
    narzedzie.save()

    # Logowanie
    user_name = get_user_display_name(request.user)
    app_logger.warning(user_name, f"Usunięto z generatora zamówień: {narzedzie.opis}")

    return Response({'success': True, 'message': 'Usunięto z listy zamówień'})


@api_view(['POST'])
def generator_zamowien_add_api(request):
    """
    Endpoint do ręcznego dodawania pozycji do generatora zamówień.
    """
    from .models import NarzedzieMagazynowe, Dostawca, PozycjaGeneratora
    import math

    narzedzie_id = request.data.get('narzedzie_id')
    dostawca_id = request.data.get('dostawca_id')
    ilosc = request.data.get('ilosc_do_zamowienia', 1)
    cena = request.data.get('cena_jednostkowa', 0)

    if not narzedzie_id:
        return Response({'error': 'Wybierz narzędzie'}, status=400)

    try:
        narzedzie = NarzedzieMagazynowe.objects.get(id=narzedzie_id)
    except NarzedzieMagazynowe.DoesNotExist:
        return Response({'error': 'Narzędzie nie istnieje'}, status=404)

    # Sprawdź czy pozycja już istnieje
    if PozycjaGeneratora.objects.filter(narzedzie_typ=narzedzie).exists():
        return Response({'error': 'To narzędzie jest już w generatorze'}, status=400)

    # Pobierz dostawcę jeśli podano
    dostawca = None
    if dostawca_id:
        try:
            dostawca = Dostawca.objects.get(id=dostawca_id)
        except Dostawca.DoesNotExist:
            return Response({'error': 'Dostawca nie istnieje'}, status=400)

    # Utwórz pozycję generatora
    PozycjaGeneratora.objects.create(
        narzedzie_typ=narzedzie,
        dostawca=dostawca,
        ilosc_do_zamowienia=ilosc,
        cena_jednostkowa=cena
    )

    # Logowanie
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

            # Grupuj według dostawcy
            from collections import defaultdict
            grouped = defaultdict(list)

            for pozycja in pozycje_generatora:
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
                    ostatni_nr = int(ostatnie_zamowienie.numer.split('/')[-1])
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

                utworzone_zamowienia.append({
                    'id': zamowienie.id,
                    'numer': zamowienie.numer,
                    'dostawca': dostawca.nazwa_firmy
                })

            # Wyczyść tabelę PozycjaGeneratora
            PozycjaGeneratora.objects.all().delete()

            # Logowanie
            user_name = get_user_display_name(request.user)
            numery = ', '.join([z['numer'] for z in utworzone_zamowienia])
            app_logger.success(user_name, f"Wygenerowano {len(utworzone_zamowienia)} zamówień: {numery}")

            return Response({
                'success': True,
                'message': f'Utworzono {len(utworzone_zamowienia)} zamówień',
                'zamowienia': utworzone_zamowienia
            })

    except Exception as e:
        return Response({'error': str(e)}, status=500)


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

    # Sprawdź czy dostawca ma email
    if not zamowienie.email_docelowy:
        return Response({'error': 'Dostawca nie ma przypisanego adresu email'}, status=400)

    # Wyślij email
    result = send_zamowienie_email(zamowienie)

    if result['success']:
        # Zaktualizuj status i datę wysłania
        zamowienie.status = 'sent'
        zamowienie.data_wyslania = timezone.now()
        zamowienie.save()

        # Logowanie
        user_name = get_user_display_name(request.user)
        dostawca = zamowienie.dostawca.nazwa_firmy if zamowienie.dostawca else 'nieznany'
        app_logger.success(user_name, f"Wysłano email z zamówieniem {zamowienie.numer} do: {dostawca} ({zamowienie.email_docelowy})")

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
    }

    return JsonResponse(config)


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
            queryset = queryset.filter(pobieranie_narzedzi=True)
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
        ).prefetch_related('egzemplarze').annotate(
            ilosc_nowych=Coalesce(Subquery(nowe_subquery), Value(0)),
            ilosc_uzywanych_dostepnych=Coalesce(Subquery(uzywane_subquery), Value(0)),
            ilosc_w_uzyciu=Coalesce(Subquery(w_uzyciu_subquery), Value(0)),
        ).annotate(
            # Razem = Nowe + Używane + W użyciu (suma wszystkich sztuk)
            calkowita_ilosc=Coalesce(Subquery(nowe_subquery), Value(0)) +
                           Coalesce(Subquery(uzywane_subquery), Value(0)) +
                           Coalesce(Subquery(w_uzyciu_subquery), Value(0))
        )
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
        ).prefetch_related('egzemplarze').annotate(
            ilosc_nowych=Coalesce(Subquery(nowe_subquery), Value(0)),
            ilosc_uzywanych_dostepnych=Coalesce(Subquery(uzywane_subquery), Value(0)),
            ilosc_w_uzyciu=Coalesce(Subquery(w_uzyciu_subquery), Value(0)),
        ).annotate(
            # Razem = Nowe + Używane + W użyciu (suma wszystkich sztuk)
            calkowita_ilosc=Coalesce(Subquery(nowe_subquery), Value(0)) +
                           Coalesce(Subquery(uzywane_subquery), Value(0)) +
                           Coalesce(Subquery(w_uzyciu_subquery), Value(0))
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

        return queryset.order_by('-data_zakupu')

    def destroy(self, request, *args, **kwargs):
        """
        Usuwa egzemplarz:
        - Jeśli stan = 'uszkodzone' lub 'uszkodzone_regeneracja' → tworzy wpis w Uszkodzenie i usuwa egzemplarz
        - W pozostałych przypadkach → usuwa fizycznie
        """
        egzemplarz = self.get_object()

        # Sprawdź czy egzemplarz jest uszkodzony
        if egzemplarz.stan in ['uszkodzone', 'uszkodzone_regeneracja']:
            # Przygotuj dane lokalizacji
            lokalizacja_opis = ''
            if egzemplarz.lokalizacja:
                lokalizacja_opis = f"{egzemplarz.lokalizacja.szafa}/{egzemplarz.lokalizacja.polka}/{egzemplarz.lokalizacja.kolumna}"

            # Przygotuj kategorię
            kategoria_narzedzia = ''
            if egzemplarz.narzedzie_typ and egzemplarz.narzedzie_typ.podkategoria:
                kategoria_narzedzia = f"{egzemplarz.narzedzie_typ.podkategoria.kategoria.nazwa} / {egzemplarz.narzedzie_typ.podkategoria.nazwa}"

            # Pobierz ostatnią historię użycia
            ostatnia_historia = egzemplarz.historia.order_by('-data_wydania').first()
            maszyna_nazwa = ''
            pracownik_nazwisko = ''
            pracownik_imie = ''

            if ostatnia_historia:
                if ostatnia_historia.maszyna:
                    maszyna_nazwa = ostatnia_historia.maszyna.nazwa
                if ostatnia_historia.pracownik:
                    pracownik_nazwisko = ostatnia_historia.pracownik.nazwisko
                    pracownik_imie = ostatnia_historia.pracownik.imie

            # Mapowanie stanu na czytelny tekst
            stan_tekst = 'Uszkodzone' if egzemplarz.stan == 'uszkodzone' else 'Uszkodzone do regeneracji'

            # Utwórz wpis w tabeli Uszkodzenie z pełnymi danymi
            Uszkodzenie.objects.create(
                egzemplarz=None,
                narzedzie_typ=egzemplarz.narzedzie_typ,
                narzedzie_opis=egzemplarz.narzedzie_typ.opis,
                numer_katalogowy=egzemplarz.narzedzie_typ.numer_katalogowy or '',
                kategoria_narzedzia=kategoria_narzedzia,
                lokalizacja_opis=lokalizacja_opis,
                stan=stan_tekst,
                maszyna_nazwa=maszyna_nazwa,
                pracownik_nazwisko=pracownik_nazwisko,
                pracownik_imie=pracownik_imie,
                opis_uszkodzenia=''  # Pusty jak wymagane
            )

        # Loguj usunięcie
        user_name = get_user_display_name(request.user)
        opis = f"{egzemplarz.narzedzie_typ.opis} (ID: {egzemplarz.id})"
        if egzemplarz.stan in ['uszkodzone', 'uszkodzone_regeneracja']:
            app_logger.warning(user_name, f"Usunięto uszkodzony egzemplarz: {opis}")
        else:
            app_logger.warning(user_name, f"Usunięto egzemplarz narzędzia: {opis}")

        # Usuń egzemplarz
        egzemplarz.delete()

        return Response(status=status.HTTP_204_NO_CONTENT)


class HistoriaUzyciaNarzedziaViewSet(viewsets.ModelViewSet):
    queryset = HistoriaUzyciaNarzedzia.objects.select_related(
        'egzemplarz__narzedzie_typ__podkategoria__kategoria',
        'maszyna',
        'pracownik'
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

        try:
            historia = EgzemplarzService.wydaj_egzemplarz(
                egzemplarz_id=egzemplarz_id,
                maszyna_id=maszyna_id,
                pracownik_id=pracownik_id,
                czesciowe_wydanie=czesciowe_wydanie,
                ilosc_sztuk=ilosc_sztuk
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

            # Jeśli uszkodzone lub uszkodzone_regeneracja, utwórz wpis w tabeli uszkodzeń
            if stan_po_zwrocie in ['uszkodzone', 'uszkodzone_regeneracja']:
                opis_domyslny = 'Uszkodzenie podczas użycia' if stan_po_zwrocie == 'uszkodzone' else 'Uszkodzenie do regeneracji'
                Uszkodzenie.objects.create(
                    egzemplarz=egzemplarz_zwrocony,
                    opis_uszkodzenia=request.data.get('uwagi', opis_domyslny),
                    pracownik=historia.pracownik
                )

            # Logowanie zwrotu
            user_name = get_user_display_name(request.user)
            narzedzie_opis = historia.egzemplarz.narzedzie_typ.opis
            stan_map = {'nowe': 'nowe', 'uzywane': 'używane', 'uszkodzone': 'uszkodzone', 'uszkodzone_regeneracja': 'do regeneracji'}
            stan_tekst = stan_map.get(stan_po_zwrocie, stan_po_zwrocie)
            if stan_po_zwrocie in ['uszkodzone', 'uszkodzone_regeneracja']:
                app_logger.warning(user_name, f"Zwrócono narzędzie jako {stan_tekst}: {narzedzie_opis}")
            else:
                app_logger.success(user_name, f"Zwrócono narzędzie ({stan_tekst}): {narzedzie_opis}")

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
        """Filtrowanie - tylko zapotrzebowania aktualnego użytkownika"""
        queryset = super().get_queryset()
        if self.request.user.is_authenticated and not self.request.user.is_superuser:
            queryset = queryset.filter(technolog=self.request.user)
        return queryset.order_by('-data_utworzenia')

    def perform_create(self, serializer):
        """Automatycznie przypisz technologa przy tworzeniu"""
        serializer.save(technolog=self.request.user)

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
        Zwraca wszystkie wysłane zapotrzebowania dla magazyniera.
        Dostępne dla wszystkich użytkowników.
        """
        zapotrzebowania = ZapotrzebowanieTechnologa.objects.filter(
            status='submitted'
        ).select_related('technolog').prefetch_related('pozycje').order_by('-data_wyslania')

        serializer = self.get_serializer(zapotrzebowania, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def zrealizuj(self, request, pk=None):
        """
        Zmienia status zapotrzebowania na 'completed'.
        """
        zapotrzebowanie = self.get_object()

        if zapotrzebowanie.status != 'submitted':
            return Response(
                {'error': 'Tylko wysłane zapotrzebowanie może być zrealizowane'},
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
        app_logger.success(user_name, f"Zrealizowano zapotrzebowanie (ID: {zapotrzebowanie.id}) od: {technolog}")

        serializer = self.get_serializer(zapotrzebowanie)
        return Response({
            'success': True,
            'message': 'Zapotrzebowanie zostało zrealizowane',
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
            'data_wydruku': settings.PDF_DATA_DOKUMENTU,
            'wersja_dokumentu': getattr(settings, 'PDF_WERSJA_DOKUMENTU', 1),
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
        """Filtrowanie - tylko pozycje zapotrzebowań aktualnego użytkownika"""
        queryset = super().get_queryset()
        if not self.request.user.is_superuser:
            queryset = queryset.filter(zapotrzebowanie__technolog=self.request.user)

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