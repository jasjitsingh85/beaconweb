from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import authentication
from rest_framework.authtoken.models import Token
from rest_framework import status
from beaconWeb.apps.beacon.models.point_of_sale import PointOfSale
from beaconWeb.apps.beacon.models.tab import Tab
from beaconWeb.apps.beacon.models.tab_item import TabItem
from beaconWeb.REST.serializers import TabItemSerializer, TabSerializer
from beaconWeb.apps.beacon.common.utils.point_of_sale import get_tab_and_tab_items, close_tab

class TabAPI(APIView):

    authentication_classes = (authentication.TokenAuthentication,)

    def get(self, request, format=None):
        response = {}
        auth_token = request.auth
        if Token.objects.filter(key=auth_token).exists():
            token = Token.objects.get(key=auth_token)
            user = token.user
            print user.username
            tab, tab_items = get_tab_and_tab_items(user, request.QUERY_PARAMS)
            response['tab_items'] = TabItemSerializer(tab_items, many=True).data
            response['tab'] = TabSerializer(tab).data
            return Response(response, status=status.HTTP_200_OK)
        else:
            response['message'] = "Auth token does not exist"
            return Response(response, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def post(self, request, format=None):
        response = {}
        auth_token = request.auth
        if Token.objects.filter(key=auth_token).exists():
            token = Token.objects.get(key=auth_token)
            user = token.user
            print user.username
            tab = close_tab(user, request.DATA)
            if not tab:
                return Response(response, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            if tab.payment_authorization:
                response['payment_successful'] = True
            else:
                response['payment_successful'] = False
            response['tab'] = TabSerializer(tab).data
            return Response(response, status=status.HTTP_200_OK)
        else:
            response['message'] = "Auth token does not exist"
            return Response(response, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

