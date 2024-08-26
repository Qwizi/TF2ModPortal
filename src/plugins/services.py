import zipfile
from pathlib import Path

import markdown
import requests
from bs4 import BeautifulSoup
from django.conf import settings
from django.core.files.storage import default_storage

from plugins.models import Plugin, Category, SupportedGame, PluginFile, Tag


class SourceModPluginDownloader:
    def __init__(self, url):
        self.url = url
        self.soup = None
        self.version = None
        self.name = None
        self.path = f"downloads/plugins/{self.name}/"
        self.dir = Path(settings.MEDIA_ROOT) / self.path
        self.file_name = None
        self.plugin_url = None
        self.description = None
        self.author = None

    def get_blank_url(self):
        return self.url

    def get_plugin_details(self):
        # Extract plugin version
        table = self.soup.find('table', id=lambda x: x and x.startswith('post'))
        plugin_version = None
        plugin_category = None
        plugin_game = None
        # Extract plugin version
        version_div = table.find('div', string='Plugin Version: ')

        if version_div:
            parent_td = version_div.find_parent('td')
            if parent_td:
                next_td = parent_td.find_next_sibling('td')
                if next_td:
                    plugin_version = next_td.find('div').get_text(strip=True)

            # Extract plugin category
        category_div = table.find('div', string='Plugin Category: ')
        plugin_category = None
        if category_div:
            parent_td = category_div.find_parent('td')
            if parent_td:
                next_td = parent_td.find_next_sibling('td')
                if next_td:
                    plugin_category = next_td.find('div').get_text(strip=True)

        # Extract plugin game
        game_div = table.find('div', string='Plugin Game: ')
        plugin_game = None
        if game_div:
            parent_td = game_div.find_parent('td')
            if parent_td:
                next_td = parent_td.find_next_sibling('td')
                if next_td:
                    plugin_game = next_td.find('div').get_text(strip=True)
        return {
            'version': plugin_version,
            'category': plugin_category,
            'game': plugin_game
        }

    def get_plugin_name(self):
        # Get the plugin name from the title of the page
        plugin_name_div = self.soup.find('div', style=lambda x: x and 'font-size: 14pt' in x)
        if plugin_name_div:
            plugin_name = plugin_name_div.find('a').text
            return plugin_name
        return None

    def get_plugin_description(self):
        # Get the plugin description
        post_message_div = self.soup.find('div', id=lambda x: x and x.startswith('post_message_'))
        post_description = None
        if post_message_div:
            post_description = post_message_div.get_text(separator='\n', strip=True)
            post_description = markdown.markdown(post_description)
        return post_description

    def get_plugin_author(self):
        # Find the div with id starting with 'postmenu_'
        postmenu_div = self.soup.find('div', id=lambda x: x and x.startswith('postmenu_'))
        if postmenu_div:
            # Extract the author name and URL from the 'a' tag within this div
            author_tag = postmenu_div.find('a', class_='bigusername')
            if author_tag:
                author_name = author_tag.get_text(strip=True)
                author_url = f"{self.get_blank_url()}{author_tag['href']}"
                return {
                    "name": author_name,
                    "profile_url": author_url
                }
        return None

    def get_source_file(self):
        fieldset = self.soup.find('fieldset', class_='fieldset')
        if fieldset:
            for a_tag in fieldset.find_all('a', href=True):
                file_name = a_tag.text.strip()
                file_url = a_tag['href']
                if file_name == "Get Source":
                    # (vampire.sp - 142 views - 2.0 KB) -> vampire.sp
                    sp_file_name = a_tag.find_next_sibling(text=True).strip().split(" - ")[0].replace("(", "").strip()
                    return {
                        "source": {
                            "file_name": sp_file_name,
                            "url": f"{self.get_blank_url()}{file_url}"
                        }
                    }
        return None

    def get_compiled_file(self):
        fieldset = self.soup.find('fieldset', class_='fieldset')
        if fieldset:
            for a_tag in fieldset.find_all('a', href=True):
                file_name = a_tag.text.strip()
                file_url = a_tag['href']
                if "smx" in file_name:
                    return {
                        "compiled_plugin": {
                            "file_name": file_name,
                            "url": f"{self.get_blank_url()}{file_url}"
                        }
                    }
        return None

    def get_plugin_file(self, sp_file_name):
        fieldset = self.soup.find('fieldset', class_='fieldset')
        if fieldset:
            for a_tag in fieldset.find_all('a', href=True):
                file_name = a_tag.text.strip()
                file_url = a_tag['href']
                if file_name == "Get Plugin":
                    return {
                        "plugin": {
                            "file_name": sp_file_name.split(".")[0] + ".smx",
                            "url": file_url
                        }}
        return None

    def get_links(self):
        links = []
        source_file = self.get_source_file()
        if source_file:
            links.append(source_file)
            plugin_file = self.get_plugin_file(source_file['source']['file_name'])
            if plugin_file:
                links.append(plugin_file)
        compiled_file = self.get_compiled_file()
        if compiled_file:
            links.append(compiled_file)
        return links

    def get_plugin_info(self, plugin_url):
        details = self.get_plugin_details()
        return {
            "name": self.get_plugin_name(),
            "description": self.get_plugin_description(),
            "author": self.get_plugin_author(),
            "version": details['version'],
            "category": details['category'],
            "game": details['game'],
            "url": plugin_url,
            "download_links": self.get_links(),
        }

    def download_files(self, plugin, version):
        tag = Tag.objects.get(plugin=plugin, version=version)
        plugin_files = PluginFile.objects.filter(tag=tag)
        for plugin_file in plugin_files:
            response = requests.get(plugin_file.download_url)
            response.raise_for_status()
            file_path = None
            if plugin_file.file_type == PluginFile.FileType.SP:
                file_path = Path(
                    settings.MEDIA_ROOT) / "tmp/downloads/plugins/" / plugin.id / "addons/sourcemod/scripting" / plugin_file.file_name
            if plugin_file.file_type == PluginFile.FileType.SMX:
                file_path = Path(
                    settings.MEDIA_ROOT) / "tmp/downloads/plugins/" / plugin.id / "addons/sourcemod/plugins" / plugin_file.file_name
            file_path.parent.mkdir(parents=True, exist_ok=True)
            with default_storage.open(file_path, 'wb+') as destination:
                destination.write(response.content)
        return plugin

    def download_smx_file(self, plugin, version):
        tag = Tag.objects.get(plugin=plugin, version=version)

        smx_file = PluginFile.objects.filter(tag=tag, file_type=PluginFile.FileType.SMX).first()
        if smx_file:
            response = requests.get(smx_file.download_url)
            response.raise_for_status()
            file_path = Path(
                settings.MEDIA_ROOT) / "downloads/plugins/" / plugin.id / "addons/sourcemod/plugins" / smx_file.file_name
            with default_storage.open(file_path, 'wb+') as destination:
                destination.write(response.content)
            return smx_file.file_name
        # remove from the link last part https://forums.alliedmods.net/showthread.php?p=548207 only https://forums.alliedmods.net/
        # url = self.url.split("showthread.php")[0]
        # response = requests.get(f"{url}/{smx_link[1]}")
        # response.raise_for_status()
        # name = smx_link[0].split(".")[0]
        # file_name = Path(smx_link[0]).name
        # file_path = Path(settings.MEDIA_ROOT) / "downloads/plugins/" / name / "addons/sourcemod/plugins" / file_name
        # file_path.parent.mkdir(parents=True, exist_ok=True)
        # with default_storage.open(file_path, 'wb+') as destination:
        #     destination.write(response.content)
        # return file_name

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

    def save_to_db(self, plugin_info):
        category, created_category = Category.objects.get_or_create(name=plugin_info['category'])
        supported_game, created_game = SupportedGame.objects.get_or_create(name=plugin_info['game'], app_id=440,
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
        tag, tag_created = Tag.objects.get_or_create(plugin=plugin, version=plugin_info['version'], defaults={
            "is_latest": True
        })

        plugin_files = []
        for link in plugin_info['download_links']:
            file_type = None
            if "source" in link:
                file_type = PluginFile.FileType.SP
                plugin_files.append(PluginFile.objects.create(
                    file_type=file_type,
                    file_name=link["source"]['file_name'],
                    download_url=link["source"]['url'],
                    tag=tag
                ))
            if "compiled_plugin" in link:
                file_type = PluginFile.FileType.SMX
                plugin_files.append(PluginFile.objects.create(
                    file_type=file_type,
                    file_name=link["compiled_plugin"]['file_name'],
                    download_url=link["compiled_plugin"]['url'],
                    tag=tag
                ))
            if "plugin" in link:
                file_type = PluginFile.FileType.SMX
                plugin_files.append(PluginFile.objects.create(
                    file_type=file_type,
                    file_name=link["plugin"]['file_name'],
                    download_url=link["plugin"]['url'],
                    tag=tag
                ))
        return plugin, plugin_files

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

    def get_plugin(self, plugin_url):
        # Download the plugin from the SourceMod website
        response = requests.get(plugin_url)
        response.raise_for_status()

        # Parse the HTML content
        self.soup = BeautifulSoup(response.content, 'html.parser')
        plugin_info = self.get_plugin_info(plugin_url)

        if Plugin.objects.filter(original_name=plugin_info['name'], author=plugin_info["author"]["name"]).exists():
            plugin = Plugin.objects.get(name=plugin_info['name'], author=plugin_info["author"]["name"])
            if Tag.objects.filter(plugin=plugin, version=plugin_info['version']).exists():
                print(f"Plugin {plugin.name} already exists in the database")
                return

        plugin, plugin_file = self.save_to_db(plugin_info)
        print(f"Saved plugin {plugin.name} to the database")

    def find_plugins(self):
        url = "https://www.sourcemod.net/plugins.php?cat=0&mod=5&title=&author=&description=&search=1"
        response = requests.get(url)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')
        plugins = []

        # find second div with class well
        well = soup.find_all('div', class_='well')[1]
        table = well.find('table')
        # find all rows in the table and skip the first one
        rows = table.find_all('tr')[1:]
        for row in rows:
            # skip header row td not th
            name_td = row.find_all('td')[1]
            name_a = name_td.find('a')
            plugin_name = name_a.text.strip()
            plugin_url = name_a['href'].strip()
            plugins.append({
                'name': plugin_name,
                'url': plugin_url
            })

        return plugins
# smx_file_name = None
# sp_file_name = None
# translation_file_name = None
# for link in links.items():
#     if "smx" in link[0]:
#         smx_file_name = self.download_smx_file(link)
#         break
# for link in links.items():
#     if "smx" in link[0]:
#         self.download_smx_file(link)
#         print(f"Downloaded {smx_file_name}")
#     if "Get Source" in link[0]:
#         print(f"Downloading {link[0]}")
#         sp_file_name = self.download_sp_file(link, smx_file_name)
#     if "txt" in link[0]:
#         print(f"Downloading {link[0]}")
#         translation_file_name = self.download_translation_file(link, smx_file_name)
#         print(f"Downloaded {translation_file_name}")
# zip_file = self.make_archive(smx_file_name.split(".")[0], "1.0")
# self.save_to_db(name=smx_file_name.split(".")[0], version="1.0", smx_file=smx_file_name, sp_file=sp_file_name,
#                 cfg_file=translation_file_name, zip_file=zip_file)
