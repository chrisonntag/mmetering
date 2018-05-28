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
        data = import_data + [{}] + export_data

        assert len(import_data) > 0
        assert len(export_data) > 0

        print("Import data:")
        print(import_data)
        print("Export data:")
        print(export_data)

        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        worksheet = workbook.add_worksheet('Abrechnung')

        bold = workbook.add_format({'bold': True})
        dateformat = workbook.add_format({'num_format': 'dd.mm.yy hh:mm'})
        # Widen the first column in order to make the text clearer.
        worksheet.set_column(0, 9, width=15)

        # TODO: get headers from import_data dictionaries
        longest_header = max(import_data, key=len)
        table_headers = list(longest_header.keys())
        """
        [('PK', ''), ('SN', ''), ('Bezug', ''), ('Zaehlerstand', 'kWh'), ('Uhrzeit', ''),
        ('Gesamtverbrauch', 'kWh'), ('Anteil Versorger', 'kWh'), ('Anteil PV', 'kWh'),
        ('Anteil BHKW', 'kWh'), ('Vormonat', 'kWh')]
        """

        for i, header in enumerate(table_headers):
            worksheet.write(0, i, header, bold)

        for row, record in enumerate(data):
            row += 2  # move everything two rows downwards
            column = 0
            for key, value in record.items():
                if key == 'Uhrzeit':
                    # TODO: make that more dynamically
                    worksheet.write(row, column, value, dateformat)
                else:
                    worksheet.write(row, column, value)

                column += 1

        workbook.close()
        output.seek(0)

        response = HttpResponse(output.read(),
                                content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
        response['Content-Disposition'] = 'attachment; filename="mmetering%s.xlsx"' % str(datetime.today())

        return response
