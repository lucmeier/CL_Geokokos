__author__ = 'lukasmeier'

from django import forms
from Page import models

class MarkAsCorrectForm(forms.Form):
    correct = forms.BooleanField(widget=forms.CheckboxInput(attrs={'onclick' : 'submit();'}), required=False, label="vollständig korrigiert")

class GeoNameCheckboxPair(forms.Form):


    def __init__(self, attributes_verified, attributes_deleted):
        self.attributes_verfied = attributes_verified
        self.attributes_deleted = attributes_deleted
        self.verified = forms.BooleanField(widget=forms.CheckboxInput(attrs=attributes_verified), required=False, label="")
        self.deleted = forms.BooleanField(widget=forms.CheckboxInput(attrs=attributes_deleted), required=False, label="vollständig korrigiert")


class GeoNameCheckBoxPairs(forms.Form):
    pairs = list()
    def __init__(self, geonames):
        attributes = dict()
        for geoname in geonames:
            attribute_list = list()
            attribute_list.append(('name', geoname[0] + '_' + geoname[2]))
            _id = geoname[2]
            if geoname[0] == 'GN':
                geoname = models.GeoName.objects.all().filter(id=_id)[0]
                if geoname.validation_state == 'verif':
                    attribute_list.append(('checked', ''))
            if geoname[0] == 'UNKN' or geoname[0] == 'AMBG':
                geoname_unclear = models.GeoNameUnclear.objects.all().filter(id=_id)[0]
                if geoname_unclear.validation_state == 'verif':
                    attribute_list.append(('checked', ''))
            for attribute in attribute_list:
                attributes[attribute[0]] = attribute[1]


