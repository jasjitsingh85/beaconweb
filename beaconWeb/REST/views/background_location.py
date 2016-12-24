from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import authentication
from rest_framework.authtoken.models import Token
from beaconWeb.apps.beacon.common.utils.location import save_background_location
from rest_framework import status


class BackgroundLocationAPI(APIView):

    authentication_classes = (authentication.TokenAuthentication,)

    def post(self, request, format=None):
        response = {}
        auth_token = request.auth
        if Token.objects.filter(key=auth_token).exists():
            token = Token.objects.get(key=auth_token)
            user = token.user
            success = save_background_location(user, request.DATA)
            # success = True
            if success:
                return Response(response, status=status.HTTP_200_OK)
            else:
                response['message'] = "Failed to save location"
                return Response(response, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        else:
            response['message'] = "Auth token does not exist"
            return Response(response, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
