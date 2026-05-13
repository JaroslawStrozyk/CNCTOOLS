"""
Data migration: nowe grupy stanowiskowe + likwidacja 'produkcja-magazyn'.

Tworzy 4 nowe grupy (małymi literami): brygadzista, tokarz, frezer, ślusarz.
Wszyscy userzy z grupy 'produkcja-magazyn' przenoszeni do 'brygadzista'.
Grupa 'produkcja-magazyn' jest kasowana. Grupa 'produkcja' pozostaje bez zmian.

Mapowanie uprawnień (logika w TOOLS/views_inertia.py):
  - PRODUKCJA_GROUPS         = {produkcja, frezer, ślusarz}
  - PRODUKCJA_MAGAZYN_GROUPS = {brygadzista, tokarz}
"""
from django.db import migrations


NOWE_GRUPY = ['brygadzista', 'tokarz', 'frezer', 'ślusarz']
STARA_GRUPA = 'produkcja-magazyn'
GRUPA_DOCELOWA_PRZY_MIGRACJI = 'brygadzista'


def forwards(apps, schema_editor):
    Group = apps.get_model('auth', 'Group')

    # 1. Utwórz 4 nowe grupy (idempotentnie)
    for nazwa in NOWE_GRUPY:
        Group.objects.get_or_create(name=nazwa)

    # 2. Przenieś userów z produkcja-magazyn → brygadzista, skasuj starą grupę
    try:
        stara = Group.objects.get(name=STARA_GRUPA)
    except Group.DoesNotExist:
        return

    docelowa = Group.objects.get(name=GRUPA_DOCELOWA_PRZY_MIGRACJI)
    for u in stara.user_set.all():
        u.groups.add(docelowa)
        u.groups.remove(stara)

    stara.delete()


def backwards(apps, schema_editor):
    Group = apps.get_model('auth', 'Group')

    # Odtwórz produkcja-magazyn
    stara, _ = Group.objects.get_or_create(name=STARA_GRUPA)

    # Przenieś brygadzistów z powrotem (best effort — nie wiemy, kto pierwotnie był brygadzistą)
    try:
        brygadzista = Group.objects.get(name=GRUPA_DOCELOWA_PRZY_MIGRACJI)
        for u in brygadzista.user_set.all():
            u.groups.add(stara)
            u.groups.remove(brygadzista)
    except Group.DoesNotExist:
        pass

    # Skasuj 4 nowe grupy
    Group.objects.filter(name__in=NOWE_GRUPY).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('TOOLS', '0048_narzedzie_cena_jednostkowa'),
        ('auth', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(forwards, backwards),
    ]
