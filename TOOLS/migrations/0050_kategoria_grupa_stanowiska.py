from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('TOOLS', '0049_grupy_stanowisk'),
    ]

    operations = [
        migrations.AddField(
            model_name='kategoria',
            name='grupa_stanowiska',
            field=models.CharField(
                blank=True,
                choices=[('tokarz', 'tokarz'), ('frezer', 'frezer'), ('ślusarz', 'ślusarz')],
                help_text='Jeśli ustawione, tylko userzy z tej grupy stanowiska zobaczą narzędzia z tej kategorii w widoku Produkcja/Magazyn.',
                max_length=20,
                null=True,
                verbose_name='Grupa stanowiska',
            ),
        ),
    ]
