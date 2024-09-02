import enum
import shutil
import zipfile
from io import BytesIO
from pathlib import Path

from django.conf import settings
from django.core.files import File
from django.core.files.storage import default_storage
from requests import Response

from plugins.models import PluginFile
from sourcemod.models import SourceMod
from tf2modportal.services import BaseSourceModeDownloader


class SourceModDownloader(BaseSourceModeDownloader):
    def __init__(self):
        super().__init__()
        self.model = SourceMod


class BaseFileManager:
    def __init__(self):
        self.base_path = Path(settings.MEDIA_ROOT) / "downloads"
        self.base_plugins_download_path = self.base_path / "plugins"
        self.base_builds_download_path = self.base_path / "builds"
        self.base_sourcemod_download_path = self.base_path / "sourcemod"
        self.base_metamod_download_path = self.base_path / "metamod"
        self.addons_dir = "addons/sourcemod"
        self.plugins_dir = f"{self.addons_dir}/plugins"
        self.scripting_dir = f"{self.addons_dir}/scripting"
        self.include_dir = f"{self.scripting_dir}/include"
        self.translations_dir = f"{self.addons_dir}/translations"
        self.maps_dir = "maps"
        self.sound_dir = "sound"
        self.models_dir = "models"
        self.materials_dir = "materials"

    def unzip(self, file_path: Path, dest_path: Path):
        full_dest_path = self.base_path / dest_path
        # Unzip the file
        with zipfile.ZipFile(file_path, "r") as zip_ref:
            zip_ref.extractall(full_dest_path)
        # os.remove(file_path)

    def zip(self, archive_name: str, file_path: Path, dest_path: Path):
        full_file_path = self.base_path / file_path
        full_archive_path = self.base_path / dest_path
        archive_path = full_archive_path / archive_name
        plugin_dir_files = [file for file in full_file_path.rglob("*") if file.suffix != '.zip']
        with default_storage.open(archive_path, 'wb+') as archive:
            with zipfile.ZipFile(archive, 'w') as zip_file:
                for file in plugin_dir_files:
                    zip_file.write(file, file.relative_to(full_file_path))
        return archive_path

    def move(self, file_path: Path, dest_path: Path):
        dest_path = self.base_path / dest_path
        dest_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(file_path, dest_path)
        return dest_path

    def copy(self, file_path: Path, dest_path: Path):
        dest_path = self.base_path / dest_path
        dest_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy(file_path, dest_path)
        return dest_path

    def delete(self, file_path):
        file_path = self.base_path / file_path
        if file_path.exists():
            file_path.unlink()


class MoveType(str, enum.Enum):
    PLUGIN_DOWNLOAD = "plugin_download"
    PLUGIN_BUILD = "plugin_build"
    SOURCEMOD_DOWNLOAD = "sourcemod_download"
    METAMOD_DOWNLOAD = "metamod_download"
    SOURCEMOD_BUILD = "sourcemod_build"
    METAMOD_BUILD = "metamod_build"


class FileManager(BaseFileManager):
    def save_file(self, response: Response, plugin_file, tag):
        file_path = None
        file_path_to_save = f"{tag.plugin.id}/{tag.version}/"
        base_path = self.base_plugins_download_path / tag.plugin.id / tag.version / "files"
        if plugin_file.file_type == PluginFile.FileType.SMX:
            file_path = base_path / self.plugins_dir / plugin_file.file_name
            file_path_to_save = f"{tag.plugin.id}/{tag.version}/files/addons/sourcemod/plugins/{plugin_file.file_name}"
        elif plugin_file.file_type == PluginFile.FileType.SP:
            file_path = base_path / self.scripting_dir / plugin_file.file_name
            file_path_to_save = f"{tag.plugin.id}/{tag.version}/files/addons/sourcemod/scripting/{plugin_file.file_name}"
        elif plugin_file.file_type == PluginFile.FileType.ZIP:
            file_path = self.base_plugins_download_path / tag.plugin.id / tag.version / "archives" / plugin_file.file_name
            file_path_to_save = f"{tag.plugin.id}/{tag.version}/archives/{plugin_file.file_name}"
        file_path.parent.mkdir(parents=True, exist_ok=True)
        django_file = File(BytesIO(response.content), name=plugin_file.file_name)
        plugin_file.file.save(file_path_to_save, django_file, save=True)

        return file_path

    def move_files(self, obj_id: str, version: str, temp: bool = False):
        plugin_dir = self.base_plugins_download_path / obj_id / version if not temp else self.base_plugins_download_path / obj_id / version / "temp"
        dest_dir = self.base_plugins_download_path / obj_id / version / "files"
        for file in plugin_dir.rglob("*"):
            if file.suffix == ".smx":
                if "disabled" in file.parts:
                    self.move(file, dest_dir / self.plugins_dir / "disabled" / file.name)
                else:
                    self.move(file, dest_dir / self.plugins_dir / file.name)
            elif file.suffix == ".sp":
                self.move(file, dest_dir / self.scripting_dir / file.name)
            elif file.suffix == ".inc":
                self.move(file, dest_dir / self.include_dir / file.name)
            elif "phrases" in file.name:
                self.move(file, dest_dir / "translations" / file.name)
            elif file.suffix == ".txt":
                self.move(file, dest_dir / file.name)
            elif file.suffix == ".cfg":
                self.move(file, dest_dir / file.name)
            elif file.suffix == ".bsp":
                self.move(file, dest_dir / self.maps_dir / file.name)
            elif file.suffix in [".wav", ".mp3"]:
                self.move(file, dest_dir / self.sound_dir / file.name)
            elif file.suffix == ".mdl":
                self.move(file, dest_dir / self.models_dir / file.name)
            elif file.suffix == ".vmt":
                self.move(file, dest_dir / self.materials_dir / file.name)

    def archive_files(self, obj_id: str, archive_name: str, version: str):
        dest_path = self.base_plugins_download_path / obj_id / version
        base_path = self.base_plugins_download_path / obj_id / version / "files"
        archive_path = self.zip(archive_name, base_path, dest_path)
        return archive_path
