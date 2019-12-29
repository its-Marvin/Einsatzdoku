from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from django.urls import reverse
from django.shortcuts import get_object_or_404, render
from django.core import serializers
from django.core.exceptions import PermissionDenied
from django.http import HttpResponseServerError
import json
import datetime

from .models import Einstellungen, Einsatz, Meldung, Fahrzeug, Fahrzeuge, Stichwort, Ort, Person, Lagekarte, Zug


def index(request):
    Ort.objects.get_or_create(PLZ=0, Kurzname="ZZZ", Langname="Freitext")
    einstellungen = Einstellungen.objects.filter(pk=1)[0]
    alle_Einsaetze = Einsatz.objects.filter(Training=False).order_by('-Nummer')
    alle_Stichworte = Stichwort.objects.order_by('Kurzname')
    alle_Orte = Ort.objects.order_by('Kurzname')
    autor = request.user if request.user.is_authenticated else None
    context = {
        'training': False,
        'einstellungen': einstellungen,
        'autor': autor,
        'alle_Einsaetze': alle_Einsaetze,
        'alle_Stichworte': alle_Stichworte,
        'alle_Orte': alle_Orte,
    }
    return render(request, 'doku/index.html', context)


def index_training(request):
    Ort.objects.get_or_create(PLZ=0, Kurzname="ZZZ", Langname="Freitext")
    einstellungen = Einstellungen.objects.filter(pk=1)[0]
    alle_Einsaetze = Einsatz.objects.filter(Training=True).order_by('-Nummer')
    alle_Stichworte = Stichwort.objects.order_by('Kurzname')
    alle_Orte = Ort.objects.order_by('Kurzname')
    autor = request.user if request.user.is_authenticated else None
    context = {
        'training': True,
        'einstellungen': einstellungen,
        'autor': autor,
        'alle_Einsaetze': alle_Einsaetze,
        'alle_Stichworte': alle_Stichworte,
        'alle_Orte': alle_Orte,
    }
    return render(request, 'doku/index.html', context)


def einsatz(request, einsatz_id):
    einstellungen = Einstellungen.objects.filter(pk=1)[0]
    try:
        einsatz = Einsatz.objects.filter(Nummer=einsatz_id)[0]
    except:
        einsatz = None
    aktive_Einsaetze = Einsatz.objects.filter(Ende=None).filter(Training=einsatz.Training).order_by('-Nummer')
    alle_Meldungen = Meldung.objects.order_by('-Erstellt').filter(Einsatz=einsatz_id)
    eingesetzte_Fahrzeuge = Fahrzeug.objects.filter(Einsatz=einsatz_id)
    alle_Personen = Person.objects.filter(Einsatz=einsatz_id)
    alle_Fahrzeuge = Fahrzeuge.objects.filter()
    autor = request.user if request.user.is_authenticated else None
    context = {
        'training': einsatz.Training,
        'einstellungen': einstellungen,
        'autor': autor,
        'einsatz': einsatz,
        'aktive_Einsaetze': aktive_Einsaetze,
        'alle_Meldungen': alle_Meldungen,
        'eingesetzte_Fahrzeuge': eingesetzte_Fahrzeuge,
        'alle_Fahrzeuge': alle_Fahrzeuge,
        'alle_Personen': alle_Personen,
    }
    return render(request, 'doku/einsatz.html', context)


def lagekarte(request, einsatz_id):
    einsatz = get_object_or_404(Einsatz, pk=einsatz_id)
    if request.method == "POST":
        if request.POST['image'] and request.POST['canvas_data']:
            karte = Lagekarte(Bild=request.POST['image'], Data=request.POST['canvas_data'], Einsatz=einsatz)
            karte.save()
            return HttpResponse("Success")
            #return HttpResponseRedirect(reverse('doku:lagekarte', args=[einsatz_id]))
        else:
            return HttpResponseServerError
    else:
        einstellungen = Einstellungen.objects.filter(pk=1)[0]
        aktive_Einsaetze = Einsatz.objects.filter(Ende=None).filter(Training=einsatz.Training).order_by('-Nummer')
        lagekarten = Lagekarte.objects.filter(Einsatz=einsatz_id).order_by('-Erstellt')
        autor = request.user if request.user.is_authenticated else None
        context = {
            'training': einsatz.Training,
            'einstellungen': einstellungen,
            'autor': autor,
            'einsatz': einsatz,
            'lagekarten': lagekarten,
            'aktive_Einsaetze': aktive_Einsaetze,
        }
        return render(request, 'doku/lagekarte.html', context)


