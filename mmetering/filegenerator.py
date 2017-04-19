import csv, xlsxwriter, io
from datetime import datetime, date, timedelta
from django.http import HttpResponse, QueryDict
from mmetering.summaries import DownloadOverview

class DummyRequest:
  GET = None

class File:
  def __init__(self, request):
    self._request = DummyRequest
    if request is not None:
      self._request = request

class CSV(File):
  def getFile(self):
    # Create the HttpResponse object with the appropriate CSV header.
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="mmetering%s.csv"' % str(datetime.today())

    data = DownloadOverview(self._request.GET).getData()

    writer = csv.writer(response)
    writer.writerow(['SN', 'Bezug', 'Zaehlerstand', 'Uhrzeit'])
    for i in range(0, len(data)):
      writer.writerow(data[i])

    return response

class XLS(File):
  def getFileUntil(self, until):
    start = (until - timedelta(days=1)).strftime('%d.%m.%Y')
    end = until.strftime('%d.%m.%Y')
    self._request.GET = QueryDict("start=%s&end=%s" % (start, end))
    return self.getFile()

  def getFile(self):
    output = io.BytesIO()
    data = DownloadOverview(self._request.GET).getData()

    workbook = xlsxwriter.Workbook(output, {'in_memory': True})
    worksheet = workbook.add_worksheet()

    bold = workbook.add_format({'bold': True})
    time = workbook.add_format({'num_format': 'dd.mm.yy hh:mm'})
    # Widen the first column to make the text clearer.
    worksheet.set_column('B:B', 12)
    worksheet.set_column('C:C', 15)
    worksheet.set_column('D:D', 12)
    worksheet.set_column('E:E', 12)
    worksheet.write('B2', 'SN', bold)
    worksheet.write('C2', 'Bezug', bold)
    worksheet.write('D2', 'Zaehlerstand', bold)
    worksheet.write('E2', 'Uhrzeit', bold)

    for i in range(0, len(data)):
      # worksheet.write(zeile, spalte, wert)
      worksheet.write(i+2, 1, data[i][0])
      worksheet.write(i+2, 2, data[i][1])
      worksheet.write(i+2, 3, data[i][2])
      worksheet.write(i+2, 4, data[i][3], time)

    workbook.close()
    output.seek(0)

    response = HttpResponse(output.read(),
                            content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    response['Content-Disposition'] = 'attachment; filename="mmetering%s.xlsx"' % str(datetime.today())

    return response
