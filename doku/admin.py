from django.contrib import admin

# Register your models here.
from .models import Einsatz, Fahrzeuge, Ort, Stichwort, Meldung, Einstellungen, Zug


class OrtAdmin(admin.ModelAdmin):
    list_display = ('PLZ', 'Kurzname', 'Langname')


class FahrzeugeAdmin(admin.ModelAdmin):
    list_display = ('Funkname', 'Typ', 'Ort')


class StichwortAdmin(admin.ModelAdmin):
    list_display = ('Kurzname', 'Langname')


# admin.site.register(Einsatz)
admin.site.register(Fahrzeuge, FahrzeugeAdmin)
admin.site.register(Ort, OrtAdmin)
admin.site.register(Stichwort, StichwortAdmin)
admin.site.register(Einstellungen)
admin.site.register(Zug)
