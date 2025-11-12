from datetime import datetime

def oblicz_czas_uzytkowania_narzedzia(data_wydania, data_zwrotu=None):
    if not data_zwrotu:
        data_zwrotu = datetime.now()
    if not isinstance(data_wydania, datetime) or not isinstance(data_zwrotu, datetime):
        raise TypeError("Daty muszą być obiektami datetime.")
    return data_zwrotu - data_wydania