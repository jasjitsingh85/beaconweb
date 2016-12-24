from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import permissions
from beaconWeb.apps.happy_hours.models import HappyHour
from rest_framework import status
from beaconWeb.REST.serializers import HappyHourDetailSerializer


class HappyHourDetailAPI(APIView):

    permission_classes = (permissions.AllowAny,)
    def get(self, request, format=None):
        response = {}
        happy_hour_id = request.QUERY_PARAMS['id']
        if HappyHour.objects.filter(pk=happy_hour_id).exists():
            happy_hour = HappyHour.objects.get(pk=happy_hour_id)
            happy_hour.place.load_extras()
            serializer = HappyHourDetailSerializer(happy_hour)
            response['happy_hour'] = serializer.data
            return Response(response, status=status.HTTP_200_OK)
        else:
            return Response(response, status=status.HTTP_404_NOT_FOUND)