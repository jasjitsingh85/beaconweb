from django.contrib.auth.models import User
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import permissions
from rest_framework.authtoken.models import Token
from django.db.models.signals import post_save
from django.dispatch import receiver
from beaconWeb.common_utils import normalize_phone_number
from beaconWeb.apps.beacon.common.utils.user_profile import *
from beaconWeb.REST.serializers import ProfileSerializer
from rest_framework import status


class UserProfileAPI(APIView):
    """
    User profile operations
    POST (Create/Register a user) - Required Params: phone_number, password, first_name, last_name, email
    phone_number -- user's phone number
    password -- user's password
    first_name -- user's first name
    last_name -- user's last name
    email -- user's email
    GET (Get your user) - Required params: none
    PUT (Update your user) - password, first_name, last_name

    """
    permission_classes = (permissions.AllowAny,)

    def post(self, request, format=None):
        response = {}
        print str(request.DATA)
        normalizedPhoneNumber = normalize_phone_number(request.DATA['phone_number'])
        if User.objects.filter(username=request.DATA['phone_number']).exists() or Profile.objects.filter(normalized_phone=normalizedPhoneNumber).exists():
            response['message'] = "User with phone number already exists."
            return Response(response, status=status.HTTP_400_BAD_REQUEST)
        else:
            user = create_user(request.DATA)
            if user:
                if Profile.objects.filter(user=user).exists():
                    p = Profile.objects.get(user=user)
                    serializer = ProfileSerializer(p)
                    return Response(serializer.data)
            else:
                response['message'] = "Failed to create a user."
                return Response(response, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def get(self, request, format=None):
        response = {}
        auth_token = request.auth
        if Token.objects.filter(key=auth_token).exists():
            token = Token.objects.get(key=auth_token)
            if Profile.objects.filter(user=token.user).exists():
                pf = Profile.objects.get(user=token.user)
                serializer = ProfileSerializer(pf)
                return Response(serializer.data)
            else:
                response['message'] = "No profile associated with this user"
                return Response(response, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        else:
            response['message'] = "No user associated with token found"
            return Response(response, status=status.HTTP_401_UNAUTHORIZED)

    def put(self, request, format=None):
        response = {}
        auth_token = request.auth
        if Token.objects.filter(key=auth_token).exists():
            token = Token.objects.get(key=auth_token)
            if 'password' and 'first_name' and 'last_name' in request.DATA:
                update_user(token.user, request.DATA)
                return Response(response, status=status.HTTP_200_OK)
            elif 'device_token' in request.DATA:
                response['message'] = add_device_and_assign_to_user(token.user, request.DATA)
                return Response(response, status=status.HTTP_200_OK)
            else:
                response['message'] = "Failed to update user"
                return Response(response, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        else:
            response['message'] = "No user associated with token found to update"
            return Response(response, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


    #register a signal to create restframework auth tokens when new users are saved
    @receiver(post_save, sender=User)
    def create_auth_token(sender, instance=None, created=False, **kwargs):
        print "received user post-save signal"
        if created:
            Token.objects.create(user=instance)
