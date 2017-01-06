from django.shortcuts import render
from mmetering.models import MeterData



def render_home(request):
  """A view of all bands."""
  data = MeterData.objects.all()
  return render(request, 'mmetering/home.html', {'data': data})
