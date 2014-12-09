__author__ = 'lukasmeier'

from django import forms

class MarkAsCorrectForm(forms.Form):


    correct = forms.BooleanField(widget=forms.CheckboxInput(attrs={'onclick' : 'submit();'}),required=False, label="vollständig korrigiert")
