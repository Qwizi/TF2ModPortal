# Generated by Django 5.1 on 2024-08-24 19:08

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('sourcemod', '0001_initial'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='sourcemod',
            name='file',
        ),
        migrations.AddField(
            model_name='sourcemod',
            name='linux_file',
            field=models.FileField(blank=True, null=True, upload_to='sourcemod/linux/'),
        ),
        migrations.AddField(
            model_name='sourcemod',
            name='windows_file',
            field=models.FileField(blank=True, null=True, upload_to='sourcemod/windows/'),
        ),
    ]
