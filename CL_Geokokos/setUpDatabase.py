__author__ = 'lukasmeier'
'''Populate MySQL database for the Page app with content from Text + Berg Corpus and Geolocation databases'''

import sqlite3
from xml.etree import cElementTree as ET
import mysql.connector

geokokos_db = local_setting = mysql.connector.connect(host="localhost",user="root", passwd="", db ="geokokos_db")

def _get_zip_codes(zip_code, zip_code_file='information_sources/plz_l_20141117.txt'):
    zip_codes = dict()
    with open(zip_code_file, 'r') as f:
        for line in f.readlines():
            line = line.split('\t')
            if line[2] not in zip_codes:
                zip_codes[line[2]] =  line[4]
    return zip_codes.get(zip_code, 'UNKN')

def _open_div(token_id):
    layout_element_cursor = geokokos_db.cursor()
    #insert layoutElement into database/ retrieve id
    layout_element_cursor.execute('''INSERT INTO Page_layoutelement (type) VALUES (%s)''', ('div',))
    geokokos_db.commit()
    layout_element_cursor.execute('''SELECT id FROM Page_layoutelement WHERE id = (SELECT MAX(id) FROM Page_layoutelement)''')
    last_layout_element_id_inserted = layout_element_cursor.fetchone()[0]
    #insert token id layoutElement id into linktable
    layout_element_cursor.execute('''INSERT INTO Page_layoutelement_tokens (layoutelement_id, token_id) VALUES (%s, %s)''', (last_layout_element_id_inserted, token_id))
    geokokos_db.commit()
    layout_element_cursor.close()

def _add_token_to_div(token_id):
    '''Adds token to last layout element that has been created'''
    layout_element_cursor = geokokos_db.cursor()
    layout_element_cursor.execute('''SELECT id FROM Page_layoutelement WHERE id = (SELECT MAX(id) FROM Page_layoutelement)''')
    last_layout_element_id_inserted = layout_element_cursor.fetchone()[0]
    layout_element_cursor.execute('''INSERT INTO Page_layoutelement_tokens (layoutelement_id, token_id) VALUES (%s, %s)''', (last_layout_element_id_inserted, token_id))
    geokokos_db.commit()
    layout_element_cursor.close()

def import_corpus(file_name):
    #Adding Yearbook
    print(20 * '*' + 'start adding yearbook' + 20 * '*')
    yearbook_cursor = geokokos_db.cursor()
    yearbook = ET.parse(file_name).getroot()
    yearbook_properties = (yearbook.attrib['id'], file_name[file_name.rfind('/') + 1:-4]) #book id, filename
    yearbook_cursor.execute ('''INSERT INTO Page_yearbook (year, file_name) VALUES(%s, %s)''', yearbook_properties)
    geokokos_db.commit()
    yearbook_cursor.close()
    #Adding Pages
    yearbook_id_cursor = geokokos_db.cursor()
    yearbook_id_cursor.execute('''SELECT id FROM Page_yearbook WHERE id = (SELECT MAX(id) FROM Page_yearbook)''')
    last_yearbook_id_inserted = yearbook_id_cursor.fetchone()[0]
    yearbook_id_cursor.close()
    #prepare xml processing
    page_tokens_spannos = list()
    yearbook_iterator = iter(ET.iterparse(file_name,  events=('start', 'end')))
    last_div_tokens = list()
    for event, elem in yearbook_iterator:
        if event == 'start' and elem.tag == 'w' and elem.text is not None and 'n' in elem.attrib:
            page_tokens_spannos.append((elem.text, elem.attrib['n']))
        if event =='start' and elem.tag == 'div':
            if len(page_tokens_spannos) == 0:
                last_div_tokens.append(len(page_tokens_spannos))
            else:
                last_div_tokens.append(len(page_tokens_spannos))
        if event == 'start' and elem.tag == 'pb':
            #inserting one page into database
            page_cursor = geokokos_db.cursor()
            n = int()
            if 'facs' in elem.attrib:
                n = elem.attrib['facs']
            else:
                n = -1
            page_properties = ('dummy_scan_url', n, last_yearbook_id_inserted, False)
            page_cursor.execute('''INSERT INTO Page_page (scan_url, pb_n, yearbook_id, correct) VALUES (%s, %s, %s, %s)''', page_properties)
            geokokos_db.commit()
            #retrieving last page_id inserted
            page_cursor.execute('''SELECT id FROM Page_page WHERE id = (SELECT MAX(id) FROM Page_page)''')
            last_page_id_inserted = page_cursor.fetchone()[0]
            page_cursor.close()
            #adding tokens to page
            last_token_id_inserted = int
            for i in enumerate(page_tokens_spannos):
                token_cursor = geokokos_db.cursor()
                token_properties = (page_tokens_spannos[i[0]][0], page_tokens_spannos[i[0]][1], last_page_id_inserted)
                token_cursor.execute('''INSERT INTO Page_token (content, tb_key, page_id) VALUES (%s, %s, %s)''', token_properties)
                geokokos_db.commit()
                token_cursor.execute('''SELECT id FROM Page_token WHERE id = (SELECT MAX(id) FROM Page_token)''')
                last_token_id_inserted = token_cursor.fetchone()[0]
                if i[0] == 0:
                    _open_div(last_token_id_inserted)
                elif i[0] in last_div_tokens:
                    _open_div(last_token_id_inserted)
                else:
                    _add_token_to_div(last_token_id_inserted)
                token_cursor.close()
            print ('added page ' +  n)
            last_div_tokens.clear()
            page_tokens_spannos.clear()
    geokokos_db.close()
    print(20 * '*' + 'finished adding yearbook' + 20 * '*')

