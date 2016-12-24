from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import authentication
from beaconWeb.apps.beacon.models.deal import Deal
from beaconWeb.REST.serializers import DealSerializer
from rest_framework import permissions
from rest_framework import status
from beaconWeb.apps.merchant.utils import *
from rest_framework.authtoken.models import Token
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User

class MerchantDealsAPI(APIView):

    authentication_classes = (authentication.TokenAuthentication,)

    def get(self, request, format=None):
        response = {}
        auth_token = request.auth
        if Token.objects.filter(key=auth_token).exists():
            token = Token.objects.get(key=auth_token)
            default_deal, recurring_deal = get_merchant_deals(token.user.profile.deal_place)
            response['default_deal'] = DealSerializer(default_deal, many=True).data
            response['recurring_deal'] = DealSerializer(recurring_deal, many=True).data
            return Response(response, status=status.HTTP_200_OK)
        else:
            return Response(response, status=status.HTTP_401_UNAUTHORIZED)

    # #register a signal to create restframework auth tokens when new users are saved
    # @receiver(post_save, sender=User)
    # def create_auth_token(sender, instance=None, created=False, **kwargs):
    #     print "received user post-save signal"
    #     if created:
    #         Token.objects.create(user=instance)