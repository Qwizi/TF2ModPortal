# Generated by Django 5.1 on 2024-08-26 17:45

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('plugins', '0011_remove_tag_files_pluginfile_tag'),
    ]

    operations = [
        migrations.AddField(
            model_name='plugin',
            name='original_name',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
    ]