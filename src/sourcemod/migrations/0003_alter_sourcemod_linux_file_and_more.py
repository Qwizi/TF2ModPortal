# Generated by Django 5.1 on 2024-08-24 20:01

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('sourcemod', '0002_remove_sourcemod_file_sourcemod_linux_file_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='sourcemod',
            name='linux_file',
            field=models.FileField(blank=True, null=True, upload_to='downloads/sourcemod/linux/'),
        ),
        migrations.AlterField(
            model_name='sourcemod',
            name='windows_file',
            field=models.FileField(blank=True, null=True, upload_to='downloads/sourcemod/windows/'),
        ),
    ]
