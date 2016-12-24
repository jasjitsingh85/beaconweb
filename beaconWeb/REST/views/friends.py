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


class FriendsAPI(APIView):
    """
    Contact list storing, suggested friend list retrieving
    POST (store contacts) - Required params: contact (Usage: &contact[]={name:kamran, phone:123}&contact[]=...)
        (this might be tricky - if you have issues, refer to iOS project - or just email me)
    GET (get friends on Hotspot, recent friends, suggested friends) - Required params: none

    Response for GET:
    "Friends on Hotspot" group has key "all_profiles"
    "Recents" is split into keys "profile_recents" and "contacts_recents". These need to be combined on the front end.
    profile_recents are those recents contacts who are on Hotspot. contact_recents are those recents that aren't on Hotspot
    "Suggested" is also split into keys "users" and "contacts". Users are those who are suggested who are also on Hotspot
    contacts are those who are suggested who aren't on Hotspot


    """

    authentication_classes = (authentication.TokenAuthentication,)

    def post(self, request, format=None):
        response = {}
        auth_token = request.auth
        if Token.objects.filter(key=auth_token).exists():
            token = Token.objects.get(key=auth_token)
            contact_list = request.DATA.getlist('contact[]')
            store_contact_list(token.user, contact_list)
            return Response(response, status.HTTP_200_OK)
        else:
            response['message'] = "No user associated with token found"
            return Response(response, status=status.HTTP_401_UNAUTHORIZED)

    def get(self, request, format=None):
        response = {}
        auth_token = request.auth
        if Token.objects.filter(key=auth_token).exists():
            token = Token.objects.get(key=auth_token)
            t0 = time.time()
            # job = get_recent_and_suggested_list.delay(token.user)
            # while job.result is None:
            #     time.sleep(1)
            # profiles_suggested = job.result[0]
            # contacts_suggested = job.result[1]
            # profiles_recent = job.result[2]
            # contacts_recent = job.result[3]
            # all_profiles = job.result[4]
            profiles_suggested = []
            contacts_suggested = []
            profiles_recent = []
            contacts_recent = []
            all_profiles = []
            t1 = time.time()
            print "suggested call " + str(t1-t0)
            pfSerializer = ProfileSerializer(profiles_suggested, many=True)
            contactSerializer = ContactSerializer(contacts_suggested, many=True)
            profileRecentsSerializer = ProfileSerializer(profiles_recent, many=True)
            contactRecentsSerializer = ContactSerializer(contacts_recent, many=True)
            allProfilesSerializer = ProfileSerializer(all_profiles, many=True)
            response['all_profiles'] = allProfilesSerializer.data
            response['users'] = pfSerializer.data
            response['contacts'] = contactSerializer.data
            response['profile_recents'] = profileRecentsSerializer.data
            response['contacts_recents'] = contactRecentsSerializer.data
            return Response(response, status.HTTP_200_OK)
        else:
            response['message'] = "No user associated with token found"
            return Response(response, status=status.HTTP_401_UNAUTHORIZED)