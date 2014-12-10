from django.contrib import admin
from Page import models

class TokenInline(admin.TabularInline):
    model = models.Token
    exclude = ('tb_id', 'content')


class PageAdmin(admin.ModelAdmin):
    list_display = ('pb_n', 'yearbook', 'scan_url')
    search_fields = ('pb_n',)
    ordering = ('yearbook', 'pb_n')
    inlines = [TokenInline, ]
    readonly_fields = ('pb_n', 'yearbook')

class TokenAdmin(admin.ModelAdmin):
    search_fields = ('content', 'tb_key')
    ordering = ('tb_key',)
    readonly_fields = ('tb_key', 'content', 'page')

class GeoNameAdmin(admin.ModelAdmin):
    readonly_fields = ('tokens', 'geolocation')

class GeoNameUnclearAdmin(admin.ModelAdmin):
    readonly_fields = ('tokens',)


class LayoutElementAdmin(admin.ModelAdmin):
    readonly_fields = ('tokens',)

class GeoLocationAdmin(admin.ModelAdmin):
    fields = ('name', 'type', 'geoloc_reference', 'coordinates')
    search_fields = ('name',)
    ordering = ('name',)
    readonly_fields = ('geoloc_reference', 'coordinates')



# Register your models here.
admin.site.register(models.Yearbook)
admin.site.register(models.Page, PageAdmin)
admin.site.register(models.Token, TokenAdmin)
admin.site.register(models.GeoLocation, GeoLocationAdmin)
admin.site.register(models.GeoName, GeoNameAdmin)
admin.site.register(models.LayoutElement, LayoutElementAdmin)
admin.site.register(models.GeoNameUnclear, GeoNameUnclearAdmin)
#admin.site.register(GeoCoordinates)
#admin.site.register(ForeignGeoLocationId)

