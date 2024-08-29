from django.conf import settings
from django.db import models
from prefix_id import PrefixIDField


class Build(models.Model):
    id = PrefixIDField(primary_key=True, prefix='build_', editable=False)
    name = models.CharField(max_length=255)
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    description = models.TextField()
    version = models.CharField(max_length=50)
    plugins_tags = models.ManyToManyField('plugins.Tag', related_name='builds')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name
