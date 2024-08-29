from django.contrib import admin
from unfold.admin import ModelAdmin

from builds.models import Build


# Register your models here.

@admin.register(Build)
class BuildAdmin(ModelAdmin):
    pass
