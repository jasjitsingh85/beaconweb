from rest_framework.views import APIView
from rest_framework import status
from rest_framework.response import Response
from beaconWeb.apps.beacon.common.utils.email_capture import store_email
from rest_framework import permissions


class EmailCaptureAPI(APIView):
    """
    Text App Link Operations
    POST (send SMS): Required Params - phone
    """

    permission_classes = (permissions.AllowAny,)

    def post(self, request, format=None):
        response = {}
        store_email(request.DATA)
        return Response(response, status=status.HTTP_200_OK)