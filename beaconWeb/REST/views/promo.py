from rest_framework.views import APIView
from rest_framework import status
from rest_framework.response import Response
from rest_framework.authtoken.models import Token
from rest_framework import permissions
from beaconWeb.apps.beacon.common.utils.rewards import *


class PromoAPI(APIView):
    """
    Text App Link Operations
    POST (send SMS): Required Params - phone
    """

    permission_classes = (permissions.AllowAny,)

    def get(self, request, format=None):
        response = {}
        auth_token = request.auth
        token = Token.objects.get(key=auth_token)
        promo_code = token.user.profile.promo_code
        response['promo_code'] = promo_code
        response['email_subject'] = get_email_subject()
        response['email_body'] = get_email_body(promo_code)
        response['sms_message'] = get_sms_message(promo_code)
        return Response(response, status=status.HTTP_200_OK)

    def post(self, request, format=None):
        response = {}
        auth_token = request.auth
        token = Token.objects.get(key=auth_token)
        promo_code = request.DATA['promo_code']
        response['message'] = check_promo_code(token.user, promo_code)
        return Response(response, status=status.HTTP_200_OK)