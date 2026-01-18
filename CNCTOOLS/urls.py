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
    logout(request)
    return redirect('/')


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
    path('admin/', admin.site.urls),
    path('install/<str:filename>', serve_install_file, name='serve_install'),  # Pliki instalacyjne
    path('', include('pwa.urls')),  # PWA manifest i service worker
    path('', include('TOOLS.urls')),  # API i widoki
]


if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
