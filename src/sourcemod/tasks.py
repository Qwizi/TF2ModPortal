from pathlib import Path

from celery import shared_task
from django.conf import settings

from sourcemod.services import SourceModDownloader
from tf2modportal.services import FileExtractor


@shared_task
def download_latest_sourcemod_version():
    # Fetch the SourceMod downloads page
    try:
        sourcemod_downloader = SourceModDownloader()
        return sourcemod_downloader.download()
    except Exception as e:
        return {"status": "error", "error": str(e)}


@shared_task
def extract_sourcemod_files():
    windows_dir = Path(settings.MEDIA_ROOT) / 'downloads/sourcemod/windows'
    linux_dir = Path(settings.MEDIA_ROOT) / 'downloads/sourcemod/linux'
    build_dir = Path(settings.MEDIA_ROOT) / 'build'

    extractor_windows = FileExtractor(windows_dir, linux_dir, build_dir)
    extractor_windows.extract_files("linux")
    extractor_windows.extract_files("windows")
