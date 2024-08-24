import zipfile
from pathlib import Path

import requests
from bs4 import BeautifulSoup
from django.conf import settings
from django.core.files.storage import default_storage

from plugins.models import Plugin


class SourceModPluginDownloader:
    def __init__(self, url):
        self.url = url
        self.soup = None
        self.version = None
        self.name = None
        self.path = f"downloads/plugins/{self.name}/"
        self.dir = Path(settings.MEDIA_ROOT) / self.path
        self.file_name = None

    def get_links(self):
        links = {}
        fieldset = self.soup.find('fieldset', class_='fieldset')
        if fieldset:
            for a_tag in fieldset.find_all('a', href=True):
                file_name = a_tag.text.strip()
                url = a_tag['href']
                links[file_name] = url
        return links

    def download_smx_file(self, smx_link):
        # remove from the link last part https://forums.alliedmods.net/showthread.php?p=548207 only https://forums.alliedmods.net/
        url = self.url.split("showthread.php")[0]
        response = requests.get(f"{url}/{smx_link[1]}")
        response.raise_for_status()
        name = smx_link[0].split(".")[0]
        file_name = Path(smx_link[0]).name
        file_path = Path(settings.MEDIA_ROOT) / "downloads/plugins/" / name / "addons/sourcemod/plugins" / file_name
        file_path.parent.mkdir(parents=True, exist_ok=True)
        with default_storage.open(file_path, 'wb+') as destination:
            destination.write(response.content)
        return file_name

    def download_sp_file(self, sp_link, file_name):
        url = self.url.split("showthread.php")[0]
        response = requests.get(f"{url}/{sp_link[1]}")
        response.raise_for_status()
        name = file_name.split(".")[0]
        file_name = name + ".sp"
        file_name = Path(file_name).name
        file_path = Path(settings.MEDIA_ROOT) / "downloads/plugins/" / name / "addons/sourcemod/scripting" / file_name
        file_path.parent.mkdir(parents=True, exist_ok=True)
        with default_storage.open(file_path, 'wb+') as destination:
            destination.write(response.content)
        return file_name

    def download_translation_file(self, translation_link, file_name):
        url = self.url.split("showthread.php")[0]
        response = requests.get(f"{url}/{translation_link[1]}")
        response.raise_for_status()
        name = file_name.split(".")[0]
        file_name = translation_link[0]
        file_name = Path(file_name).name
        file_path = Path(
            settings.MEDIA_ROOT) / "downloads/plugins/" / name / "addons/sourcemod/translations" / file_name
        file_path.parent.mkdir(parents=True, exist_ok=True)
        with default_storage.open(file_path, 'wb+') as destination:
            destination.write(response.content)
        return file_name

    def save_to_db(self, name, version, smx_file=None, sp_file=None, cfg_file=None, zip_file=None):
        plugin = Plugin.objects.create(
            name=name,
            version=version,
            smx_file=f"downloads/plugins/{name}/addons/sourcemod/plugins/{smx_file}",
            sp_file=f"downloads/plugins/{name}/addons/sourcemod/scripting/{sp_file}",
            cfg_file=f"downloads/plugins/{name}/addons/sourcemod/configs/{cfg_file}",
            zip_file=f"downloads/plugins/{name}/{zip_file}",
        )
        plugin.save()

    def make_archive(self, name, version):
        # Create a ZIP archive of the plugin files and ignore zip files
        plugin_dir = Path(settings.MEDIA_ROOT) / "downloads/plugins" / name
        archive_dir = Path(settings.MEDIA_ROOT) / "downloads/plugins" / name
        archive_name = f"{name}_{version}.zip"
        archive_path = archive_dir / archive_name
        # ignore zip files
        plugin_dir_files = [file for file in plugin_dir.rglob("*") if file.suffix != '.zip']
        with default_storage.open(archive_path, 'wb+') as archive:
            with zipfile.ZipFile(archive, 'w') as zip_file:
                for file in plugin_dir_files:
                    zip_file.write(file, file.relative_to(plugin_dir))
        return archive_name

    def download(self):
        # Download the plugin from the SourceMod website
        response = requests.get(self.url)
        response.raise_for_status()
        # Parse the HTML content
        self.soup = BeautifulSoup(response.content, 'html.parser')
        links = self.get_links()
        smx_file_name = None
        sp_file_name = None
        translation_file_name = None
        for link in links.items():
            if "smx" in link[0]:
                smx_file_name = self.download_smx_file(link)
                break
        for link in links.items():
            if "smx" in link[0]:
                self.download_smx_file(link)
                print(f"Downloaded {smx_file_name}")
            if "Get Source" in link[0]:
                print(f"Downloading {link[0]}")
                sp_file_name = self.download_sp_file(link, smx_file_name)
            if "txt" in link[0]:
                print(f"Downloading {link[0]}")
                translation_file_name = self.download_translation_file(link, smx_file_name)
                print(f"Downloaded {translation_file_name}")
        zip_file = self.make_archive(smx_file_name.split(".")[0], "1.0")
        self.save_to_db(name=smx_file_name.split(".")[0], version="1.0", smx_file=smx_file_name, sp_file=sp_file_name,
                        cfg_file=translation_file_name, zip_file=zip_file)

