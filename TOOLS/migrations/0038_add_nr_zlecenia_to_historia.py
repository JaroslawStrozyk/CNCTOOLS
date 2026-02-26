from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('TOOLS', '0037_add_oznaczenie_to_egzemplarz'),
    ]

    operations = [
        migrations.AddField(
            model_name='historiauzyciaNarzedzia',
            name='nr_zlecenia',
            field=models.CharField(blank=True, max_length=100, null=True, verbose_name='Nr zlecenia'),
        ),
    ]
