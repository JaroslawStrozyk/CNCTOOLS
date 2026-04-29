# tools/urls.py
from django.urls import path, include
from django.contrib.auth.decorators import login_required
from django.views.generic import TemplateView
from rest_framework.routers import DefaultRouter
from . import views
from .views_inertia import (
    login_view as login_inertia_view,
    login_submit,
    login_by_card,
    logout_view as logout_inertia_view,
    magazyn_view as magazyn_inertia_view,
    zakupy_view as zakupy_inertia_view,
    zamowienia_view as zamowienia_inertia_view,
    ustawienia_view as ustawienia_inertia_view,
    generator_view as generator_inertia_view,
    realizacja_view as realizacja_inertia_view,
    faktury_view as faktury_inertia_view,
    zwroty_view as zwroty_inertia_view,
    zapotrzebowania_view as zapotrzebowania_inertia_view,
    produkcja_view as produkcja_inertia_view,
    technologia_view as technologia_inertia_view,
    kierownik_view as kierownik_inertia_view,
    logi_view as logi_inertia_view,
    magazyn_update_view,
)

router = DefaultRouter()

# Podstawowe endpointy
router.register(r'kategorie', views.KategoriaViewSet, basename='kategoria')
router.register(r'podkategorie', views.PodkategoriaViewSet, basename='podkategoria')
router.register(r'dostawcy', views.DostawcaViewSet, basename='dostawca')
router.register(r'lokalizacje', views.LokalizacjaViewSet, basename='lokalizacja')
router.register(r'maszyny', views.MaszynaViewSet, basename='maszyna')
router.register(r'pracownicy', views.PracownikViewSet, basename='pracownik')
router.register(r'faktury', views.FakturaZakupuViewSet, basename='faktura')

# Narzędzia magazynowe
router.register(r'narzedzia', views.NarzedzieMagazynoweViewSet, basename='narzedzie')
router.register(r'narzedzia-zakupy', views.NarzedzieMagazynoweZakupyViewSet, basename='narzedzie-zakupy')
router.register(r'narzedzia-prod', views.NarzedzieMagazynoweProdViewSet, basename='narzedzie-prod')
router.register(r'egzemplarze', views.EgzemplarzNarzedziaViewSet, basename='egzemplarz')
router.register(r'historia', views.HistoriaUzyciaNarzedziaViewSet, basename='historia')
router.register(r'uszkodzenia', views.UszkodzenieViewSet, basename='uszkodzenie')

# Zamówienia
router.register(r'zamowienia', views.ZamowienieViewSet, basename='zamowienie')
router.register(r'pozycje-zamowien', views.PozycjaZamowieniaViewSet, basename='pozycja-zamowienia')
router.register(r'realizacje', views.RealizacjaZamowieniaViewSet, basename='realizacja')
router.register(r'pozycje-realizacji', views.PozycjaRealizacjiViewSet, basename='pozycja-realizacji')

# Zapotrzebowania technologów
router.register(r'zapotrzebowania', views.ZapotrzebowanieTechnologaViewSet, basename='zapotrzebowanie')
router.register(r'pozycje-zapotrzebowan', views.PozycjaZapotrzebowaniaViewSet, basename='pozycja-zapotrzebowania')

