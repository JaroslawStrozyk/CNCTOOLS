from django.contrib import admin
from django.contrib.admin.sites import AdminSite
from django.urls import path, include, re_path
from django.conf import settings
from django.conf.urls.static import static
from django.shortcuts import redirect
from django.http import FileResponse, Http404
import os


# Nadpisujemy logout admina żeby przekierowywał na stronę główną
def admin_logout(request):
    from django.contrib.auth import logout
    if getattr(settings, 'CNC_TOKEN_TRYB', 'wylaczony') != 'wylaczony':
        from cnc_wspolne.middleware import wyloguj_do_portalu
        return wyloguj_do_portalu(request)
    logout(request)
    return redirect('/')


def admin_login(request):
    """Panel serwisowy: przy logowaniu przez Portal — ekran Portalu zamiast logowania Django admin.
    Portal wpuszcza tu kontami ze `staff` (flagi st/su w tokenie)."""
    if getattr(settings, 'CNC_TOKEN_TRYB', 'wylaczony') == 'wylaczony':
        return admin.site.login(request)
    from urllib.parse import quote
    from django.utils.http import url_has_allowed_host_and_scheme
    nastepny = request.GET.get('next') or '/admin/'
    if not url_has_allowed_host_and_scheme(nastepny, allowed_hosts=None) or not nastepny.startswith('/'):
        nastepny = '/admin/'
    if request.user.is_authenticated and request.user.is_staff:
        return redirect(nastepny)
    return redirect(f"{settings.CNC_PORTAL_URL_LOGOWANIA}?next={quote(nastepny)}")


def serve_install_file(request, filename):
    """
    Serwuje pliki z katalogu install/ (certyfikaty, instalatory).
    Dostępne publicznie bez autoryzacji.
    URL: /install/<filename>
    """
    file_path = os.path.join(settings.INSTALL_ROOT, filename)

    # Zabezpieczenie przed path traversal
    if '..' in filename or filename.startswith('/'):
        raise Http404("Nieprawidłowa nazwa pliku")

    if os.path.exists(file_path) and os.path.isfile(file_path):
        # Określ typ MIME
        content_types = {
            '.crt': 'application/x-x509-ca-cert',
            '.pem': 'application/x-pem-file',
            '.zip': 'application/zip',
            '.exe': 'application/octet-stream',
        }
        ext = os.path.splitext(filename)[1].lower()
        content_type = content_types.get(ext, 'application/octet-stream')

        response = FileResponse(open(file_path, 'rb'), content_type=content_type)
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        return response

    raise Http404(f"Plik nie istnieje: {filename}")


urlpatterns = [
    path('admin/logout/', admin_logout, name='admin_logout'),  # Przed admin/
    path('admin/login/', admin_login, name='admin_login'),  # Przed admin/
    path('admin/', admin.site.urls),
    path('install/<str:filename>', serve_install_file, name='serve_install'),  # Pliki instalacyjne
    path('', include('pwa.urls')),  # PWA manifest i service worker
    path('', include('TOOLS.urls')),  # API i widoki
]


if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