def neuer_Einsatz(request):
    if not request.user.is_authenticated:
        raise PermissionDenied
    try:
        ort = get_object_or_404(Ort, Kurzname=request.POST['Ort'])
        stichwort = get_object_or_404(Stichwort, Kurzname=request.POST['Stichwort'])
        ort_frei = request.POST.get('Freitext', "")
        adresse = request.POST['Adresse']
    except:
        return HttpResponse("<h1>Fehler bei der Verarbeitung</h1><h2>Ungültige Daten für die Einsatzanlage</h2>")
    else:
        e = Einsatz(Stichwort=stichwort, Adresse=adresse, Ort=ort, OrtFrei=ort_frei)
        e.save()
        return HttpResponseRedirect(reverse('doku:einsatz', args=[e.pk]))


def neues_Training(request):
    if not request.user.is_authenticated:
        raise PermissionDenied
    try:
        ort = get_object_or_404(Ort, Kurzname=request.POST['Ort'])
        stichwort = get_object_or_404(Stichwort, Kurzname=request.POST['Stichwort'])
        ort_frei = request.POST.get('Freitext', "")
        adresse = request.POST['Adresse']
    except:
        return HttpResponse("<h1>Fehler bei der Verarbeitung</h1><h2>Ungültige Daten für die Einsatzanlage</h2>")
    else:
        e = Einsatz(Stichwort=stichwort, Adresse=adresse, Ort=ort, OrtFrei=ort_frei, Training=True)
        e.save()
        return HttpResponseRedirect(reverse('doku:einsatz', args=[e.pk]))


def einsatznummer(request, einsatz_id):
    if not request.user.is_authenticated:
        raise PermissionDenied
    einsatz = get_object_or_404(Einsatz, pk=einsatz_id)
    try:
        einsatz.extNummer = int(request.POST['extENr'])
        einsatz.save()
    except:
        return HttpResponseServerError()
    return HttpResponse("Success")


def einsatzleiter(request, einsatz_id):
    if not request.user.is_authenticated:
        raise PermissionDenied
    einsatz = get_object_or_404(Einsatz, pk=einsatz_id)
    try:
        einsatz.Einsatzleiter = request.POST['einsatzleiter']
        einsatz.save()
    except:
        return HttpResponseServerError()
    return HttpResponse("Success")


def neue_Meldung(request, einsatz_id):
    if not request.user.is_authenticated:
        raise PermissionDenied
    einsatz = get_object_or_404(Einsatz, pk=einsatz_id)
    try:
        inhalt = request.POST['Inhalt']
    except:
        return HttpResponse("<h1>Fehler bei der Verarbeitung</h1>")
    else:
        if request.POST.get('Wichtig') is None:
            wichtig = False
        else:
            wichtig = True
        #Neue Meldung anlegen
        m = Meldung(Inhalt=inhalt, Wichtig=wichtig, Einsatz=einsatz, Autor=request.user)
        m.save()
        return HttpResponseRedirect(reverse('doku:einsatz', args=[einsatz_id]))


def neue_Person(request, einsatz_id):
    if not request.user.is_authenticated:
        raise PermissionDenied
    einsatz = get_object_or_404(Einsatz, pk=einsatz_id)
    try:
        nachname = request.POST['Nachname']
        vorname = request.POST['Vorname']
        rolle = request.POST['Rolle']
        notizen = request.POST['Notizen']
    except:
        return HttpResponse("<h1>Fehler bei der Verarbeitung</h1>")
    else:
        try:
            p = Person.objects.filter(Einsatz=einsatz).filter(Nachname=nachname).filter(Vorname=vorname)[0]
            p.Notizen = notizen
        except:
            p = Person(Nachname=nachname, Vorname=vorname, Rolle=rolle, Notizen=notizen, Einsatz=einsatz)
        p.save()
        return HttpResponseRedirect(reverse('doku:einsatz', args=[einsatz_id]))


