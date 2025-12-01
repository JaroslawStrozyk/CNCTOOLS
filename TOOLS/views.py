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
from django.utils import timezone
from datetime import datetime

from .models import (
    Kategoria, Podkategoria, NarzedzieMagazynowe, EgzemplarzNarzedzia,
    Lokalizacja, Maszyna, HistoriaUzyciaNarzedzia, FakturaZakupu,
    Dostawca, Pracownik, Uszkodzenie, Zamowienie, PozycjaZamowienia,
    RealizacjaZamowienia, PozycjaRealizacji
)
from .serializers import (
    KategoriaSerializer, PodkategoriaSerializer, NarzedzieMagazynoweSerializer,
    EgzemplarzNarzedziaSerializer, LokalizacjaSerializer, MaszynaSerializer,
    HistoriaUzyciaNarzedziaSerializer, FakturaZakupuSerializer,
    DostawcaSerializer, PracownikSerializer, UszkodzenieSerializer,
    ZamowienieSerializer, PozycjaZamowieniaSerializer,
    RealizacjaZamowieniaSerializer, PozycjaRealizacjiSerializer
)
from .services import EgzemplarzService, LokalizacjaService


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
def odpady_view(request):
    return render(request, 'odpady.html')


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

        return Response({
            'success': True,
            'message': result['message']
        })
    else:
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


class KategoriaViewSet(viewsets.ModelViewSet):
    queryset = Kategoria.objects.prefetch_related('podkategorie').all()
    serializer_class = KategoriaSerializer


class PodkategoriaViewSet(viewsets.ModelViewSet):
    queryset = Podkategoria.objects.select_related('kategoria').all()
    serializer_class = PodkategoriaSerializer


class DostawcaViewSet(viewsets.ModelViewSet):
    queryset = Dostawca.objects.all()
    serializer_class = DostawcaSerializer


class LokalizacjaViewSet(viewsets.ModelViewSet):
    queryset = Lokalizacja.objects.all()
    serializer_class = LokalizacjaSerializer

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
            return Response(
                {'message': f'Dodano {liczba_utworzonych} lokalizacji dla szafy {szafa}.'},
                status=status.HTTP_201_CREATED
            )
        except ValidationError as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )


class MaszynaViewSet(viewsets.ModelViewSet):
    queryset = Maszyna.objects.all()
    serializer_class = MaszynaSerializer


class PracownikViewSet(viewsets.ModelViewSet):
    queryset = Pracownik.objects.all()
    serializer_class = PracownikSerializer
    pagination_class = StandardResultsSetPagination


class FakturaZakupuViewSet(viewsets.ModelViewSet):
    queryset = FakturaZakupu.objects.select_related('dostawca').all()
    serializer_class = FakturaZakupuSerializer
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        queryset = super().get_queryset()
        narzedzie_id = self.request.query_params.get('narzedzie_id', None)

        if narzedzie_id:
            queryset = queryset.filter(
                egzemplarze__narzedzie_typ_id=narzedzie_id
            ).distinct()

        return queryset.order_by('-data_wystawienia')


class NarzedzieMagazynoweViewSet(viewsets.ModelViewSet):
    serializer_class = NarzedzieMagazynoweSerializer

    def get_queryset(self):
        from django.db.models import Value, Subquery, OuterRef
        from django.db.models.functions import Coalesce

        # Subquery dla ilości nowych (stan='nowe')
        nowe_subquery = EgzemplarzNarzedzia.objects.filter(
            narzedzie_typ=OuterRef('pk'),
            stan='nowe'
        ).values('narzedzie_typ').annotate(
            total=Sum('ilosc_w_komplecie')
        ).values('total')

        # Subquery dla ilości używanych (stan='uzywane')
        uzywane_subquery = EgzemplarzNarzedzia.objects.filter(
            narzedzie_typ=OuterRef('pk'),
            stan='uzywane'
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
            # Razem = Nowe + Używane (suma dostępnych sztuk)
            calkowita_ilosc=Coalesce(Subquery(nowe_subquery), Value(0)) + Coalesce(Subquery(uzywane_subquery), Value(0))
        )
        return queryset.order_by('podkategoria__kategoria__nazwa', 'podkategoria__nazwa', 'opis')


class NarzedzieMagazynoweZakupyViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = NarzedzieMagazynoweSerializer

    def get_queryset(self):
        from django.db.models import Value, Subquery, OuterRef
        from django.db.models.functions import Coalesce

        # Subquery dla ilości nowych (stan='nowe')
        nowe_subquery = EgzemplarzNarzedzia.objects.filter(
            narzedzie_typ=OuterRef('pk'),
            stan='nowe'
        ).values('narzedzie_typ').annotate(
            total=Sum('ilosc_w_komplecie')
        ).values('total')

        # Subquery dla ilości używanych (stan='uzywane')
        uzywane_subquery = EgzemplarzNarzedzia.objects.filter(
            narzedzie_typ=OuterRef('pk'),
            stan='uzywane'
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
            # Razem = Nowe + Używane (suma dostępnych sztuk)
            calkowita_ilosc=Coalesce(Subquery(nowe_subquery), Value(0)) + Coalesce(Subquery(uzywane_subquery), Value(0))
        )
        return queryset.order_by('podkategoria__kategoria__nazwa', 'podkategoria__nazwa', 'opis')


class EgzemplarzNarzedziaViewSet(viewsets.ModelViewSet):
    queryset = EgzemplarzNarzedzia.objects.select_related(
        'narzedzie_typ__podkategoria__kategoria',
        'lokalizacja',
        'faktura_zakupu'
    ).all()
    serializer_class = EgzemplarzNarzedziaSerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        narzedzie_typ_id = self.request.query_params.get('narzedzie_typ_id', None)

        if narzedzie_typ_id:
            queryset = queryset.filter(narzedzie_typ_id=narzedzie_typ_id)

        return queryset.order_by('-data_zakupu')


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

        try:
            historia = EgzemplarzService.wydaj_egzemplarz(
                egzemplarz_id=egzemplarz_id,
                maszyna_id=maszyna_id,
                pracownik_id=pracownik_id
            )
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

        try:
            historia = EgzemplarzService.zwroc_egzemplarz(
                historia_id=historia.id,
                stan_po_zwrocie=stan_po_zwrocie
            )

            # Zapisz pracownika zwracającego
            if pracownik_zwracajacy_id:
                try:
                    pracownik_zwracajacy = Pracownik.objects.get(id=pracownik_zwracajacy_id)
                    historia.pracownik_zwracajacy = pracownik_zwracajacy
                    historia.save()
                except Pracownik.DoesNotExist:
                    pass

            # Jeśli uszkodzone lub uszkodzone_regeneracja, utwórz wpis w tabeli uszkodzeń
            if stan_po_zwrocie in ['uszkodzone', 'uszkodzone_regeneracja']:
                opis_domyslny = 'Uszkodzenie podczas użycia' if stan_po_zwrocie == 'uszkodzone' else 'Uszkodzenie do regeneracji'
                Uszkodzenie.objects.create(
                    egzemplarz=historia.egzemplarz,
                    opis_uszkodzenia=request.data.get('uwagi', opis_domyslny),
                    pracownik=historia.pracownik
                )

            serializer = self.get_serializer(historia)
            return Response(serializer.data)
        except ValidationError as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )


class UszkodzenieViewSet(viewsets.ModelViewSet):
    queryset = Uszkodzenie.objects.select_related(
        'egzemplarz__narzedzie_typ__podkategoria__kategoria',
        'pracownik'
    ).all()
    serializer_class = UszkodzenieSerializer

    def get_queryset(self):
        return super().get_queryset().order_by('-data_uszkodzenia')


class ZamowienieViewSet(viewsets.ModelViewSet):
    queryset = Zamowienie.objects.select_related('dostawca').prefetch_related('pozycje').all()
    serializer_class = ZamowienieSerializer

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
        pass


class PozycjaZamowieniaViewSet(viewsets.ModelViewSet):
    queryset = PozycjaZamowienia.objects.select_related(
        'zamowienie',
        'narzedzie_typ__podkategoria__kategoria'
    ).all()
    serializer_class = PozycjaZamowieniaSerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        zamowienie_id = self.request.query_params.get('zamowienie_id', None)
        if zamowienie_id:
            queryset = queryset.filter(zamowienie_id=zamowienie_id)
        return queryset


class RealizacjaZamowieniaViewSet(viewsets.ModelViewSet):
    queryset = RealizacjaZamowienia.objects.select_related(
        'zamowienie__dostawca',
        'lokalizacja_domyslna'
    ).prefetch_related('pozycje').all()
    serializer_class = RealizacjaZamowieniaSerializer

    @action(detail=True, methods=['post'])
    def zatwierdz(self, request, pk=None):
        """Tworzy egzemplarze, loguje, aktualizuje status"""
        pass


class PozycjaRealizacjiViewSet(viewsets.ModelViewSet):
    queryset = PozycjaRealizacji.objects.select_related(
        'realizacja',
        'pozycja_zamowienia__narzedzie_typ',
        'lokalizacja'
    ).all()
    serializer_class = PozycjaRealizacjiSerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        realizacja_id = self.request.query_params.get('realizacja_id', None)
        if realizacja_id:
            queryset = queryset.filter(realizacja_id=realizacja_id)
        return queryset