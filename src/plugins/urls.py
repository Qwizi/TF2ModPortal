from django.urls import path

from plugins.views import PluginListView, PluginDetailView, PluginDownloadView

app_name = 'plugins'

urlpatterns = [
    path("", PluginListView.as_view(), name="index"),
    path("download/<str:pk>/", PluginDownloadView.as_view(), name="download"),
    path("<path:tagged_name>/", PluginDetailView.as_view(), name="detail"),

]
