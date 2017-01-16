from rest_framework import viewsets
from rest_framework.filters import OrderingFilter
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from rest_framework.views import APIView

from mmetering.summaries import LoadProfileOverview

class APIClass(APIView):
  test = "hallo"

class APILoadProfileView(APIClass):
  """Powers loadprofile dashboard widget."""

  def get(self, request, format=None):
    overview = LoadProfileOverview(request.GET)
    return Response(overview.to_dict())