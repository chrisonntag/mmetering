from django.shortcuts import render
from django.views.generic import TemplateView
from mmetering.models import Activities
from mmetering.summaries import DataOverview
from mmetering.filegenerator import CSV, XLS

from django.views.generic.edit import FormView
from mmetering.forms import ContactForm

class IndexView(TemplateView):
  def get(self, request, *args, **kwargs):
    data = DataOverview(request.GET)
    return render(request, 'mmetering/home.html', data.to_dict())

class DownloadView(TemplateView):
  def saveActivity(self, request, file_ending):
    text = "Der Benutzer %s hat eine Zusammenfassung der " \
           "Verbrauchsdaten heruntergeladen" % (request.user.username)
    activity = Activities(title="%s-Datei heruntergeladen" % file_ending, text=text)
    activity.save()

  def get(self, request, *args, **kwargs):
    format = request.GET.get('format')
    if format == 'csv':
      self.saveActivity(request, "CSV")
      csv_file = CSV(request)
      return csv_file.getFile()
    elif format == 'xls':
      self.saveActivity(request, "Excel")
      xls_file = XLS(request)
      return xls_file.getFile()
    else:
      return render(request, 'mmetering/download.html', {})

class ContactView(FormView):
  template_name = 'mmetering/contact.html'
  form_class = ContactForm
  success_url = '/contact/success'

  def form_valid(self, form):
    # This method is called when valid form data has been POSTed.
    # It should return an HttpResponse.
    form.send_email()
    return super(ContactView, self).form_valid(form)
