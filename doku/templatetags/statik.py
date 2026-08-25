"""Template-Tags fuer statische Dateien mit Cache-Busting.

Der Browser haelt JS/CSS sonst sehr lange im Cache, wodurch nach einem Update
alte Skripte weiterlaufen. Deshalb wird an die URL der Aenderungszeitstempel
der Datei angehaengt: aendert sich die Datei, aendert sich die URL.
"""
import os

from django import template
from django.contrib.staticfiles import finders
from django.templatetags.static import static

register = template.Library()

# Kleiner Cache, damit die Datei nicht bei jedem Rendern angefasst wird
_versionen = {}


@register.simple_tag
def static_v(pfad):
    url = static(pfad)
    try:
        datei = _versionen.get(pfad)
        if datei is None:
            datei = finders.find(pfad) or ""
            _versionen[pfad] = datei
        if datei and os.path.exists(datei):
            return "%s?v=%d" % (url, int(os.path.getmtime(datei)))
    except Exception:
        pass
    return url

