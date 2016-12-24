from django.conf.urls import patterns, url
from beaconWeb.REST.views.user_profile import UserProfileAPI
from beaconWeb.REST.views.hotspot import HotspotAPI
from beaconWeb.REST.views.content import ContentAPI
from beaconWeb.REST.views.invite import InviteAPI
from beaconWeb.REST.views.hotspot_follow import HotspotFollowAPI
from beaconWeb.REST.views.friends import FriendsAPI
from beaconWeb.REST.views.location import LocationAPI
from beaconWeb.REST.views.login import LoginUserAPI
from beaconWeb.REST.views.image import ImageAPI
from beaconWeb.REST.views.message import MessageAPI
from beaconWeb.REST.views.text_app_link import TextAppLinkAPI
from beaconWeb.REST.views.saw_invite import SawInviteAPI
from beaconWeb.REST.views.beacon import BeaconAPI
from beaconWeb.REST.views.hotspot import HotspotAPI
from beaconWeb.REST.views.push_notification import PUSHAPI
from beaconWeb.REST.views.recommendation import RecommendationAPI
from beaconWeb.REST.views.sms_reply import SMSReplyAPI
from beaconWeb.REST.views.contact_status import ContactStatusAPI
from beaconWeb.REST.views.contact_groups import ContactGroupAPI
from beaconWeb.REST.views.happy_hours import HappyHourAPI
from beaconWeb.REST.views.happy_hour_detail import HappyHourDetailAPI
from beaconWeb.REST.views.deals import DealsAPI
from beaconWeb.REST.views.deal import DealAPI
from beaconWeb.REST.views.deal_status import DealStatusAPI
from beaconWeb.REST.views.event_status import EventStatusAPI
from beaconWeb.REST.views.deal_apply import DealApplyAPI
from beaconWeb.REST.views.deal_redeem import DealRedeemAPI
from beaconWeb.REST.views.deal_feedback import DealFeedbackAPI
from beaconWeb.REST.views.region_state import RegionStateAPI
from beaconWeb.REST.views.community_manager_dashboard import CommunityManagerDashboardAPI
from beaconWeb.REST.views.merchant_login import MerchantLoginAPI
from beaconWeb.REST.views.merchant_dashboard import MerchantDealsAPI
from beaconWeb.REST.views.client_token import ClientTokenAPI
from beaconWeb.REST.views.purchases import PurchasesAPI
from beaconWeb.REST.views.venmo import VenmoOAuthAPI
from beaconWeb.REST.views.rewards_voucher import RewardsVoucherAPI
from beaconWeb.REST.views.reward_item import RewardItemAPI
from beaconWeb.REST.views.rewards import RewardsAPI
from beaconWeb.REST.views.friend_profile import FriendProfileAPI
from beaconWeb.REST.views.favorite_feed import FavoriteFeedAPI
from beaconWeb.REST.views.friend_suggested import FriendSuggestedAPI
from beaconWeb.REST.views.invite_friends_to_app import InviteFriendsToAppAPI
from beaconWeb.REST.views.promo import PromoAPI
from beaconWeb.REST.views.check_in import CheckInAPI
from beaconWeb.REST.views.view_tracker import ViewTrackerAPI
from beaconWeb.REST.views.events import EventsAPI
from beaconWeb.REST.views.facebook_permissions import FacebookPermissionsAPI
from beaconWeb.REST.views.places import PlacesAPI
from beaconWeb.REST.views.friend_manage import FriendManageAPI
from beaconWeb.REST.views.tab import TabAPI
from beaconWeb.REST.views.check_in_v2 import CheckInV2API
from beaconWeb.REST.views.background_location import BackgroundLocationAPI
from beaconWeb.REST.views.reserve import ReserveAPI
from beaconWeb.REST.views.swipe_and_match import SwipeMatchAPI
from beaconWeb.REST.views.cash_payment import CashPaymentAPI
from beaconWeb.REST.views.web_promo import WebPromoAPI
from beaconWeb.REST.views.email_status import EmailStatusAPI
from beaconWeb.REST.views.staffer_reply import StafferReplyAPI
from beaconWeb.REST.views.email_capture import EmailCaptureAPI

