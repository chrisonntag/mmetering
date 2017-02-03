import csv
import xlsxwriter
import io
from django.shortcuts import render, render_to_response, redirect
from django.views import View
from django.views.generic import TemplateView
from django.contrib.auth import authenticate, login, logout
from mmetering.models import Activities
from mmetering.summaries import DataOverview, CSVResponse
from django.http import HttpResponse
from datetime import datetime

from django.views.generic.edit import FormView
from mmetering.forms import ContactForm

class IndexView(TemplateView):
  def get(self, request, *args, **kwargs):
    data = DataOverview(request.GET)
    return render(request, 'mmetering/home.html', data.to_dict())

class DownloadView(TemplateView):
  def getCSV(self, request):
    # Create the HttpResponse object with the appropriate CSV header.
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="mmetering%s.csv"' % str(datetime.today())

    data = CSVResponse().getData()

    writer = csv.writer(response)
    writer.writerow(['Zaehlernummer', 'Uhrzeit', 'Wert'])
    for i in range(0, len(data)):
      writer.writerow(data[i])

    text = "Der Benutzer %s hat eine Zusammenfassung der " \
           "Verbrauchsdaten bis zum %s heruntergeladen" % (request.user.username, datetime.today())
    activity = Activities(title="CSV-Datei heruntergeladen", text=text)
    activity.save()

    return response

  def getXLS(self, request):
    output = io.BytesIO()
    data = CSVResponse().getData()

    workbook = xlsxwriter.Workbook(output, {'in_memory': True})
    worksheet = workbook.add_worksheet()

    bold = workbook.add_format({'bold': True})
    time = workbook.add_format({'num_format': 'dd.mm.yy hh:mm'})
    # Widen the first column to make the text clearer.
    worksheet.set_column('A:A', 15)
    worksheet.set_column('B:B', 15)
    worksheet.write('A1', 'Zaehlernummer', bold)
    worksheet.write('B1', 'Uhrzeit', bold)
    worksheet.write('C1', 'Wert', bold)

    for i in range(1, len(data)):
      #worksheet.write(zeile, spalte, wert)
      worksheet.write(i, 0, data[i][0])
      worksheet.write(i, 1, data[i][1], time)
      worksheet.write(i, 2, data[i][2])

    workbook.close()
    output.seek(0)

    response = HttpResponse(output.read(),
                            content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    response['Content-Disposition'] = 'attachment; filename="mmetering%s.xlsx"' % str(datetime.today())

    text = "Der Benutzer %s hat eine Zusammenfassung der " \
           "Verbrauchsdaten bis zum %s heruntergeladen" % (request.user.username, datetime.today())
    activity = Activities(title = "Excel-Datei heruntergeladen", text = text)
    activity.save()

    return response

  def get(self, request, *args, **kwargs):
    format = request.GET.get('format');
    if format == 'csv':
      return self.getCSV(request)
    elif format == 'xls':
      return self.getXLS(request)
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
