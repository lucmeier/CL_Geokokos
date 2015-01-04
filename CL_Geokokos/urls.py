from django.conf.urls import patterns, include, url
from django.contrib import admin


admin.autodiscover()
urlpatterns = patterns('',
    # Examples:
    # url(r'^$', 'Geokokos.views.home', name='home'),
    # url(r'^blog/', include('blog.urls')),

    url(r'^admin/', include(admin.site.urls)),
    url(r'kokos/(SAC.+)/(\d{1,3})/$', 'Page.views.page.main', name='page_view'),
    url(r'kokos/SAC.+/\d{1,3}/new_geoname/', 'Page.views.page.new_geoName', name='new_geoname')
)