def _get_token_id(spanno, yearbook):
    '''Fetch django token id given spanno and yearbook'''
    geokokos_db =  mysql.connector.connect(host="localhost",user="root", passwd="", db ="geokokos_db")
    token_id_cursor = geokokos_db.cursor()
    token_id_cursor.execute('''SELECT Page_token.id FROM Page_token, Page_page, Page_yearbook
WHERE tb_key = %s AND Page_page.id = Page_token.page_id AND Page_yearbook.id = Page_page.yearBook_id
AND Page_yearbook.file_name = %s''', (spanno, yearbook[:-4]))
    result =  token_id_cursor.fetchone()
    geokokos_db.close()
    if result is not None:
        return result[0]

def  _process_stid(stid):
    '''preprocess messy stid no (all of them are messy'''
    if stid.startswith('s') and stid != 's23':
        return (stid[1:], 'ST')
    if stid == '0':
        return (stid, 'UNKN')
    if stid.startswith('g') and stid != 'g23':
        return (stid[1:], 'UNKN') #geonames
    if stid == 's23' or stid == 'g23' or stid == '23' or stid.startswith('cg'):
        return (stid, 'AMBG')
    if not stid.startswith('s') and not stid.startswith('g') and len(stid) == 4:
        return (stid, 'ZIP')
    if len(stid) == 7:
        try:
            int(stid)
        except ValueError:
            return ('0', 'UNKN')
        return (stid, 'ST')
    else:
        return (stid, 'UNKN')

def _get_token_ids(spannos, yearbook):
    '''Returns a list containing django token ids given '''
    token_ids = list()
    if spannos is not None:
        for spanno in spannos:
            if spanno is not None:
                if _get_token_id(spanno, yearbook) is not None:
                    token_ids.append(_get_token_id(spanno, yearbook))
    return token_ids

def _get_geolocation_id(stid):
    cursor = geokokos_db.cursor(buffered=True)
    stid_type = stid[1]
    if stid_type == 'ST' or stid_type == 'GN':
        swisstopo_id = stid[0]
        cursor.execute('''SELECT name, Page_geolocation.type, value, Page_geolocation.id
FROM Page_geolocation_geoloc_reference, Page_GeoLocationReference, Page_geolocation
WHERE Page_geolocation.id = Page_geolocation_geoloc_reference.geolocation_id
    AND Page_geolocation_geoloc_reference.geolocationreference_id = Page_geolocationreference.id AND value = %s''', (swisstopo_id,))
        return cursor.fetchone()[3]
    elif stid_type == 'ZIP':
        place_name = _get_zip_codes(stid[0])
        cursor.execute("""SELECT name, Page_geolocation.type, value, Page_geolocation.id
FROM Page_geolocation_geoloc_reference, Page_GeoLocationReference, Page_geolocation
WHERE Page_geolocation.id = Page_geolocation_geoloc_reference.geolocation_id
    AND Page_geolocation_geoloc_reference.geolocationreference_id = Page_geolocationreference.id AND name=%s and Page_geolocation.type = 'PL'""", (place_name,))
        ret = cursor.fetchone()
        if ret is None or len(ret) !=4:
            return None
        else:
            return ret[3]

