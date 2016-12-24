from django.conf import settings
from rest_framework.views import APIView
from rest_framework.authtoken.models import Token
from rest_framework.response import Response
from rest_framework import authentication
from beaconWeb.apps.beacon.models.deal_status import DealStatus
from beaconWeb.apps.beacon.models.contact import Contact
from beaconWeb.apps.beacon.models.beacon_follow import BeaconFollow
from beaconWeb.apps.beacon.common.constants.beacon_status_values import BEACON_FOLLOW_STATUS
from beaconWeb.apps.beacon.common.constants.deal_status import DEAL_STATUS
from beaconWeb.apps.beacon.common.utils.favorite_feed import follow_redemption_location
from beaconWeb.apps.beacon.common.utils.rewards import check_for_referral_reward
from beaconWeb.apps.beacon.common.utils.rewards import add_drink_redemption_reward
from beaconWeb.REST.serializers import DealSerializer
from beaconWeb.apps.beacon.common.utils.rewards import redeem_reward_item
from rest_framework import status

class DealRedeemAPI(APIView):

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

        if str(auth_token) == settings.MOBILE_VIEW_TOKEN:
            deal_status = DealStatus.objects.get(pk=int(deal_id))
        else:
            if DealStatus.objects.filter(user=user, deal__pk=deal_id).exists():
                deal_status = DealStatus.objects.filter(user=user, deal__pk=deal_id).latest('date_created')
                # if deal_status.payment_authorization == "REWARD":
                #     redeem_reward_item(user)
                # check_user_and_send_repayment_requests(deal_status)
                # add_drink_redemption_reward(deal_status)
            else:
                contacts = Contact.objects.filter(normalized_phone=user.username)
                deal_status = DealStatus.objects.filter(contact__in=contacts, deal__pk=deal_id).latest('date_created')

        current_status = deal_status.deal_status
        next_status = current_status
        if current_status == DEAL_STATUS.UNLOCKED:
            next_status = DEAL_STATUS.REDEEMED
            message = "You unlocked this deal"
            follow_redemption_location(user, deal_status.deal.place)
            check_for_referral_reward(user)
        elif current_status == DEAL_STATUS.REDEEMED:
            message = "This deal has already been redeemed"
        else:
            message = "This deal is locked"
        deal_status.deal_status = next_status
        deal_status.save()

        #check in user if not already
        beacon_follow = BeaconFollow.objects.get(user=deal_status.user, contact=deal_status.contact, beacon=deal_status.beacon)
        beacon_follow.state = BEACON_FOLLOW_STATUS.HERE
        beacon_follow.save()
        
        response['previous_deal_status'] = current_status
        response['deal_status'] = next_status
        response['message'] = message

        return Response(response, status=status.HTTP_200_OK)