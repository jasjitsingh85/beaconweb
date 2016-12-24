from rest_framework.views import APIView
from rest_framework import status
from rest_framework.response import Response
from rest_framework.authtoken.models import Token
from rest_framework import permissions
from beaconWeb.apps.beacon.common.common_utils import store_email_status


class EmailStatusAPI(APIView):
    """
    Text App Link Operations
    POST (send SMS): Required Params - phone
    """

    permission_classes = (permissions.AllowAny,)

    def post(self, request, format=None):
        response = {}
        store_email_status(request.DATA)
        return Response(response, status=status.HTTP_200_OK)