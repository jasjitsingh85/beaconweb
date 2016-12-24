from beaconWeb.apps.beacon.models import DealStatus, Deal, Rewards, RewardItem, ContactStatus, Contact, DealPlace
from beaconWeb.apps.beacon.common.constants.reward_types import REWARD_TYPES
from beaconWeb.apps.beacon.common.constants.reward_values import REWARD_VALUES
from beaconWeb.apps.beacon.common.utils.deals import get_list_of_places_for_user
from beaconWeb.apps.beacon.analytics.analytics import promo_dct
from beaconWeb.apps.beacon.common.utils.favorite_feed import follow_redemption_location
from datetime import datetime, timedelta
from django.contrib.auth.models import User
from beaconWeb.apps.beacon.models.promo import Promo
from beaconWeb.apps.beacon.models.web_promo import WebPromo
from beaconWeb.apps.beacon.models.brand_ambassador import BrandAmbassador
from beaconWeb.apps.beacon.tasks.send_sms import *
from beaconWeb.apps.beacon.common.utils.deals import add_favorites_to_deals
import uuid
from django.db.models import Q

# promo_codes = ["j12", "r13", "w69", "100", "101", "102", "103", "104", "105", "106", "107", "108", "109", "110", "111", "112", "113", "114", "115", "116", "117", "118", "119", "120", "121", "122", "m15", "e10", "e11", "e12", "e13", "e14", "e15", "e16", "e17", "e18", "m3d2", "free7"]

def get_active_vouchers(user):
    active_vouchers = Rewards.objects.filter(reward_type=REWARD_TYPES.PURCHASE, isRedeemed=False, user=user)
    return active_vouchers


def add_drink_redemption_reward(deal_status):
    reward_receipient = deal_status.beacon.creator
    Rewards.objects.create(user=reward_receipient, reward_type=REWARD_TYPES.DRINK_REDEMPTION, reward_value=REWARD_VALUES.DRINK_REDEMPTION)


def get_nearby_rewards(user, latitude, longitude):
    place_ids = get_list_of_places_for_user(user, latitude,longitude)
    unlocked_deals = []
    locked_deals = []
    if len(place_ids) > 0:
        unlocked_deals, locked_deals = get_active_rewards(place_ids, user.profile.reward_score)
        unlocked_deals.sort(key=lambda x: x.item_cost)
        locked_deals.sort(key=lambda x: x.item_cost)
    unlocked_deals = add_favorites_to_deals(user, unlocked_deals)
    locked_deals = add_favorites_to_deals(user, locked_deals)
    return unlocked_deals, locked_deals


def get_active_rewards(place_ids, reward_score):
    deals = Deal.objects.filter(active=True, place_id__in=place_ids, in_app_payment=True)
    unlocked_deals = []
    locked_deals = []
    for deal in deals:
        deal.is_reward_item = False
        if reward_score >= (deal.item_cost * REWARD_VALUES.DOLLAR_TO_COST_POINT_MULTIPLER):
            unlocked_deals.append(deal)
        else:
            locked_deals.append(deal)
    return unlocked_deals, locked_deals


def purchase_reward_item(user, request_data):
    if 'deal_id' not in request_data:
        return False
    deal_id = int(request_data['deal_id'])
    deal = Deal.objects.get(pk=deal_id)
    point_cost = deal.item_cost * -1 * REWARD_VALUES.DOLLAR_TO_COST_POINT_MULTIPLER
    Rewards.objects.create(user=user, reward_type=REWARD_TYPES.PURCHASE, deal=deal, reward_value=point_cost)


def redeem_reward(request_data):
    if 'voucher_id' not in request_data:
        return False
    voucher_id = int(request_data['voucher_id'])
    item = Rewards.objects.get(pk=voucher_id)
    item.isRedeemed = True
    item.save()


def add_points(user, request_data):
    date_joined = user.date_joined
    if 'referring_user' not in request_data:
        return False
    if Rewards.objects.filter(user=user, reward_type=REWARD_TYPES.REFERRAL).exists():
        return False
    if date_joined > (datetime.now() - timedelta(days=1)):
        current_user = user
        referring_user = User.objects.get(username=request_data['referring_user'])
        current_user_reward = Rewards(user=current_user, reward_type=REWARD_TYPES.REFERRAL, reward_value=100)
        referring_user_reward = Rewards(user=referring_user, reward_type=REWARD_TYPES.REFERRAL, reward_value=100)
        current_user_reward.save()
        referring_user_reward.save()
    else:
        return False


