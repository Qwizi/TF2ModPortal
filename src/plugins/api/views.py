from rest_framework import viewsets, filters

from plugins.api.serializers import PluginSerializer
from plugins.models import Plugin


class PluginViewSet(viewsets.ModelViewSet):
    queryset = Plugin.objects.all()
    serializer_class = PluginSerializer
    filter_backends = [filters.SearchFilter]
    search_fields = ["name", "tags__tagged_name"]