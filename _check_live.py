import django, os
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "einsatzdoku.settings")
django.setup()
from django.test.utils import setup_test_environment, teardown_test_environment
from django.test.runner import DiscoverRunner
setup_test_environment()
runner = DiscoverRunner(verbosity=0)
alt = runner.setup_databases()
from django.test import Client
from django.contrib.auth import get_user_model
from doku.models import *
u = get_user_model().objects.create_user(username="t", password="x")
o = Ort.objects.create(PLZ=1, Kurzname="A", Langname="AA")
s = Stichwort.objects.create(Kurzname="B1", Langname="Brand")
e = Einsatz.objects.create(Stichwort=s, Adresse="Alt 1", Ort=o)
c = Client(); c.force_login(u)
print("Version vor Aenderung:", EinsatzRevision.get_version(e.pk))
c.post(f"/{e.pk}/Adresse", {"adresse": "Neu 9"})
print("nach Adresse       :", EinsatzRevision.get_version(e.pk))
c.post(f"/{e.pk}/Einsatzleiter", {"einsatzleiter": "Meier"})
print("nach Einsatzleiter :", EinsatzRevision.get_version(e.pk))
c.post(f"/{e.pk}/Einsatznummer", {"extENr": "4711"})
print("nach Einsatznummer :", EinsatzRevision.get_version(e.pk))
import json
st = json.loads(c.get(f"/{e.pk}/state").content)
print("state:", st["version"], st["einsatz"]["Adresse"], st["einsatz"]["Einsatzleiter"], st["einsatz"]["extNummer"])
runner.teardown_databases(alt); teardown_test_environment()
