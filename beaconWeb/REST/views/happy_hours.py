from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import permissions
from beaconWeb.apps.happy_hours.utils import fetch_happy_hours
from rest_framework import status
from beaconWeb.REST.serializers import HappyHourSerializer
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger


class HappyHourAPI(APIView):

    permission_classes = (permissions.AllowAny,)
    def get(self, request, format=None):
        response = {}
        latitude = float(request.QUERY_PARAMS['latitude'])
        longitude = float(request.QUERY_PARAMS['longitude'])
        day = int(request.QUERY_PARAMS['day'])
        page = int(request.QUERY_PARAMS['page'])
        time = float(request.QUERY_PARAMS['time'])
        now = int(request.QUERY_PARAMS['now'])
        upcoming = int(request.QUERY_PARAMS['upcoming'])
        happy_hours = fetch_happy_hours(latitude, longitude, day, time, now, upcoming)
        page_size = 20
        paginator = Paginator(happy_hours, page_size)
        try:
            happy_hours = paginator.page(page)
        except PageNotAnInteger:
            happy_hours = paginator.page(1)
        except EmptyPage:
            happy_hours = paginator.page(paginator.num_pages)
        serializer = HappyHourSerializer(happy_hours, many=True)
        response['happy_hours'] = serializer.data
        response['page'] = page
        response['num_pages'] = paginator.num_pages
        return Response(response, status=status.HTTP_200_OK)