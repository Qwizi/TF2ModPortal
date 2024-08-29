import re
import uuid
from pathlib import Path

import requests
from django.conf import settings
from django.core.files.storage import default_storage
from django.db import models
from django.utils.text import slugify
from prefix_id import PrefixIDField


class Tag(models.Model):
    id = PrefixIDField(prefix="tag", primary_key=True)
    tagged_name = models.CharField(max_length=255)
    plugin = models.ForeignKey('Plugin', on_delete=models.CASCADE, related_name='tags')
    version = models.CharField(max_length=255)
    is_latest = models.BooleanField(default=False)
    archive_file = models.FileField(upload_to='downloads/plugins', blank=True, null=True)

    def __str__(self):
        return f"{self.tagged_name}"

    def prepare_author(self):
        # Remove spaces from author name, replace with underscores, and make lowercase, e.g. qwizi
        return self.plugin.author.replace(" ", "_").lower()

    def prepare_tagged_name(self):
        # Make the final tagged name, e.g. qwizi/awesomest-plugin:1.0.0 like docker
        author = self.prepare_author()
        return f"{author}/{self.plugin.slug}:{self.version}"

    def save(self, *args, **kwargs):
        if not self.tagged_name:
            self.tagged_name = self.prepare_tagged_name()
        super().save(*args, **kwargs)


class PluginFile(models.Model):
    class FileType(models.TextChoices):
        SMX = 'smx', 'SourceMod Plugin'
        SP = 'sp', 'SourcePawn Script'
        CFG = 'cfg', 'Configuration File'
        ZIP = 'zip', 'Zip Archive'

    id = PrefixIDField(prefix="plugin_file", primary_key=True)
    file_name = models.CharField(max_length=255, default="plugin.smx")
    file_type = models.CharField(max_length=255, choices=FileType.choices, default=FileType.SMX)
    file = models.FileField(upload_to='downloads/plugins/', blank=True, null=True)
    tag = models.ForeignKey(Tag, on_delete=models.CASCADE, related_name='files', blank=True, null=True)
    download_url = models.URLField(blank=True, null=True)

    def __str__(self):
        return f"{self.file_type} {self.file.name}"

    def get_file_path(self):
        return Path(settings.MEDIA_ROOT) / self.file.name

    def get_file_name(self):
        return Path(self.file.name).name


class Category(models.Model):
    id = PrefixIDField(prefix="category", primary_key=True)
    name = models.CharField(max_length=255)
    slug = models.SlugField(unique=True)

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        self.slug = slugify(self.name)
        super().save(*args, **kwargs)


class SupportedGame(models.Model):
    id = PrefixIDField(prefix="game", primary_key=True)
    name = models.CharField(max_length=255)
    app_id = models.IntegerField()
    icon = models.URLField()

    def __str__(self):
        return self.name


class Plugin(models.Model):
    class PluginSource(models.TextChoices):
        SOURCEMOD = 'sourcemod', 'SourceMod'
        GITHUB = 'github', 'GitHub'

    id = PrefixIDField(prefix="plugin", primary_key=True)
    short_id = models.CharField(max_length=255, unique=True, blank=True, null=True)
    plugin_source = models.CharField(max_length=50, choices=PluginSource.choices, default=PluginSource.SOURCEMOD)
    supported_games = models.ManyToManyField(SupportedGame, related_name='plugins')
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='plugins', blank=True, null=True)
    slug = models.SlugField(unique=True, blank=True, null=True, max_length=255)
    name = models.CharField(max_length=255)
    original_name = models.CharField(max_length=255, blank=True, null=True)
    author = models.CharField(max_length=255, blank=True, null=True)
    version = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    url = models.URLField(null=True, blank=True)

    def __str__(self):
        return f"{self.name} - {self.plugin_source}"

    def prepare_name(self):
        # Remove any variations of TF2, Team Fortress 2, version numbers, dates, and special characters
        pattern = re.compile(
            r'\b(TF2|tf2|Team Fortress 2|v?\d+(\.\d+)*|(\d{4}-\d{2}-\d{2})|(\d{2}/\d{2}/\d{4})|[-_:\"\'{}\[\]\\/|.,()])\b',
            re.IGNORECASE)
        cleaned_name = pattern.sub('', self.original_name)
        # Remove any remaining special characters
        cleaned_name = re.sub(r'[-_:\"\'{}\[\]\\/|.,()]', '', cleaned_name)
        # Remove extra spaces
        cleaned_name = re.sub(r'\s+', ' ', cleaned_name)
        return cleaned_name.strip()

    def slugify(self):
        return slugify(self.name)

    def generate_short_id(self):
        while True:
            short_id = str(uuid.uuid4())[:8]
            if not Plugin.objects.filter(short_id=short_id).exists():
                return short_id

    def download_file(self, url, file_name, file_type):
        response = requests.get(url)
        response.raise_for_status()
        file_path = None
        if file_type == PluginFile.FileType.SP:
            file_path = Path(
                settings.MEDIA_ROOT) / "tmp/downloads/plugins/" / self.id / file_name
        if file_type == PluginFile.FileType.SMX:
            file_path = Path(
                settings.MEDIA_ROOT) / "tmp/downloads/plugins/" / self.id / file_name
        file_path.parent.mkdir(parents=True, exist_ok=True)
        with default_storage.open(file_path, 'wb+') as destination:
            destination.write(response.content)

    def get_files_to_download(self, version):
        tag = self.tags.filter(version=version).first()
        if not tag:
            return
        plugin_files = tag.files.all()
        return plugin_files, tag

    def get_tagged_name(self, version=None):
        if not version:
            return self.tags.first().tagged_name
        return self.tags.filter(version=version).first().tagged_name

    def get_latest_version(self):
        return self.tags.filter(is_latest=True).first().version

    def save(self, *args, **kwargs):
        if not self.short_id:
            self.short_id = self.generate_short_id()
        self.name = self.prepare_name()
        self.slug = self.slugify()
        super().save(*args, **kwargs)
