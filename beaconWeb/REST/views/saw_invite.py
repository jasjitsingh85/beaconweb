from django.conf import settings
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import authentication
from rest_framework.authtoken.models import Token
from rest_framework import status
from beaconWeb.apps.beacon.common.utils.saw_invite import *


class SawInviteAPI(APIView):
    """
    Anytime a user opens a Hotspot's detail page (the last page of the flow), you should post to saw_invite
    POST (Saw invite) - Required params: beacon_id
    beacon_id -- ID of Beacon

    """

    authentication_classes = (authentication.TokenAuthentication,)

    def post(self, request, format=None):
        response = {}
        auth_token = request.auth
        if str(auth_token) == settings.MOBILE_VIEW_TOKEN:
            if 'inviteId' in request.DATA:
                invite_id = request.DATA["inviteId"]
                print invite_id
                response['message'] = mobileview_saw_invite(invite_id)
                return Response(response, status=status.HTTP_200_OK)
            else:
                response['message'] = "inviteId not provided"
                return Response(response, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        elif Token.objects.filter(key=auth_token).exists():
            token = Token.objects.get(key=auth_token)
            #just change to false to stop showing prompt in app
            response['show_prompt'] = saw_invite(token.user, request.DATA)
            return Response(response, status=status.HTTP_200_OK)
        else:
            response['message'] = "No user associated with token found"
            return Response(response, status=status.HTTP_401_UNAUTHORIZED)