from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import authentication
from rest_framework.authtoken.models import Token
from beaconWeb.apps.beacon.common.utils.friends import *
import time
from django_rq import job
from django.conf import settings
from rest_framework import status
from beaconWeb.REST.serializers import ProfileSerializer, ContactSerializer

class FriendProfileAPI(APIView):
    """


    """

    authentication_classes = (authentication.TokenAuthentication,)

    def get(self, request, format=None):
        response = {}
        auth_token = request.auth
        if Token.objects.filter(key=auth_token).exists():
            token = Token.objects.get(key=auth_token)
            t0 = time.time()
            profiles = get_profiles(token.user)
            t1 = time.time()
            print "Profiles Call " + str(t1-t0)
            serialized_profiler = ProfileSerializer(profiles, many=True)
            response['all_profiles'] = serialized_profiler.data
            return Response(response, status.HTTP_200_OK)
        else:
            response['message'] = "No user associated with token found"
            return Response(response, status=status.HTTP_401_UNAUTHORIZED)