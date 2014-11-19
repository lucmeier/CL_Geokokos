from django.db import models
from django.contrib import admin
from django.core import exceptions, urlresolvers
import CL_Geokokos
# Create your models here.


class Yearbook(models.Model):
    file_name = models.CharField(max_length=30)
    year = models.CharField(max_length=10)

    def __str__(self):
        return self.file_name


class Page(models.Model):
    scan_url = models.CharField(max_length=50)  # file name of image scan
    pb_n = models.IntegerField(verbose_name='Facsimile No')
    yearbook = models.ForeignKey(Yearbook)

    def __str__(self):
        return self.yearbook.file_name + ': Page ' + str(self.pb_n)


class PageManager(models.Manager):
    def _get_page(self, facs_no, yrb):
        yrb = Yearbook.objects.all().filter(file_name=yrb)
        pg = Page.objects.get(yearbook=yrb, pb_n=int(facs_no))
        return pg

    def get_previous_following(self, yrb, facs_no):
        page = self._get_page(facs_no, yrb)
        page_id = page.id
        yearbook_id = page.yearbook.id
        return self._get_previous(page_id, yearbook_id), self._get_following(page_id, yearbook_id)


    def div_list(self, yrb, facs_no):
        '''Returns a list of div elements containing (token, attribute) tuples for a given page.'''
        pg = self._get_page(facs_no, yrb)
        tokens = Token.objects.all().filter(page=pg)
        layoutElements = LayoutElement.objects.all().filter(tokens=tokens)
        geonames = GeoName.objects.all().filter(tokens=tokens)
        geonames_token_ids = list()
        for geoname in geonames:
            for token in geoname.tokens.all():
                geonames_token_ids.append(token.id)
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
                    tkns.append(('gn', tkn.spaced_token(before)))
                else:
                    tkns.append(('token', tkn.spaced_token(before)))
                before = tkn.content
            divs.append(tkns)
        return divs

    def _get_previous(self, page_id, yearbook_id):
        previous = page_id - 1
        try:
            previous_page = Page.objects.get(id=previous)
        except exceptions.ObjectDoesNotExist:
            return page_id
        if previous_page.yearbook_id != yearbook_id:
            return page_id
        return previous_page.pb_n

    def _get_following(selfs, page_id, yearbook_id):
        following = page_id + 1
        try:
            following_page = Page.objects.get(id=following)
        except exceptions.ObjectDoesNotExist:
            return page_id
        if following_page.yearbook_id != yearbook_id:
            return page_id
        return following_page.pb_n


class Token(models.Model):
    content = models.CharField(max_length=200)  # what the token contains
    tb_key = models.CharField(max_length=15,
                              verbose_name='Text + Berg No')  # Text+Berg Token id: article-sentence-token
    page = models.ForeignKey(Page)

    def __str__(self):
        return self.tb_key + ': ' + self.content

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
    validation_state = models.CharField(max_length=10)
    geolocation = models.ForeignKey(GeoLocation)  # GeoLocation that is represented in this GeoName

    def __str__(self):
        return self.geolocation.name


class LayoutElement(models.Model):
    tokens = models.ManyToManyField(Token)
    type = models.CharField(max_length=3)



