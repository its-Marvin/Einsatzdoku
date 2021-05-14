from django.http import HttpResponse, HttpResponseRedirect, JsonResponse, HttpResponseNotAllowed, HttpResponseForbidden
from django.urls import reverse
from django.shortcuts import get_object_or_404, render
from django.core import serializers
from django.core.exceptions import PermissionDenied
from django.http import HttpResponseServerError
import json
import datetime
import os

from .models import Einstellungen, Einsatz, Meldung, Fahrzeug, Fahrzeuge, Stichwort, Ort, Person, Lagekarte, Zug, \
    Einsatzstellen_Notizen
from .models import Einsatzstellen, Einheiten


def index(request):
    Ort.objects.get_or_create(PLZ=0, Kurzname="ZZZ", Langname="Freitext")
    einstellungen = Einstellungen.objects.get_or_create(pk=1)[0]
    alle_Einsaetze = Einsatz.objects.filter(Training=False).order_by('-Nummer')
    alle_Stichworte = Stichwort.objects.order_by('Kurzname')
    alle_Orte = Ort.objects.order_by('Kurzname')
    autor = request.user if request.user.is_authenticated else None
    jahre = []
    for einsatz in alle_Einsaetze:
        if einsatz.Ende:
            if einsatz.getYear() not in jahre:
                jahre.append(einsatz.getYear())
    context = {
        'training': False,
        'einstellungen': einstellungen,
        'autor': autor,
        'alle_Einsaetze': alle_Einsaetze,
        'alle_Stichworte': alle_Stichworte,
        'alle_Orte': alle_Orte,
        'jahre': sorted(jahre, reverse=True),
    }
    return render(request, 'doku/index.html', context)


def index_training(request):
    Ort.objects.get_or_create(PLZ=0, Kurzname="ZZZ", Langname="Freitext")
    einstellungen = Einstellungen.objects.get_or_create(pk=1)[0]
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
    einstellungen = Einstellungen.objects.get_or_create(pk=1)[0]
    try:
        einsatz = Einsatz.objects.filter(Nummer=einsatz_id)[0]
    except:
        einsatz = None
    aktive_Einsaetze = Einsatz.objects.filter(Ende=None).filter(Training=einsatz.Training).order_by('-Nummer')
    alle_Meldungen = Meldung.objects.order_by('-Erstellt').filter(Einsatz=einsatz_id)
    eingesetzte_Fahrzeuge = Fahrzeug.objects.filter(Einsatz=einsatz_id).order_by('Name__Zug', 'Name__Ort__Langname', 'Name__Funkname')
    alle_Personen = Person.objects.filter(Einsatz=einsatz_id)
    alle_Fahrzeuge = Fahrzeuge.objects.filter()
    alle_Zuege = Zug.objects.filter()
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
        'alle_Zuege': alle_Zuege,
    }
    return render(request, 'doku/einsatz.html', context)


def oel_einsatzstelle_notiz(request, einsatz_id, einsatzstelle_id):
    if request.method == "POST":
        if not request.user.is_authenticated:
            return HttpResponseForbidden()
        try:
            error = ""
            einsatz = get_object_or_404(Einsatz, pk=einsatz_id)
            einsatzstelle = get_object_or_404(Einsatzstellen, pk=einsatzstelle_id)
            notiztext = request.POST.get('Notiz', "Fehler!").strip()
            if notiztext != "":
                notiz = Einsatzstellen_Notizen(Einsatzstelle=einsatzstelle, Notiz=notiztext, Einsatz=einsatz)
                notiz.save()
            else:
                error = "Notiz darf nicht leer sein."
        except Exception:
            error = "Fehler beim Anlegen einer neuen Notiz."
        return oel_response(request, einsatz_id, error=error)
    else:
        return HttpResponseRedirect(reverse('doku:oel', args=[einsatz_id]))


