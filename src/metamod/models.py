from pathlib import Path

from django.conf import settings
from django.db import models
from prefix_id import PrefixIDField


# Create your models here.
class MetaMod(models.Model):
    id = PrefixIDField(prefix="metamod_", primary_key=True)
    version = models.CharField(max_length=50, unique=True)
    windows_file = models.FileField(upload_to='downloads/metamod/windows/', null=True, blank=True)
    linux_file = models.FileField(upload_to='downloads/metamod/linux/', null=True, blank=True)

    def __str__(self):
        return f"Metamod {self.version}"

    def get_windows_file_path(self):
        return Path(settings.MEDIA_ROOT) / self.windows_file.name

    def get_linux_file_path(self):
        return Path(settings.MEDIA_ROOT) / self.linux_file.name