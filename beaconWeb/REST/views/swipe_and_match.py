from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import authentication
from rest_framework.authtoken.models import Token
from beaconWeb.apps.beacon.common.utils.friends import *
from beaconWeb.apps.beacon.common.utils.swipe_and_match import *
import time
from django_rq import job
from django.conf import settings
from rest_framework import status
from beaconWeb.REST.serializers import DatingProfileSerializer


class SwipeMatchAPI(APIView):
    """
    """

    authentication_classes = (authentication.TokenAuthentication,)

    def get(self, request, format=None):
        response = {}
        auth_token = request.auth
        if Token.objects.filter(key=auth_token).exists():
            token = Token.objects.get(key=auth_token)
            dating_profile = get_dating_profile(token.user)
            if 'event_id' in request.QUERY_PARAMS:
                dating_queue = get_dating_queue_from_request(token.user, request.QUERY_PARAMS)
                matches = get_matches(token.user, request.QUERY_PARAMS)
                response['dating_profile'] = DatingProfileSerializer(dating_profile).data
                response['dating_queue'] = DatingProfileSerializer(dating_queue, many=True).data
                response['matches'] = DatingProfileSerializer(matches, many=True).data
                return Response(response, status.HTTP_200_OK)
            else:
                response['dating_profile'] = DatingProfileSerializer(dating_profile).data
                return Response(response, status.HTTP_200_OK)
        else:
            response['message'] = "No user associated with token found"
            return Response(response, status=status.HTTP_401_UNAUTHORIZED)

    def post(self, request, format=None):
        response = {}
        auth_token = request.auth
        if Token.objects.filter(key=auth_token).exists():
            token = Token.objects.get(key=auth_token)
            dating_profile = save_dating_profile(token.user, request.DATA)
            response['dating_profile'] = DatingProfileSerializer(dating_profile).data
            if 'event_id' in request.DATA:
                dating_queue = get_dating_queue(token.user, int(request.DATA['event_id']), dating_profile)
                matches = get_matches(token.user, request.DATA)
                response['dating_queue'] = DatingProfileSerializer(dating_queue, many=True).data
                response['matches'] = DatingProfileSerializer(matches, many=True).data
            return Response(response, status.HTTP_200_OK)
        else:
            response['message'] = "No user associated with token found"
            return Response(response, status=status.HTTP_401_UNAUTHORIZED)

    def put(self, request, format=None):
        response = {}
        auth_token = request.auth
        if Token.objects.filter(key=auth_token).exists():
            token = Token.objects.get(key=auth_token)
            dating_profile_match = save_match_selection(token.user, request.DATA)
            response['dating_profile_match'] = DatingProfileSerializer(dating_profile_match, many=True).data
            return Response(response, status.HTTP_200_OK)
        else:
            response['message'] = "No user associated with token found"
            return Response(response, status=status.HTTP_401_UNAUTHORIZED)