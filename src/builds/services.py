from core.services import BaseFileManager, FileManager
from plugins.models import PluginFile


class BuildService:
    def __init__(self):
        self.file_manager = FileManager()

    def move_files(self, build):
        tags = build.plugins_tags.all()
        file_paths = []
        for tag in tags:
            files = tag.files.filter(
                file_type__in=[PluginFile.FileType.SMX, PluginFile.FileType.SP, PluginFile.FileType.CFG]).all()
            for file in files:
                file_path = file.get_file_path()
                if file.file_type == PluginFile.FileType.SMX:
                    file_paths.append(self.file_manager.copy(file_path, self.file_manager.base_builds_download_path / build.id / build.version / "files" / "addons" / "sourcemod" / "plugins" / file.get_file_name()))
                if file.file_type == PluginFile.FileType.SP:
                    file_paths.append(self.file_manager.copy(file_path, self.file_manager.base_builds_download_path / build.id / build.version / "files" / "addons" / "sourcemod" / "scripting" / file.get_file_name()))
                if file.file_type == PluginFile.FileType.CFG:
                    file_paths.append(self.file_manager.copy(file_path, self.file_manager.base_builds_download_path / build.id / build.version / "files" / "addons" / "sourcemod" / "translations" / file.get_file_name()))
        return file_paths

    def archive_files(self, build):
        dest_path = self.file_manager.base_builds_download_path / build.id
        base_path = self.file_manager.base_builds_download_path / build.id / build.version / "files"
        archive_path = self.file_manager.zip(f"{build.name}-{build.version}.zip", base_path, dest_path)
        return archive_path
