from django.urls import path, include
from plugins.api.urls import router as plugins_router

urlpatterns = [
    path("", include(plugins_router.urls)),
]