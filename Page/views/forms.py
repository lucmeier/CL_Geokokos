__author__ = 'lukasmeier'
import autocomplete_light
from django import forms
from Page import models

class MarkAsCorrectForm(forms.Form):
    correct = forms.BooleanField(widget=forms.CheckboxInput(attrs={'onclick' : 'submit();'}), required=False, label="vollständig korrigiert")


class VerifyGeoNameForm(forms.Form):
    '''to verify a single GeoName via pop up-box'''
    verified = forms.BooleanField(widget=forms.CheckboxInput(attrs={'onclick' : 'submit();'}), required=False, label="verifiziert")


class GeoLocationAutocomplete(autocomplete_light.AutocompleteListTemplate):
    reg = models.Region.objects.all().filter(abbreviation='GR')

    choices =  [geoname.get_display_name() for geoname in models.GeoLocation.objects.all().filter(region=reg)]

autocomplete_light.register(GeoLocationAutocomplete)


autocomplete_light.register(GeoLocationAutocomplete)

class GeoLocationForm(forms.Form):
    geolocation = autocomplete_light.ChoiceField('GeoLocationAutocomplete')
    not_in_db = forms.BooleanField(label='GeoLocation nicht in Datenbank vorhanden', required=False)
    ambiguous = forms.BooleanField(label='Geolaction in Datenbank vorhanden, zweideutig', required=False)
    user_notes = forms.CharField(label='Anmerkungen/ Hinweise', required=False, max_length=500)