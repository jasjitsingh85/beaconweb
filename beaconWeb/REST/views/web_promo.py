from rest_framework.views import APIView
from rest_framework import status
from rest_framework.response import Response
from rest_framework.authtoken.models import Token
from rest_framework import permissions
from beaconWeb.apps.beacon.common.utils.rewards import *


class WebPromoAPI(APIView):
    """
    Text App Link Operations
    POST (send SMS): Required Params - phone
    """

    permission_classes = (permissions.AllowAny,)

    def post(self, request, format=None):
        response = {}
        promo_code = request.DATA['promo_code']
        event_id = int(request.DATA['event_id'])
        response['price'], response['content'] = check_web_promo_code(promo_code, event_id)
        if response['price'] and response['content']:
            return Response(response, status=status.HTTP_200_OK)
        else:
            return Response(response, status=status.HTTP_500_INTERNAL_SERVER_ERROR)