urlpatterns = patterns('REST.views',
       url(r'^login/', LoginUserAPI.as_view()),
       url(r'^message/', MessageAPI.as_view()),
       url(r'^invite/', InviteAPI.as_view()),
       url(r'^image/', ImageAPI.as_view()),
       url(r'^user/me/', UserProfileAPI.as_view()),
       url(r'^beacon/', BeaconAPI.as_view()),
       url(r'^hotspot/', HotspotAPI.as_view()),
       url(r'^follow/', HotspotFollowAPI.as_view()),
       url(r'^location/', LocationAPI.as_view()),
       url(r'^background/location/', BackgroundLocationAPI.as_view()),
       url(r'^friends/', FriendsAPI.as_view()),
       url(r'^friend/profiles/', FriendProfileAPI.as_view()),
       url(r'^friend/suggested/', FriendSuggestedAPI.as_view()),
       url(r'^content/', ContentAPI.as_view()),
       url(r'^text-app-link/', TextAppLinkAPI.as_view()),
       url(r'^saw_invite/', SawInviteAPI.as_view()),
       url(r'^device/activate/android/', PUSHAPI.as_view()),
       url(r'^recommendation/', RecommendationAPI.as_view()),
       url(r'^contact_status/', ContactStatusAPI.as_view()),
       url(r'^sms-reply/', SMSReplyAPI.as_view()),
       url(r'^contact_group/', ContactGroupAPI.as_view()),
       url(r'^deal_status/', DealStatusAPI.as_view()),
       url(r'^deals/', DealsAPI.as_view()),
       url(r'^deal/detail/', DealAPI.as_view()),
       url(r'^deal/apply/', DealApplyAPI.as_view()),
       url(r'^deal/redeem/', DealRedeemAPI.as_view()),
       url(r'^deal/feedback/', DealFeedbackAPI.as_view()),
       url(r'^region_state/', RegionStateAPI.as_view()),
       url(r'^dashboard/campus_manager/', CommunityManagerDashboardAPI.as_view()),
       url(r'^merchant/login/', MerchantLoginAPI.as_view()),
       url(r'^merchant/deals/', MerchantDealsAPI.as_view()),
       url(r'^client_token/', ClientTokenAPI.as_view()),
       url(r'^purchases/', PurchasesAPI.as_view()),
       url(r'^venmo_oauth/', VenmoOAuthAPI.as_view()),
       url(r'^rewards/', RewardsAPI.as_view()),
       url(r'^reward/voucher/', RewardsVoucherAPI.as_view()),
       url(r'^reward/item/', RewardItemAPI.as_view()),
       url(r'^invite-friends-to-app/', InviteFriendsToAppAPI.as_view()),
       url(r'^promo/', PromoAPI.as_view()),
       url(r'^favorite-feed/', FavoriteFeedAPI.as_view()),
       url(r'^check-in/', CheckInAPI.as_view()),
       url(r'^v2/check-in/', CheckInV2API.as_view()),
       url(r'^view-tracker/', ViewTrackerAPI.as_view()),
       url(r'^events/', EventsAPI.as_view()),
       url(r'^facebook-token/', FacebookPermissionsAPI.as_view()),
       url(r'^places/', PlacesAPI.as_view()),
       url(r'^friend/manage/', FriendManageAPI.as_view()),
       url(r'^tab/', TabAPI.as_view()),
       url(r'^reserve/', ReserveAPI.as_view()),
       url(r'^swipe-match/', SwipeMatchAPI.as_view()),
       url(r'^cash-payment/', CashPaymentAPI.as_view()),
       url(r'^event-status/', EventStatusAPI.as_view()),
       url(r'^web-promo/', WebPromoAPI.as_view()),
       url(r'^email-status/', EmailStatusAPI.as_view()),
       url(r'^staffer-reply/', StafferReplyAPI.as_view()),
       url(r'^email-capture/', EmailCaptureAPI.as_view()),
)