from rest_framework import serializers
from beaconWeb.apps.beacon.models.profile import Profile
from django.contrib.auth.models import User
from beaconWeb.apps.beacon.models import Beacon
from beaconWeb.apps.beacon.models import Contact
from beaconWeb.apps.beacon.models import ContentOption
from beaconWeb.apps.beacon.models import DatingProfile
from beaconWeb.apps.beacon.models import Deal, DealPlace, DealStatus, DealHours, Feedback, Rewards, SyndicatedDeal, SyndicatedEvents, PlacePhotos, PointOfSale, Tab, TabItem, SponsoredEvent, EventStatus
from beaconWeb.apps.happy_hours.models import HappyHour, Place, City
from beaconWeb.apps.beacon.classes.guest import Guest
from beaconWeb.apps.beacon.models import Image
from beaconWeb.apps.beacon.models import Message
import time


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'first_name', 'last_name')


class ProfileSerializer(serializers.Serializer):
    id = serializers.Field()
    user = UserSerializer()
    activated = serializers.BooleanField()
    phone_number = serializers.Field()
    normalized_phone = serializers.Field()
    gender = serializers.Field()
    date_updated = serializers.Field()
    token = serializers.Field()
    avatar_url = serializers.Field()
    reward_score = serializers.Field()
    promo_code = serializers.Field()


class DateProfileSerializer(serializers.Serializer):
    id = serializers.Field()
    user = UserSerializer()
    activated = serializers.BooleanField()
    phone_number = serializers.Field()
    normalized_phone = serializers.Field()
    gender = serializers.Field()
    date_updated = serializers.Field()
    avatar_url = serializers.Field()
    reward_score = serializers.Field()
    promo_code = serializers.Field()


#class ProfileSerializer(serializers.ModelSerializer):
#    user = UserSerializer()
#    class Meta:
#        model = Profile
#        fields = ('id', 'user', 'phone_number', 'activated', 'normalized_phone', 'gender', 'date_updated')


class ContactSerializer(serializers.ModelSerializer):
    class Meta:
        model = Contact
        fields = ('id', 'name', 'phone_number', 'normalized_phone')


class DealPlaceForSponsoredEventSerializer(serializers.ModelSerializer):
    image_url = serializers.Field()
    has_pos = serializers.Field()
    photos = serializers.Field()

    class Meta:
        model = DealPlace
        fields = ('id', 'latitude', 'longitude', 'name', 'street_address', 'image_url', 'foursquare_id', 'place_description', 'yelp_id', 'yelp_rating_image_url', 'yelp_review_count', 'has_pos', 'photos')

class DealPlaceSerializer(serializers.ModelSerializer):
    image_url = serializers.Field()
    has_pos = serializers.Field()

    class Meta:
        model = DealPlace
        fields = ('id', 'latitude', 'longitude', 'name', 'street_address', 'image_url', 'foursquare_id', 'place_description', 'yelp_id', 'yelp_rating_image_url', 'yelp_review_count', 'has_pos')


class BeaconSerializer(serializers.ModelSerializer):
    creator = UserSerializer()
    place = DealPlaceSerializer()

    class Meta:
        model = Beacon
        fields = ('id', 'creator', 'description', 'address', 'time', 'private', 'longitude', 'latitude',
                  'date_created', 'date_updated', 'isActivated', 'place')


class ImageSerializer(serializers.Serializer):
    id = serializers.Field()
    image_key = serializers.Field()
    user = UserSerializer()
    beacon = BeaconSerializer()
    image_url = serializers.Field()


class GuestSerializer(serializers.Serializer):
    profile = ProfileSerializer()
    contact = ContactSerializer()
    status = serializers.Field()


class ContactMemberSerializer(serializers.Serializer):
    contact = ContactSerializer()


class ContactGroupSerializer(serializers.Serializer):
    id = serializers.Field()
    name = serializers.Field()
    user = UserSerializer()
    members = ContactMemberSerializer()


class BeaconWithFollowersSerializer(serializers.Serializer):
    id = serializers.Field()
    place = DealPlaceSerializer()
    profile = ProfileSerializer()
    description = serializers.Field()
    address = serializers.Field()
    time = serializers.Field()
    beacon_time = serializers.FloatField()
    expiration = serializers.FloatField()
    private = serializers.Field()
    latitude = serializers.Field()
    longitude = serializers.Field()
    guests = GuestSerializer()
    isActivated = serializers.Field()
    image_url = serializers.Field()
    images = ImageSerializer()


class MessageThread(serializers.Serializer):
    id = serializers.Field()
    image = ImageSerializer()
    sender = ProfileSerializer()
    contact = ContactSerializer()
    message = serializers.Field()
    date_created = serializers.Field()
    message_time = serializers.FloatField()
    chat_type = serializers.Field()
    profile_pic = serializers.Field()


