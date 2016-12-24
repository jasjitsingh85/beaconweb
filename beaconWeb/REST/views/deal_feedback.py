from django.conf import settings
from rest_framework.views import APIView
from rest_framework.authtoken.models import Token
from rest_framework.response import Response
from rest_framework import authentication
from beaconWeb.apps.beacon.models.deal_status import DealStatus
from beaconWeb.apps.beacon.models.deal_feedback import Feedback
from rest_framework import status
import datetime
from beaconWeb.apps.beacon.retention.emails import send_feedback_email

class DealFeedbackAPI(APIView):

    """
    This is sent when a user taps button to redeem deal
    POST - Required Params: deal_id
    deal_id -- ID of deal
    """

    authentication_classes = (authentication.TokenAuthentication,)

    def post(self, request, format=None):
        response = {}
        deal_id = request.DATA['deal_id']
        auth_token = request.auth
        user = Token.objects.get(key=auth_token).user
        if DealStatus.objects.filter(user=user, deal__pk=deal_id).exists():
            deal_status = DealStatus.objects.filter(user=user, deal__pk=deal_id).latest('date_created')
            if deal_status.feedback is None:
                feedback = Feedback.objects.create(redemption_issue=True)
                deal_status.feedback = feedback
                send_feedback_email(deal_status.user, deal_status.deal.place)
                deal_status.feedback.save()
            else:
                deal_status.feedback.redemption_issue = True
                deal_status.feedback.save()
            deal_status.save()
            response['feedback_status'] = deal_status.feedback.redemption_issue
            return Response(response, status=status.HTTP_200_OK)
        else:
            return Response(response, status=status.HTTP_500_INTERNAL_SERVER_ERROR)