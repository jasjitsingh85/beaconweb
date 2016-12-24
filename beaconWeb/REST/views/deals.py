from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import authentication
from beaconWeb.apps.beacon.common.utils.deals import nearby_deals, nearby_happy_hours
from beaconWeb.apps.beacon.common.utils.rewards import get_nearby_rewards
from beaconWeb.REST.serializers import DealSerializer, HappyHourSerializer
from rest_framework import status
from rest_framework.authtoken.models import Token
import time
from beaconWeb.apps.beacon.common.utils.location import set_location


class DealsAPI(APIView):

    """
    Get list of deals in your area
    GET (Get your user) - Required params: latitude, longitude
    latitude -- current latitude of user
    longitude -- current longitude of user

    """

    authentication_classes = (authentication.TokenAuthentication,)

    def get(self, request, format=None):
        response = {}
        auth_token = request.auth
        token = Token.objects.get(key=auth_token)
        latitude = float(request.QUERY_PARAMS['latitude'])
        longitude = float(request.QUERY_PARAMS['longitude'])
        if 'radius' in request.QUERY_PARAMS:
            radius = float(request.QUERY_PARAMS['radius'])
            if radius > 1.6:
                radius = 1.6
        else:
            radius = 1.6
        print "Radius: " + str(radius)
        set_location(token.user, latitude, longitude)
        t0 = time.time()
        deals = nearby_deals(token.user, latitude, longitude, radius)
        print "DEALS: " + str(deals)
        t1 = time.time()
        happy_hours = nearby_happy_hours(token.user, latitude, longitude, radius)
        print "HAPPY HOURS: " + str(happy_hours)
        t2 = time.time()
        print "Nearby Deals: " + str(t1-t0)
        print "Nearby Happy Hours: " + str(t2-t1)
        # unlocked_deals, locked_deals = get_nearby_rewards(token.user, latitude, longitude)
        response['deals'] = DealSerializer(deals, many=True).data
        response['happy_hours'] = HappyHourSerializer(happy_hours, many=True).data
        response['number_of_reward_items'] = token.user.profile.number_of_reward_items
        # response['unlocked_rewards'] = DealSerializer(unlocked_deals, many=True).data
        # response['locked_rewards'] = DealSerializer(locked_deals, many=True).data
        return Response(response, status=status.HTTP_200_OK)