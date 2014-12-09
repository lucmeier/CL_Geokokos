__author__ = 'lukasmeier'


'''
Populate MySQL database for the Page app with content from Text + Berg Corpus and Geolocation databases'''
import mysql.connector
import sqlite3
from xml.etree import cElementTree as ET

geokokos_db =  mysql.connector.connect(host="localhost",user="root", passwd="", db ="geokokos_db")


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


    '''Adding Yearbook'''
    print(20 * '*' + 'start adding yearbook' + 20 * '*')
    yearbook_cursor = geokokos_db.cursor()
    yearbook = ET.parse(file_name).getroot()
    yearbook_properties = (yearbook.attrib['id'], file_name[file_name.rfind('/') + 1:-4]) #book id, filename
    yearbook_cursor.execute ('''INSERT INTO Page_yearbook (year, file_name) VALUES(%s, %s)''', yearbook_properties)
    geokokos_db.commit()
    yearbook_cursor.close()

    '''Adding Pages'''
    #fetch last yearbook id used
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
    '''
    Fetch django token id given spanno and yearbook
    '''
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
    '''
    preprocess messy stid no (all of them are messy)
    '''
    if stid.startswith('s'):
        return (stid[1:], 'ST')
    if stid == '0':
        return (stid, 'UKN')
    if stid.startswith('g'):
        return (stid[1:], 'GN') #geonames
    if stid[:2] == ('cg'):
        return (stid, 'UKN')
    if len(stid) == 7:
        try:
            int(stid)
        except ValueError:
            return ('0', 'UKN')
        return (stid, 'ST')
    else:
        return (stid, 'UKN')


def _get_token_ids(spannos, yearbook):
    '''Returns a list containing django token ids given '''
    token_ids = list()
    if spannos is not None:
        for spanno in spannos:
            if spanno is not None:
                if _get_token_id(spanno, yearbook) is not None:
                    token_ids.append(_get_token_id(spanno, yearbook))
    return token_ids


def import_geonames(file_name, yearbook):
    '''
    import geonames for specific yearbook.
    '''
    root = ET.parse(file_name).getroot()
    print(20 * '*' + 'start adding geonames' + 20 * '*')
    counter = 0
    for geoname in root[0]:
        stid = _process_stid(geoname.attrib['stid'])
        if stid[1] == 'ST':
            #retrieve geolocation_id for given swisstopo id
            swisstopo_id = stid[0]
            id_cursor = geokokos_db.cursor()
            id_cursor.execute('''SELECT name, Page_geolocation.type, value, Page_geolocation.id
FROM Page_geolocation_geoloc_reference, Page_GeoLocationReference, Page_geolocation
WHERE Page_geolocation.id = Page_geolocation_geoloc_reference.geolocation_id
    AND Page_geolocation_geoloc_reference.geolocationreference_id = Page_geolocationreference.id AND value = %s''', (swisstopo_id,))
            result = id_cursor.fetchone()

            spannos = geoname.attrib['span'].split(', ') #one or several spannos
            token_ids = _get_token_ids(spannos, yearbook)
            #insert geoname into database/ retrieve id
            if result is not None:
                geoname_cursor = geokokos_db.cursor()
                geoname_cursor.execute('''INSERT INTO Page_geoname (validation_state, geolocation_id)
        VALUES (%s, %s)''', ('n/a', result[3]))
                geokokos_db.commit()
                geoname_cursor.execute('''SELECT id FROM Page_geoname WHERE id = (SELECT MAX(id) FROM Page_geoname)''')
                last_geoname_id_inserted = geoname_cursor.fetchone()[0]
                #insert link table entry
                for token_id in token_ids:
                    geoname_cursor.execute('''INSERT INTO Page_geoname_tokens (geoname_id, token_id) VALUES (%s, %s)''',(last_geoname_id_inserted, token_id))
                    geokokos_db.commit()
                    counter += 1
                    print (token_id, result, 'no', counter)

    if stid[1] == 'UKN':
        #insert entry into GeoNameUnclear table
        spannos = geoname.attrib['span'].split(', ')
        token_ids =

    print(20 * '*' + 'finished adding geonames' + 20 * '*')
    geokokos_db.close()


def get_mapping(source):
    '''
    @:returns dictionary mapping each GeoLocation type (Fels, Wald, Huegel ...) from Swisstopo or other source (Fels, Wald, Huegel ...) to a TB type.
    '''
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


def import_swisstopo_data(file_name):
    swisstopo_db = sqlite3.connect(file_name)


    #Adding Swisstopo Entries
    geokokos_types = get_mapping('swisstopo')
    swisstopo_cursor = swisstopo_db.cursor()
    swisstopo_cursor.execute('''SELECT id, name, ch_y, ch_x, latitude, longitude, kind FROM swisstopo;''')

    #inserting swisstopo geolocation into geokokos_db
    print(20 * '*' + 'start adding geolocations' + 20 * '*')

    for swisstopo_entry in swisstopo_cursor.fetchall():
        geokokos_cursor = geokokos_db.cursor()

        #insert name and type into database/retrieve last geolocation id inserted
        geokokos_cursor.execute('''INSERT INTO Page_geolocation  (name, type) VALUES (%s, %s)''', (swisstopo_entry[1], geokokos_types[swisstopo_entry[6]]))
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
        last_swisstopo_geocoordinates_id_inserted = geokokos_cursor.fetchone()[0]

        #insert swisstopo into database/retrieve id used
        geokokos_cursor.execute('''INSERT INTO Page_geocoordinates(type, latitude, longitude) VALUES (%s, %s, %s)''', ('ST', swisstopo_entry[2], swisstopo_entry[3]))
        geokokos_db.commit()
        geokokos_cursor.execute('''SELECT id FROM Page_geocoordinates WHERE id = (SELECT MAX(id) FROM Page_geocoordinates)''')
        last_wgs_geocoordinates_id_inserted = geokokos_cursor.fetchone()[0]

        #insert many to many relation (coordinates)
        geokokos_cursor.execute('''INSERT INTO Page_geolocation_coordinates(geolocation_id, geocoordinates_id) VALUES (%s, %s)''', (last_geolocation_id_inserted, last_swisstopo_geocoordinates_id_inserted))
        geokokos_cursor.execute('''INSERT INTO Page_geolocation_coordinates(geolocation_id, geocoordinates_id) VALUES (%s, %s)''', (last_geolocation_id_inserted, last_wgs_geocoordinates_id_inserted))
        geokokos_db.commit()

        geokokos_cursor.close()

        print ('added ' + swisstopo_entry[1])

    print(20 * '*' + 'finished adding geolocations' + 20 * '*')
    swisstopo_cursor.close()


#import_corpus('/Users/lukasmeier/Programming/Facharbeit/Text+Berg/Text+Berg_Release_149_v01/XML/SAC/SAC-Jahrbuch_1969_de.xml')

import_swisstopo_data('/Users/lukasmeier/Programming/Facharbeit/protoype/kokos/swisstopo/geolocations.sql')

import_geonames('/Users/lukasmeier/Programming/Facharbeit/Text+Berg/Text+Berg_Release_149_v01/XML/SAC/SAC-Jahrbuch_1969_de-ner.xml', 'SAC-Jahrbuch_1969_de.xml')


