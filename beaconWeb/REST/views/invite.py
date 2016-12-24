from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import authentication
from rest_framework.authtoken.models import Token
from beaconWeb.apps.beacon.models.beacon import Beacon
from beaconWeb.apps.beacon.common.utils.invite import *
from rest_framework import status
from django.conf import settings


class InviteAPI(APIView):
    """
    When any user wants to invite more friends to an existing deal, use /invite/
    POST - Required params: beacon (send beacon_id), &invite_list[]={name:kamran, phone:123}&invite_list[]=...)
    beacon -- ID of Beacon
    invite_list[] -- this might be tricky, same as with other ones
    """

    authentication_classes = (authentication.TokenAuthentication,)

    def post(self, request, format=None):
        response = {}
        auth_token = request.auth
        if Token.objects.filter(key=auth_token).exists():
            token = Token.objects.get(key=auth_token)
            invite_list = request.DATA.getlist('invite_list[]')
            beacon_id = request.DATA['beacon']
            beacon = Beacon.objects.get(pk=beacon_id)
            if 'message' in request.DATA:
                invite_friends(token.user, beacon, invite_list, request.DATA['message'])
            else:
                invite_friends(token.user, beacon, invite_list)
            return Response(response, status=status.HTTP_200_OK)

    def get(self, request, format=None):
        response = {}
        auth_token = request.auth
        if str(auth_token) == settings.MOBILE_VIEW_TOKEN:
            beacon_id = request.QUERY_PARAMS['beacon_id']
            here_list, going_list, invited_list = get_guestlist_for_mobileview(beacon_id)
            response['here'] = here_list
            response['going'] = going_list
            response['invited'] = invited_list
            return Response(response, status=status.HTTP_200_OK)