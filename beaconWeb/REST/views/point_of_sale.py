from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import authentication
from rest_framework.authtoken.models import Token
from rest_framework import status
from beaconWeb.apps.beacon.models.point_of_sale import PointOfSale
from beaconWeb.apps.beacon.models.ticket import Ticket
from beaconWeb.apps.beacon.models.ticket_item import TicketItem
from beaconWeb.REST.serializers import TicketItemSerializer, TicketSerializer
from beaconWeb.apps.beacon.common.utils.point_of_sale import create_omnivore_ticket_and_add_drink, check_if_ticket_claimed


class PointOfSale(APIView):

    authentication_classes = (authentication.TokenAuthentication,)

    def get(self, request, format=None):
        response = {}
        auth_token = request.auth
        if Token.objects.filter(key=auth_token).exists():
            token = Token.objects.get(key=auth_token)
            user = token.user
            deal_place_id = request.DATA['deal_place_id']
            ticket_id = request.DATA['ticket_id']
            claimTab = bool(int(request.DATA['claim_tab']))
            if claimTab:
                item_id = request.DATA['item_id']
                #ticketClaimed = check_if_ticket_claimed(user, deal_place_id, ticket_id, item_id)
                response['ticket_claimed'] = True
                return Response(response, status=status.HTTP_200_OK)
            else:
                point_of_sale = PointOfSale.objects.get(omnivore_location_id='7T688Lie')
                ticket = Ticket.objects.get(point_of_sale=point_of_sale, ticket_id='bc7LaRTy')
                ticket_items = TicketItem.objects.filter(ticket=ticket)
                response['ticket_items'] = TicketItemSerializer(ticket_items, many=True).data
                response['ticket'] = TicketSerializer(ticket)
                return Response(response, status=status.HTTP_200_OK)
        else:
            response['message'] = "Auth token does not exist"
            return Response(response, status=status.HTTP_400_BAD_REQUEST)

    def post(self, request, format=None):
        response = {}
        auth_token = request.auth
        if Token.objects.filter(key=auth_token).exists():
            token = Token.objects.get(key=auth_token)
            user = token.user
            deal_place_id = request.DATA['deal_place_id']
            ticket_id = 'bc7LaRTy'
            item_id = '6cz55XBc'
            #ticket_and_item_ids = create_omnivore_ticket_and_add_drink(user, deal_place_id)
            #ticket_id = ticket_and_item_ids[0]
            #item_id = ticket_and_item_ids[1]
            response['ticket_id'] = ticket_id
            response['item_id'] = item_id
            response['message'] = "A ticket has been created."
            return Response(response, status=status.HTTP_200_OK)
        else:
            response['message'] = "Auth token does not exist"
            return Response(response, status=status.HTTP_400_BAD_REQUEST)

    def put(self, request, format=None):
        response = {}
        auth_token = request.auth
        if Token.objects.filter(key=auth_token).exists():
            deal_place_id = request.DATA['deal_place_id']
            ticket_id = request.DATA['ticket_id']
            #close_omnivore_ticket(deal_place_id, ticket_id)
            response['message'] = "The ticket has been closed."
            return Response(response, status=status.HTTP_200_OK)
        else:
            response['message'] = "Auth token does not exist"
            return Response(response, status=status.HTTP_400_BAD_REQUEST)

