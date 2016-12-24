from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import authentication
from beaconWeb.apps.beacon.models.deal_status import DealStatus
from beaconWeb.REST.serializers import DealStatusSerializer, BeaconWithDealStatusSerializer
from beaconWeb.apps.beacon.common.common_utils import add_extra_hotspot_properties
from beaconWeb.apps.beacon.common.utils.encryption import simple_int_hash
from rest_framework import status
from django.conf import settings


class DealStatusAPI(APIView):

    authentication_classes = (authentication.TokenAuthentication,)

    def get(self, request, format=None):
        response = {}
        auth_token = request.auth
        if str(auth_token) == settings.MOBILE_VIEW_TOKEN:
            status_id = int(request.QUERY_PARAMS['deal_status_id'])
            # status_id = simple_int_hash(status_id)
            deal_status = DealStatus.objects.select_related('deal', 'beacon').get(pk=status_id)
            beacon = add_extra_hotspot_properties(deal_status.beacon)
            response['beacon'] = BeaconWithDealStatusSerializer(beacon).data
            response['contact_deal_status'] = DealStatusSerializer(deal_status).data
        return Response(response, status=status.HTTP_200_OK)