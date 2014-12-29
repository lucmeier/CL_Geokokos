from django.db import models
from django.core import exceptions
import json

class Yearbook(models.Model):
    file_name = models.CharField(max_length=30)
    year = models.CharField(max_length=10)

    def __str__(self):
        return self.file_name


class Page(models.Model):
    scan_url = models.CharField(max_length=50)  # file name of image scan
    pb_n = models.IntegerField(verbose_name='Facsimile No')
    yearbook = models.ForeignKey(Yearbook)
    correct = models.BooleanField(blank=True)

    def __str__(self):
        return self.yearbook.file_name + ': Page ' + str(self.pb_n)


class PageManager(models.Manager):
    '''Contains methods that are needed to display pages.'''

    def __init__(self, yrb, facs_no):
        self.facs_no = int(facs_no)
        self.yearbook = Yearbook.objects.get(file_name=yrb)
        self.page = Page.objects.get(yearbook=self.yearbook.id, pb_n=self.facs_no)
        self.tokens = Token.objects.all().filter(page=self.page)
        self.geonames = GeoName.objects.all().filter(tokens=self.tokens)
        self.unclear_geonames = GeoNameUnclear.objects.all().filter(tokens=self.tokens)

    def get_previous_following(self):
        '''Return facs_no of previous and following page. Returns current facs_no if there is no previous or following page in yearbook.'''
        return self._get_previous(), self._get_following()

    def get_first_last(self):
        '''Returns facs_no of first and last page in yearbook'''
        pages = list(Page.objects.all().filter(yearbook=self.yearbook))
        return pages[0].pb_n, pages[-1].pb_n

    def spans_list(self):
        '''Returns a list of span elements containing three element (token content, token type, token/geoname id) tuples for a given page.'''
        pg = self.page
        tokens = Token.objects.all().filter(page=pg)
        layoutElements = LayoutElement.objects.all().filter(tokens=tokens)
        geonames = GeoName.objects.all().filter(tokens=tokens)
        geonames_token_ids = list()
        for geoname in geonames:
            for token in geoname.tokens.all():
                geonames_token_ids.append(token.id)
        unclear_geonames = GeoNameUnclear.objects.all().filter(tokens=tokens)
        unknown_geonames_token_ids = list()
        ambiguous_geonames_token_ids = list()
        for unclear_geoname in unclear_geonames:
            for token in unclear_geoname.tokens.all():
                if unclear_geoname.type == 'UNKN':
                    unknown_geonames_token_ids.append((token.id))
                if unclear_geoname.type == 'AMBG':
                    ambiguous_geonames_token_ids.append(token.id)
        layoutElements_unique = list()
        for entry in layoutElements:
            if entry not in layoutElements_unique:
                layoutElements_unique.append(entry)
        divs = list()
        for div in layoutElements_unique:
            tkns = list()
            before = str()
            for tkn in div.tokens.all():
                if tkn.id in geonames_token_ids:
                    tkns.append(('gn', geonames.all().filter(tokens = tkn)[0].id, tkn.spaced_token(before)))
                elif tkn.id in unknown_geonames_token_ids:
                    tkns.append(('unkn', unclear_geonames.all().filter(tokens = tkn)[0].id, tkn.spaced_token(before)))
                elif tkn.id in ambiguous_geonames_token_ids:
                    tkns.append(('ambg', unclear_geonames.all().filter(tokens = tkn)[0].id, tkn.spaced_token(before)))
                else:
                    tkns.append(('token', tkn.id, tkn.spaced_token(before)))
                before = tkn.content
            divs.append(tkns)
        return divs

    def _get_previous(self):
        '''Returns facs_no of preceeding page .'''
        previous = self.page.id - 1
        try:
            previous_page = Page.objects.get(id=previous)
        except exceptions.ObjectDoesNotExist:
            return self.facs_no
        if previous_page.yearbook_id != self.yearbook.id:
            return self.facs_no
        return previous_page.pb_n

    def _get_following(self):
        '''Returns facs no of following page'''
        following = self.page.id + 1
        try:
            following_page = Page.objects.get(id=following)
        except exceptions.ObjectDoesNotExist:
            return self.facs_no
        if following_page.yearbook_id != self.yearbook.id:
            return self.facs_no
        return following_page.pb_n

    def get_sentence(self, token_id):
        '''Returns sentence containing given token.'''
        token = Token.objects.get(id=token_id)
        pg = token.page
        tb_sentence_no = token.tb_key[:token.tb_key.rfind('-')]
        page_tokens = Token.objects.all().filter(page=pg)
        sentence = list()
        for token in page_tokens:
            if token.tb_key.startswith(tb_sentence_no):
                sentence.append(token.spaced_token())
        return ''.join(sentence)


    def process_checkboxes(self, verify_or_delete, unverify):
        '''Writes user changes into database and returns updated geonames.'''
        for task in verify_or_delete:
            _id = task[0].split('_')[1]
            if task[0].startswith('GN'):
                geoname= GeoName.objects.all().filter(id=_id)[0]
                if task[1] == 'delete':
                    geoname.validation_state = 'del'
                if task[1] == 'verify':
                    geoname.validation_state = 'verif'
                geoname.save()
            if task[0].startswith('UNKN') or task[0].startswith('AMBG'):
                geoname_unclear = GeoNameUnclear.objects.all().filter(id=_id)[0]
                if task[1] == 'delete':
                    geoname_unclear.validation_state = 'del'
                if task[1] == 'verify':
                    geoname_unclear.validation_state = 'verif'
                geoname_unclear.save()
        for task in unverify:
            _id = task.split('_')[1]
            if task.startswith('GN'):
                geoname= GeoName.objects.all().filter(id=_id)[0]
                geoname.validation_state = 'uned'
                geoname.save()
            if task.startswith('UNKN') or task.startswith('AMBG'):
                geoname_unclear = GeoNameUnclear.objects.all().filter(id=_id)[0]
                geoname_unclear.validation_state = 'uned'
                geoname_unclear.save()

    def get_geonames(self):
        '''Returns  list of (unclear and clear) geonames  in page. Each item is a
        (type, sort_id, id, name, verified['checked'|'']) tuple. id depends on type.
        gn: geoname.id/ unkn|ambg: unclear_geoname_id.
        Name is lemma name for gn type and name as in token(s) for ambg or unkn type.'''
        clear_unclear_geonames = list()
        for clear_geoname in self.geonames:
            if clear_geoname.validation_state == 'del':
                continue
            sort_id = clear_geoname.tokens.all()[0].id
            clear_geoname_verified = str()
            if clear_geoname.validation_state == 'verif':
                clear_geoname_verified = 'checked='
            clear_unclear_geonames.append(('GN', sort_id, clear_geoname.id, clear_geoname.geolocation.name, clear_geoname_verified))
        for unclear_geoname in self.unclear_geonames:
            if unclear_geoname.validation_state == 'del':
                continue
            sort_id = unclear_geoname.tokens.all()[0].id
            token_content = list()
            for token in unclear_geoname.tokens.all():
                token_content.append(token.content)
            token_content = ' '.join(token_content)
            unclear_geoname_verified = str()
            if unclear_geoname.validation_state == 'verif':
                unclear_geoname_verified = 'checked='
            clear_unclear_geonames.append((unclear_geoname.type, sort_id, unclear_geoname.id, token_content, unclear_geoname_verified))
        return sorted(list(set(clear_unclear_geonames)), key=lambda srt : srt[1])

    def get_coordinates(self):
        '''Returns a list of (geoname.geolocation.name, geoname.geolocation.type, coordinates) tuples for page.'''
        coordinates = list()
        for geoname in self.geonames:
            longitude = geoname.geolocation.coordinates.all().get(type='WGS').longitude
            latitude = geoname.geolocation.coordinates.all().get(type='WGS').latitude
            coordinates.append((geoname.geolocation.name,geoname.geolocation.type, (longitude, latitude)))
        return coordinates

    def get_coordinates_java_script_array(self):
        '''Returns a '''
        js_list = list()
        colour = {'MC' : 'pink', 'MO' : 'red', 'MS' : 'green', 'LK' : 'blue', 'PL' : 'green', 'GL' : 'pink', 'VL' : 'pink'}
        for entry in self.get_coordinates():
            js_dict = dict()
            js_dict['name'] = entry[0]
            js_dict['longitude'] = str(entry[2][0])
            js_dict['latitude'] = str(entry[2][1])
            js_dict['colour'] = colour.get(entry[1], 'orange')
            js_list.append(js_dict)
        return json.dumps(js_list)

    def get_centroid(self):
        '''Returns averaged center of map (needed for rendering map in a reasonable fashion.'''
        if len(self.get_coordinates()) == 0:
            return(46.799558, 8.235897) #geographic centre of Switzerland
        latitude = 0
        longitude = 0
        coordinates = [coordinate_pair[2] for coordinate_pair in self.get_coordinates()]
        for coordinate_pair in coordinates:
            latitude += coordinate_pair[0]
            longitude += coordinate_pair[1]
        return (float(longitude/len(coordinates)), float(latitude/ len(coordinates)))

