from django.contrib import admin
from .forms import ZugForm, OrtForm

# Register your models here.
from .models import Fahrzeuge, Ort, Stichwort, Einstellungen, Zug, Icon, Einheiten, Einsatzstellen


class FahrzeugeAdmin(admin.ModelAdmin):
    list_display = ('Funkname', 'Typ', 'Ort')


class StichwortAdmin(admin.ModelAdmin):
    list_display = ('Kurzname', 'Langname')


class ZugAdmin(admin.ModelAdmin):
    form = ZugForm


class OrtAdmin(admin.ModelAdmin):
    list_display = ('PLZ', 'Kurzname', 'Langname')
    form = OrtForm


admin.site.register(Fahrzeuge, FahrzeugeAdmin)
admin.site.register(Ort, OrtAdmin)
admin.site.register(Stichwort, StichwortAdmin)
admin.site.register(Einstellungen)
admin.site.register(Zug, ZugAdmin)
admin.site.register(Icon)
admin.site.register(Einheiten)
admin.site.register(Einsatzstellen)
