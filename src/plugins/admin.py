from django.contrib import admin
from unfold.admin import ModelAdmin, TabularInline
from unfold.contrib.inlines.admin import NonrelatedTabularInline

from plugins.models import Plugin, Tag, PluginFile


class PluginFilesTagInline(NonrelatedTabularInline):  # NonrelatedStackedInline is available as well
    model = PluginFile
    tab = True
    extra = 0

    def get_form_queryset(self, obj):
        """
        Gets all nonrelated objects needed for inlines. Method must be implemented.
        """
        tags = Tag.objects.filter(plugin=obj).all()
        plugin_files = PluginFile.objects.filter(tag__in=tags).all()
        return plugin_files

    def save_new_instance(self, parent, instance):
        """
        Extra save method which can for example update inline instances based on current
        main model object. Method must be implemented.
        """
        instance.tag = parent
        instance.save()


class PluginTagInline(TabularInline):
    model = Tag
    tab = True
    fields = ['tagged_name', 'version', 'is_latest']
    extra = 0


# Register your models here.
@admin.register(Plugin)
class PluginAdmin(ModelAdmin):
    inlines = [PluginTagInline, PluginFilesTagInline]
    pass
