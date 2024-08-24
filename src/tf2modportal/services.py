import os
import shutil
import tarfile
import zipfile
from pathlib import Path

import requests
from bs4 import BeautifulSoup
from django.core.files.storage import default_storage

from tf2modportal import settings


class BaseSourceModeDownloader:
    def __init__(self):
        self.url = "https://www.sourcemod.net/downloads.php"
        self.soup = None
        self.version = None
        self.name = "sourcemod"
        self.windows_path = f"downloads/{self.name}/windows"
        self.linux_path = f"downloads/{self.name}/linux"
        self.windows_dir = Path(settings.MEDIA_ROOT) / self.windows_path
        self.linux_dir = Path(settings.MEDIA_ROOT) / self.linux_path
        self.linux_file_name = None
        self.windows_file_name = None
        self.model = None

    def download(self):
        response = requests.get(self.url)
        response.raise_for_status()

        # Parse the HTML content
        self.soup = BeautifulSoup(response.content, 'html.parser')

        windows_link, linux_link = self.get_download_links()
        self.version = self.extract_version(windows_link)
        if self.version_exists():
            return {"status": "skipped", "version": self.version}

        self.windows_file_name = self.download_file(windows_link, "windows")
        self.linux_file_name = self.download_file(linux_link, "linux")
        self.save_to_db()

    def get_download_links(self):
        links = self.soup.find_all("a", class_="quick-download download-link", href=True)
        windows_link = None
        linux_link = None
        for link in links:
            if "Windows" in link.text:
                windows_link = link.get('href')
            elif "Linux" in link.text:
                linux_link = link.get('href')
        return windows_link, linux_link

    def version_exists(self):
        return self.model.objects.filter(version=self.version).exists()

    @staticmethod
    def extract_version(link):
        return link.split('/')[-1].split('-')[1]

    def download_file(self, link, platform):
        response = requests.get(link)
        response.raise_for_status()
        filename = Path(link).name
        if platform == "windows":
            file_path = self.windows_dir / filename
        else:
            file_path = self.linux_dir / filename
        file_path.parent.mkdir(parents=True, exist_ok=True)

        with default_storage.open(file_path, 'wb+') as destination:
            destination.write(response.content)
        return filename

    def save_to_db(self):
        source_mod = self.model(version=self.version,
                                windows_file=f"{self.windows_path}/{self.windows_file_name}",
                                linux_file=f"{self.linux_path}/{self.linux_file_name}")
        source_mod.save()
        return {"status": "success", "version": self.version}


class FileExtractor:
    def __init__(self, windows_dir, linux_dir, build_dir):
        self.windows_dir = Path(windows_dir)
        self.linux_dir = Path(linux_dir)
        self.linux_build_dir = Path(build_dir) / "linux"
        self.windows_build_dir = Path(build_dir) / "windows"

    def extract_files(self, platform):
        if platform == "windows":
            source_dir = self.windows_dir
            self.windows_build_dir.mkdir(parents=True, exist_ok=True)
        else:
            source_dir = self.linux_dir
            self.linux_build_dir.mkdir(parents=True, exist_ok=True)
        if platform == "windows":
            build_dir = self.windows_build_dir
        else:
            build_dir = self.linux_build_dir
        for file in source_dir.iterdir():
            if file.is_file():

                if file.suffix == '.zip':
                    with zipfile.ZipFile(file, 'r') as zip_ref:
                        zip_ref.extractall(build_dir)
                elif file.suffix in ['.tar', '.gz', '.bz2', '.xz']:
                    with tarfile.open(file, 'r:*') as tar_ref:
                        tar_ref.extractall(build_dir)
                else:
                    shutil.copy(file, build_dir / file.name)

        for root, dirs, files in os.walk(build_dir):
            for dir in dirs:
                os.chmod(os.path.join(root, dir), 0o755)
            for file in files:
                os.chmod(os.path.join(root, file), 0o644)