def _create_geoname(geolocation_id, token_ids):
    cursor = geokokos_db.cursor(buffered=True)
    cursor.execute('''INSERT INTO Page_geoname (geolocation_id, validation_state, user_notes)
        VALUES (%s, %s, %s)''', (geolocation_id, 'uned', ''))
    geokokos_db.commit()
    cursor.execute('''SELECT id FROM Page_geoname WHERE id = (SELECT MAX(id) FROM Page_geoname)''')
    last_geoname_id_inserted = cursor.fetchone()[0]
    #insert link table entry
    for token_id in token_ids:
        cursor.execute('''INSERT INTO Page_geoname_tokens (geoname_id, token_id) VALUES (%s, %s)''',(last_geoname_id_inserted, token_id))
        geokokos_db.commit()
    cursor.close()

def _create_geoname_unclear(type, token_ids):
    cursor = geokokos_db.cursor(buffered=True)
    cursor.execute('''INSERT INTO Page_geonameunclear (type, user_notes, validation_state) VALUES (%s, %s, %s)''', (type, '', 'uned'))
    geokokos_db.commit()
    cursor.execute('''SELECT id FROM Page_geonameunclear WHERE id = (SELECT MAX(id) FROM Page_geonameunclear)''')
    last_geoname_unclear_id_inserted = cursor.fetchone()[0]
    for token_id in token_ids:
        cursor.execute('''INSERT INTO Page_geonameunclear_tokens (geonameunclear_id, token_id) VALUES (%s, %s)''', (last_geoname_unclear_id_inserted, token_id))
        geokokos_db.commit()
    cursor.close()

def import_geonames(file_name, yearbook):
    '''import geonames for specific yearbook. '''
    root = ET.parse(file_name).getroot()
    print(20 * '*' + 'start adding geonames' + 20 * '*')
    for geoname in root[0]:
        stid = _process_stid(geoname.attrib['stid'])
        spannos = geoname.attrib['span'].split(', ') #one or several spannos
        token_ids = _get_token_ids(spannos, yearbook)
        if stid[1] == 'ST' or stid[1] == 'ZIP':
            geolocation_id = _get_geolocation_id(stid)
            if geolocation_id is not None:
                _create_geoname(geolocation_id, token_ids)
            print (stid[1], 'geolocation:', geolocation_id, '/ token ids:', token_ids)
        else:
            _create_geoname_unclear(stid[1], token_ids)
    geokokos_db.close()

def import_country_codes(file_name):
    abbr_country_name_pairs = list()
    with open(file_name, 'r') as f:
        lines = f.readlines()
        for line in lines:
            abbr = line[:2]
            name = line[3:]
            abbr_country_name_pairs.append((abbr, name))
    for country in abbr_country_name_pairs:
        geokokos_cursor = geokokos_db.cursor()
        #insert name and type into database/retrieve last geolocation id inserted
        geokokos_cursor.execute('''INSERT INTO Page_country  (abbreviation, full_name) VALUES (%s, %s)''', (country[0], country[1]))
        geokokos_db.commit()
        geokokos_cursor.close()


def fill_in_swiss_cantons():
    geokokos_cursor = geokokos_db.cursor()
    geokokos_cursor.execute('''SELECT id FROM Page_country WHERE abbreviation="CH";''')
    switzerland_id = geokokos_cursor.fetchone()[0]

    cantons = {'AG': 'Aargau', 'AI' : 'Appenzell Innerrhoden', 'AR': 'Appenzell Ausserrhoden',
               'BE' : 'Bern', 'BL' : 'Basel-Land', 'BS' : 'Basel-Stadt', 'FR' : 'Fribourg',
               'GE' : 'Genève', 'GL' : 'Glarus', 'GR' : 'Graubünden', 'JU' : 'Jura',
               'LU' : 'Luzern', 'NE' : 'Neuchâtel', 'NW' : 'Nidwalden', 'OW' : 'Obwalden',
               'SG' : 'Sankt Gallen', 'SH' : 'Schaffhausen', 'SO' : 'Solothurn', 'SZ' : 'Schwyz',
               'TG' : 'Thurgau', 'TI' : 'Ticino', 'UR' : 'Uri', 'VS' : 'Valais', 'VD' : 'Vaud', 'ZG' : 'Zug', 'ZH' : 'Zürich', 'FL' : 'Fürstentum Liechtenstein', 'A' : 'Österreich', 'I' : "Campione d'Italia"}
    for canton in cantons.items():
        geokokos_cursor.execute('''INSERT INTO Page_region  (abbreviation, full_name, country_id) VALUES (%s, %s, %s)''', (canton[0], canton[1], switzerland_id))
        geokokos_db.commit()
    geokokos_cursor.close()