def oel(request, einsatz_id):
    if request.method == "GET":
        return oel_response(request, einsatz_id)
    elif request.method == "POST":
        if not request.user.is_authenticated:
            return HttpResponseForbidden()
        error = None
        ortFrei = None
        if not request.user.is_authenticated:
            raise PermissionDenied
        autor = request.user if request.user.is_authenticated else None
        try:
            einsatz = get_object_or_404(Einsatz, pk=einsatz_id)
            if 'Name' not in request.POST or request.POST['Name'] == "":
                if 'Einsatzstelle' not in request.POST:
                    raise Exception("Es muss ein Name eingegeben werden!")
            name = request.POST.get('Name', "")
            if 'neueEinsatzstelle' in request.POST:
                if 'Ort' not in request.POST:
                    raise Exception("Es muss ein Ort ausgewählt werden!")
                ort = get_object_or_404(Ort, Kurzname=request.POST['Ort'])
                if ort.Kurzname == "ZZZ":
                    ortFrei = request.POST.get('Freitext', "")
                    if not ortFrei:
                        raise Exception("Das Freitext Feld muss ausgefüllt sein!")
                anmerkungen = request.POST.get('Anmerkungen', "").strip()
                e = Einsatzstellen(Ort=ort, OrtFrei=ortFrei, Einsatz=einsatz, Name=name)
                e.save()
                if anmerkungen != "":
                    notiz = Einsatzstellen_Notizen(Einsatz=einsatz, Notiz=anmerkungen, Einsatzstelle=e)
                    notiz.save()
                e_ort = ortFrei if ortFrei else ort.Langname
                inhalt = "Neue Einsatzstelle: \"" + name + ", " + e_ort + "\""
                m = Meldung(Inhalt=inhalt, Wichtig=False, Einsatz=einsatz, Autor=autor, Zug=None)
                m.save()
            elif 'Einsatzstelle' in request.POST:
                e = Einsatzstellen.objects.filter(pk=request.POST['Einsatzstelle'])[0]
                if 'DONE' in request.POST:
                    e.Abgeschlossen = datetime.datetime.now()
                    e_ort = e.OrtFrei if e.OrtFrei else e.Ort.Langname
                    inhalt = "Einsatzstelle \"" + e.Name + ", " + e_ort + "\" abgearbeitet von \"" + e.Einheit.Name + "\""
                    m = Meldung(Inhalt=inhalt, Wichtig=False, Einsatz=einsatz, Autor=autor, Zug=None)
                    m.save()
                elif 'Einheit' in request.POST:
                    e.Einheit = Einheiten.objects.filter(pk=request.POST['Einheit'])[0]
                    e.Zugewiesen = datetime.datetime.now()
                    e_ort = e.OrtFrei if e.OrtFrei else e.Ort.Langname
                    inhalt = "Einsatzstelle \"" + e.Name + ", " + e_ort + "\" übernommen von \"" + e.Einheit.Name + "\""
                    m = Meldung(Inhalt=inhalt, Wichtig=False, Einsatz=einsatz, Autor=autor, Zug=None)
                    m.save()
                elif 'Anmerkungen' in request.POST:
                    e.Anmerkungen = request.POST['Anmerkungen']
            else:
                if Einheiten.objects.filter(Name=name).filter(Einsatz=einsatz).count() == 0:
                    e = Einheiten(Name=name, Einsatz=einsatz)
                else:
                    e = Einheiten.objects.filter(Name=name).filter(Einsatz=einsatz)[0]
            e.save()
        except Exception as err:
            error = str(err)
        return oel_response(request, einsatz_id, error)
    else:
        return HttpResponseNotAllowed(['GET', 'POST'])


def oel_response(request, einsatz_id, error=None):
    einstellungen = Einstellungen.objects.get_or_create(pk=1)[0]
    try:
        einsatz = Einsatz.objects.filter(Nummer=einsatz_id)[0]
    except:
        einsatz = None
    aktive_Einsaetze = Einsatz.objects.filter(Ende=None).filter(Training=einsatz.Training).order_by('-Nummer')
    autor = request.user if request.user.is_authenticated else None
    einsatzstellen = Einsatzstellen.objects.filter(Einsatz=einsatz_id)
    einheiten = Einheiten.objects.filter(Einsatz=einsatz_id)
    alle_Orte = Ort.objects.order_by('Kurzname')
    notizen = Einsatzstellen_Notizen.objects.filter(Einsatz=einsatz_id)
    context = {
        'training': einsatz.Training,
        'einstellungen': einstellungen,
        'autor': autor,
        'einsatz': einsatz,
        'aktive_Einsaetze': aktive_Einsaetze,
        'einsatzstellen': einsatzstellen,
        'einheiten': einheiten,
        'alle_Orte': alle_Orte,
        'notizen': notizen,
        'error': error,
    }
    return render(request, 'doku/oel.html', context)


