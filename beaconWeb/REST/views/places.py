from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import authentication
from beaconWeb.apps.beacon.common.utils.places import nearby_venues
from beaconWeb.REST.serializers import PlaceSerializer, SponsoredEventSerializer
from rest_framework import status
from rest_framework.authtoken.models import Token
import time
from beaconWeb.apps.beacon.common.utils.location import set_location
from beaconWeb.apps.beacon.common.utils.sponsored_events import get_sponsored_events


class PlacesAPI(APIView):

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
            if radius > 10.0:
                radius = 10.0
        else:
            radius = 0.5
        set_location(token.user, latitude, longitude)
        t0 = time.time()
        sponsored_events, deals, places = nearby_venues(token.user, latitude, longitude, radius)
        t1 = time.time()
        print "Nearby Venues: " + str(t1-t0)
        response['sponsored_events'] = SponsoredEventSerializer(sponsored_events, many=True).data
        response['deals'] = PlaceSerializer(deals, many=True).data
        response['non_deals'] = PlaceSerializer(places, many=True).data
        response['number_of_reward_items'] = token.user.profile.number_of_reward_items
        return Response(response, status=status.HTTP_200_OK)