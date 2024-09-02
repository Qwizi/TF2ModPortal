import zipfile
from pathlib import Path

import markdown
import requests
from bs4 import BeautifulSoup
from django.conf import settings
from django.core.files.storage import default_storage

from core.services import FileManager
from plugins.models import Plugin, Category, SupportedGame, PluginFile, Tag


class SourceModPluginDownloader:
    def __init__(self):
        self.url = "https://forums.alliedmods.net/"
        self.soup = None
        self.file_manager = FileManager()

    def get_blank_url(self):
        return self.url

    def get_plugin_details(self):
        table = self.soup.find('table', id=lambda x: x and x.startswith('post'))
        details = {}
        for key in ['version', 'category', 'game']:
            div = table.find('div', string=f'Plugin {key.capitalize()}: ')
            if div:
                next_td = div.find_parent('td').find_next_sibling('td')
                if next_td:
                    details[key] = next_td.find('div').get_text(strip=True)
        return details

    def get_plugin_name(self):
        div = self.soup.find('div', style=lambda x: x and 'font-size: 14pt' in x)
        return div.find('a').text if div else None

    def get_plugin_description(self):
        div = self.soup.find('div', id=lambda x: x and x.startswith('post_message_'))
        if div:
            soup = BeautifulSoup(div.decode_contents(), 'html.parser')
            for code_block in soup.find_all('code'):
                wrapper = soup.new_tag('div', **{'class': 'mockup-code'})
                pre = soup.new_tag('pre', **{'data-prefix': '$'})
                code_block.wrap(pre)
                pre.wrap(wrapper)
            return markdown.markdown(str(soup))
        return None

    def get_plugin_author(self):
        div = self.soup.find('div', id=lambda x: x and x.startswith('postmenu_'))
        if div:
            author_tag = div.find('a', class_='bigusername')
            if author_tag:
                return {
                    "name": author_tag.get_text(strip=True),
                    "profile_url": f"{self.get_blank_url()}{author_tag['href']}"
                }
        return {
            "name": "Unknown",
            "profile_url": None
        }

    def get_files(self):
        fieldset = self.soup.find('fieldset', class_='fieldset')
        files = []
        if fieldset:
            for a_tag in fieldset.find_all('a', href=True):
                file_name = a_tag.text.strip()
                file_url = a_tag['href']

                if file_name == "Get Source":
                    sp_file_name = a_tag.find_next_sibling(text=True).strip().split(" - ")[0].replace("(", "").strip()
                    files.append(
                        {"source": {"file_name": sp_file_name, "url": f"{self.get_blank_url()}{file_url}"}})
                if file_name == "Get Plugin":
                    files.append({"plugin": {"file_name": "Get Plugin", "url": file_url}})
                if "smx" in file_name:
                    files.append(
                        {"compiled_plugin": {"file_name": file_name, "url": f"{self.get_blank_url()}{file_url}"}})
                if file_name.endswith(".zip"):
                    files.append(
                        {"zip_attachment": {"file_name": file_name, "url": f"{self.get_blank_url()}{file_url}"}})
        return files

    def get_links(self):
        files = self.get_files()
        for file in files:
            if "plugin" in file:
                source_file = [f for f in files if "source" in f][0]
                file['plugin']['file_name'] = source_file['source']['file_name'].split(".")[0] + ".smx"
        return files

    # def get_file(self, file_type, sp_file_name=None):
    #     fieldset = self.soup.find('fieldset', class_='fieldset')
    #     files = []
    #     if fieldset:
    #         for a_tag in fieldset.find_all('a', href=True):
    #             file_name = a_tag.text.strip()
    #             file_url = a_tag['href']
    #             if file_name == file_type:
    #                 if file_type == "Get Source":
    #                     sp_file_name = a_tag.find_next_sibling(text=True).strip().split(" - ")[0].replace("(",
    #                                                                                                       "").strip()
    #                     files.append(
    #                         {"source": {"file_name": sp_file_name, "url": f"{self.get_blank_url()}{file_url}"}})
    #                 if file_type == "Get Plugin":
    #                     files.append({"plugin": {"file_name": sp_file_name.split(".")[0] + ".smx", "url": file_url}})
    #                 if "smx" in file_name:
    #                     files.append(
    #                         {"compiled_plugin": {"file_name": file_name, "url": f"{self.get_blank_url()}{file_url}"}})
    #             if file_name.endswith(".zip"):
    #                 files.append(
    #                     {"zip_attachment": {"file_name": file_name, "url": f"{self.get_blank_url()}{file_url}"}})
    #     return files
    #
    # def get_links(self):
    #     links = []
    #     source_files = self.get_file("Get Source")
    #     if source_files:
    #         links.extend(source_files)
    #         for source_file in source_files:
    #             if 'source' in source_file:
    #                 plugin_files = self.get_file("Get Plugin", source_file['source']['file_name'])
    #                 if plugin_files:
    #                     links.extend(plugin_files)
    #     compiled_files = self.get_file("smx")
    #     if compiled_files:
    #         links.extend(compiled_files)
    #     zip_files = self.get_file("zip")
    #     if zip_files:
    #         links.extend(zip_files)
    #     return links

    def get_plugin_info(self, plugin_url):
        details = self.get_plugin_details()
        return {
            "name": self.get_plugin_name(),
            "description": self.get_plugin_description() if self.get_plugin_description() else "No description available",
            "author": self.get_plugin_author(),
            "version": details.get('version') if details.get('version') else "1.0",
            "category": details.get('category') if details.get('category') else "Any",
            "game": details.get('game') if details.get('game') else "Team Fortress 2",
            "url": plugin_url,
            "download_links": self.get_links(),
        }

    def download_file(self, tag, plugin_file):
        response = requests.get(plugin_file.download_url)
        response.raise_for_status()
        file_path = self.file_manager.save_file(response, plugin_file, tag)
        return file_path

    def archive_files(self, plugin_id, plugin_name, version):
        archive_name = f"{plugin_name} {version}.zip"
        return self.file_manager.archive_files(plugin_id, archive_name, version)

    def save_to_db(self, plugin_info):
        category, _ = Category.objects.get_or_create(name=plugin_info['category'])
        supported_game, _ = SupportedGame.objects.get_or_create(name=plugin_info['game'], app_id=440,
                                                                icon="https://www.sourcemod.net/images/tf.gif")
        plugin = Plugin.objects.create(
            original_name=plugin_info['name'],
            description=plugin_info['description'],
            author=plugin_info['author']['name'],
            version=plugin_info['version'],
            url=plugin_info['url'],
            category=category,
        )
        plugin.supported_games.add(supported_game)
        tag, _ = Tag.objects.get_or_create(plugin=plugin, version=plugin_info['version'], defaults={"is_latest": True})

        plugin_files = []
        if len(plugin_info['download_links']) > 0:
            for link in plugin_info['download_links']:
                file_type = PluginFile.FileType.SP if "source" in link else PluginFile.FileType.SMX
                if "source" in link:
                    file_type = PluginFile.FileType.SP
                if "plugin" in link:
                    file_type = PluginFile.FileType.SMX
                if "compiled_plugin" in link:
                    file_type = PluginFile.FileType.SMX
                if "zip_attachment" in link:
                    file_type = PluginFile.FileType.ZIP
                plugin_files.append(PluginFile.objects.create(
                    file_type=file_type,
                    file_name=link[list(link.keys())[0]]['file_name'],
                    download_url=link[list(link.keys())[0]]['url'],
                    tag=tag
                ))
        return plugin, plugin_files

    def make_archive(self, name, version):
        plugin_dir = Path(settings.MEDIA_ROOT) / "downloads/plugins" / name
        archive_path = plugin_dir / f"{name}_{version}.zip"
        plugin_dir_files = [file for file in plugin_dir.rglob("*") if file.suffix != '.zip']
        with default_storage.open(archive_path, 'wb+') as archive:
            with zipfile.ZipFile(archive, 'w') as zip_file:
                for file in plugin_dir_files:
                    zip_file.write(file, file.relative_to(plugin_dir))
        return archive_path.name

    def get_plugin(self, plugin_url):
        response = requests.get(plugin_url)
        response.raise_for_status()
        self.soup = BeautifulSoup(response.content, 'html.parser')
        plugin_info = self.get_plugin_info(plugin_url)
        print(plugin_info)
        if Plugin.objects.filter(original_name=plugin_info['name'], author=plugin_info["author"]["name"]).exists():
            plugin = Plugin.objects.get(original_name=plugin_info['name'], author=plugin_info["author"]["name"])
            if Tag.objects.filter(plugin=plugin, version=plugin_info['version']).exists():
                return plugin

        plugin, plugin_file = self.save_to_db(plugin_info)
        return plugin

    def find_plugins(self):
        url = "https://www.sourcemod.net/plugins.php?cat=0&mod=5&title=&author=&description=&search=1"
        response = requests.get(url)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')
        plugins = []
        rows = soup.find_all('div', class_='well')[1].find('table').find_all('tr')[1:]
        for row in rows:
            name_a = row.find_all('td')[1].find('a')
            plugins.append({
                'name': name_a.text.strip(),
                'url': name_a['href'].strip()
            })
        return plugins

    def extract_downloaded_files(self, tag, plugin_files):
        plugin_dir = Path(settings.MEDIA_ROOT) / "downloads/plugins" / tag.plugin.id / tag.version / "temp"
        for file in plugin_files:
            self.file_manager.unzip(file.get_file_path(), plugin_dir)
            # Get files from the extracted directory and iterate to add to db
            self.file_manager.move_files(tag.plugin.id, tag.version, temp=True)
        # self.file_manager.move_files(tag.plugin.id, tag.version)
        self.add_extracted_files_to_db(tag)
        return plugin_dir

    def add_extracted_files_to_db(self, tag):
        plugin_dir = Path(settings.MEDIA_ROOT) / "downloads/plugins" / tag.plugin.id / tag.version / "files"
        added_files = set()

        for file in plugin_dir.rglob("*"):
            if file.suffix == ".sp" and file.name not in added_files:
                if not PluginFile.objects.filter(file_name=file.name, tag=tag,
                                                 file_type=PluginFile.FileType.SP).exists():
                    plugin_file = PluginFile.objects.create(
                        file_type=PluginFile.FileType.SP,
                        file_name=file.name,
                        tag=tag,
                    )
                    file_name = f"downloads/plugins/{tag.plugin.id}/{tag.version}/files/addons/sourcemod/scripting/{file.name}"
                    plugin_file.file.name = file_name
                    plugin_file.save()
                    added_files.add(file.name)
            if file.suffix == ".smx" and file.name not in added_files:
                if not PluginFile.objects.filter(file_name=file.name, tag=tag,
                                                 file_type=PluginFile.FileType.SMX).exists():
                    plugin_file = PluginFile.objects.create(
                        file_type=PluginFile.FileType.SMX,
                        file_name=file.name,
                        tag=tag,
                    )
                    file_name = f"downloads/plugins/{tag.plugin.id}/{tag.version}/files/addons/sourcemod/plugins/{file.name}"
                    plugin_file.file.name = file_name
                    plugin_file.save()
                    added_files.add(file.name)
