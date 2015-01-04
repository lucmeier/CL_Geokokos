__author__ = 'lukasmeier'

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