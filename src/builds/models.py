from django.conf import settings
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from prefix_id import PrefixIDField

from builds.services import BuildService


class Build(models.Model):
    id = PrefixIDField(primary_key=True, prefix='build', editable=False, max_length=255)
    name = models.CharField(max_length=255)
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    description = models.TextField()
    version = models.CharField(max_length=50)
    plugins_tags = models.ManyToManyField('plugins.Tag', related_name='builds')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name


@receiver(post_save, sender=Build)
def build_post_save(sender, instance, created, **kwargs):
    build_service = BuildService()
    print(build_service.move_files(instance))
    # print(build_service.archive_files(instance))
