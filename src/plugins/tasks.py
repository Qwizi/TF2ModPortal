from celery import shared_task, group

from plugins.models import Plugin
from plugins.services import SourceModPluginDownloader


@shared_task(bind=True)
def get_plugin(self, plugin_url):
    try:
        plugin_downloader = SourceModPluginDownloader("https://forums.alliedmods.net/")
        return plugin_downloader.get_plugin(plugin_url)
    except Exception as e:
        return {"status": "error", "error": str(e)}


@shared_task
def get_plugins():
    try:
        plugin_downloader = SourceModPluginDownloader("https://forums.alliedmods.net/")
        plugins = plugin_downloader.find_plugins()
        plugins_urls = [plugin['url'] for plugin in plugins]
        tasks = [get_plugin.s(plugin_url) for plugin_url in plugins_urls]
        job = group(tasks)
        job.apply_async()
    except Exception as e:
        return {"status": "error", "error": str(e)}


@shared_task
def download_file(plugin_id, url, file_name, file_type):
    try:
        plugin = Plugin.objects.get(id=plugin_id)
        print(f"Downloading {file_name} from {url}")
        plugin.download_file(url, file_name, file_type)
        return {"status": "success"}
    except Exception as e:
        return {"status": "error", "error": str(e)}


@shared_task
def download_plugin():
    try:
        plugins = Plugin.objects.all()
        for plugin in plugins:
            version = plugin.tags.filter(is_latest=True).first().version
            plugin_files = plugin.get_files_to_download(version)
            tasks = [download_file.s(plugin.id, plugin_file.download_url, plugin_file.file_name, plugin_file.file_type)
                     for plugin_file in plugin_files]
            job = group(tasks)
            job.apply_async()
        return {"status": "success"}

    except Exception as e:
        return {"status": "error", "error": str(e)}
