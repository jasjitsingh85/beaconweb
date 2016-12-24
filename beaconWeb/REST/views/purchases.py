from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import authentication
from beaconWeb.apps.beacon.models.deal import Deal
from beaconWeb.REST.serializers import DealSerializer
from rest_framework import status
from rest_framework.authtoken.models import Token
from beaconWeb.apps.beacon.common.utils.payments import *
from beaconWeb.apps.merchant.utils import add_deal, update_deal, deactivate_deal


class PurchasesAPI(APIView):

    authentication_classes = (authentication.TokenAuthentication,)

    def post(self, request, format=None):
        response = {}
        auth_token = request.auth
        if Token.objects.filter(key=auth_token).exists():
            token = Token.objects.get(key=auth_token)
            if 'beacon_id' in request.DATA:
                response['dismiss_payment_modal'] = authorize_payment(token.user, request.DATA['beacon_id'], request.DATA['payment_nonce'])
            elif 'is_event' in request.DATA:
                if 'payment_nonce' in request.DATA:
                    response['dismiss_payment_modal'] = authorize_payment_for_event(token.user, request.DATA['payment_nonce'])
                else:
                    response['dismiss_payment_modal'] = authorize_payment_for_event(token.user)
            else:
                response['dismiss_payment_modal'] = authorize_payment(token.user, None, request.DATA['payment_nonce'])
            return Response(response, status=status.HTTP_200_OK)
        else:
            return Response(response, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def put(self, request, format=None):
        response = {}
        auth_token = request.auth
        if Token.objects.filter(key=auth_token).exists():
            token = Token.objects.get(key=auth_token)
            # if is_mobilizer(token.user, request.DATA['beacon_id']):
            payment_on_file = check_if_payment_on_file(token.user)
            if payment_on_file:
                if 'beacon_id' in request.DATA:
                    response['dismiss_payment_modal'] = authorize_payment(token.user, request.DATA['beacon_id'])
                else:
                    response['dismiss_payment_modal'] = True
            else:
                response['dismiss_payment_modal'] = False
            # else:
            #     response['dismiss_payment_modal'] = True
            return Response(response, status=status.HTTP_200_OK)
        else:
            return Response(response, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def get(self, request, format=None):
        response = {}
        auth_token = request.auth
        if Token.objects.filter(key=auth_token).exists():
            token = Token.objects.get(key=auth_token)
            response['payment_information'] = get_customer_payment(token.user)
            return Response(response, status=status.HTTP_200_OK)
        else:
            return Response(response, status=status.HTTP_500_INTERNAL_SERVER_ERROR)