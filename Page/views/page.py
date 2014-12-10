from Page.views.forms import MarkAsCorrectForm

__author__ = 'lukasmeier'

from django.shortcuts import render_to_response, RequestContext
from .forms import MarkAsCorrectForm

import Page


def main(request, yrb, facs_no):
    pageManager = Page.models.PageManager(yrb, facs_no)
    pg = pageManager.page
    #mark as correct form
    markAsCorrectForm = MarkAsCorrectForm(request.POST or None, initial={'correct' : pg.correct})#to set initial value at runtime
    box_checked = None
    if markAsCorrectForm.is_valid():
        box_checked = markAsCorrectForm.cleaned_data['correct']
        if  box_checked:
            pg.correct = True
        else:
            pg.correct = False
        pg.save()
    #displaying page content
    spans = pageManager.spans_list()
    #displaying navigation links
    previous_following_page = pageManager.get_previous_following()
    first_last_page = pageManager.get_first_last()
    #displaying geonames_list
    geonames = pageManager.get_geonames()
    #processing the tokens should be done here rather than at the template level, the fewer for loops etc in the template the better.
    #Templates should only display content that has  a l r e a d y  been processed. Better still, the processing should be done in a model manager.
    return render_to_response('Page/templates/page.html', {'facs_no' : facs_no, 'yearbook' : yrb, 'divs': spans, 'previous_following' : previous_following_page,
                                                        'first_last' : first_last_page, 'correctForm' : markAsCorrectForm, 'correctFormValue' : box_checked,
                                                        'geonames' : geonames}, context_instance=RequestContext(request))

