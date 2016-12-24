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

class MerchantLoginAPI(APIView):

    permission_classes = (permissions.AllowAny,)

    # def post(self, request, format=None):
    #     response = {}
    #     auth_token = request.auth
    #     response['new_haven_total_user_number'] = get_total_new_haven_users()
    #     response['new_haven_active_user_number'] = get_users_in_new_haven()
    #     response['chart_labels'], response['chart_data'] = get_engagement_labels_and_data(30)
    #     return Response(response, status=status.HTTP_200_OK)

    def post(self, request, format=None):
        response = {}
        response['merchant_token'], default_deal, recurring_deal = login_merchant_user(request.DATA)
        if default_deal is not None:
            response['default_deal'] = DealSerializer(default_deal).data
            response['recurring_deal'] = DealSerializer(recurring_deal).data
        else:
            response['message'] = "Your email or password is incorrect"
        return Response(response, status=status.HTTP_200_OK)

    def put(self, request, format=None):
        response = {}
        auth_token = request.auth
        if Token.objects.filter(key=auth_token).exists():
            token = Token.objects.get(key=auth_token)
            if change_password(token.user, request.DATA):
                return Response(response, status=status.HTTP_200_OK)
            else:
                return Response(response, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        else:
            return Response(response, status=status.HTTP_401_UNAUTHORIZED)

    # #register a signal to create restframework auth tokens when new users are saved
    # @receiver(post_save, sender=User)
    # def create_auth_token(sender, instance=None, created=False, **kwargs):
    #     print "received user post-save signal"
    #     if created:
    #         Token.objects.create(user=instance)