class Token(models.Model):
    content = models.CharField(max_length=200)  # what the token contains
    tb_key = models.CharField(max_length=15,
                              verbose_name='Text + Berg No')  # Text+Berg Token id: article-sentence-token
    page = models.ForeignKey(Page)

    def __str__(self):
        return self.tb_key + ': ' + self.content

    def __lt__(self, other):
        '''sorting method'''
        return self.tb_key < other.tb_key

    def spaced_token(self, before):
        '''Returns token with correctly added spaces before or after it. '''
        if len(self.content) == 1 and self.content in ").,;:!?»'":
            return self.content
        if len(self.content) == 1 and self.content in '(«':
            return ' ' + self.content
        if len(before) == 1 and (before == '«' or before == '('):
            return self.content
        else:
            return ' ' + self.content


class GeoCoordinates(models.Model):
    '''Representing coordinates (either Swisstopo, WGS84 or None)'''
    type = models.CharField(max_length=3, choices=(('ST', 'Swisstopo'), ('WGS', 'WGS_84'), ('NO', 'None')),
                            default='NO')
    longitude = models.DecimalField(max_digits=25, decimal_places=15, default=0)
    latitude = models.DecimalField(max_digits=25, decimal_places=15, default=0)

    def __str__(self):
        return self.type + ':' + str(self.latitude) + ', ' + str(self.longitude)