def lagekarte(request, einsatz_id):
    einsatz = get_object_or_404(Einsatz, pk=einsatz_id)
    if request.method == "POST":
        if request.POST['image'] and request.POST['canvas_data']:
            karte = Lagekarte(Bild=request.POST['image'], Data=request.POST['canvas_data'], Einsatz=einsatz)
            karte.save()
            return HttpResponse("Success")
            # return HttpResponseRedirect(reverse('doku:lagekarte', args=[einsatz_id]))
        else:
            return HttpResponseServerError
    else:
        einstellungen = Einstellungen.objects.get_or_create(pk=1)[0]
        aktive_Einsaetze = Einsatz.objects.filter(Ende=None).filter(Training=einsatz.Training).order_by('-Nummer')
        lagekarten = Lagekarte.objects.filter(Einsatz=einsatz_id).order_by('-Erstellt')
        autor = request.user if request.user.is_authenticated else None
        icons = get_icons()
        context = {
            'training': einsatz.Training,
            'einstellungen': einstellungen,
            'autor': autor,
            'einsatz': einsatz,
            'lagekarten': lagekarten,
            'aktive_Einsaetze': aktive_Einsaetze,
            'icons': icons,
        }
        return render(request, 'doku/lagekarte.html', context)

def get_icons():
    icons = []
    for icon in os.listdir("doku/static/doku/icons"):
        try:
            order = int(icon.split("_")[0])
            name = icon.split("_", 1)[1].split(".")[0]
        except:
            order = 999
            try:
                name = icon.split(".")[0]
            except:
                name = icon
        icons.append({
            'path': icon,
            'name': name,
            'order': order
        })
    icons.sort(key=lambda i: (i['order'], i['name']))
    return icons


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
    if einsatz.Ende:
        raise PermissionDenied
    try:
        if request.POST.get('Zug') is None:
            inhalt = ""
        else:
            inhalt = request.POST['Zug']
        inhalt += request.POST['Inhalt']
    except:
        return HttpResponse("<h1>Fehler bei der Verarbeitung</h1>")
    else:
        try:
            zug = request.POST.get('Zug', None)[:-2]
            zug = Zug.objects.get(Name=zug)
        except:
            zug = None
        if request.POST.get('Wichtig') is None:
            wichtig = False
        else:
            wichtig = True
        #Neue Meldung anlegen
        m = Meldung(Inhalt=inhalt, Wichtig=wichtig, Einsatz=einsatz, Autor=request.user, Zug=zug)
        m.save()
        return HttpResponseRedirect(reverse('doku:einsatz', args=[einsatz_id]))


def neue_Person(request, einsatz_id):
    if not request.user.is_authenticated:
        raise PermissionDenied
    einsatz = get_object_or_404(Einsatz, pk=einsatz_id)
    if einsatz.Ende:
        raise PermissionDenied
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
    if einsatz.Ende:
        raise PermissionDenied
    try:
        name = get_object_or_404(Fahrzeuge, pk=request.POST['Name'])
        besatzung = request.POST['Besatzung']
        zugfuehrer = int(besatzung.split("/")[0])
        gruppenfuehrer = int(besatzung.split("/")[1])
        mannschaft = int(besatzung.split("/")[2])
        atemschutz = request.POST.get('Atemschutz', 0)
        if atemschutz == "":
            atemschutz = 0
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
    neueMeldungen = serializers.serialize("json", Meldung.objects.select_related().filter(Einsatz=einsatz).filter(pk__gt=lastID))
    return JsonResponse(neueMeldungen, safe=False)


def summe_Personal(request, einsatz_id):
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
