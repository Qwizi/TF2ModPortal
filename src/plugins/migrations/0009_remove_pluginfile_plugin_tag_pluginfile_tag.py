# Generated by Django 5.1 on 2024-08-26 16:49

import django.db.models.deletion
import prefix_id.field
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('plugins', '0008_alter_plugin_slug'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='pluginfile',
            name='plugin',
        ),
        migrations.CreateModel(
            name='Tag',
            fields=[
                ('id', prefix_id.field.PrefixIDField(editable=False, max_length=27, prefix='tag_', primary_key=True, serialize=False, unique=True)),
                ('tagged_name', models.CharField(max_length=255)),
                ('version', models.CharField(max_length=255)),
                ('is_latest', models.BooleanField(default=False)),
                ('plugin', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='tags', to='plugins.plugin')),
            ],
        ),
        migrations.AddField(
            model_name='pluginfile',
            name='tag',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='files', to='plugins.tag'),
        ),
    ]