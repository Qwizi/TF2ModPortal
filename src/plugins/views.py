import os

from django.http import HttpResponse, JsonResponse, FileResponse
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.views import View
from django.views.generic import ListView, DetailView

from plugins.models import Plugin, Tag


class PluginListView(ListView):
    model = Plugin
    template_name = "plugins/index.html"
    paginate_by = 28
    context_object_name = "plugins"


class PluginDetailView(DetailView):
    model = Plugin
    template_name = 'plugins/detail.html'
    context_object_name = 'plugin'

    def get_object(self):
        tagged_name = self.kwargs['tagged_name']
        return get_object_or_404(Plugin, tags__tagged_name=tagged_name)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        tag = self.object.tags.get(tagged_name=self.kwargs['tagged_name'])
        files_structure = tag.get_files_structure()
        context['files_structure'] = files_structure
        return context


class PluginDownloadView(View):
    def get(self, request, *args, **kwargs):
        pk = self.kwargs['pk']
        tag = get_object_or_404(Tag, pk=pk)
        archive_file = tag.archive_file
        if archive_file:
            file_name = os.path.basename(archive_file.name)
            response = FileResponse(archive_file)
            response['Content-Disposition'] = f'attachment; filename="{file_name}"'
            return response
        return redirect(reverse("plugins:detail", kwargs={"tagged_name": tag.tagged_name}))
