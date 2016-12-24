from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import authentication
from beaconWeb.apps.beacon.models.deal import Deal
from beaconWeb.REST.serializers import DealSerializer
from rest_framework import status
from beaconWeb.apps.merchant.utils import add_deal, update_deal, deactivate_deal


class DealAPI(APIView):

    """
    GET (Get your user) - Required params: none

    """

    authentication_classes = (authentication.TokenAuthentication,)

    def get(self, request, format=None):
        response = {}
        deal_id = int(request.QUERY_PARAMS['deal_id'])
        deal = Deal.objects.get(pk=deal_id)
        response['deals'] = DealSerializer(deal).data
        return Response(response, status=status.HTTP_200_OK)

    def put(self, request, format=None):
        response = {}
        default_deal, recurring_deal = update_deal(request.DATA)
        response['default_deal'] = DealSerializer(default_deal, many=True).data
        response['recurring_deal'] = DealSerializer(recurring_deal, many=True).data
        return Response(response, status=status.HTTP_200_OK)

    def post(self, request, format=None):
        response = {}
        default_deal, recurring_deal = add_deal(request.DATA)
        response['default_deal'] = DealSerializer(default_deal, many=True).data
        response['recurring_deal'] = DealSerializer(recurring_deal, many=True).data
        return Response(response, status=status.HTTP_200_OK)

    def delete(self, request, format=None):
        response = {}
        default_deal, recurring_deal = deactivate_deal(request.DATA)
        response['default_deal'] = DealSerializer(default_deal).data
        response['recurring_deal'] = DealSerializer(recurring_deal).data
        return Response(response, status=status.HTTP_200_OK)