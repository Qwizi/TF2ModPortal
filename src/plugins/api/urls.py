from rest_framework import routers

from plugins.api.views import PluginViewSet

router = routers.DefaultRouter()
router.register(r'plugins', PluginViewSet)