def get_mapping(source):
    '''Returns dictionary mapping each GeoLocation type (Fels, Wald, Huegel ...) from Swisstopo or other source (Fels, Wald, Huegel ...) to a TB type.'''
    mountain, glacier, lake, city, valley, mountain_cabin, misc = 'MO', 'GL', 'LA', 'PL', 'VL', 'MC', 'MS' #Text + Berg GeoTypes (Misc has been added)
    if source == 'swisstopo':
        return {
            'Fels': mountain,
            'Wald' : misc,
            'Huegel' : mountain,
            'Flurname' : city,
            'Einzelhaus' : city,
            'Graben' : misc,
            'Streusiedl' : city,
            'Weiler' : city,
            'Zoll' : misc,
            'Nebental' : valley,
            'KGemeinde' : city,
            'Huette' : mountain_cabin,
            'Fusspass' : mountain,
            'Quelle' : misc,
            'KBach' : misc,
            'Brunnen' : misc,
            'Weg' : misc,
            'Turm' : misc,
            'Fluss' : misc,
            'Bach' : misc,
            'Gebiet' : city,
            'Sportanl' : misc,
            'Bruecke' : misc,
            'Weiher' : lake,
            'Industrie' : city,
            'MOrtschaft' : city,
            'HistOrt' : city,
            'KSee' : lake,
            'Ruine' : misc,
            'MGemeinde' : city,
            'Hoehle' : misc,
            'OeffGeb' : misc,
            'Sumpf' : misc,
            'Schloss' : misc,
            'Strassenpas' : misc,
            'KOrtschaft' : city,
            'Bahnhof' : misc,
            'Friedhof' : misc,
            'Kirche' : misc,
            'GGemeinde' : city,
            'Strasse' : misc,
            'Flugplatz' : misc,
            'GSee' : lake,
            'Wasserfall' : misc,
            'Park' : misc,
            'Hafen' : misc,
            'Denkmal' : misc,
            'Grat' : misc,
            'GOrtschaft' : city,
            'HGemeinde' : city,
            'Hotel' : misc,
            'Haupttal' : valley,
            'ErrBlock' : misc,
            'Tunnel' : misc,
            'Massiv' : mountain,
            'Stausee' : lake,
            'KGipfel' : mountain,
            'Gletscher' : glacier,
            'GGipfel' : mountain,
            'HGipfel' : mountain,
            'Staumauer' : misc
                }
    if source == 'geoname':
        return {

        }

def _get_swiss_cantons():
    geokokos_cursor = geokokos_db.cursor()
    geokokos_cursor.execute('''SELECT Page_region.id, Page_region.abbreviation FROM Page_region, Page_country WHERE country_id = Page_country.id AND
Page_country.abbreviation = 'CH';''', )
    res = geokokos_cursor.fetchall()
    cantons = dict()
    for canton in res:
        cantons[canton[1]] = canton[0]
    geokokos_cursor.close()
    return cantons

def _get_country_id(country_code):
    geokokos_cursor = geokokos_db.cursor(buffered=True)
    geokokos_cursor.execute('''SELECT id FROM Page_country WHERE abbreviation=%s''', (country_code,))
    res = geokokos_cursor.fetchone()
    geokokos_cursor.close()
    if res is not None:
        return res[0]
    else:
        return False


def _get_region_id(region_name, country_code):
    geokokos_cursor = geokokos_db.cursor(buffered=True)
    geokokos_cursor.execute('''SELECT * FROM Page_region WHERE full_name=%s''', (region_name,))
    res = geokokos_cursor.fetchall()
    geokokos_cursor.close()
    if not res is None and len(res) == 1:
        geokokos_cursor.close()
        return res[0][0]
    else:
        geokokos_cursor = geokokos_db.cursor()
        if not _get_country_id(country_code):
            return False
        geokokos_cursor.execute('''INSERT INTO Page_region  (abbreviation, full_name, country_id) VALUES (%s, %s, %s)''', ('', region_name, _get_country_id(country_code)))
        geokokos_db.commit()
        geokokos_cursor.execute('''SELECT id FROM Page_region WHERE id = (SELECT MAX(id) FROM Page_region)''')
        last_province_id_inserted = geokokos_cursor.fetchone()[0]
        geokokos_cursor.close()
        return last_province_id_inserted



