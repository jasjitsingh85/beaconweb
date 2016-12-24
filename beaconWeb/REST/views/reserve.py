from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import authentication
from rest_framework.authtoken.models import Token
from rest_framework import status
from beaconWeb.REST.serializers import SponsoredEventSerializer
from beaconWeb.apps.beacon.common.utils.reserve import reserve_ticket, toggle_interested, get_event, redeem_ticket, check_event_time, has_capacity


class ReserveAPI(APIView):

    authentication_classes = (authentication.TokenAuthentication,)

    def get(self, request, format=None):
        response = {}
        auth_token = request.auth
        if Token.objects.filter(key=auth_token).exists():
            token = Token.objects.get(key=auth_token)
            event_id = request.QUERY_PARAMS['event_id']
            event = get_event(token.user, event_id)
            serializer = SponsoredEventSerializer(event)
            response['sponsored_event'] = serializer.data
            return Response(response, status=status.HTTP_200_OK)
        else:
            response['message'] = "No user associated with token found"
            return Response(response, status=status.HTTP_401_UNAUTHORIZED)

    def post(self, request, format=None):
        response = {}
        auth_token = request.auth
        if Token.objects.filter(key=auth_token).exists():
            token = Token.objects.get(key=auth_token)
            user = token.user
            event = reserve_ticket(user, request.DATA)
            if event:
                response['sponsored_event'] = SponsoredEventSerializer(event).data
                return Response(response, status=status.HTTP_200_OK)
            else:
                response['card_decline'] = True
                return Response(response, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        else:
            response['message'] = "Auth token does not exist"
            return Response(response, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def put(self, request, format=None):
        response = {}
        auth_token = request.auth
        if Token.objects.filter(key=auth_token).exists():
            token = Token.objects.get(key=auth_token)
            user = token.user
            if check_event_time(request.DATA):
                event = redeem_ticket(user, request.DATA)
                response['sponsored_event'] = SponsoredEventSerializer(event).data
            return Response(response, status=status.HTTP_200_OK)
        else:
            response['message'] = "Auth token does not exist"
            return Response(response, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