urlpatterns = [
    # ===== NOWY SYSTEM INERTIA (Vue SPA) =====
    path('', login_inertia_view, name='login'),
    path('login/', login_submit, name='login-submit'),
    path('api/login-card/', login_by_card, name='login-card'),
    path('logout/', logout_inertia_view, name='logout'),
    path('magazyn/', magazyn_inertia_view, name='magazyn'),
    path('magazyn/update', magazyn_update_view, name='magazyn-update'),
    path('zakupy/', zakupy_inertia_view, name='zakupy'),
    path('zamowienia/', zamowienia_inertia_view, name='zamowienia'),
    path('ustawienia/', ustawienia_inertia_view, name='ustawienia'),
    path('generator/', generator_inertia_view, name='generator'),
    path('realizacja/', realizacja_inertia_view, name='realizacja'),
    path('faktury/', faktury_inertia_view, name='faktury'),
    path('zwroty/', zwroty_inertia_view, name='zwroty'),
    path('zapotrzebowania/', zapotrzebowania_inertia_view, name='zapotrzebowania'),
    path('produkcja/', produkcja_inertia_view, name='produkcja'),
    path('technologia/', technologia_inertia_view, name='technologia'),
    path('kierownik/', kierownik_inertia_view, name='kierownik'),
    path('logi/', logi_inertia_view, name='logi'),

    # ===== POMOC (statyczne strony przewodników) =====
    path('pomoc/zamowienia/',
         login_required(TemplateView.as_view(template_name='help/zamowienia.html')),
         name='pomoc-zamowienia'),
    path('pomoc/magazyn/',
         login_required(TemplateView.as_view(template_name='help/magazyn.html')),
         name='pomoc-magazyn'),
    path('pomoc/zakupy/',
         login_required(TemplateView.as_view(template_name='help/zakupy.html')),
         name='pomoc-zakupy'),

    # ===== API =====
    # Zamówienia — custom endpointy (muszą być PRZED router.urls)
    path('api/zamowienia/wyslij-do-zatwierdzenia/', views.wyslij_do_zatwierdzenia_api,
         name='zamowienia-wyslij-do-zatwierdzenia'),
    path('api/zamowienia/zatwierdz/', views.zatwierdz_zamowienia_api,
         name='zamowienia-zatwierdz'),
    path('api/zamowienia/cofnij-do-roboczej/', views.cofnij_do_roboczej_api,
         name='zamowienia-cofnij-do-roboczej'),
    path('api/zamowienia/cofnij-do-zatwierdzone/', views.cofnij_do_zatwierdzone_api,
         name='zamowienia-cofnij-do-zatwierdzone'),
    path('api/zamowienia/zmien-dostawce/', views.zmien_dostawce_api,
         name='zamowienia-zmien-dostawce'),

    path('api/', include(router.urls)),
    path('api/generator-zamowien/', views.generator_zamowien_api, name='generator-zamowien'),
    path('api/generator-zamowien/add/', views.generator_zamowien_add_api, name='generator-zamowien-add'),
    path('api/generator-zamowien/gotowe/', views.generator_zamowien_gotowe_api, name='generator-zamowien-gotowe'),
    path('api/generator-zamowien/<int:narzedzie_id>/update/', views.generator_zamowien_update_api,
         name='generator-zamowien-update'),
    path('api/generator-zamowien/<int:narzedzie_id>/delete/', views.generator_zamowien_delete_api,
         name='generator-zamowien-delete'),
    path('api/generator-zamowien/przypisz-pozycje/<int:pozycja_id>/',
         views.generator_zamowien_przypisz_pozycje_api,
         name='generator-zamowien-przypisz-pozycje'),
    path('api/generator-zamowien/odrzuc-pozycje/<int:pozycja_id>/',
         views.generator_zamowien_odrzuc_pozycje_api,
         name='generator-zamowien-odrzuc-pozycje'),

    # Email endpoints
    path('api/email/test/', views.test_email_view, name='test_email'),
    path('api/email/config/', views.email_config_view, name='email_config'),
    path('api/zamowienia/<int:zamowienie_id>/wyslij-email/', views.wyslij_email_zamowienie_api,
         name='zamowienia-wyslij-email'),

    # Logi endpoints
    path('api/logi/biezace/', views.logi_biezace_view, name='logi-biezace'),
    path('api/logi/biezace/pdf/', views.logi_pdf_biezace_view, name='logi-biezace-pdf'),
    path('api/logi/pliki/', views.logi_pliki_view, name='logi-pliki'),
    path('api/logi/pliki/<str:filename>/', views.logi_plik_content_view, name='logi-plik-content'),
    path('api/logi/pliki/<str:filename>/pdf/', views.logi_pdf_archiwum_view, name='logi-archiwum-pdf'),

    # Zamówienia testowe
    path('api/email/zamowienia-testowe/', views.toggle_zamowienia_testowe, name='toggle-zamowienia-testowe'),

    # Wzory dokumentów (dla ISO)
    path('api/dokumenty/wzor/<str:typ>/', views.dokument_wzor_view, name='dokument-wzor'),

    # Eksport inwentury
    path('api/eksport/inwentura/pdf/', views.inwentura_pdf_view, name='inwentura-pdf'),
    path('api/eksport/inwentura/xls/', views.inwentura_xls_view, name='inwentura-xls'),
]