def add_promo_reward_items(user, referring_user=None, promo_code=None):
    reward_item = add_reward_item(user)
    reward_item.promo_code = promo_code
    reward_item.save()
    push_message_for_user = "You've received a free drink on Hotspot!"
    send_sms(push_message_for_user, [user.profile.normalized_phone])
    if (referring_user is not None) and (promo_code is not None):
        user.profile.used_promo_code = promo_code
        user.profile.save()


def check_for_referral_reward(user):
    promo_code = user.profile.used_promo_code
    if Promo.objects.filter(promo_code=promo_code).exists():
        promo_object = Promo.objects.get(promo_code=promo_code)
        add_reward_item_for_referring_user(user, promo_object.referring_user)
        user.profile.used_promo_code = promo_code + "_REWARD_SENT"
        user.profile.save()


def add_reward_item_for_referring_user(user, referring_user):
    add_reward_item(referring_user)
    push_message_for_referring_user = "You've received a free drink on Hotspot for inviting {0}!".format(user.first_name)
    send_sms(push_message_for_referring_user, [referring_user.profile.normalized_phone])


def add_reward_items_for_referral(user, referring_user):
    add_reward_item(user)
    add_reward_item(referring_user)
    push_message_for_referring_user = "You've received a free drink on Hotspot for inviting {0}!".format(user.first_name)
    push_message_for_user = "You've received a free drink on Hotspot!"
    send_sms(push_message_for_referring_user, [referring_user.profile.normalized_phone])
    send_sms(push_message_for_user, [user.profile.normalized_phone])


def add_reward_item(user):
    reward_item = RewardItem(user=user)
    reward_item.save()
    return reward_item


def add_manual_reward_item(user, message="You've received a free drink on Hotspot!"):
    reward_item = RewardItem(user=user)
    reward_item.save()
    # sms_message_for_user = "You've received a free drink on Hotspot!"
    send_sms(message, [user.profile.normalized_phone])


def get_contacts(user):
    contacts = Contact.objects.filter(normalized_phone=user.profile.normalized_phone)
    return contacts


def check_if_user_was_referred(user):
    user_as_contacts = get_contacts(user)
    lowercase_full_user_name = (user.first_name + " " + user.last_name).lower()
    if DealStatus.objects.filter(user=user, date_created__gte=datetime.now()-timedelta(days=1)).exists():
        deal_status = DealStatus.objects.filter(user=user, date_created__gte = datetime.now()-timedelta(days=1)).latest('date_created')
        add_reward_items_for_referral(deal_status.user, deal_status.invited_by)
        contact_status = ContactStatus.objects.get(deal_status=deal_status)
        contact_status.installed_app = True
        contact_status.save()
    elif ContactStatus.objects.filter(contact__in=user_as_contacts).exists():
        contact_status = ContactStatus.objects.filter(contact__in=user_as_contacts).latest('date_created')
        add_reward_items_for_referral(user, contact_status.referring_user)
        contact_status.installed_app = True
        contact_status.save()
    elif ContactStatus.objects.filter(phone_number=user.profile.normalized_phone).exists():
        add_reward_item(user)
        contact_status = ContactStatus.objects.filter(phone_number=user.profile.normalized_phone).latest('date_created')
        contact_status.installed_app = True
        contact_status.save()
        push_message_for_user = "You've received a free drink on Hotspot!"
        send_sms(push_message_for_user, [user.profile.normalized_phone])
    # elif any(s in lowercase_full_user_name for s in promo_codes):
    #     add_reward_item(user)
    #     push_message_for_user = "You've received a free drink on Hotspot!"
    #     send_sms(push_message_for_user, [user.profile.normalized_phone])


