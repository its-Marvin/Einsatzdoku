from django.db import migrations


class Migration(migrations.Migration):
    """Setzt die Standardsortierung fuer Meldungen auf (Erstellt, pk).

    Reine Metadaten-Aenderung - es wird kein Datenbankschema veraendert.
    """

    dependencies = [
        ('doku', '0001_initial'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='meldung',
            options={'ordering': ('Erstellt', 'pk')},
        ),
    ]

