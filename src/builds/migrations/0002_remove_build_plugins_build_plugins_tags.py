# Generated by Django 5.1 on 2024-08-26 18:39

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('builds', '0001_initial'),
        ('plugins', '0012_plugin_original_name'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='build',
            name='plugins',
        ),
        migrations.AddField(
            model_name='build',
            name='plugins_tags',
            field=models.ManyToManyField(related_name='builds', to='plugins.tag'),
        ),
    ]
