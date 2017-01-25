from datetime import datetime, timedelta, date
from django.shortcuts import render, render_to_response
from django.db.models import Max, Sum, Count, F, Avg, Q
from django.template import RequestContext
from mmetering.models import Flat, Meter, MeterData
from django.views import View
from django.views.generic import TemplateView
from mmetering.summaries import DataOverview

class IndexView(TemplateView):
  def get(self, request, *args, **kwargs):
    data = DataOverview(request.GET)
    return render(request, 'mmetering/home.html', data.to_dict())

def render_download(request):
  return render(request, 'mmetering/download.html')

def render_contact(request):
  return render(request, 'mmetering/contact.html')