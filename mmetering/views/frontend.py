from datetime import datetime, timedelta, date
from django.shortcuts import render, render_to_response
from django.db.models import Max, Sum, Count, F, Avg, Q
from django.template import RequestContext
from mmetering.models import Flat, Meter, MeterData
from django.views import View

class IndexView(View):
  template_name = 'mmetering/home.html'
  times = {
    'today':          date.today(),
    'yesterday':      date.today() - timedelta(days=1),
    'current_week':   (date.today()-timedelta(days=7), date.today()),
    'last_week':      (date.today()-timedelta(days=14), date.today()-timedelta(days=7)),
    'current_month':  (date.today()-timedelta(days=30), date.today()),
    'last_month':     (date.today()-timedelta(days=60), date.today()-timedelta(days=30))
  }

  def get(self, request):
    data = MeterData.objects.all()
    data = data.filter(meter__flat__modus__exact='IM')

    # get total consumption until today
    import_ids = data.filter(meter__flat__modus__exact='IM').values('meter_id').annotate(
      max_value=Max('value')).order_by()
    q_statement = Q()
    for pair in import_ids:
      q_statement |= (Q(meter_id__exact=pair['meter_id']) & Q(value=pair['max_value']))
    total = sum(data.filter(q_statement).values_list('value', flat=True).distinct())

    # get total consumption until last week
    import_ids_last = data.filter(meter__flat__modus__exact='IM', saved_time__lte=self.times['last_week'][1]).values(
      'meter_id').annotate(max_value=Max('value')).order_by()
    q_statement_last = Q()
    for pair in import_ids_last:
      q_statement_last |= (Q(meter_id__exact=pair['meter_id']) & Q(value=pair['max_value']))
    total_last_week = sum(data.filter(q_statement_last).values_list('value', flat=True).distinct())

    data_last_day = data.filter(saved_time__range=[self.times['yesterday'], self.times['today']])
    data = data_last_day.values('saved_time').annotate(value_sum=Sum('value'))

    if request.GET.get('start'):
      start = list(map(int, request.GET.get('start').split('/')))
      end = list(map(int, request.GET.get('end').split('/')))
      if start[1] == end[1]:
        start[1] -= 1

      startRange = date(start[2], start[0], start[1])
      endRange = date(end[2], end[0], end[1])

      data_query = MeterData.objects.all().filter(saved_time__range=[startRange, endRange])
      data = data_query.values('saved_time').annotate(value_sum=Sum('value'))

    return render(
      request,
      'mmetering/home.html',
      {
        'verbraucher': Flat.objects.filter(modus='IM'),
        'lieferaten': Flat.objects.filter(modus='EX'),
        'total': total / 1000,  # /1000 convert to kwH
        'total_last_week': total_last_week,
        'day_low': data_last_day.values('saved_time').order_by('value').first(),
        'day_high': data_last_day.values('saved_time').order_by('-value').first(),
        'data': data,
        'avg_current': {'value__avg': 7.6},
        'avg_last': {'value__avg': 5.4},
      }
    )

def render_download(request):
  return render(request, 'mmetering/download.html')
