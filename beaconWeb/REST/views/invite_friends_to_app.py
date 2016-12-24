from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import authentication
from beaconWeb.apps.beacon.common.utils.deals import invite_friends_to_app
from rest_framework.authtoken.models import Token
from rest_framework import status


class InviteFriendsToAppAPI(APIView):

    """
    Set a new deal
    POST - Required Params:
    deal_id -- ID of deal
    time -- UNIX time stamp for deal start time
    custom_message -- message associated with deal
    invite_list[] --  invite_list[] usage: &invite_list[]={name:kamran, phone:123}&invite_list[]=...)
    """

    authentication_classes = (authentication.TokenAuthentication,)

    def post(self, request, format=None):
        response = {}
        user = Token.objects.get(key=request.auth).user
        invite_list = request.DATA.getlist('invite_list[]')
        custom_message = request.DATA.get('custom_message')
        invite_friends_to_app(user, invite_list, custom_message)
        return Response(response, status=status.HTTP_200_OK)