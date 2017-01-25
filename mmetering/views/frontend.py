from django.shortcuts import render, render_to_response
from django.views import View
from django.views.generic import TemplateView
from mmetering.summaries import DataOverview
import csv
from django.http import HttpResponse
from datetime import datetime

from django.views.generic.edit import FormView
from mmetering.forms import ContactForm

class IndexView(TemplateView):
  def get(self, request, *args, **kwargs):
    data = DataOverview(request.GET)
    return render(request, 'mmetering/home.html', data.to_dict())

def render_download(request):
  # Create the HttpResponse object with the appropriate CSV header.
  response = HttpResponse(content_type='text/csv')
  response['Content-Disposition'] = 'attachment; filename="mmetering%s.csv"' % str(datetime.today())

  writer = csv.writer(response)
  writer.writerow(['First row', 'Foo', 'Bar', 'Baz'])
  writer.writerow(['Second row', 'A', 'B', 'C', '"Testing"', "Here's a quote"])

  return response

def render_contact(request):
  return render(request, 'mmetering/contact.html')

class ContactView(FormView):
  template_name = 'mmetering/contact.html'
  form_class = ContactForm
  success_url = '/contact'

  def form_valid(self, form):
    form.send_email()
    return super(ContactView, self).form_valid(form)