def authorize_reward_item(user, request_data):
    if 'deal_status_id' not in request_data:
        return False
    deal_status = DealStatus.objects.get(pk=int(request_data['deal_status_id']))
    if RewardItem.objects.filter(user=user, isRedeemed=False, reward_type=REWARD_TYPES.DRINK).exists():
        deal_status.payment_authorization = "REWARD"
        reward_item = RewardItem.objects.filter(user=user, isRedeemed=False, reward_type=REWARD_TYPES.DRINK)[0]
        reward_item.isRedeemed = True
        reward_item.save()
        deal_status.save()


def redeem_reward_item(user):
    reward_item = RewardItem.objects.filter(user=user, isRedeemed=False, reward_type=REWARD_TYPES.DRINK)[0]
    reward_item.isRedeemed = True
    reward_item.save()


def add_promo_code(user, promo_code):
    promo_code = promo_code.lower()
    if check_contact_status(user):
        if Promo.objects.filter(promo_code=promo_code).exists():
            if not RewardItem.objects.filter(promo_code__isnull=False, user=user, reward_type=REWARD_TYPES.DRINK).exists():
                if promo_code in promo_dct:
                    venue = DealPlace.objects.get(id=promo_dct[promo_code]['id'])
                    follow_redemption_location(user, venue)
                promo_object = Promo.objects.get(promo_code=promo_code)
                referring_user = promo_object.referring_user
                for i in range(promo_object.item_number):
                    if referring_user is not None:
                        add_promo_reward_items(user, referring_user, promo_code)
                    # else:
                    # add_promo_reward_items(user, None, promo_code)
                return "Code applied successfully"
            else:
                return "Promo has already been applied"
        else:
            return "Code is invalid"
    else:
        return "Code can't be used with other offers"


def check_contact_status(user):
    phone_number = user.profile.normalized_phone
    contacts = Contact.objects.filter(normalized_phone=phone_number)
    deal_statuses = DealStatus.objects.filter(user=user)
    all_contact_statuses = ContactStatus.objects.filter(Q(phone_number=phone_number) | Q(contact__in=contacts) | Q(deal_status__in=deal_statuses))
    if all_contact_statuses.filter(installed_app=True).exists():
        return False
    else:
        return True

def create_custom_promo_code(promo_code, number_of_items):
    if Promo.objects.filter(promo_code=promo_code).exists():
        print 'Promo code already exists'
    else:
        promo = Promo(item_number=number_of_items, promo_code=promo_code)
        print 'Promo code ' + promo_code + ' has been added'
        promo.save()


def get_email_subject():
    return """Try Hotspot, here's a free drink!"""


def get_email_body(promo_code):
    message = "I found an app, Hotspot, that gets us sweet drink specials at nearby bars. Use my promo code, " + promo_code + " and we both get a free drink"
    return message


def get_sms_message(promo_code):
    message = "I found an app, Hotspot, that gets us sweet drink specials. Use my promo code " + promo_code + " and we both get a free drink: http://bit.ly/1QkEBw1"
    return message


def check_promo_code(user, promo_code):
    promo_code = promo_code.lower()
    if Promo.objects.filter(promo_code=promo_code).exists():
        if not RewardItem.objects.filter(promo_code__isnull=False, user=user, reward_type=REWARD_TYPES.DRINK).exists():
            if promo_code in promo_dct:
                venue = DealPlace.objects.get(id=promo_dct[promo_code]['id'])
                follow_redemption_location(user, venue)
            promo_object = Promo.objects.get(promo_code=promo_code)
            referring_user = promo_object.referring_user
            for i in range(promo_object.item_number):
                if referring_user is not None:
                    add_promo_reward_items(user, referring_user, promo_code)
                else:
                    add_promo_reward_items(user, None, promo_code)
            print "Code applied successfully"
        else:
            print "Promo has already been applied"
    else:
        print "Code is invalid"


def check_web_promo_code(promo_code, event_id):
    if WebPromo.objects.filter(code__iexact=promo_code, event_id=event_id).exists():
        web_promo = WebPromo.objects.get(code__iexact=promo_code, event_id=event_id)
        return web_promo.price, web_promo.content
    elif BrandAmbassador.objects.filter(promo_code__iexact=promo_code).exists():
        ambassador = BrandAmbassador.objects.get(promo_code__iexact=promo_code)
        content = "{0} just saved you $5 on every ticket your purchase!".format(ambassador.name)
        return 15, content
    else:
        return False, False