def neues_Fahrzeug(request, einsatz_id):
    if not request.user.is_authenticated:
        raise PermissionDenied
    einsatz = get_object_or_404(Einsatz, pk=einsatz_id)
    try:
        name = get_object_or_404(Fahrzeuge, pk=request.POST['Name'])
        besatzung = request.POST['Besatzung']
        zugfuehrer = int(besatzung.split("/")[0])
        gruppenfuehrer = int(besatzung.split("/")[1])
        mannschaft = int(besatzung.split("/")[2])
        atemschutz = request.POST.get('Atemschutz', 0)
    except:
        return HttpResponse("<h1>Fehler bei der Verarbeitung</h1>")
    else:
        try:
            f = Fahrzeug.objects.filter(Einsatz=einsatz).filter(Name=name)[0]
            f.Zugfuehrer=zugfuehrer
            f.Gruppenfuehrer=gruppenfuehrer
            f.Mannschaft=mannschaft
            f.Atemschutz=atemschutz
        except:
            f = Fahrzeug(Name=name, Zugfuehrer=zugfuehrer, Gruppenfuehrer=gruppenfuehrer, Mannschaft=mannschaft, Atemschutz=atemschutz, Einsatz=einsatz, Autor=request.user)
        f.save()
        return HttpResponseRedirect(reverse('doku:einsatz', args=[einsatz_id]))


def einsatzende(request, einsatz_id):
    if not request.user.is_authenticated:
        raise PermissionDenied
    autor = request.user if request.user.is_authenticated else None
    try:
        einsatz = Einsatz.objects.filter(Nummer=einsatz_id)[0]
    except:
        einsatz = None
    else:
        if autor:
            einsatz.Ende = datetime.datetime.now();
            einsatz.save()
    return HttpResponseRedirect(reverse('doku:index'))


def meldung(request, einsatz_id):
    einsatz = get_object_or_404(Einsatz, pk=einsatz_id)
    try:
        lastID = request.GET['lastID']
    except:
        lastID = 0
    neueMeldungen = serializers.serialize("json", Meldung.objects.filter(Einsatz=einsatz).filter(pk__gt=lastID))
    #neueMeldungen = { 'error': 'Fehler in der Verarbeitung'}
    return JsonResponse(neueMeldungen, safe=False)
    #.filter(Nummer__gt=lastID))


def summe_Personal(request, einsatz_id):
    einsatz = get_object_or_404(Einsatz, pk=einsatz_id)
    zuege = Zug.objects.all()
    summe = {}
    zf = 0
    gf = 0
    ms = 0
    agt = 0
    for zug in zuege:
        summe[zug.Name] = {
        'zugfuehrer': 0,
        'gruppenfuehrer': 0,
        'mannschaft': 0,
        'atemschutz': 0
        }
        try:
            for fahrzeug in Fahrzeug.objects.filter(Einsatz=einsatz_id).filter(Name__Zug__Name__contains=zug.Name):
                summe[zug.Name]['zugfuehrer'] += fahrzeug.Zugfuehrer
                zf += fahrzeug.Zugfuehrer
                summe[zug.Name]['gruppenfuehrer'] += fahrzeug.Gruppenfuehrer
                gf += fahrzeug.Gruppenfuehrer
                summe[zug.Name]['mannschaft'] += fahrzeug.Mannschaft
                ms += fahrzeug.Mannschaft
                summe[zug.Name]['atemschutz'] += fahrzeug.Atemschutz
                agt += fahrzeug.Atemschutz
        except FileExistsError:
            summe.pop(zug.Name)
    summe['Gesamt'] = {
        'zugfuehrer': zf,
        'gruppenfuehrer': gf,
        'mannschaft': ms,
        'atemschutz': agt
    }
    return JsonResponse(json.dumps(summe), safe=False)


def toggleNightmode(request):
    user = request.user if request.user.is_authenticated else None
    user.profile.nightmode = False if user.profile.nightmode else True
    user.profile.save()
    return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/'))
