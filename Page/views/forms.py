__author__ = 'lukasmeier'
import autocomplete_light
from django import forms
from Page import models

class MarkAsCorrectForm(forms.Form):
    correct = forms.BooleanField(widget=forms.CheckboxInput(attrs={'onclick' : 'submit();'}), required=False, label="vollständig korrigiert")


class VerifyGeoNameForm(forms.Form):
    '''to verify a single GeoName via pop up-box'''
    def __init__(self, id, checked):
        self.checked = checked
        self.id = id # e. g. "GN_212"
        self.verified = forms.BooleanField(widget=forms.CheckboxInput(attrs={'onclick' : 'submit();'}), required=False, label="verifiziert")

class ChooseGeoLocationForm(forms.Form):
    '''To choose approriate geolocation'''
    pass


class GeoLocationAutocomplete(autocomplete_light.AutocompleteModelBase):
    search_fields = ['^name', '^type']
    model = models.GeoLocation
autocomplete_light.register(GeoLocationAutocomplete)

class OsAutocomplete(autocomplete_light.AutocompleteListTemplate):
    choices =  [geoname.name + ' ' + geoname.type for geoname in models.GeoLocation.objects.all()]



autocomplete_light.register(OsAutocomplete)

class OsAutocompleteForm(forms.Form):
    os = autocomplete_light.ChoiceField('OsAutocomplete')