from rest_framework import serializers

from plugins.models import Plugin, PluginFile, Tag


class PluginFileSerializer(serializers.ModelSerializer):
    class Meta:
        model = PluginFile
        fields = '__all__'


class TagSerializer(serializers.ModelSerializer):
    files = PluginFileSerializer(many=True, read_only=True)

    class Meta:
        model = Tag
        fields = '__all__'


class PluginSerializer(serializers.ModelSerializer):
    tags = TagSerializer(many=True, read_only=True)

    class Meta:
        model = Plugin
        fields = '__all__'
