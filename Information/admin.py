from django.contrib import admin
from Information import models

class FaqAdmin(admin.ModelAdmin):
    ordering = ['question', 'content']




# Register your models here.
admin.site.register(models.Information)
admin.site.register(models.FaqElement, FaqAdmin)
admin.site.register(models.NewsPiece)