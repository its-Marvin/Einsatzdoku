from django.urls import path, include

from . import views

app_name = 'doku'
urlpatterns = [
    path('', views.index, name='index'),
    path('Einsatz/all', views.get_aktive_einsaetze, name='alleEinsaetze'),
    path('Einsatz/add', views.neuer_Einsatz, name='neuerEinsatz'),
    path('Ort/<int:ort_id>', views.get_ort, name='getOrt'),
    path('Stichwort/<str:stichwort_id>', views.get_stichwort, name='getStichwort'),
    path('Nachtmodus', views.toggleNightmode, name='toggleNightmode'),
    path('<int:einsatz_id>', views.einsatz, name='einsatz'),
    path('<int:einsatz_id>/Einsatznummer', views.einsatznummer, name='einsatznummer'),
    path('<int:einsatz_id>/Einsatzleiter', views.einsatzleiter, name='einsatzleiter'),
    path('<int:einsatz_id>/Lagekarte', views.lagekarte, name='lagekarte'),
    path('<int:einsatz_id>/Meldung', views.meldung, name='Meldung'),
    path('<int:einsatz_id>/Meldung/neu', views.neue_Meldung, name='neueMeldung'),
    path('<int:einsatz_id>/Personal', views.summe_Personal, name='summePersonal'),
    path('<int:einsatz_id>/Fahrzeug/neu', views.neues_Fahrzeug, name='neuesFahrzeug'),
    path('<int:einsatz_id>/Person/neu', views.neue_Person, name='neuePerson'),
    path('<int:einsatz_id>/Einsatzende', views.einsatzende, name='einsatzende'),
    path('<int:einsatz_id>/OEL', views.oel, name='oel'),
    path('<int:einsatz_id>/OEL/<int:einsatzstelle_id>/notiz', views.oel_einsatzstelle_notiz, name='neueNotiz'),
    path('training/', views.index_training, name='index_training'),
    path('training/Einsatz', views.neues_Training, name='neuesTraining'),
    path('Benutzer/', include('django.contrib.auth.urls')),
]