def import_geoname_data(file_name):
    geonames_db = sqlite3.connect(file_name)
    geonames_cursor = geonames_db.cursor()
    geonames_cursor.execute('''SELECT * FROM geonames;''')
     #inserting swisstopo geolocation into geokokos_db
    print(20 * '*' + 'start adding geolocations (Geonames)' + 20 * '*')
    for geoname_entry in geonames_cursor.fetchall():
        geokokos_cursor = geokokos_db.cursor()
        #insert name and type into database/retrieve last geolocation id inserted
        if geoname_entry[2] == 'CH' or geoname_entry[2] == 'FL' or not _get_region_id(geoname_entry[3], geoname_entry[2]):#to catch Swiss-related stuff and exceptions
            continue
        geokokos_cursor.execute('''INSERT INTO Page_geolocation  (name, type, region_id) VALUES (%s, %s, %s)''', (geoname_entry[1], 'MO', _get_region_id(geoname_entry[3], geoname_entry[2])))
        geokokos_db.commit()
        geokokos_cursor.execute('''SELECT id FROM Page_geolocation WHERE id = (SELECT MAX(id) FROM Page_geolocation)''')
        last_geolocation_id_inserted = geokokos_cursor.fetchone()[0]
        #insert geoname id into database/ retrieve last external reference id inserted
        geokokos_cursor.execute('''INSERT INTO Page_geolocationreference (value, type) VALUES (%s, %s)''', (geoname_entry[0], 'GN'))
        geokokos_db.commit()
        geokokos_cursor.execute('''SELECT id FROM Page_geolocation WHERE id = (SELECT MAX(id) FROM Page_geolocation)''')
        last_reference_id_inserted = geokokos_cursor.fetchone()[0]
        #insert many to many relation (geoloc reference [swisstopo|geonames|...)
        geokokos_cursor.execute('''INSERT INTO Page_geolocation_geoloc_reference (geolocation_id, geolocationreference_id) VALUES (%s, %s)''', (last_geolocation_id_inserted, last_reference_id_inserted))
        geokokos_db.commit()
        #insert wgs coordinates into database/retrieve id used
        geokokos_cursor.execute('''INSERT INTO Page_geocoordinates(type, longitude, latitude) VALUES (%s, %s, %s)''', ('WGS', geoname_entry[5], geoname_entry[4]))
        geokokos_db.commit()
        geokokos_cursor.execute('''SELECT id FROM Page_geocoordinates WHERE id = (SELECT MAX(id) FROM Page_geocoordinates)''')
        last_wgs_geocoordinates_id_inserted = geokokos_cursor.fetchone()[0]
        #insert many to many relation (coordinates)
        #geokokos_cursor.execute('''INSERT INTO Page_geolocation_coordinates(geolocation_id, geocoordinates_id) VALUES (%s, %s)''', (last_geolocation_id_inserted, last_swisstopo_geocoordinates_id_inserted))
        geokokos_cursor.execute('''INSERT INTO Page_geolocation_coordinates(geolocation_id, geocoordinates_id) VALUES (%s, %s)''', (last_geolocation_id_inserted, last_wgs_geocoordinates_id_inserted))
        geokokos_db.commit()
        geokokos_cursor.close()
        print ('added ' + geoname_entry[1])
    print(20 * '*' + 'finished adding geolocations' + 20 * '*')

    geonames_cursor.close()




