from rest_framework.parsers import JSONParser
from rest_framework.response import Response
from rest_framework.views import APIView

from mmetering.summaries import LoadProfileOverview, DataOverview

class APILoadProfileView(APIView):
  """Powers loadprofile dashboard widget."""
  parser_classes = (JSONParser,)

  def get(self, request, format=None):
    loadprofile = LoadProfileOverview(request.GET)
    return Response(loadprofile.to_dict())

class APIDataOverviewView(APIView):
  parser_classes = (JSONParser,)

  def get(self, request, format=None):
    overview = DataOverview(request.GET)
    return Response(overview.to_dict())
