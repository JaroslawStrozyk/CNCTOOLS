from django.conf import settings


def vite_settings(request):
    """
    Przekazuje ustawienia Vite do szablonów.
    Zmienna `debug` jest dostepna niezaleznie od INTERNAL_IPS.
    """
    # Pobierz dev_mode z nowej konfiguracji DJANGO_VITE
    vite_config = getattr(settings, 'DJANGO_VITE', {})
    dev_mode = vite_config.get('default', {}).get('dev_mode', settings.DEBUG)

    return {
        'debug': dev_mode,  # Używaj dev_mode zamiast DEBUG
        'vite_dev_mode': dev_mode,
    }
