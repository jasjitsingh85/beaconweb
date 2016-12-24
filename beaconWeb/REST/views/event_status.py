from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import authentication
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework import permissions
from beaconWeb.apps.beacon.common.common_utils import check_into_event


class EventStatusAPI(APIView):

    permission_classes = (permissions.AllowAny,)

    def post(self, request, format=None):
        response = {}
        check_into_event(request.DATA)
        return Response(response, status=status.HTTP_200_OK)