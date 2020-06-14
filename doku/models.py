from django.db import models
from django.core.validators import MaxValueValidator, MinValueValidator
from django.contrib.auth import get_user_model
from django.contrib.auth.models import User
from django.dispatch import receiver
from django.db.models.signals import post_save
from datetime import datetime, timezone
import pytz


class Meldung(models.Model):
    Inhalt = models.TextField(blank=False)
    Wichtig = models.BooleanField(default=False)
    Erstellt = models.DateTimeField(auto_now_add=True, editable=False)
    Autor = models.ForeignKey(get_user_model(), on_delete=models.PROTECT, editable=False)
    Einsatz = models.ForeignKey('Einsatz', on_delete=models.PROTECT, editable=False)
    Zug = models.ForeignKey('Zug', on_delete=models.SET_NULL, null=True, default=None, blank=True)

    def __str__(self):
        return self.Erstellt.strftime('%H:%M:%S') + " - " + str(self.Inhalt) + " [" + str(self.Autor) + "]"

    def getTimeCreated(self):
        return self.Erstellt.astimezone(pytz.timezone("Europe/Berlin")).strftime('%H:%M')

    def getDateCreated(self):
        return self.Erstellt.astimezone(pytz.timezone("Europe/Berlin")).strftime('%d %B %Y')

    def getTimeOrDate(self):
        if self.Erstellt.date() == datetime.now().date():
            return self.getTimeCreated()
        else:
            return self.getDateCreated() + " " + self.getTimeCreated()


class Einsatz(models.Model):
    Erstellt = models.DateTimeField(auto_now_add=True, editable=False)
    Nummer = models.AutoField(primary_key=True, editable=False)
    extNummer = models.IntegerField(null=True)
    Einsatzleiter = models.CharField(max_length=200, default="")
    Stichwort = models.ForeignKey('Stichwort', null=False, on_delete=models.PROTECT)
    Adresse = models.CharField(max_length=200)
    Ort = models.ForeignKey('Ort', on_delete=models.PROTECT)
    OrtFrei = models.CharField(max_length=200, null=True)
    Ende = models.DateTimeField(default=None, null=True, editable=False)
    Training = models.BooleanField(default=False)

    def __str__(self):
        return str(self.Nummer) + "_" + self.Stichwort.Kurzname + "_" + self.Ort.Kurzname

    def getYear(self):
        return self.Erstellt.astimezone(pytz.timezone("Europe/Berlin")).strftime('%Y')

    def getDuration(self):
        if self.Ende:
            return self.Ende - self.Erstellt
        else:
            return datetime.now() - self.Erstellt

    def getMapsCompatibleAdress(self):
        if self.OrtFrei:
            return self.Adresse + ", " + self.OrtFrei
        else:
            return self.Adresse + ", " + self.Ort.Langname


class Zug(models.Model):
    Name = models.CharField(max_length=50, null=False)
    Farbe = models.CharField(max_length=7, default="#bbbbbb")

    def __str__(self):
        return str(self.Name)


class Ort(models.Model):
    PLZ = models.IntegerField(primary_key=True, validators=[MinValueValidator(0), MaxValueValidator(99999)])
    Kurzname = models.CharField(max_length=3, null=False)
    Langname = models.CharField(max_length=20, null=False)

    def __str__(self):
        return str(self.Langname)


class Stichwort(models.Model):
    Kurzname = models.CharField(max_length=4, primary_key=True)
    Langname = models.CharField(max_length=50, null=False)

    def __str__(self):
        return str(self.Kurzname) + " " + str(self.Langname)


class Fahrzeug(models.Model):
    Zugfuehrer = models.IntegerField(validators=[MinValueValidator(0), MaxValueValidator(9)])
    Gruppenfuehrer = models.IntegerField(validators=[MinValueValidator(0), MaxValueValidator(9)])
    Mannschaft = models.IntegerField(validators=[MinValueValidator(0), MaxValueValidator(9)])
    Atemschutz = models.IntegerField(validators=[MinValueValidator(0), MaxValueValidator(9)])
    Name = models.ForeignKey('Fahrzeuge', editable=False, on_delete=models.PROTECT)
    Autor = models.ForeignKey(get_user_model(), on_delete=models.PROTECT, editable=False)
    Einsatz = models.ForeignKey('Einsatz', on_delete=models.PROTECT, editable=False)

    def __str__(self):
        return str(self.Name.Funkname) + " - Stärke: " + str(self.Zugfuehrer) + "/" + str(
            self.Gruppenfuehrer) + "/" + str(self.Mannschaft) + " (" + str(self.Atemschutz) + " AGT)"


class Fahrzeuge(models.Model):
    Funkname = models.CharField(max_length=8, primary_key=True)
    Ort = models.ForeignKey('Ort', on_delete=models.PROTECT)
    Typ = models.CharField(max_length=10, null=False)
    Zug = models.ForeignKey('Zug', on_delete=models.PROTECT)

    def __str__(self):
        return str(self.Funkname) + " " + self.Typ + " " + self.Ort.Langname


class Person(models.Model):
    Nachname = models.CharField(max_length=50, null=False, editable=False)
    Vorname = models.CharField(max_length=50, null=False, editable=False)
    Rolle = models.CharField(max_length=50, null=False, editable=False)
    Notizen = models.CharField(max_length=200)
    Einsatz = models.ForeignKey('Einsatz', on_delete=models.PROTECT, editable=False)

    def __str__(self):
        return self.Nachname + ", " + self.Vorname + " (" + self.Rolle + ")"


class Lagekarte(models.Model):
    Erstellt = models.DateTimeField(auto_now_add=True, editable=False)
    Bild = models.TextField(default="0", blank=False)
    Data = models.TextField(default="")
    Einsatz = models.ForeignKey('Einsatz', on_delete=models.PROTECT, editable=False)


class Icon(models.Model):
    Name = models.CharField(max_length=200, null=False)
    icon = models.ImageField(upload_to="icons")

    def __str__(self):
        return self.Name


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    nightmode = models.BooleanField(default=True)


class SingletonModel(models.Model):
    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        self.pk = 1
        super(SingletonModel, self).save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        pass

    @classmethod
    def load(cls):
        obj, created = cls.objects.get_or_create(pk=1)
        return obj


class Einstellungen(SingletonModel):
    Name = models.CharField(max_length=50, null=False, default="Einsatzverwaltung")
    Hydranten = models.CharField(max_length=1000, null=False, default="http://openfiremap.org/")
    Lagekarten = models.BooleanField(default=True)
    Personen = models.BooleanField(default=True)
    Fahrzeuge = models.BooleanField(default=True)
    Einsatzleiter = models.BooleanField(default=True)
    Einsatznummer = models.BooleanField(default=True)

    def __str__(self):
        return "Allgemeine Einstellungen"


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)


@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    profile = Profile.objects.get_or_create(user=instance)
    instance.profile.save()
