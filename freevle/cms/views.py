# Create your views here.
from datetime import datetime

from django.views.generic.detail import DetailView
from django.shortcuts import render_to_response
from django.template import RequestContext

from freevle.news.models import NewsMessage

class PageDetailView(DetailView):
    def get_queryset(self):
        parent_slug = self.kwargs.get('parent', None)
        return self.model._default_manager.filter(parent__slug=parent_slug)

def index(request):
    now = datetime.now()
    lastnews = NewsMessage.objects.filter(publish__lt=now)
    if lastnews.count() > 0:
        lastnews = lastnews[0]
    data = RequestContext(request, {'lastnews': lastnews})
    return render_to_response('index.html', data)
