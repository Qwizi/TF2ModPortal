from pathlib import Path

from celery import shared_task, group, chord, chain
from celery.exceptions import Ignore
from django.conf import settings
from django.core.files.storage import default_storage

from plugins.models import Plugin, PluginFile, Tag
from plugins.services import SourceModPluginDownloader


@shared_task(bind=True, name='plugins.tasks.get_plugin')
def get_plugin(self, plugin_url):
    try:
        plugin_downloader = SourceModPluginDownloader()
        plugin = plugin_downloader.get_plugin(plugin_url)
        download_plugin_files.s(plugin.id).apply_async()
        return {
            "status": "success",
            "message": f"Downloaded {plugin.name}",
            "plugin": plugin.name,
            "url": plugin_url
        }
    except Exception as e:
        self.update_state(state='FAILURE', meta={'error': repr(e)})
        raise Ignore()


@shared_task(bind=True, name='plugins.tasks.get_plugins')
def get_plugins(self):
    try:
        plugin_downloader = SourceModPluginDownloader()
        plugins = plugin_downloader.find_plugins()
        tasks = [get_plugin.s(plugin['url']) for plugin in plugins]
        job = group(tasks)
        job.apply_async()
        return {
            "status": "success",
            "message": f"Scheduled {len(plugins)} plugins for download",
            "num_plugins": len(plugins),
        }
    except Exception as e:
        self.update_state(state='FAILURE', meta={'error': str(e)})
        raise Ignore()


@shared_task(bind=True, name='plugins.tasks.archive_plugin_files')
def archive_plugin_files(self, *args, **kwargs):
    tag_id = kwargs.get("tag_id")
    if not tag_id:
        return {"status": "error", "message": "No tag_id provided"}
    try:
        tag = Tag.objects.get(id=tag_id)
        plugin_downloader = SourceModPluginDownloader()
        archive_file = plugin_downloader.archive_files(tag.plugin.id, tag.plugin.name, tag.version)
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


@shared_task(bind=True)
def extract_downloads_files(self, *args, **kwargs):
    try:
        tag_id = kwargs.get("tag_id")
        tag = Tag.objects.get(id=tag_id)
        plugin_downloader = SourceModPluginDownloader()
        plugin_files = tag.files.filter(file_type=PluginFile.FileType.ZIP)
        plugin_downloader.extract_downloaded_files(tag, plugin_files)
        return {
            "status": "success",
            "message": "Extracted downloaded files",
        }

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
        download_tasks = [download_plugin_file.s(tag.id, plugin_file.id) for plugin_file in plugin_files]
        # job = chord(download_tasks)(archive_plugin_files.s(tag_id=tag.id))
        post_download_tasks = []
        if any(plugin_file.file_type == PluginFile.FileType.ZIP for plugin_file in plugin_files):
            post_download_tasks.append(extract_downloads_files.s(tag_id=tag.id))
        post_download_tasks.append(archive_plugin_files.s(tag_id=tag.id))

        job = chord(download_tasks)(chain(*post_download_tasks))
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
