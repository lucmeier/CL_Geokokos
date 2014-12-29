Aufsetzen von Geokokos

Voraussetzungen
- MySQL 
- Django Version 1.6
- Python 3.4
- Swisstopo-Datenbank (erstellt durch Scriptsammlung von https://pub.cl.uzh.ch:11443/lukasmeier/geokokos_daten/tree/master)
- Git
- local_settings.py (aus https://pub.cl.uzh.ch:11443/lukasmeier/geokokos_daten/tree/master)
- Text+Berg-Korpus lokal vorhanden

Aufsetzen
1. https://github.com/lucmeier/CL_Geokokos klonen
2. local_settings.py in Hauptverzeichnis kopieren (https://pub.cl.uzh.ch:11443/lukasmeier/geokokos_daten/tree/master)
3. MySQL-Datenbank erstellen: CREATE SCHEMA `geokokos_db` DEFAULT CHARACTER SET utf8;
4. manage.py syncdb ausführen. Mit diesem Schritt werden in der Datenbank die entsprechenden Tabellen angelegt. 
5. setUpDatabase-py durchlaufen lassen (Kann einige Zeit dauern):
  1. Swisstopo daten laden: Funktion import_swisstopo_data(path_to_swisstopo.sql). Dieser Schritt ist nur einmal nötig.
  2. gewünschte Korpora laden: Funktion import_corpus(path_to_corpus_file)
  3. geonames der geladenen Korpora laden: Funktion import_geonames(path_to_ner_file, corpus_file_name)
  --> mögliche Aufrufe sind schon am Ende der Datei eingetragen
  Werden Schritte 2 und 3 direkt hintereinander ausgeführt, bricht das Script gelegentlich ab. 
  In einem solchen Fall einfach die Funktion import_geonames nochmals einzeln starten.

Starten
1. Projekt lokal starten: manage.py runserver
2. Administration: http://127.0.0.1:8000/admin/
3. Aufbau der URLs: http://127.0.0.1:8000/kokos/SAC-Jahrbuch_YYYY_LANGCODE/FACSNO

