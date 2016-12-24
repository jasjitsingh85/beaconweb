from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import authentication
from beaconWeb.apps.beacon.models.deal import Deal
from beaconWeb.REST.serializers import DealSerializer
from rest_framework import permissions
from rest_framework import status
from beaconWeb.apps.beacon.analytics.analytics import get_users_in_new_haven, get_engagement_labels_and_data, get_total_new_haven_users


class CommunityManagerDashboardAPI(APIView):

    permission_classes = (permissions.AllowAny,)

    def get(self, request, format=None):
        response = {}
        response['new_haven_total_user_number'] = get_total_new_haven_users()
        response['new_haven_active_user_number'] = get_users_in_new_haven()
        response['chart_labels'], response['chart_data'] = get_engagement_labels_and_data(30)
        return Response(response, status=status.HTTP_200_OK)