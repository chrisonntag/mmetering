import csv
import io
import xlsxwriter
from datetime import datetime, timedelta

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
    def get_file(self):
        # Create the HttpResponse object with the appropriate CSV header.
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="mmetering%s.csv"' % str(datetime.today())

        data = DownloadOverview(self._request.GET).get_data()

        writer = csv.writer(response)
        writer.writerow(['SN', 'Bezug', 'Zaehlerstand', 'Uhrzeit'])
        for i in range(0, len(data)):
            writer.writerow(data[i])

        return response


class XLS(File):
    def get_file_until(self, until):
        start = (until - timedelta(days=1)).strftime('%d.%m.%Y')
        end = until.strftime('%d.%m.%Y')
        self._request.GET = QueryDict("start=%s&end=%s" % (start, end))
        return self.get_file()

    def get_file(self):
        output = io.BytesIO()
        import_data, export_data = DownloadOverview(self._request.GET).get_data()
        data = import_data + [('', '')] + export_data

        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        worksheet = workbook.add_worksheet()

        bold = workbook.add_format({'bold': True})
        time = workbook.add_format({'num_format': 'dd.mm.yy hh:mm'})
        # Widen the first column to make the text clearer.
        worksheet.set_column(0, 9, width=15)

        table_headers = [('SN', ''), ('Bezug', ''), ('Zaehlerstand', 'kWh'), ('Uhrzeit', ''),
                         ('Gesamtverbrauch', 'kWh'), ('Anteil Versorger', 'kWh'), ('Anteil PV', 'kWh'),
                         ('Anteil BHKW', 'kWh'), ('Vormonat', 'kWh')]

        for i in range(0, 9):
            worksheet.write(0, i, table_headers[i][0], bold)
            if table_headers[i][1]:
                worksheet.write(1, i, '[%s]' % table_headers[i][1])

        for i in range(0, len(data)):
            for j in range(0, len(data[i])):
                # worksheet.write(row, column, content)
                if j == 3:
                    # provided the fourth value is the datetime
                    # TODO: make that more dynamically
                    worksheet.write(i + 3, j, data[i][j], time)
                else:
                    worksheet.write(i + 3, j, data[i][j])

        workbook.close()
        output.seek(0)

        response = HttpResponse(output.read(),
                                content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
        response['Content-Disposition'] = 'attachment; filename="mmetering%s.xlsx"' % str(datetime.today())

        return response
