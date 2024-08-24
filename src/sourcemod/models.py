from pathlib import Path

import requests
from bs4 import BeautifulSoup
from django.conf import settings
from django.db import models
from prefix_id import PrefixIDField


class SourceMod(models.Model):
    id = PrefixIDField(prefix="sourcemod_", primary_key=True)
    version = models.CharField(max_length=50, unique=True)
    windows_file = models.FileField(upload_to='downloads/sourcemod/windows/', null=True, blank=True)
    linux_file = models.FileField(upload_to='downloads/sourcemod/linux/', null=True, blank=True)

    def __str__(self):
        return f"SourceMod {self.version}"

    def get_windows_file_path(self):
        return Path(settings.MEDIA_ROOT) / self.windows_file.name

    def get_linux_file_path(self):
        return Path(settings.MEDIA_ROOT) / self.linux_file.name