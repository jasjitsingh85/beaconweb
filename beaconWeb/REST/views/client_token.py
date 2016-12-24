from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import authentication
from beaconWeb.apps.beacon.models.deal import Deal
from beaconWeb.REST.serializers import DealSerializer
from rest_framework import status
from rest_framework.authtoken.models import Token
from beaconWeb.apps.beacon.common.utils.payments import *
from beaconWeb.apps.merchant.utils import add_deal, update_deal, deactivate_deal


class ClientTokenAPI(APIView):

    """
    GET (Get your user) - Required params: none

    """

    authentication_classes = (authentication.TokenAuthentication,)

    def get(self, request, format=None):
        response = {}
        auth_token = request.auth
        if Token.objects.filter(key=auth_token).exists():
            token = Token.objects.get(key=auth_token)
            response['client_token'] = get_client_token(token.user)
            return Response(response, status=status.HTTP_200_OK)
        else:
            return Response(response, status=status.HTTP_500_INTERNAL_SERVER_ERROR)