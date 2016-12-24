from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import permissions
from beaconWeb.apps.beacon.common.utils.content import *
from django.conf import settings
from rest_framework.authtoken.models import Token
from beaconWeb.apps.beacon.common.utils.message import *
from rest_framework import status
from beaconWeb.REST.serializers import ContentSerializer


class ContentAPI(APIView):
    """
    Beacon operations
    GET (get message thread for beacon): Required Params - None
    """

    permission_classes = (permissions.AllowAny,)

    def get(self, format=None):
        response = {}
        content = ContentOption.objects.all()
        serializer = ContentSerializer(content, many=True)
        response['content'] = serializer.data
        return Response(response, status=status.HTTP_200_OK)