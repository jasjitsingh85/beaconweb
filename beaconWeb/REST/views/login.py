from rest_framework.views import APIView
from rest_framework import status
from rest_framework.response import Response
from rest_framework.authtoken.models import Token
from rest_framework import permissions
from beaconWeb.apps.beacon.models import Profile
from beaconWeb.REST.serializers import ProfileSerializer
from django.contrib.auth.models import User
from beaconWeb.apps.beacon.common.common_utils import send_activation_code
import time


class LoginUserAPI(APIView):

    """
    When any user wants to invite more friends to an existing deal, use /invite/
    POST - Required params: phone_number (Token not required with this)
    phone_number -- User's phone number
    PUT - Required params: activation_code (four digit activation code that is texted once user puts in phone_number)
    activation_code -- four digit activation code sent after user types in phone number
    """

    permission_classes = (permissions.AllowAny,)

    def post(self, request):
        response = {}
        username = request.DATA.get('phone_number')
        print "Login Username: " + username
        if User.objects.filter(username=username).exists():
            user = User.objects.get(username=username)
            if Profile.objects.filter(user=user).exists():
                profile = Profile.objects.get(user=user)
                t1 = time.time()
                send_activation_code(profile)
                t2 = time.time()
                print "Time to send SMS"
                print t2-t1
                serializer = ProfileSerializer(profile)
                return Response(serializer.data)
            else:
                return Response(response, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        else:
            response['message'] = "User was not found"
            return Response(response, status=status.HTTP_400_BAD_REQUEST)

    def put(self, request, format=None):
        print "entered view"
        response = {}
        auth_token = request.auth
        print auth_token
        if Token.objects.filter(key=auth_token).exists():
            print "token exists"
            token = Token.objects.get(key=auth_token)
            if 'activation_code' in request.DATA:
                print "activation code exists"
                code = request.DATA['activation_code']
                if Profile.objects.filter(user=token.user).exists():
                    profile = token.user.profile
                    if profile.activation_code == code:
                        profile.activated = True
                        profile.save()
                        response['message'] = "Login successful"
                        serializer = ProfileSerializer(profile)
                        return Response(serializer.data)
                    else:
                        response['message'] = "Activation code does not match"
                        return Response(response, status=status.HTTP_400_BAD_REQUEST)
                else:
                    return Response(response, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            else:
                return Response(response, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        else:
            print "Auth token does not exist"
            return Response(response, status=status.HTTP_500_INTERNAL_SERVER_ERROR)