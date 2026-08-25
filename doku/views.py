from django.http import HttpResponse, HttpResponseRedirect, JsonResponse, HttpResponseNotAllowed, HttpResponseForbidden
from django.urls import reverse
from django.shortcuts import get_object_or_404, render
from django.core import serializers
from django.core.exceptions import PermissionDenied
from django.http import HttpResponseServerError, StreamingHttpResponse
from django.shortcuts import redirect
from django.utils import timezone
from django.utils.http import url_has_allowed_host_and_scheme
from django.db.models import Count
import asyncio
import json
import os
import time

from django.utils.html import escape

from .models import Einstellungen, Einsatz, Meldung, Fahrzeug, Fahrzeuge, Stichwort, Ort, Person, Zug, \
    Einsatzstellen_Notizen, ZugExtra, User, Profile, EinsatzRevision
from .models import Einsatzstellen, Einheiten
from .pdf import build_einsatz_pdf

# Takt, in dem der Server nach Aenderungen schaut (Sekunden)
SSE_POLL_INTERVAL = 1.0
# Abstand der Keep-Alive-Kommentare, damit Proxies die Verbindung offen halten
SSE_PING_INTERVAL = 20.0
# Maximale Lebensdauer eines Streams; danach verbindet der Browser neu
SSE_MAX_LIFETIME = 3600.0


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
    first_run = False
    if len(User.objects.all()) == 0:
        first_run = True
    context = {
        'training': False,
        'einstellungen': einstellungen,
        'autor': autor,
        'alle_Einsaetze': alle_Einsaetze,
        'alle_Stichworte': alle_Stichworte,
        'alle_Orte': alle_Orte,
        'jahre': sorted(jahre, reverse=True),
        'first_run': first_run,
    }
    return render(request, 'doku/index.html', context)


def get_aktive_einsaetze(request):
    alle_einsaetze = Einsatz.objects.filter(Training=False).order_by('-Nummer')
    data = serializers.serialize('json', alle_einsaetze)
    return JsonResponse(data, safe=False)


def get_aktive_trainings_einsaetze(request):
    alle_einsaetze = Einsatz.objects.filter(Training=True).order_by('-Nummer')
    data = serializers.serialize('json', alle_einsaetze)
    return JsonResponse(data, safe=False)


def index_training(request):
    Ort.objects.get_or_create(PLZ=0, Kurzname="ZZZ", Langname="Freitext")
    einstellungen = Einstellungen.objects.get_or_create(pk=1)[0]
    alle_Einsaetze = Einsatz.objects.filter(Training=True).order_by('-Nummer')
    alle_Stichworte = Stichwort.objects.order_by('Kurzname')
    alle_Orte = Ort.objects.order_by('Kurzname')
    autor = request.user if request.user.is_authenticated else None
    jahre = []
    for einsatz in alle_Einsaetze:
        if einsatz.Ende:
            if einsatz.getYear() not in jahre:
                jahre.append(einsatz.getYear())
    context = {
        'training': True,
        'einstellungen': einstellungen,
        'autor': autor,
        'alle_Einsaetze': alle_Einsaetze,
        'alle_Stichworte': alle_Stichworte,
        'alle_Orte': alle_Orte,
        'jahre': sorted(jahre, reverse=True),
    }
    return render(request, 'doku/index.html', context)


def zug_fuer_ort(ort):
    """Ermittelt den Zug, der zu einem Einsatzort gehoert.

    Der Zug wird ueber die am Ort stationierten Fahrzeuge bestimmt. Beim
    Sonder-Ort "Freitext" (PLZ 0) gibt es keinen zugehoerigen Zug, damit die
    Meldungserfassung dann ohne Vorauswahl startet.
    """
    if ort is None or ort.PLZ == 0:
        return None
    zug_id = Fahrzeuge.objects.filter(Ort=ort).values('Zug') \
        .annotate(anzahl=Count('Zug')).order_by('-anzahl', 'Zug') \
        .values_list('Zug', flat=True).first()
    if zug_id is None:
        return None
    return Zug.objects.filter(pk=zug_id).first()


