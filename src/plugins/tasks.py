from celery import shared_task

from plugins.services import SourceModPluginDownloader


@shared_task
def download_plugin():
    plugin_downloader = SourceModPluginDownloader("https://forums.alliedmods.net/showthread.php?p=2806692")
    return plugin_downloader.download()
