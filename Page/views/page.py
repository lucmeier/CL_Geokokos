__author__ = 'lukasmeier'

from django.shortcuts import render
import Page

def main(request, yrb, facs_no):
    pageManager = Page.models.PageManager()
    divs = pageManager.div_list(yrb, facs_no)
    previous_following_page = pageManager.get_previous_following(yrb, facs_no)
    first_last_page = pageManager.get_first_last(yrb)
    #processing the tokens should be done here rather than at the template level, the fewer for loops etc in the template the better.
    #Templates should only display content that has  a l r e a d y  been processed. Better still, the processing should be done in a model manager.
    return render(request, 'Page/templates/page.html', {'facs_no' : facs_no, 'yearbook' : yrb, 'divs': divs, 'previous_following' : previous_following_page,
                                                        'first_last' : first_last_page})

