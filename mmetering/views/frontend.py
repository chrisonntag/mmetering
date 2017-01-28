from django.shortcuts import render, render_to_response, redirect
from django.views import View
from django.views.generic import TemplateView
from django.contrib.auth import authenticate, login, logout
from mmetering.summaries import DataOverview, CSVResponse
import csv
from django.http import HttpResponse
from datetime import datetime

from django.views.generic.edit import FormView
from mmetering.forms import ContactForm

class IndexView(TemplateView):
  def get(self, request, *args, **kwargs):
    data = DataOverview(request.GET)
    return render(request, 'mmetering/home.html', data.to_dict())

class DownloadView(TemplateView):
  def get(self, request, *args, **kwargs):
    # Create the HttpResponse object with the appropriate CSV header.
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="mmetering%s.csv"' % str(datetime.today())

    data = CSVResponse().getData()

    writer = csv.writer(response)
    writer.writerow(['Zaehlernummer', 'Uhrzeit', 'Wert'])
    for i in range(0, len(data)):
      writer.writerow(data[i])

    return response

class ContactView(FormView):
  template_name = 'mmetering/contact.html'
  form_class = ContactForm
  success_url = '/contact/success'

  def form_valid(self, form):
    # This method is called when valid form data has been POSTed.
    # It should return an HttpResponse.
    form.send_email()
    return super(ContactView, self).form_valid(form)
