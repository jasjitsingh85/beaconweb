from rest_framework.views import APIView
from rest_framework.response import Response
from django.conf import settings
from rest_framework.authtoken.models import Token
from beaconWeb.apps.beacon.common.utils.message import *
from rest_framework import status
from beaconWeb.REST.serializers import MessageThread


class MessageAPI(APIView):
    """
    Beacon operations
    POST (post message sent by user): Required Params - beacon, message or image
    beacon -- ID of Beacon
    message -- message to be added to chat
    GET (get message thread for beacon): Required Params - beacon
    beacon -- ID of Beacon
    """

    def post(self, request, format=None):
        response = {}
        auth_token = request.auth
        token = Token.objects.get(key=auth_token)
        store_message(token.user, request.DATA)
        return Response(response, status=status.HTTP_200_OK)

    def get(self, request, format=None):
        response = {}
        auth_token = request.auth
        if Token.objects.filter(key=auth_token).exists():
            messageThread = get_message_thread(request.QUERY_PARAMS)
            serializer = MessageThread(messageThread, many=True)
            response['messages'] = serializer.data
            return Response(response, status=status.HTTP_200_OK)
        else:
            response['message'] = "No user associated with token found"
            return Response(response, status=status.HTTP_401_UNAUTHORIZED)