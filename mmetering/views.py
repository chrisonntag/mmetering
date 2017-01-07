import datetime
from django.shortcuts import render
from django.db.models import Max, Sum, Count, F, Avg, Q
from mmetering.models import Flat, Meter, MeterData

def render_home(request):
  data = MeterData.objects.all()
  import_ids = data.filter(meter__flat__modus__exact='IM').values('meter_id').annotate(max_value=Max('value')).order_by()

  q_statement = Q()
  for pair in import_ids:
    q_statement |= (Q(meter_id__exact=pair['meter_id']) & Q(value=pair['max_value']))

  current_month = datetime.datetime.now().month
  current_year = datetime.datetime.now().year
  last_month = datetime.datetime.now().month - 1 if datetime.datetime.now().month > 1 else 12
  last_year = datetime.datetime.now().year - 1

  return render(
    request,
    'mmetering/home.html',
    {
      'verbraucher': Flat.objects.filter(modus='IM'),
      'lieferaten': Flat.objects.filter(modus='EX'),
      'total': sum(data.filter(q_statement).values_list('value', flat=True).distinct()),
      'flats': Flat.objects.all(),
      'meter': Meter.objects.all(),
      'data': data,
      'avg_current': data.filter(saved_time__month=current_month, saved_time__year=current_year).aggregate(Avg('value')),
      'avg_last': data.filter(saved_time__month=last_month, saved_time__year=last_year).aggregate(Avg('value')),
      'avg_div': {'value__avg': 5.5}
    }
  )