class BeaconMobileSerializer(serializers.Serializer):
    id = serializers.Field()
    creator = UserSerializer()
    description = serializers.Field()
    address = serializers.Field()
    time = serializers.Field()
    beacon_time = serializers.FloatField()
    follow = serializers.Field()
    private = serializers.Field()
    latitude = serializers.Field()
    longitude = serializers.Field()
    invite_number = serializers.Field()
    image_urls = serializers.Field()
    isActivated = serializers.Field()
    date_updated = serializers.Field()
    date_created = serializers.Field()


class ContentSerializer(serializers.ModelSerializer):
    class Meta:
        model = ContentOption
        fields = ('id', 'display_location', 'content_option')


class ContentOptionSerializer(serializers.Serializer):
    friend_already_invited = ContentSerializer()
    invite_new_users = ContentSerializer()
    no_hotspot_content = ContentSerializer()
    hotspot_placeholder = ContentSerializer()
    zero_hotspot = ContentSerializer()


class DealHoursSerializer(serializers.ModelSerializer):
    days = serializers.CharField()

    class Meta:
        model = DealHours
        fields = ('start', 'end', 'days', 'event_date')


class DealSerializer(serializers.ModelSerializer):
    place = DealPlaceSerializer()
    hours = DealHoursSerializer()
    item_point_cost = serializers.Field()
    item_market_price = serializers.Field()
    is_reward_item = serializers.Field()
    is_followed = serializers.Field()

    class Meta:
        model = Deal
        fields = ('id', 'deal_description', 'deal_description_short', 'invite_requirement', 'bonus_description', 'bonus_invite_requirement',
                  'invite_description', 'invite_prompt', 'notification_text', 'place', 'additional_info', 'hours', 'deal_type', 'in_app_payment', 'item_name', 'item_price', 'item_point_cost', 'item_market_price', 'reward_eligibility', 'is_reward_item', 'is_followed')


class FeedbackSerializer(serializers.ModelSerializer):

    class Meta:
        model = Feedback
        fields = ('date_created', 'redemption_issue')


class DealStatusSerializer(serializers.ModelSerializer):
    user = UserSerializer()
    contact = ContactSerializer()
    start_time = serializers.Field()
    end_time = serializers.Field()
    feedback_boolean = serializers.Field()
    payment_authorization = serializers.Field()
    conditional_image_url = serializers.Field()

    class Meta:
        model = DealStatus
        fields = ('id', 'deal_status', 'bonus_status', 'user', 'contact', 'start_time', 'end_time', 'feedback_boolean', 'payment_authorization', 'conditional_image_url')


class BeaconWithDealStatusSerializer(BeaconWithFollowersSerializer):
    image_url = serializers.Field()
    deal_statuses = DealStatusSerializer(required=False)
    deal = DealSerializer(required=False)


#happy hours
class CitySerializer(serializers.ModelSerializer):
    class Meta:
        model = City
        fields = ('id', 'name')


class HappyHourPlaceSerializer(serializers.ModelSerializer):
    distance = serializers.FloatField()
    large_image_url = serializers.Field()

    class Meta:
        model = Place
        fields = ('id', 'foursquare_id', 'yelp_id', 'longitude', 'latitude', 'name', 'distance', 'image_url', 'large_image_url', 'place_description', 'street_address', 'yelp_id', 'yelp_rating_image_url', 'yelp_review_count')


class HappyHourPlaceDetailSerializer(serializers.ModelSerializer):
    large_image_url = serializers.Field()
    rating = serializers.Field()
    review_count = serializers.Field()
    phone = serializers.Field()
    city = CitySerializer()
    photos = serializers.Field()
    price = serializers.Field()
    place_description = serializers.Field()
    class Meta:
        model = Place
        fields = ('id', 'longitude', 'latitude', 'name', 'rating', 'review_count', 'image_url', 'large_image_url', 'phone', 'street_address', "city", "zip_code", "photos", "price", "place_description")


class HappyHourSerializer(serializers.ModelSerializer):
    place = DealPlaceSerializer()
    is_followed = serializers.Field()

    class Meta:
        model = SyndicatedDeal
        fields = ('id', 'description', 'place', 'start', 'end', 'is_followed')


class HappyHourDetailSerializer(serializers.ModelSerializer):
    place = HappyHourPlaceDetailSerializer()

    class Meta:
        model = HappyHour
        fields = ('id', 'description', 'place', 'start', 'end')


class RewardsSerializer(serializers.ModelSerializer):
    deal = DealSerializer()

    class Meta:
        model = Rewards
        fields = ('id', 'reward_type', 'deal', 'reward_value', 'isRedeemed')


class EventsSerializer(serializers.ModelSerializer):
    place = DealPlaceSerializer()
    start_time = serializers.Field()
    web_url = serializers.Field()
    deep_link_url = serializers.Field()

    class Meta:
        model = SyndicatedEvents
        fields = ('id', 'title', 'website', 'start_time', 'place', 'web_url', 'deep_link_url')


