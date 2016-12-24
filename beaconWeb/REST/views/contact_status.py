from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework import permissions
from beaconWeb.apps.beacon.common.utils.contact_status import *
from rest_framework.authtoken.models import Token


class ContactStatusAPI(APIView):

    permission_classes = (permissions.AllowAny,)

    def put(self, request, format=None):
        response = {}
        data = request.DATA
        update_contact_status(data)
        return Response(response, status=status.HTTP_200_OK)


    def post(self, request, format=None):
        response = {}
        auth_token = request.auth
        token = Token.objects.get(key=auth_token)
        update_contact_status_for_referred_phone(token.user, request.DATA)
        return Response(response, status=status.HTTP_200_OK)
