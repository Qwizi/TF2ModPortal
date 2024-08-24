from django.contrib import admin

from plugins.models import Plugin


# Register your models here.
@admin.register(Plugin)
class PluginAdmin(admin.ModelAdmin):
    pass
