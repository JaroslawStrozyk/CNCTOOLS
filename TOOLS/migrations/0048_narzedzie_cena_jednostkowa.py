from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('TOOLS', '0047_narzedzie_utworzone_wraz_z_zamowieniem'),
    ]

    operations = [
        migrations.AddField(
            model_name='narzedziemagazynowe',
            name='cena_jednostkowa',
            field=models.DecimalField(
                blank=True,
                decimal_places=2,
                help_text='Ostatnia użyta lub ręcznie ustawiona cena jednostkowa.',
                max_digits=10,
                null=True,
                verbose_name='Cena jednostkowa',
            ),
        ),
    ]
