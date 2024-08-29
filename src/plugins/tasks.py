from pathlib import Path

from celery import shared_task, group, chord
from celery.exceptions import Ignore
from django.conf import settings
from django.core.files.storage import default_storage

from plugins.models import Plugin, PluginFile, Tag
from plugins.services import SourceModPluginDownloader


@shared_task(bind=True, name='plugins.tasks.get_plugin')
def get_plugin(self, plugin_url):
    try:
        plugin_downloader = SourceModPluginDownloader()
        plugin, plugin_file = plugin_downloader.get_plugin(plugin_url)
        download_plugin_files.s(plugin.id).apply_async()
        return {
            "status": "success",
            "message": f"Downloaded {plugin.name}",
            "plugin": plugin.name,
            "plugin_file": plugin_file,
            "url": plugin_url
        }
    except Exception as e:
        self.update_state(state='FAILURE', meta={'error': str(e)})
        raise Ignore()


@shared_task(bind=True, name='plugins.tasks.get_plugins')
def get_plugins(self):
    try:
        plugin_downloader = SourceModPluginDownloader()
        plugins = plugin_downloader.find_plugins()
        plugins_urls = [plugin['url'] for plugin in plugins]
        tasks = [get_plugin.s(plugin_url) for plugin_url in plugins_urls]
        job = group(tasks)
        job.apply_async()
        num_plugins = len(plugins)
        return {
            "status": "success",
            "message": f"Scheduled {num_plugins} plugins for download",
            "num_plugins": num_plugins,
        }
    except Exception as e:
        self.update_state(state='FAILURE', meta={'error': str(e)})
        raise Ignore()


@shared_task(bind=True, name='plugins.tasks.archive_plugin_files')
def archive_plugin_files(self, *args, tag_id=None, **kwargs):
    if tag_id is None:
        return {"status": "error", "message": "No tag_id provided"}
    try:
        tag = Tag.objects.get(id=tag_id)
        plugin = tag.plugin
        plugin_downloader = SourceModPluginDownloader()
        archive_file = plugin_downloader.archive_files(plugin.id, plugin.name, tag.version)
        archive_file_rel = Path(archive_file).relative_to(Path(settings.MEDIA_ROOT) / "downloads/plugins")
        if not tag.archive_file:
            with default_storage.open(archive_file, 'rb') as archive:
                tag.archive_file.save(archive_file_rel, archive)
            Path.unlink(Path(archive_file))
        return {
            "status": "success",
            "message": f"Archived {tag.plugin.name} {tag.version}",
            "tag_id": tag.id,
        }
    except Tag.DoesNotExist as e:
        self.update_state(state='FAILURE', meta={'error': str(e)})
        raise Ignore()
    except Exception as e:
        self.update_state(state='FAILURE', meta={'error': str(e)})
        raise Ignore()


@shared_task(bind=True, name='plugins.tasks.download_plugin_file')
def download_plugin_file(self, tag_id, plugin_file_id):
    try:
        tag = Tag.objects.get(id=tag_id)
        plugin_file = PluginFile.objects.get(id=plugin_file_id)
        plugin_downloader = SourceModPluginDownloader()
        plugin_downloader.download_file(tag, plugin_file)
        return {
            "status": "success",
            "message": f"Downloaded {plugin_file.file_name} for {tag.plugin.name} {tag.version}",
            "tag_id": tag.id,
            "plugin_file_id": plugin_file.id

        }
    except Exception as e:
        self.update_state(state='FAILURE', meta={'error': str(e)})
        raise Ignore()


@shared_task(bind=True, name='plugins.tasks.download_plugin_files')
def download_plugin_files(self, plugin_id):
    try:
        plugin = Plugin.objects.get(id=plugin_id)
        version = plugin.tags.filter(is_latest=True).first().version
        plugin_files, tag = plugin.get_files_to_download(version)

        # Log tag_id
        print(f"Starting download tasks for tag_id: {tag.id}")

        # Create a list of download tasks
        download_tasks = [download_plugin_file.s(tag.id, plugin_file.id) for plugin_file in plugin_files]

        # Chord with archiving task as the callback
        job = chord(download_tasks)(archive_plugin_files.s(tag_id=tag.id))

        return {
            "status": "success",
            "message": f"Scheduled {len(plugin_files)} files for download",
            "plugin": plugin.name,
            "tag_id": tag.id,
            "version": version
        }
    except Exception as e:
        self.update_state(state='FAILURE', meta={'error': str(e)})
        raise Ignore()
