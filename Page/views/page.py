__author__ = 'lukasmeier'

from django.shortcuts import render_to_response, RequestContext, render
from .forms import MarkAsCorrectForm, VerifyGeoNameForm, GeoLocationForm

import Page
import Page.models
import time

def main(request, yrb, facs_no):
    pageManager = Page.models.PageManager(yrb, facs_no)
    #Handling single geoname validation (via pop-up box)
    for item in  request.POST.items():
        if (item[0].startswith('unkn_') or item[0].startswith('ambg_') or item[0].startswith('gn_')) and item[1] == 'verify':
            pageManager.process_single_verification(item[0])
    pg = pageManager.page
    #mark as correct form
    markAsCorrectForm = MarkAsCorrectForm(request.POST or None, initial={'correct' : pg.correct})#to set initial value at runtime
    box_checked = None
    #displaying geonames_list
    geonames = pageManager.get_geonames()
    #processing geonamelist changes
    if 'checkboxes' in request.POST and request.POST['checkboxes'] == 'abschicken':
        verify_or_delete = [entry for entry in request.POST.items() if entry[1] == 'delete' or entry[1] == 'verify']
        verify_or_delete_ids = [entry[0] for entry in verify_or_delete]
        if len(verify_or_delete) > 0:
            unverify = [(geoname[0] + '_' + str(geoname[2])) for geoname in geonames if len(verify_or_delete) > 0 and (geoname[0] + '_' + str(geoname[2])) not in verify_or_delete_ids]
        else:
            unverify = [(geoname[0] + '_' + str(geoname[2])) for geoname in geonames]
        pageManager.process_checkboxes(verify_or_delete, unverify)
        time.sleep(1) #to give enough time for the server to process data
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
    updated_geonames = pageManager.get_geonames()
    #processing the tokens should be done here rather than at the template level, the fewer for loops etc in the template the better.
    #Templates should only display content that has  a l r e a d y  been processed. Better still, the processing should be done in a model manager.
    return render_to_response('Page/templates/page.html', {'verify_geoname_form' : VerifyGeoNameForm(), 'facs_no' : facs_no, 'yearbook' : yrb, 'divs': spans, 'previous_following' : previous_following_page,
                                                        'first_last' : first_last_page, 'correctForm' : markAsCorrectForm, 'correctFormValue' : box_checked,
                                                        'geonames' : updated_geonames, 'centre' : pageManager.get_centroid(),
                                                        'coordinates_array' : pageManager.get_coordinates_java_script_array(), 'dropdown_content_path' : 'static/js/dropdowncontent.js'},
                              context_instance=RequestContext(request))



def new_geoName(request):
    context_ids = list()
    for entry in request.GET.lists():
        for e in entry:
            if e == 'selection' or e == 'selection[]':
               context_ids =  [int(token_id.split('_')[1]) for token_id in entry[1]]
    newGeoNameManager = Page.models.NewGeoNameManager(context_ids)
    context =  newGeoNameManager.get_context()
    print (request.POST)
    return render(request, 'Page/templates/new_geoname.html', {'context_ids' : context_ids, 'context' : context, 'test_form' : GeoLocationForm()}, context_instance=RequestContext(request))