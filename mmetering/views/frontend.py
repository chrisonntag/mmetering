from django.shortcuts import render, render_to_response
from django.views import View
from django.views.generic import TemplateView
from mmetering.summaries import DataOverview

from django.views.generic.edit import FormView
from mmetering.forms import ContactForm

class IndexView(TemplateView):
  def get(self, request, *args, **kwargs):
    data = DataOverview(request.GET)
    return render(request, 'mmetering/home.html', data.to_dict())

def render_download(request):
  return render(request, 'mmetering/download.html')

def render_contact(request):
  return render(request, 'mmetering/contact.html')

class ContactView(FormView):
  template_name = 'mmetering/contact.html'
  form_class = ContactForm
  success_url = '/contact'

  def form_valid(self, form):
    form.send_email()
    return super(ContactView, self).form_valid(form)