def import_swisstopo_data(file_name):
    swisstopo_db = sqlite3.connect(file_name)
    #Adding Swisstopo Entries
    geokokos_types = get_mapping('swisstopo')
    swisstopo_cursor = swisstopo_db.cursor()
    swisstopo_cursor.execute('''SELECT id, name, ch_y, ch_x, latitude, longitude, kind, canton FROM swisstopo;''')
    #inserting swisstopo geolocation into geokokos_db
    print(20 * '*' + 'start adding geolocations (Swisstopo)' + 20 * '*')
    cantons = _get_swiss_cantons()
    for swisstopo_entry in swisstopo_cursor.fetchall():
        geokokos_cursor = geokokos_db.cursor()
        #insert name and type into database/retrieve last geolocation id inserted
        geokokos_cursor.execute('''INSERT INTO Page_geolocation  (name, type, region_id) VALUES (%s, %s, %s)''', (swisstopo_entry[1], geokokos_types[swisstopo_entry[6]], cantons[swisstopo_entry[7]]))
        geokokos_db.commit()
        geokokos_cursor.execute('''SELECT id FROM Page_geolocation WHERE id = (SELECT MAX(id) FROM Page_geolocation)''')
        last_geolocation_id_inserted = geokokos_cursor.fetchone()[0]
        #insert swisstopo id into database/ retrieve last external reference id inserted
        geokokos_cursor.execute('''INSERT INTO Page_geolocationreference (value, type) VALUES (%s, %s)''', (swisstopo_entry[0], 'ST'))
        geokokos_db.commit()
        geokokos_cursor.execute('''SELECT id FROM Page_geolocation WHERE id = (SELECT MAX(id) FROM Page_geolocation)''')
        last_reference_id_inserted = geokokos_cursor.fetchone()[0]
        #insert many to many relation (geoloc reference [swisstopo|geonames|...)
        geokokos_cursor.execute('''INSERT INTO Page_geolocation_geoloc_reference (geolocation_id, geolocationreference_id) VALUES (%s, %s)''', (last_geolocation_id_inserted, last_reference_id_inserted))
        geokokos_db.commit()
        #insert wgs coordinates into database/retrieve id used
        geokokos_cursor.execute('''INSERT INTO Page_geocoordinates(type, latitude, longitude) VALUES (%s, %s, %s)''', ('WGS', swisstopo_entry[4], swisstopo_entry[5]))
        geokokos_db.commit()
        geokokos_cursor.execute('''SELECT id FROM Page_geocoordinates WHERE id = (SELECT MAX(id) FROM Page_geocoordinates)''')
        last_wgs_geocoordinates_id_inserted = geokokos_cursor.fetchone()[0]
        #insert swisstopo into database/retrieve id used
        """geokokos_cursor.execute('''INSERT INTO Page_geocoordinates(type, latitude, longitude) VALUES (%s, %s, %s)''', ('ST', swisstopo_entry[2], swisstopo_entry[3]))
        geokokos_db.commit()
        geokokos_cursor.execute('''SELECT id FROM Page_geocoordinates WHERE id = (SELECT MAX(id) FROM Page_geocoordinates)''')
        last_swisstopo_geocoordinates_id_inserted = geokokos_cursor.fetchone()[0]"""
        #insert many to many relation (coordinates)
        #geokokos_cursor.execute('''INSERT INTO Page_geolocation_coordinates(geolocation_id, geocoordinates_id) VALUES (%s, %s)''', (last_geolocation_id_inserted, last_swisstopo_geocoordinates_id_inserted))
        geokokos_cursor.execute('''INSERT INTO Page_geolocation_coordinates(geolocation_id, geocoordinates_id) VALUES (%s, %s)''', (last_geolocation_id_inserted, last_wgs_geocoordinates_id_inserted))
        geokokos_db.commit()
        geokokos_cursor.close()
        print ('added ' + swisstopo_entry[1])
    print(20 * '*' + 'finished adding geolocations' + 20 * '*')
    swisstopo_cursor.close()


#import_country_codes('/Users/lukasmeier/Programming/Facharbeit/CL_Geokokos/CL_Geokokos/information_sources/country.csv')
#fill_in_swiss_cantons()
#import_swisstopo_data('/Users/lukasmeier/Programming/Facharbeit/geokokos_daten/swisstopo/geolocations.sql')
import_geoname_data('/Users/lukasmeier/Programming/Facharbeit/geokokos_daten/geonames/geonames.sql')

#import_corpus('/Users/lukasmeier/Programming/Facharbeit/Text+Berg/Text+Berg_Release_149_v01/XML/SAC/SAC-Jahrbuch_1969_de.xml')

#import_geonames('/Users/lukasmeier/Programming/Facharbeit/Text+Berg/Text+Berg_Release_149_v01/XML/SAC/SAC-Jahrbuch_1969_de-ner.xml', 'SAC-Jahrbuch_1969_de.xml')

