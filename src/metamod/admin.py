from django.contrib import admin

from metamod.models import MetaMod


# Register your models here.

@admin.register(MetaMod)
class MetaModAdmin(admin.ModelAdmin):
    pass
