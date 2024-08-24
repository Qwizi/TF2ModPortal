from sourcemod.models import SourceMod
from tf2modportal.services import BaseSourceModeDownloader


class SourceModDownloader(BaseSourceModeDownloader):
  def __init__(self):
    super().__init__()
    self.model = SourceMod
