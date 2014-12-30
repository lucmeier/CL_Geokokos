__author__ = 'lukasmeier'

from django.shortcuts import render_to_response, RequestContext, redirect
from .forms import MarkAsCorrectForm

import Page
import Page.models

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
    if 'checkboxes' in request.POST and request.POST['checkboxes'] == 'abschicken':
        verify_or_delete = [entry for entry in request.POST.items() if entry[1] == 'delete' or entry[1] == 'verify']
        verify_or_delete_ids = [entry[0] for entry in verify_or_delete]
        print (verify_or_delete_ids)
        if len(verify_or_delete) > 0:
            unverify = [(geoname[0] + '_' + str(geoname[2])) for geoname in geonames if len(verify_or_delete) > 0 and (geoname[0] + '_' + str(geoname[2])) not in verify_or_delete_ids]
        else:
            unverify = [(geoname[0] + '_' + str(geoname[2])) for geoname in geonames]
        print ('verify or delete', verify_or_delete, '\n', 'unverivy', unverify)
        pageManager.process_checkboxes(verify_or_delete, unverify)
    updated_geonames = pageManager.get_geonames()
    #processing the tokens should be done here rather than at the template level, the fewer for loops etc in the template the better.
    #Templates should only display content that has  a l r e a d y  been processed. Better still, the processing should be done in a model manager.
    return render_to_response('Page/templates/page.html', {'facs_no' : facs_no, 'yearbook' : yrb, 'divs': spans, 'previous_following' : previous_following_page,
                                                        'first_last' : first_last_page, 'correctForm' : markAsCorrectForm, 'correctFormValue' : box_checked,
                                                        'geonames' : updated_geonames, 'centre' : pageManager.get_centroid(),
                                                        'coordinates_array' : pageManager.get_coordinates_java_script_array(), 'dropdown_content_path' : DROPDOWN_CONTENT_PATH},
                              context_instance=RequestContext(request))

DROPDOWN_CONTENT_PATH = 'static/js/dropdowncontent.js'