__author__ = 'lukasmeier' #source (partly): http://django-autocomplete-light.readthedocs.org/en/stable-2.x.x/tutorial.html

import autocomplete_light
from Page.models import GeoLocation

# This will generate a PersonAutocomplete class
autocomplete_light.register(GeoLocation,
    # Just like in ModelAdmin.search_fields
    search_fields=['name', 'type'],
    attrs={
        # This will set the input placeholder attribute:
        'placeholder': 'Suche ... ',
        # This will set the yourlabs.Autocomplete.minimumCharacters
        # options, the naming conversion is handled by jQuery
        'data-autocomplete-minimum-characters': 1,
    },
    # This will set the data-widget-maximum-values attribute on the
    # widget container element, and will be set to
    # yourlabs.Widget.maximumValues (jQuery handles the naming
    # conversion).
    widget_attrs={
        'data-widget-maximum-values': 4,
        # Enable modern-style widget !
        'class': 'modern-style',
    },
)