from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import permissions
from rest_framework import status
from rest_framework.authtoken.models import Token
from beaconWeb.apps.beacon.common.utils.events import *
from beaconWeb.REST.serializers import EventsSerializer


class EventsAPI(APIView):

    permission_classes = (permissions.AllowAny,)

    def get(self, request, format=None):
        response = {}
        auth_token = request.auth
        token = Token.objects.get(key=auth_token)
        events = get_events_for_user(token.user)
        print str(events)
        response['events'] = EventsSerializer(events, many=True).data
        return Response(response, status=status.HTTP_200_OK)