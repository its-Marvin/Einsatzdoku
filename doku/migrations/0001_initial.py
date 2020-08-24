# Generated by Django 3.0.5 on 2020-06-14 13:51

from django.conf import settings
import django.core.validators
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Einsatz',
            fields=[
                ('Erstellt', models.DateTimeField(auto_now_add=True)),
                ('Nummer', models.AutoField(editable=False, primary_key=True, serialize=False)),
                ('extNummer', models.IntegerField(null=True)),
                ('Einsatzleiter', models.CharField(default='', max_length=200)),
                ('Adresse', models.CharField(max_length=200)),
                ('OrtFrei', models.CharField(max_length=200, null=True)),
                ('Ende', models.DateTimeField(default=None, editable=False, null=True)),
                ('Training', models.BooleanField(default=False)),
            ],
        ),
        migrations.CreateModel(
            name='Einstellungen',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('Name', models.CharField(default='Einsatzverwaltung', max_length=50)),
                ('Hydranten', models.CharField(default='http://openfiremap.org/', max_length=1000)),
                ('Lagekarten', models.BooleanField(default=True)),
                ('Personen', models.BooleanField(default=True)),
                ('Fahrzeuge', models.BooleanField(default=True)),
                ('Einsatzleiter', models.BooleanField(default=True)),
                ('Einsatznummer', models.BooleanField(default=True)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Icon',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('Name', models.CharField(max_length=200)),
                ('icon', models.ImageField(upload_to='icons')),
            ],
        ),
        migrations.CreateModel(
            name='Ort',
            fields=[
                ('PLZ', models.IntegerField(primary_key=True, serialize=False, validators=[django.core.validators.MinValueValidator(0), django.core.validators.MaxValueValidator(99999)])),
                ('Kurzname', models.CharField(max_length=3)),
                ('Langname', models.CharField(max_length=20)),
            ],
        ),
        migrations.CreateModel(
            name='Stichwort',
            fields=[
                ('Kurzname', models.CharField(max_length=4, primary_key=True, serialize=False)),
                ('Langname', models.CharField(max_length=50)),
            ],
        ),
        migrations.CreateModel(
            name='Zug',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('Name', models.CharField(max_length=50)),
                ('Farbe', models.CharField(default='#bbbbbb', max_length=7)),
            ],
        ),
        migrations.CreateModel(
            name='Profile',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nightmode', models.BooleanField(default=True)),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='Person',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('Nachname', models.CharField(editable=False, max_length=50)),
                ('Vorname', models.CharField(editable=False, max_length=50)),
                ('Rolle', models.CharField(editable=False, max_length=50)),
                ('Notizen', models.CharField(max_length=200)),
                ('Einsatz', models.ForeignKey(editable=False, on_delete=django.db.models.deletion.PROTECT, to='doku.Einsatz')),
            ],
        ),
        migrations.CreateModel(
            name='Meldung',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('Inhalt', models.TextField()),
                ('Wichtig', models.BooleanField(default=False)),
                ('Erstellt', models.DateTimeField(auto_now_add=True)),
                ('Autor', models.ForeignKey(editable=False, on_delete=django.db.models.deletion.PROTECT, to=settings.AUTH_USER_MODEL)),
                ('Einsatz', models.ForeignKey(editable=False, on_delete=django.db.models.deletion.PROTECT, to='doku.Einsatz')),
                ('Zug', models.ForeignKey(blank=True, default=None, null=True, on_delete=django.db.models.deletion.SET_NULL, to='doku.Zug')),
            ],
        ),
        migrations.CreateModel(
            name='Lagekarte',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('Erstellt', models.DateTimeField(auto_now_add=True)),
                ('Bild', models.TextField(default='0')),
                ('Data', models.TextField(default='')),
                ('Einsatz', models.ForeignKey(editable=False, on_delete=django.db.models.deletion.PROTECT, to='doku.Einsatz')),
            ],
        ),
        migrations.CreateModel(
            name='Fahrzeuge',
            fields=[
                ('Funkname', models.CharField(max_length=8, primary_key=True, serialize=False)),
                ('Typ', models.CharField(max_length=10)),
                ('Ort', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='doku.Ort')),
                ('Zug', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='doku.Zug')),
            ],
        ),
        migrations.CreateModel(
            name='Fahrzeug',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('Zugfuehrer', models.IntegerField(validators=[django.core.validators.MinValueValidator(0), django.core.validators.MaxValueValidator(9)])),
                ('Gruppenfuehrer', models.IntegerField(validators=[django.core.validators.MinValueValidator(0), django.core.validators.MaxValueValidator(9)])),
                ('Mannschaft', models.IntegerField(validators=[django.core.validators.MinValueValidator(0), django.core.validators.MaxValueValidator(9)])),
                ('Atemschutz', models.IntegerField(validators=[django.core.validators.MinValueValidator(0), django.core.validators.MaxValueValidator(9)])),
                ('Autor', models.ForeignKey(editable=False, on_delete=django.db.models.deletion.PROTECT, to=settings.AUTH_USER_MODEL)),
                ('Einsatz', models.ForeignKey(editable=False, on_delete=django.db.models.deletion.PROTECT, to='doku.Einsatz')),
                ('Name', models.ForeignKey(editable=False, on_delete=django.db.models.deletion.PROTECT, to='doku.Fahrzeuge')),
            ],
        ),
        migrations.AddField(
            model_name='einsatz',
            name='Ort',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='doku.Ort'),
        ),
        migrations.AddField(
            model_name='einsatz',
            name='Stichwort',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='doku.Stichwort'),
        ),
    ]
