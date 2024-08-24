from pathlib import Path

from celery import shared_task
from django.conf import settings

from metamod.services import MetaModDownloader
from tf2modportal.services import FileExtractor


@shared_task
def download_latest_metamod_version():
    try:
        metamod_downloader = MetaModDownloader()
        return metamod_downloader.download()
    except Exception as e:
        return {"status": "error", "error": str(e)}


@shared_task
def extract_metamod_files():
    windows_dir = Path(settings.MEDIA_ROOT) / 'downloads/metamod/windows'
    linux_dir = Path(settings.MEDIA_ROOT) / 'downloads/metamod/linux'
    build_dir = Path(settings.MEDIA_ROOT) / 'build'

    extractor_windows = FileExtractor(windows_dir, linux_dir, build_dir)
    extractor_windows.extract_files("linux")
    extractor_windows.extract_files("windows")
