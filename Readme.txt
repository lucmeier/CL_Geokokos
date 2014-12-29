Aufsetzen von Geokokos

Voraussetzungen
MySQL 
Django Version 1.6
Python 3.4
Swisstopo-Datenbank (erstellt durch Scriptsammlung von https://pub.cl.uzh.ch:11443/siclemat/geokokosdaten/)
Git
local_settings.py (aus https://pub.cl.uzh.ch:11443/siclemat/geokokosdaten/)
Text+Berg-Korpus lokal vorhanden

Aufsetzen
https://github.com/lucmeier/CL_Geokokos laden
local_settings.py in Hauptverzeichnis kopieren
MySQL-Datenbank erstellen: CREATE SCHEMA `geokokos_db` DEFAULT CHARACTER SET utf8;
manage.py -syncdb ausführen
setUpDatabase-py durchlaufen lassen

Starten
Projekt lokal starten: manage.py -runserver
Administration: http://127.0.0.1:8000/admin/
Aufbau der URLs: http://127.0.0.1:8000/kokos/SAC-Jahrbuch_YYYY_LANGCODE/FACSNO

