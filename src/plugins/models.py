from pathlib import Path

from django.conf import settings
from django.db import models
from prefix_id import PrefixIDField


class Plugin(models.Model):
    class PluginSource(models.TextChoices):
        SOURCEMOD = 'sourcemod', 'SourceMod'
        GITHUB = 'github', 'GitHub'

    id = PrefixIDField(prefix="plugin_", primary_key=True)
    plugin_source = models.CharField(max_length=50, choices=PluginSource.choices, default=PluginSource.SOURCEMOD)
    name = models.CharField(max_length=50)
    version = models.CharField(max_length=50)
    smx_file = models.FileField(upload_to='downloads/plugins/', null=True, blank=True)
    sp_file = models.FileField(upload_to='downloads/plugins/', null=True, blank=True)
    cfg_file = models.FileField(upload_to='downloads/plugins/', null=True, blank=True)
    zip_file = models.FileField(upload_to='downloads/plugins/', null=True, blank=True)

    def __str__(self):
        return f"{self.name} {self.version} {self.plugin_source}"

    def get_smx_file_path(self):
        return Path(settings.MEDIA_ROOT) / self.smx_file.name

    def get_sp_file_path(self):
        return Path(settings.MEDIA_ROOT) / self.sp_file.name

    def get_cfg_file_path(self):
        return Path(settings.MEDIA_ROOT) / self.cfg_file.name

    def get_zip_file_path(self):
        return Path(settings.MEDIA_ROOT) / self.zip_file.name