class FavoriteFeedSerializer(serializers.Serializer):
    source = serializers.Field()
    message = serializers.Field()
    thumbnail = serializers.Field()
    image_url = serializers.Field()
    name = serializers.Field()
    date_created = serializers.DateTimeField()


class DealSerializerV2(serializers.ModelSerializer):
    place = DealPlaceSerializer()
    hours = DealHoursSerializer()
    item_market_price = serializers.Field()
    is_reward_item = serializers.Field()
    image_url = serializers.Field()
    total_check_ins = serializers.Field()

    class Meta:
        model = Deal
        fields = ('id', 'place', 'deal_description', 'deal_description_short', 'invite_requirement', 'bonus_description', 'bonus_invite_requirement',
                  'invite_description', 'invite_prompt', 'notification_text', 'additional_info', 'hours', 'deal_type', 'in_app_payment', 'item_name', 'item_price', 'total_check_ins', 'item_market_price', 'reward_eligibility', 'is_reward_item')


class HappyHourSerializerV2(serializers.ModelSerializer):
    # place = DealPlaceSerializer()
    # is_followed = serializers.Field()

    class Meta:
        model = SyndicatedDeal
        fields = ('id', 'description', 'start', 'end')


class EventsSerializerV2(serializers.ModelSerializer):
    # place = DealPlaceSerializer()
    start_time = serializers.Field()
    web_url = serializers.Field()
    deep_link_url = serializers.Field()

    class Meta:
        model = SyndicatedEvents
        fields = ('id', 'title', 'website', 'start_time', 'web_url', 'deep_link_url')


class PointOfSaleSerializer(serializers.ModelSerializer):
    location_id = serializers.Field()

    class Meta:
        model = PointOfSale
        fields = ('id', 'location_id')


class PlaceSerializer(serializers.ModelSerializer):
    deal = DealSerializerV2()
    happy_hour = HappyHourSerializerV2()
    events = EventsSerializerV2()
    is_followed = serializers.Field()
    is_reward_item = serializers.Field()
    image_url = serializers.Field()
    photos = serializers.Field()
    has_pos = serializers.Field()
    point_of_sale = PointOfSaleSerializer()

    class Meta:
        model = DealPlace
        fields = ('id', 'latitude', 'longitude', 'name', 'street_address', 'image_url', 'foursquare_id', 'place_description', 'yelp_id', 'yelp_rating_image_url', 'yelp_review_count', 'deal', 'is_followed', 'place_type', 'neighborhood', 'happy_hour', 'events', 'photos', 'has_pos')


class TabItemSerializer(serializers.ModelSerializer):
    name = serializers.Field()
    price = serializers.Field()
    deal = DealSerializerV2()

    class Meta:
        model = TabItem
        fields = ('id', 'name', 'price', 'deal')


class TabSerializer(serializers.ModelSerializer):
    api_tab_id = serializers.Field()
    tab_claimed = serializers.Field()
    subtotal = serializers.Field()
    other_charges = serializers.Field()
    service_charges = serializers.Field()
    tax = serializers.Field()
    discount = serializers.Field()
    convenience_fee = serializers.Field()
    total = serializers.Field()
    closed = serializers.Field()

    class Meta:
        model = Tab
        fields = ('id', 'api_tab_id', 'tab_claimed', 'subtotal', 'other_charges', 'service_charges', 'tax', 'discount', 'convenience_fee', 'total', 'closed', 'payment_authorization')


class EventStatusSerializer(serializers.ModelSerializer):
    # event = SponsoredEventSerializer()

    class Meta:
        model = EventStatus
        fields = ('id', 'status', 'is_presale')


class SponsoredEventSerializer(serializers.ModelSerializer):
    place = DealPlaceForSponsoredEventSerializer()
    start_time = serializers.Field()
    end_time = serializers.Field()
    social_message = serializers.Field()
    status_message = serializers.Field()
    web_url = serializers.Field()
    deep_link_url = serializers.Field()
    event_status = EventStatusSerializer()
    is_sold_out = serializers.Field()
    presale_active = serializers.Field()

    class Meta:
        model = SponsoredEvent
        fields = ('id', 'title', 'item_name', 'item_price', 'capacity', 'place', 'start', 'end', 'start_time', 'end_time', 'social_message', 'status_message', 'description', 'web_url', 'deep_link_url', 'event_status', 'is_sold_out', 'chat_channel_url', 'presale_item_price', 'presale_active')


class DatingProfileSerializer(serializers.ModelSerializer):
    dating_profile = DateProfileSerializer()

    class Meta:
        model = DatingProfile
        fields = ('id', 'dating_profile', 'user_gender', 'preference', 'image_url', 'has_setup', 'age')