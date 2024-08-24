from django.contrib import admin

from sourcemod.models import SourceMod


@admin.register(SourceMod)
class SourceModAdmin(admin.ModelAdmin):
    list_display = ('version',)
    search_fields = ('version',)
    ordering = ('version',)
    readonly_fields = ('version',)
    fields = ('version', 'windows_file', 'linux_file')
    list_per_page = 25