class GeoLocationReference(models.Model):
    '''Representing Swisstopo, GeoName, or other reference to other data such as Swisstopo or Geoname.'''
    type = models.CharField(max_length=2,
                            choices=(('ST', 'Swisstopo'), ('GN', 'GeoNames'), ('OT', 'Other'), ('NO', 'None')),
                            default='NO')
    value = models.CharField(max_length=15, default='None')

    def __str__(self):
        return self.type + ': ' + self.value


class GeoLocation(models.Model):
    name = models.CharField(max_length=100)
    coordinates = models.ManyToManyField(GeoCoordinates, related_name='Coordinates')
    type = models.CharField(max_length=2, choices=(
    ('MO', 'Mountain'), ('GL', 'Glacier'), ('PL', 'Place'), ('RI', 'River'), ('LA', 'Lake'), ('VL', 'Valley'),
    ('MC', 'Mountain Cabin'), ('MS', 'Misc')))
    geoloc_reference = models.ManyToManyField(GeoLocationReference, related_name='Swisstopo, Geoname or other id')

    def __str__(self):
        return self.name + ' (' + self.type + ')'

    class Meta:
        ordering = ['name', 'type']


class GeoName(models.Model):
    tokens = models.ManyToManyField(Token)  # By what token(s) this GeoName is represented
    validation_state = models.CharField(max_length=5, choices=(('uned', 'unedited'), ('verif', 'verified'), ('del', 'deleted')), default='uned')
    geolocation = models.ForeignKey(GeoLocation)  # GeoLocation that is represented in this GeoName
    user_notes = models.TextField(max_length=500, blank=True, default='')

    def __str__(self):
        return self.geolocation.name


class GeoNameUnclear(models.Model):
    '''
    Representing GeoName that could not be linked with GeoLocation. This can happen
   in two instances:
    a) Tokens are certain to be a GeoName. However, the GeoName is ambiguous (i. e. Schafberg).
    b) Tokens are deemed to be a GeoName. However, no GeoLocation under this name is known (i. e. Textberggipfel).
    Users can add notes to these objects (when they believe to have information of value concerning this
    GeonName that would later allow for the GeoName to be attributed to a GeoLocation.
    '''
    tokens = models.ManyToManyField(Token)
    type = models.CharField(max_length=4, choices=(('UNKN', 'unknown'), ('AMBG', 'ambiguous')))
    validation_state = models.CharField(max_length=5, choices=(('uned', 'unedited'), ('verif', 'verified'), ('del', 'deleted')), default='uned')

    user_notes = models.TextField(max_length=500, blank=True, default='')

    def __str__(self):
        return self.type

class LayoutElement(models.Model):
    tokens = models.ManyToManyField(Token)
    type = models.CharField(max_length=3)
