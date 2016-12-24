from rest_framework.views import APIView
from rest_framework import status
from rest_framework.response import Response
from rest_framework.authtoken.models import Token
from rest_framework import permissions
from beaconWeb.apps.beacon.common.common_utils import text_app_link, text_app_link_no_free_drink, text_payment_link


class TextAppLinkAPI(APIView):
    """
    Text App Link Operations
    POST (send SMS): Required Params - phone
    """

    permission_classes = (permissions.AllowAny,)

    def post(self, request, format=None):
        response = {}
        if 'phone' in request.DATA and 'promo' in request.DATA:
            text_app_link_no_free_drink(request.DATA['phone'])
            return Response(response, status=status.HTTP_200_OK)
        elif 'phone' in request.DATA:
            text_app_link(request.DATA['phone'])
            return Response(response, status=status.HTTP_200_OK)
        elif 'phone_number' and 'event_id' in request.DATA:
            text_payment_link(request.DATA)
            return Response(response, status=status.HTTP_200_OK)
        else:
            response['message'] = "No user associated with token found"
            return Response(response, status=status.HTTP_500_INTERNAL_SERVER_ERROR)