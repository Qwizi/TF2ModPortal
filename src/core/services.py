import enum
import os
import shutil
import zipfile
from pathlib import Path

from django.conf import settings
from django.core.exceptions import SuspiciousFileOperation
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
        self.include_dir = f"{self.addons_dir}/{self.scripting_dir}/include"
        self.translations_dir = f"{self.addons_dir}/translations"

    def unzip(self, file_path: Path, dest_path: Path):
        full_dest_path = self.base_path / dest_path
        # Unzip the file
        with zipfile.ZipFile(file_path, "r") as zip_ref:
            zip_ref.extractall(full_dest_path)
        os.remove(file_path)

    def zip(self, archive_name: str, file_path: Path, dest_path: Path):
        full_file_path = self.base_path / file_path
        full_archive_path = self.base_path / dest_path
        archive_path = full_archive_path / archive_name
        # ignore zip files

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
    def __init__(self):
        super().__init__()
        self.smx_files = []
        self.sp_files = []
        self.inc_files = []
        self.zip_files = []
        self.translation_files = []
        self.config_files = []

    def add_smx_file(self, file_path: Path):
        # Check if the file is a .smx file
        if file_path.suffix == ".smx":
            raise ValueError("File is not a .smx file")
        self.smx_files.append(file_path)

    def add_sp_file(self, file_path: Path):
        # Check if the file is a .sp file
        if file_path.suffix == ".sp":
            raise ValueError("File is not a .sp file")
        self.sp_files.append(file_path)

    def add_inc_file(self, file_path: Path):
        # Check if the file is a .inc file
        if file_path.suffix == ".inc":
            raise ValueError("File is not a .inc file")
        self.inc_files.append(file_path)

    def add_zip_file(self, file_path: Path):
        # Check if the file is a .zip file
        if file_path.suffix == ".zip":
            raise ValueError("File is not a .zip file")
        self.zip_files.append(file_path)

    def add_translation_file(self, file_path: Path):
        # Check if the file is a .txt file
        if file_path.suffix == ".txt":
            raise ValueError("File is not a .txt file")
        self.translation_files.append(file_path)

    def add_config_file(self, file_path: Path):
        # Check if the file is a .cfg file
        if file_path.suffix == ".cfg":
            raise ValueError("File is not a .cfg file")
        self.config_files.append(file_path)

    def save_file(self, response: Response, file_type: PluginFile.FileType, obj_id: str, file_name: str, version: str):
        file_path = None
        base_path = self.base_plugins_download_path / obj_id / version
        if file_type == PluginFile.FileType.SMX:
            file_path = base_path / self.plugins_dir / file_name
        elif file_type == PluginFile.FileType.SP:
            file_path = base_path / self.scripting_dir / file_name
        file_path.parent.mkdir(parents=True, exist_ok=True)
        with default_storage.open(file_path, 'wb+') as destination:
            destination.write(response.content)
        return file_path

    def archive_files(self, obj_id: str, archive_name: str, version: str):
        plugin_dir = self.base_plugins_download_path / obj_id / version
        archive_path = self.zip(archive_name, plugin_dir, plugin_dir)
        return archive_path

    def move_smx_files(self, move_type: MoveType, obj_id: str):
        if not self.smx_files:
            return
        if move_type == MoveType.PLUGIN_DOWNLOAD:
            for file in self.smx_files:
                dest_path = self.base_plugins_download_path / obj_id / self.plugins_dir / file.name
                self.move(file, dest_path)

    def move_sp_files(self, move_type: MoveType, obj_id: str):
        if not self.sp_files:
            return
        if move_type == MoveType.PLUGIN_DOWNLOAD:
            for file in self.sp_files:
                dest_path = self.base_plugins_download_path / obj_id / self.scripting_dir / file.name
                self.move(file, dest_path)

    def move_inc_files(self, move_type: MoveType, obj_id: str):
        if not self.inc_files:
            return
        if move_type == MoveType.PLUGIN_DOWNLOAD:
            for file in self.inc_files:
                dest_path = self.base_plugins_download_path / obj_id / self.include_dir / file.name
                self.move(file, dest_path)