def einsatz(request, einsatz_id):
    einstellungen = Einstellungen.objects.get_or_create(pk=1)[0]
    try:
        einsatz = Einsatz.objects.filter(Nummer=einsatz_id)[0]
    except:
        einsatz = None
    aktive_Einsaetze = Einsatz.objects.filter(Ende=None).filter(Training=einsatz.Training).order_by('-Nummer')
    alle_Meldungen = Meldung.objects.order_by('-Erstellt', '-pk').filter(Einsatz=einsatz_id)
    eingesetzte_Fahrzeuge = Fahrzeug.objects.filter(Einsatz=einsatz_id).order_by('Name__Zug', 'Name__Ort__Langname',
                                                                                 'Name__Funkname')
    alle_Personen = Person.objects.filter(Einsatz=einsatz_id)
    alle_Fahrzeuge = Fahrzeuge.objects.filter()
    alle_Zuege = Zug.objects.filter()
    autor = request.user if request.user.is_authenticated else None
    auto_pdf_export = request.GET.get('auto_pdf', '0') == '1'
    vorgabe_zug = zug_fuer_ort(einsatz.Ort if einsatz else None)
    context = {
        'training': einsatz.Training,
        'einstellungen': einstellungen,
        'autor': autor,
        'einsatz': einsatz,
        'auto_pdf_export': auto_pdf_export,
        'aktive_Einsaetze': aktive_Einsaetze,
        'alle_Meldungen': alle_Meldungen,
        'eingesetzte_Fahrzeuge': eingesetzte_Fahrzeuge,
        'alle_Fahrzeuge': alle_Fahrzeuge,
        'alle_Personen': alle_Personen,
        'alle_Zuege': alle_Zuege,
        'vorgabe_zug': vorgabe_zug,
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
            notiztext = escape(request.POST.get('Notiz', "Fehler!").strip())
            if notiztext != "":
                notiz = Einsatzstellen_Notizen(Einsatzstelle=einsatzstelle, Notiz=notiztext, Einsatz=einsatz)
                notiz.save()
            else:
                error = "Notiz darf nicht leer sein."
        except Exception:
            error = "Fehler beim Anlegen einer neuen Notiz."
        return HttpResponseRedirect(reverse('doku:oel', args=[einsatz_id]))
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
                    ortFrei = escape(request.POST.get('Freitext', ""))
                    if not ortFrei:
                        raise Exception("Das Freitext Feld muss ausgefüllt sein!")
                anmerkungen = escape(request.POST.get('Anmerkungen', "").strip())
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
                    e.Abgeschlossen = timezone.now()
                    e_ort = e.OrtFrei if e.OrtFrei else e.Ort.Langname
                    inhalt = "Einsatzstelle \"" + e.Name + ", " + e_ort + "\" abgearbeitet von \"" + e.Einheit.Name + "\""
                    m = Meldung(Inhalt=inhalt, Wichtig=False, Einsatz=einsatz, Autor=autor, Zug=None)
                    m.save()
                elif 'Einheit' in request.POST:
                    e.Einheit = Einheiten.objects.filter(pk=request.POST['Einheit'])[0]
                    e.Zugewiesen = timezone.now()
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


def adresse(request, einsatz_id):
    if not request.user.is_authenticated:
        raise PermissionDenied
    einsatz = get_object_or_404(Einsatz, pk=einsatz_id)
    try:
        einsatz.Adresse = request.POST['adresse']
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
    except Exception:
        return _state_antwort(request, einsatz_id, fehler="Meldung konnte nicht gelesen werden.", status=400)
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
        # Neue Meldung anlegen
        m = Meldung(Inhalt=inhalt, Wichtig=wichtig, Einsatz=einsatz, Autor=request.user, Zug=zug)
        m.save()
        return _state_antwort(request, einsatz_id)


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
    except Exception:
        return _state_antwort(request, einsatz_id, fehler="Person konnte nicht gelesen werden.", status=400)
    else:
        try:
            p = Person.objects.filter(Einsatz=einsatz).filter(Nachname=nachname).filter(Vorname=vorname)[0]
            p.Notizen = notizen
        except:
            p = Person(Nachname=nachname, Vorname=vorname, Rolle=rolle, Notizen=notizen, Einsatz=einsatz)
        p.save()
        return _state_antwort(request, einsatz_id)


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
    except Exception:
        return _state_antwort(request, einsatz_id, fehler="Ungueltige Fahrzeug- oder Staerkeangabe.", status=400)
    else:
        try:
            f = Fahrzeug.objects.filter(Einsatz=einsatz).filter(Name=name)[0]
            f.Zugfuehrer = zugfuehrer
            f.Gruppenfuehrer = gruppenfuehrer
            f.Mannschaft = mannschaft
            f.Atemschutz = atemschutz
        except:
            f = Fahrzeug(Name=name, Zugfuehrer=zugfuehrer, Gruppenfuehrer=gruppenfuehrer, Mannschaft=mannschaft,
                         Atemschutz=atemschutz, Einsatz=einsatz, Autor=request.user)
        f.save()
        return _state_antwort(request, einsatz_id)


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
            einsatz.Ende = timezone.now()
            einsatz.save()
            ziel = reverse('doku:einsatz', args=[einsatz.Nummer]) + '?auto_pdf=1'
            if _wants_json(request):
                return JsonResponse({
                    'ok': True,
                    'version': EinsatzRevision.get_version(einsatz.Nummer),
                    'redirect': ziel,
                })
            return HttpResponseRedirect(ziel)
    if _wants_json(request):
        return JsonResponse({'ok': False, 'error': 'Einsatz nicht gefunden.'}, status=404)
    return HttpResponseRedirect(reverse('doku:index'))


def meldung(request, einsatz_id):
    einsatz = get_object_or_404(Einsatz, pk=einsatz_id)
    lastID = request.GET.get('lastID', 0)
    neueMeldungen = serializers.serialize("json", Meldung.objects.select_related().filter(Einsatz=einsatz).filter(
        pk__gt=lastID).order_by('Erstellt', 'pk'))
    return JsonResponse(neueMeldungen, safe=False)


# ---------------------------------------------------------------------------
# Live-Synchronisation des kompletten Einsatzzustands
# ---------------------------------------------------------------------------

def _iso(zeitpunkt):
    return zeitpunkt.isoformat() if zeitpunkt else None


def _wants_json(request):
    """Erkennt Anfragen der Live-Oberflaeche (fetch) gegenueber Formular-Posts."""
    if request.headers.get('X-Requested-With') in ('fetch', 'XMLHttpRequest'):
        return True
    return 'application/json' in request.headers.get('Accept', '')


def _state_antwort(request, einsatz_id, fehler=None, status=200):
    """Antwort fuer Schreibzugriffe: JSON fuer fetch, sonst klassischer Redirect."""
    if _wants_json(request):
        daten = {
            'ok': fehler is None,
            'version': EinsatzRevision.get_version(einsatz_id),
        }
        if fehler:
            daten['error'] = str(fehler)
        return JsonResponse(daten, status=status if fehler else 200)
    if fehler:
        return HttpResponse("<h1>Fehler bei der Verarbeitung</h1><h2>" + escape(str(fehler)) + "</h2>")
    return HttpResponseRedirect(reverse('doku:einsatz', args=[einsatz_id]))


def build_einsatz_state(einsatz):
    """Kompletter, fuer alle Clients identischer Zustand eines Einsatzes."""
    meldungen = Meldung.objects.filter(Einsatz=einsatz).select_related('Autor', 'Zug').order_by('-Erstellt', '-pk')
    fahrzeuge = Fahrzeug.objects.filter(Einsatz=einsatz).select_related('Name', 'Name__Zug', 'Name__Ort') \
        .order_by('Name__Zug', 'Name__Ort__Langname', 'Name__Funkname')
    zuege_extra = ZugExtra.objects.filter(Einsatz=einsatz).order_by('Name')
    personen = Person.objects.filter(Einsatz=einsatz).order_by('Nachname', 'Vorname')
    einsatzstellen = Einsatzstellen.objects.filter(Einsatz=einsatz).select_related('Ort', 'Einheit')

    return {
        'version': EinsatzRevision.get_version(einsatz.pk),
        'einsatz': {
            'Nummer': einsatz.Nummer,
            'extNummer': einsatz.extNummer,
            'Einsatzleiter': einsatz.Einsatzleiter,
            'Stichwort': str(einsatz.Stichwort),
            'Adresse': einsatz.Adresse,
            'Ort': einsatz.Ort.Langname,
            'OrtFrei': einsatz.OrtFrei,
            'Erstellt': _iso(einsatz.Erstellt),
            'Ende': _iso(einsatz.Ende),
            'Training': einsatz.Training,
        },
        'meldungen': [{
            'pk': m.pk,
            'Inhalt': m.Inhalt,
            'Wichtig': m.Wichtig,
            'Erstellt': _iso(m.Erstellt),
            'Autor': (m.Autor.get_full_name() or m.Autor.get_username()) if m.Autor else "",
            'Zug': m.Zug.Name if m.Zug else None,
            'Farbe': m.Zug.Farbe if m.Zug else None,
        } for m in meldungen],
        'fahrzeuge': [{
            'pk': f.pk,
            'Funkname': f.Name.Funkname,
            'Typ': f.Name.Typ,
            'Ort': f.Name.Ort.Langname,
            'Zug': f.Name.Zug.Name,
            'Farbe': f.Name.Zug.Farbe,
            'Zugfuehrer': f.Zugfuehrer,
            'Gruppenfuehrer': f.Gruppenfuehrer,
            'Mannschaft': f.Mannschaft,
            'Atemschutz': f.Atemschutz,
        } for f in fahrzeuge],
        'zuege_extra': [{
            'pk': z.pk,
            'Name': z.Name,
            'Zugfuehrer': z.Zugfuehrer,
            'Gruppenfuehrer': z.Gruppenfuehrer,
            'Mannschaft': z.Mannschaft,
            'Atemschutz': z.Atemschutz,
        } for z in zuege_extra],
        'staerken': berechne_summe_personal(einsatz.pk),
        'personen': [{
            'pk': p.pk,
            'Nachname': p.Nachname,
            'Vorname': p.Vorname,
            'Rolle': p.Rolle,
            'Notizen': p.Notizen,
        } for p in personen],
        'einsatzstellen': {
            'gesamt': einsatzstellen.count(),
            'offen': einsatzstellen.filter(Abgeschlossen=None).count(),
        },
    }


def einsatz_state(request, einsatz_id):
    """Liefert den gesamten Einsatzzustand als JSON-Snapshot."""
    einsatz = get_object_or_404(Einsatz, pk=einsatz_id)
    return JsonResponse(build_einsatz_state(einsatz))


async def einsatz_events(request, einsatz_id):
    """Server-Sent-Events: meldet allen Clients Aenderungen am Einsatz.

    Es wird nur die Versionsnummer uebertragen; der Client holt daraufhin den
    kompletten Snapshot. So bleiben alle geoeffneten Geraete auf demselben
    Stand, ohne dass zusaetzliche Infrastruktur (Redis o.ae.) noetig ist.
    """
    try:
        client_version = int(request.GET.get('version', 0))
    except (TypeError, ValueError):
        client_version = 0

    async def event_stream():
        letzte_version = client_version
        letzter_ping = time.monotonic()
        start = time.monotonic()
        # Initialer Kommentar, damit der Browser die Verbindung als offen sieht
        yield ": verbunden\n\n"
        try:
            while time.monotonic() - start < SSE_MAX_LIFETIME:
                aktuelle_version = await EinsatzRevision.objects.filter(Einsatz_id=einsatz_id) \
                    .values_list('Version', flat=True).afirst()
                aktuelle_version = aktuelle_version or 0
                if aktuelle_version != letzte_version:
                    letzte_version = aktuelle_version
                    letzter_ping = time.monotonic()
                    yield "event: change\ndata: " + json.dumps({'version': aktuelle_version}) + "\n\n"
                elif time.monotonic() - letzter_ping > SSE_PING_INTERVAL:
                    letzter_ping = time.monotonic()
                    yield ": ping\n\n"
                await asyncio.sleep(SSE_POLL_INTERVAL)
        except asyncio.CancelledError:
            # Client hat die Verbindung geschlossen
            raise

    antwort = StreamingHttpResponse(event_stream(), content_type='text/event-stream')
    antwort['Cache-Control'] = 'no-cache, no-transform'
    antwort['X-Accel-Buffering'] = 'no'
    antwort['Connection'] = 'keep-alive'
    return antwort


def berechne_summe_personal(einsatz_id):
    """Staerken je Zug (inkl. externer Zuege) und Gesamtsumme."""
    zuege = Zug.objects.all()
    extra_zuege = ZugExtra.objects.filter(Einsatz=einsatz_id)
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
    for zug in extra_zuege:
        summe[zug.Name] = {
            'zugfuehrer': zug.Zugfuehrer,
            'gruppenfuehrer': zug.Gruppenfuehrer,
            'mannschaft': zug.Mannschaft,
            'atemschutz': zug.Atemschutz
        }
        zf += zug.Zugfuehrer
        gf += zug.Gruppenfuehrer
        ms += zug.Mannschaft
        agt += zug.Atemschutz
    summe['Gesamt'] = {
        'zugfuehrer': zf,
        'gruppenfuehrer': gf,
        'mannschaft': ms,
        'atemschutz': agt
    }
    return summe


def summe_Personal(request, einsatz_id):
    return JsonResponse(json.dumps(berechne_summe_personal(einsatz_id)), safe=False)


def add_extra_zug(request, einsatz_id):
    if not request.user.is_authenticated:
        raise PermissionDenied
    einsatz = get_object_or_404(Einsatz, pk=einsatz_id)
    if einsatz.Ende:
        raise PermissionDenied
    try:
        name = request.POST['Name']
        besatzung = request.POST['Besatzung']
        zugfuehrer = int(besatzung.split("/")[0])
        gruppenfuehrer = int(besatzung.split("/")[1])
        mannschaft = int(besatzung.split("/")[2])
        atemschutz = request.POST.get('Atemschutz', 0)
        if atemschutz == "":
            atemschutz = 0
    except Exception:
        return _state_antwort(request, einsatz_id, fehler="Ungueltige Zug- oder Staerkeangabe.", status=400)
    else:
        try:
            z = ZugExtra.objects.filter(Einsatz=einsatz).filter(Name=name)[0]
            z.Zugfuehrer = zugfuehrer
            z.Gruppenfuehrer = gruppenfuehrer
            z.Mannschaft = mannschaft
            z.Atemschutz = atemschutz
        except:
            z = ZugExtra(Name=name, Zugfuehrer=zugfuehrer, Gruppenfuehrer=gruppenfuehrer, Mannschaft=mannschaft,
                         Atemschutz=atemschutz, Einsatz=einsatz)
        z.save()
        return _state_antwort(request, einsatz_id)


def get_ort(request, ort_id):
    o = get_object_or_404(Ort, pk=ort_id)
    o = serializers.serialize('json', [o])
    return JsonResponse(o, safe=False)


def get_stichwort(request, stichwort_id):
    o = get_object_or_404(Stichwort, pk=stichwort_id)
    o = serializers.serialize('json', [o])
    return JsonResponse(o, safe=False)


def get_zug(request, zug_id):
    o = get_object_or_404(Zug, pk=zug_id)
    o = serializers.serialize('json', [o])
    return JsonResponse(o, safe=False)


def toggleNightmode(request):
    if not request.user.is_authenticated:
        raise PermissionDenied
    profil = Profile.objects.get_or_create(user=request.user)[0]
    profil.nightmode = not profil.nightmode
    profil.save()
    ziel = request.META.get('HTTP_REFERER', '/')
    # Offene Weiterleitungen auf fremde Hosts verhindern
    if not url_has_allowed_host_and_scheme(ziel, allowed_hosts={request.get_host()},
                                           require_https=request.is_secure()):
        ziel = '/'
    return HttpResponseRedirect(ziel)


def neuer_benutzer(request):
    if request.method == 'POST':
        if len(User.objects.all()) == 0:
            username = request.POST["username"]
            password = request.POST["password"]
            user = User.objects.create_user(username=username.lower(), password=password, email="")
            user.is_staff = True
            user.is_superuser = True
            user.save()
            return redirect('doku:index')
    raise PermissionDenied


def _build_einsatz_pdf_response(request, einsatz):
    einstellungen = Einstellungen.objects.get_or_create(pk=1)[0]
    alle_Meldungen = Meldung.objects.order_by('-Erstellt', '-pk').filter(Einsatz=einsatz.Nummer)
    eingesetzte_Fahrzeuge = Fahrzeug.objects.filter(Einsatz=einsatz.Nummer).order_by('Name__Zug', 'Name__Ort__Langname',
                                                                                       'Name__Funkname')
    externe_zuege = ZugExtra.objects.filter(Einsatz=einsatz.Nummer).order_by('Name')
    alle_Personen = Person.objects.filter(Einsatz=einsatz.Nummer)
    fahrzeug_gesamt_zugfuehrer = 0
    fahrzeug_gesamt_gruppenfuehrer = 0
    fahrzeug_gesamt_mannschaft = 0
    fahrzeug_gesamt_agt = 0
    for fahrzeug in eingesetzte_Fahrzeuge:
        fahrzeug_gesamt_zugfuehrer += fahrzeug.Zugfuehrer
        fahrzeug_gesamt_gruppenfuehrer += fahrzeug.Gruppenfuehrer
        fahrzeug_gesamt_mannschaft += fahrzeug.Mannschaft
        fahrzeug_gesamt_agt += fahrzeug.Atemschutz
    for zug in externe_zuege:
        fahrzeug_gesamt_zugfuehrer += zug.Zugfuehrer
        fahrzeug_gesamt_gruppenfuehrer += zug.Gruppenfuehrer
        fahrzeug_gesamt_mannschaft += zug.Mannschaft
        fahrzeug_gesamt_agt += zug.Atemschutz

    fahrzeug_gesamt_personal = fahrzeug_gesamt_zugfuehrer + fahrzeug_gesamt_gruppenfuehrer + fahrzeug_gesamt_mannschaft
    dauer = einsatz.getDuration()
    dauer_gesamtsekunden = max(int(dauer.total_seconds()), 0)
    dauer_tage = dauer_gesamtsekunden // 86400
    dauer_stunden = (dauer_gesamtsekunden % 86400) // 3600
    dauer_minuten = (dauer_gesamtsekunden % 3600) // 60

    context = {
        'einsatz': einsatz,
        'einstellungen': einstellungen,
        'alle_Meldungen': alle_Meldungen,
        'eingesetzte_Fahrzeuge': eingesetzte_Fahrzeuge,
        'externe_zuege': externe_zuege,
        'fahrzeug_gesamt_zugfuehrer': fahrzeug_gesamt_zugfuehrer,
        'fahrzeug_gesamt_gruppenfuehrer': fahrzeug_gesamt_gruppenfuehrer,
        'fahrzeug_gesamt_mannschaft': fahrzeug_gesamt_mannschaft,
        'fahrzeug_gesamt_agt': fahrzeug_gesamt_agt,
        'fahrzeug_gesamt_personal': fahrzeug_gesamt_personal,
        'alle_Personen': alle_Personen,
        'dauer_tage': dauer_tage,
        'dauer_stunden': dauer_stunden,
        'dauer_minuten': dauer_minuten,
        'today': timezone.now(),
    }

    pdf = build_einsatz_pdf(context)

    response = HttpResponse(pdf, content_type='application/pdf')
    ext_nummer = einsatz.extNummer if einsatz.extNummer else einsatz.Nummer
    filename = f'Einsatzdoku_{ext_nummer}_{einsatz.Stichwort.Kurzname}_{einsatz.Ort.Kurzname}.pdf'
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    return response


def einsatz_pdf_export(request, einsatz_id):
    """Generiert ein PDF-Export einer Einsatzdokumentation"""
    try:
        einsatz = Einsatz.objects.filter(Nummer=einsatz_id)[0]
    except:
        return HttpResponseServerError("Einsatz nicht gefunden")

    try:
        return _build_einsatz_pdf_response(request, einsatz)
    except Exception as e:
        return HttpResponseServerError(f"Fehler beim Generieren des PDF: {str(e)}")

