from django.contrib.auth.models import User
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.authtoken.models import Token
from beaconWeb.apps.beacon.common.utils.image import *
from rest_framework import status


class ImageAPI(APIView):

    """
    Beacon operations
    POST (Upload an Image) -
    GET (A link to Image on s3) -

    """

    def post(self, request, format=None):
        response = {}
        auth_token = request.auth
        if Token.objects.filter(key=auth_token).exists():
            token = Token.objects.get(key=auth_token)
            user = token.user
            image = store_image(user, request.FILES)
            response['image_url'] = "https://s3.amazonaws.com/hotspot-photo/" + str(image.image_key)
        else:
            response['message'] = "No user associated with token found"
            return Response(response, status=status.HTTP_401_UNAUTHORIZED)
        return Response(response, status=status.HTTP_200_OK)

    def get(self, request, format=None):
        response = {}
        auth_token = request.auth
        if Token.objects.filter(key=auth_token).exists():
            token = Token.objects.get(key=auth_token)
            image_url = get_image(token.user, request.QUERY_PARAMS)
            response['image_url'] = image_url
            return Response(response, status=status.HTTP_200_OK)
        else:
            response['message'] = "No user associated with token found"
            return Response(response, status=status.HTTP_401_UNAUTHORIZED)