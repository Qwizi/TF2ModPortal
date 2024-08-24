from pathlib import Path

from django.conf import settings

from metamod.models import MetaMod
from tf2modportal.services import BaseSourceModeDownloader


class MetaModDownloader(BaseSourceModeDownloader):
    def __init__(self):
        super().__init__()
        self.name = "metamod"
        self.url = "https://www.sourcemm.net/downloads.php?branch=stable"
        self.model = MetaMod
        self.windows_path = f"downloads/{self.name}/windows"
        self.linux_path = f"downloads/{self.name}/linux"
        self.windows_dir = Path(settings.MEDIA_ROOT) / self.windows_path
        self.linux_dir = Path(settings.MEDIA_ROOT) / self.linux_path
        self.model = MetaMod