import braintree
from django.db.models import Q
from beaconWeb.apps.beacon.models import DealStatus, Beacon, Payment, EventStatus, SponsoredEvent, CashPayment, WebPromo, BrandAmbassador
from datetime import datetime, timedelta
from beaconWeb.apps.beacon.common.constants.deal_status import DEAL_STATUS
from django.contrib.auth.models import User
from beaconWeb.apps.beacon.common.constants.event_status import EVENT_STATUS
from beaconWeb.apps.beacon.common.common_utils import get_presale_status
from beaconWeb.apps.beacon.analytics.analytics import excluded_users
from beaconWeb.apps.beacon.retention.emails import send_marketing_email, send_web_order_confirmation, send_receipt
from django.conf import settings
from beaconWeb.apps.beacon.common.common_utils import get_current_web_price

if settings.ENVIRONMENT and settings.ENVIRONMENT == 'Staging':
    braintree.Configuration.configure(
        braintree.Environment.Sandbox,
        '92szcn5tcrkdnh9z',
        'fbg29zqwfb3zjspj',
        '359239026002edc9de1e139ee8d76f72'
    )
else:
    braintree.Configuration.configure(
        braintree.Environment.Production,
        'c9zkknmmybm6778w',
        '8xcmpngmd5wgkm99',
        'e3a83a606ee128985268f6c46deb9a8a'
    )


def get_client_token(user=None):
    # braintree.Configuration.configure(
    #     braintree.Environment.Production,
    #     'c9zkknmmybm6778w',
    #     '8xcmpngmd5wgkm99',
    #     'e3a83a606ee128985268f6c46deb9a8a'
    # )

    try:
        if user:
            return braintree.ClientToken.generate({
                "customer_id": str(user.id)
            })
        else:
            return braintree.ClientToken.generate()
    except Exception:
        return braintree.ClientToken.generate()


# def create_transaction(user, request_data):
#     if not 'payment_nonce' in request_data:
#         return False
#     else:
#         nonce = request_data['payment_nonce']
#         result = braintree.Transaction.sale({
#             "amount": "10.00",
#             "customer_id": str(jeff.id)
#         })


def check_if_payment_on_file(user):

    try:
        customer = braintree.Customer.find(str(user.id))
        if len(customer.payment_methods) > 0:
            return True
        else:
            return False
    except Exception:
        create_payments_user(user)
        return False


def create_payments_user(user):
    result = braintree.Customer.create({
        "id": user.id,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "phone": user.username,
    })
    return result.is_success


def create_payment_method(user, payment_nonce):
    payment_info = braintree.PaymentMethod.create({
                    "customer_id": str(user.id),
                    "payment_method_nonce": payment_nonce,
                    "options": {
                        "verify_card": True,
                        "make_default": True
                    }
                })
    return payment_info


def change_payment_method(user, payment_nonce, has_payment):
    # if has_payment:
    #     sale_result = braintree.Transaction.sale({
    #         "amount": "0.01",
    #         "payment_method_nonce": payment_nonce,
    #     })
    #
    #     if sale_result.is_success:
    #         payment_token = sale_result.transaction.credit_card['token']
    #         if payment_token:
    #             result = braintree.PaymentMethod.update(str(payment_token), {
    #                 "options": {
    #                     "make_default": True
    #                 }
    #             })
    #     #     void_result = braintree.Transaction.void(str(sale_result.transaction.id))
    #
    #     return sale_result
    # else:
    result = create_payment_method(user, payment_nonce)
    return result


def make_payment_method_default(user, payment_token):
    print "PAYMENT TOKEN: " + str(payment_token)
    result = braintree.PaymentMethod.update(str(payment_token), {
        "options": {
            "make_default": True
        }
    })
    return result


def authorize_payment_for_event(user, payment_nonce=None):
    # amount_to_authorize = 1
    if payment_nonce:
        result = create_payment_method(user, payment_nonce)
        return result.is_success
    else:
        return True
    # result = braintree.Transaction.sale({
    #                 "customer_id": str(user.id),
    #                 "amount": str(amount_to_authorize)
    #             })
    #
    # return result.is_success


def authorize_payment(user, beacon_id=None, payment_nonce=None):
    if beacon_id is None:
        has_payment = check_if_payment_on_file(user)
        result = change_payment_method(user, payment_nonce, has_payment)
        # print "Payment Nonce: " + str(payment_nonce)
        # print "Make Default: " + str(payment_info.transaction)
        # print "Credit card:  " + str(payment_info.transaction.credit_card)
        # make_payment_method_default(user, payment_info.transaction.credit_card['token'])
        return result.is_success
    else:
        beacon = Beacon.objects.get(pk=int(beacon_id))
        # if beacon.creator.id == user.id:
        deal_status = DealStatus.objects.get(user=user, beacon=beacon)
        if deal_status.payment_authorization is None:
            amount_to_authorize = get_amount_to_authorize(deal_status)
            print "Authorizing Payment"
            if payment_nonce is None:
                print "No Payment Nonce Provided"
                result = braintree.Transaction.sale({
                    "customer_id": str(user.id),
                    "amount": str(amount_to_authorize)
                })
            else:
                print "Payment Nonce Provided"
                print str(amount_to_authorize)
                print str(payment_nonce)
                payment_info = create_payment_method(user, payment_nonce)
                result = braintree.Transaction.sale({
                    "customer_id": str(user.id),
                    "amount": str(amount_to_authorize)
                })
                print "Successful Authorization: " + str(result.is_success)
            if result.is_success:
                deal_status.payment_authorization = result.transaction.id
                deal_status.save()
                # deal_statuses = DealStatus.objects.filter(beacon=deal_status.beacon)
                # for deal_status in deal_statuses:
                #     deal_status.payment_authorization = result.transaction.id
                #     deal_status.save()
            return result.is_success
        else:
            print "Authorization already complete"
            return True
        # else:
        #     print "User isn't mobilizer"
        #     return True


def authorize_payment_for_entire_tab(tab):
    user = tab.user
    amount_to_authorize = tab.amount_paid + tab.convenience_fee
    result = braintree.Transaction.sale({
        "customer_id": str(user.id),
        "amount": str(amount_to_authorize)
    })
    print "Successful Authorization: " + str(result.is_success)
    if result.is_success:
        tab.payment_authorization = result.transaction.id
        tab.save()
        return True
    elif result.transaction:
        print("Error processing transaction:")
        print("  code: " + result.transaction.processor_response_code)
        print("  text: " + result.transaction.processor_response_text)
        send_marketing_email("info@gethotspotapp.com", "BRAINTREE ERROR", ['wxu121@gmail.com'], "BRAINTREE ERROR processing transaction", "BRAINTREE ERROR processing transaction", "BRAINTREE ERROR processing transaction", "test")
        return False
    else:
        for error in result.errors.deep_errors:
            print("attribute: " + error.attribute)
            print("  code: " + error.code)
            print("  message: " + error.message)
        send_marketing_email("info@gethotspotapp.com", "BRAINTREE ERROR", ['wxu121@gmail.com'], "BRAINTREE DEEP ERROR", "BRAINTREE DEEP ERROR", "BRAINTREE DEEP ERROR", "test")
        return False


def get_amount_to_authorize(deal_status):
    if deal_status.deal.item_price is not None:
        item_price = deal_status.deal.item_price
        # deal_statuses = DealStatus.objects.filter(beacon=deal_status.beacon)
        # amount_to_authorize = item_price * len(deal_statuses)
        # return amount_to_authorize
        return deal_status.deal.item_price
    else:
        return False


def is_mobilizer(user, beacon_id):
    beacon = Beacon.objects.get(pk=int(beacon_id))
    if beacon.creator.id == user.id:
        return True
    else:
        return False


def get_total_cost(redeemed_deal_statuses):
    total = 0
    for deal_status in redeemed_deal_statuses:
        total = total + deal_status.deal.item_price
    return total


def settle_single_redemption(deal_status):
    auth_code = deal_status.payment_authorization
    print "Submitting for settlement: {0} for ${1} on {2}".format(auth_code, str(deal_status.deal.item_price), str(deal_status.date_created))
    try:
        result = braintree.Transaction.submit_for_settlement(auth_code)
        if result.is_success:
            print "Successfully Settled (single)"
            payment = Payment(payment_authorization=auth_code, is_submitted=True)
            payment.save()
            print "Payment object {0} created with auth code {1}".format(str(payment.id), auth_code)
            deal_status.payment = payment
            deal_status.save()
            print "Deal_status {0} updated with payment {1}".format(str(deal_status.id), str(payment.id))
        else:
            print "Single settlement {0} for user {1} failed".format(auth_code, str(user.id))
        return deal_status
    except:
        print "Single settlement {0} for user {1} failed".format(auth_code, str(user.id))
        return False


def settle_deal_payments(deal_statuses, last_successful_settlement):
    user = deal_statuses[0].user
    #last_successful_settlement = Payment.objects.filter(is_submitted=True).latest('date_submitted').date_submitted
    current_date = datetime.now()
    redeemed = deal_statuses.filter(deal_status=DEAL_STATUS.REDEEMED)
    unredeemed = deal_statuses.exclude(deal_status=DEAL_STATUS.REDEEMED)
    paid = []
    unpaid = []
    try:
        print "{0} {1} {2} had {3} redemptions and {4} unused deal_statuses".format(str(user.id), user.first_name, user.last_name, str(len(redeemed)), str(len(unredeemed)))
    except:
        print "{0} had {1} redemptions and {2} unused deal_statuses".format(str(user.id), str(len(redeemed)), str(len(unredeemed)))
    if len(redeemed) == 0:
        print "No redemptions for user {0}".format(str(user.id))
    #submit a single transaction for settlement
    elif len(redeemed) == 1:
        deal_status = redeemed[0]
        result = settle_single_redemption(deal_status)
        #returns deal_status if transaction successfully settled
        if result == deal_status:
            paid.append(result)
        else:
            unpaid.append(deal_status)
    #bundles transactions, create new authorization and immediately settle
    elif len(redeemed) > 1:
        total_cost = get_total_cost(redeemed)
        print "Total cost = ${0}".format(str(total_cost))
        bundled_result = braintree.Transaction.sale({
            "customer_id": str(user.id),
            "amount": str(total_cost),
            "options": {
                "submit_for_settlement": True
            }
        })
        if bundled_result.is_success:
            auth_code = bundled_result.transaction.id
            print "Successfully settled (bundled): {0} for ${1}".format(auth_code, str(total_cost))
            payment = Payment(payment_authorization=auth_code, is_submitted=True)
            payment.save()
            print "Payment object {0} created with auth code {1}".format(str(payment.id), auth_code)
            for deal_status in redeemed:
                deal_status.payment = payment
                deal_status.save()
                paid.append(deal_status)
                print "Deal_status {0} updated with payment {1}".format(str(deal_status.id), str(payment.id))
                #void unused authorizations
                auth_code = deal_status.payment_authorization
                result = braintree.Transaction.void(str(auth_code))
                if result.is_success:
                    print "Transaction {0} voided for user {1}".format(auth_code,str(user.id))
                else:
                    print "Transaction {0} not voided".format(auth_code,str(user.id))
        #submit individual authorizations for settlement if bundled payment fails
        else:
            print "Bundled settlement user {0} failed".format(str(user.id))
            for deal_status in redeemed:
                result = settle_single_redemption(deal_status)
                if result:
                    paid.append(deal_status)
                else:
                    unpaid.append(deal_status)
    #if all paid, void authorizations on unused deal_status objects
    if len(unpaid) == 0:
        if len(unredeemed) > 0:
            for unredeemed_deal_status in unredeemed:
                auth_code = unredeemed_deal_status.payment_authorization
                result = braintree.Transaction.void(str(auth_code))
                if result.is_success:
                    print "Transaction {0} voided for user {1}".format(auth_code,str(user.id))
                else:
                    print "Transaction {0} not voided".format(auth_code,str(user.id))
    if len(unpaid) > 0:
        print "User {0} has {1} unpaid redemptions:".format(str(user.id), str(len(unpaid)))
        for x in unpaid:
            print "deal_status {0}, payment_authorization {1} ".format(str(deal_status.id), x.payment_authorization)
    #send a receipt
    if len(paid) > 0:
        total_paid = get_total_cost(paid)
        try:
            send_receipt(paid, last_successful_settlement, current_date, total_paid)
            print "Receipt sent to user {0}".format(str(user.id))
        except:
            print "Emailed failed for user {0}".format(str(user.id))
    else:
        print "No receipt needed"


def submit_for_settlement_deals():
    # braintree.Configuration.configure(
    #      braintree.Environment.Production,
    #      'c9zkknmmybm6778w',
    #      '8xcmpngmd5wgkm99',
    #      'e3a83a606ee128985268f6c46deb9a8a'
    # )
    last_settled_deal_status = DealStatus.objects.filter(payment__isnull=False).latest('date_created')
    last_successful_settlement = last_settled_deal_status.payment.date_submitted
    current_date = datetime.now()
    deal_statuses = DealStatus.objects.filter(date_created__gt=last_successful_settlement, date_created__lte=current_date, contact__isnull=True, payment_authorization__isnull=False).exclude(user__in=excluded_users).exclude(payment_authorization="REWARD").exclude(payment_authorization="UNREDEEMED_REWARD")
    user_with_tabs_ids = deal_statuses.distinct('user').values_list('user', flat=True)
    users_with_tabs = User.objects.filter(pk__in=user_with_tabs_ids)
    print "{0} users with {1} deal_statuses from {2} to {3}".format(str(len(users_with_tabs)), str(len(deal_statuses)), last_successful_settlement.strftime("%Y-%m-%d"), current_date.strftime("%Y-%m-%d"))
    print " "
    if len(users_with_tabs) > 0:
        for user in users_with_tabs:
            authorized_deal_statuses = deal_statuses.filter(user=user)
            if len(authorized_deal_statuses) > 0:
                try:
                    settle_deal_payments(authorized_deal_statuses, last_successful_settlement)
                    print "Tab Settled for {0} {1} {2}".format(str(user.id), user.first_name, user.last_name)
                except:
                    print "Settle Payment Failed for User: " + str(user.id)
            print " "
    else:
        print "No tabs to settle"


def get_event_statuses_in_range(min_date, max_date):
    events_in_range = SponsoredEvent.objects.filter(start__gte=min_date, end__lt=max_date)
    event_statuses = EventStatus.objects.filter(Q(event__in=events_in_range), Q(status="U") | Q(status="R"))
    return event_statuses


def add_payment_to_db(event_status, price, result):
    auth_code = result.transaction.id
    print "Successfully settled: {0} for ${1}".format(auth_code, str(price))
    payment = Payment(payment_authorization=auth_code, is_submitted=True)
    payment.save()
    print "Payment object {0} created with auth code {1}".format(str(payment.id), auth_code)
    event_status.payment = payment
    event_status.is_presale = get_presale_status(event_status)
    event_status.save()
    print "Event_status {0} updated with payment {1}".format(str(event_status.id), str(payment.id))


def settle_single_event_transaction(event_status,price):
    user = event_status.user
    print "Price for status {0} = ${1}".format(str(event_status.id),str(price))
    if not event_status.payment:
        result = braintree.Transaction.sale({
            "customer_id": str(user.id),
            "amount": str(price),
            "options": {
                "submit_for_settlement": True
            }
        })
        if result.is_success:
            add_payment_to_db(event_status,price,result)
            #if we add tracking for reservations authorizations, add voiding here
            print "Successful settlement for user {0} on event {1}".format(str(user.id), event_status.event.place.name)
        else:
            print "Settlement failed for user {0}".format(str(user.id))
            print result.message
    else:
        print "Status {0} has already been paid, cancelling settlement".format(str(event_status.id))

#Manually adjust last_successful settlement for first run
def submit_events_for_settlement(event_statuses):
    #last_settled_event_status = EventStatus.objects.filter(payment__isnull=False).latest('date_created')
    #last_successful_settlement = last_settled_event_status.payment.date_submitted
    #last_successful_settlement = datetime(2016,3,1)
    #current_date = datetime.now()
    #event_statuses = get_event_statuses_in_range(last_succesful_settlement,current_date)
    statuses_qs = EventStatus.objects.filter(pk__in=[x.pk for x in event_statuses])
    redeemed = statuses_qs.filter(status="R")
    unredeemed = statuses_qs.filter(status="U")
    #settle each event status
    for status in redeemed:
        price = status.event.item_price
        try:
            settle_single_event_transaction(status,price)
            print "\n"
        except:
            print "Settlement failed: user {0} and status {1}".format(str(status.user.id), status.id)
    for status in unredeemed:
        price = 1.0
        try:
            settle_single_event_transaction(status,price)
            print "\n"
        except:
            print "Settlement failed: user {0} and status {1}".format(str(status.user.id), status.id)

def submit_for_settlement_sandbox(users):
    #testing in sandbox
    braintree.Configuration.configure(
        braintree.Environment.Sandbox,
        '92szcn5tcrkdnh9z',
        'fbg29zqwfb3zjspj',
        '359239026002edc9de1e139ee8d76f72'
    )
    last_successful_settlement = Payment.objects.filter(is_submitted=True).latest('date_submitted').date_submitted
    current_date = datetime.now()
    #testing. For prod, remove (user__in=users) AND ADD .exclude(user__in=excluded_users)
    deal_statuses = DealStatus.objects.filter(user__in=users, date_created__gt=last_successful_settlement, date_created__lte=current_date, contact__isnull=True, payment_authorization__isnull=False).exclude(payment_authorization="REWARD")
    user_with_tabs_ids = deal_statuses.distinct('user').values_list('user', flat=True)
    users_with_tabs = User.objects.filter(pk__in=user_with_tabs_ids)
    print "{0} users with {1} deal_statuses from {2} to {3}".format(str(len(users_with_tabs)), str(len(deal_statuses)), last_successful_settlement.strftime("%Y-%m-%d"), current_date.strftime("%Y-%m-%d"))
    print " "
    if len(users_with_tabs) > 0:
        for user in users_with_tabs:
            authorized_deal_statuses = deal_statuses.filter(user=user)
            if len(authorized_deal_statuses) > 0:
                try:
                    settle_deal_payments(authorized_deal_statuses)
                    print "Tab Settled for {0} {1} {2}".format(str(user.id), user.first_name, user.last_name)
                except:
                    print "Settle Payment Failed for User: " + str(user.id)
            print " "
    else:
        print "No tabs to settle"


def sandbox_testing_add_authorizatons(users):
    braintree.Configuration.configure(
        braintree.Environment.Sandbox,
        '92szcn5tcrkdnh9z',
        'fbg29zqwfb3zjspj',
        '359239026002edc9de1e139ee8d76f72'
    )
    last_successful_settlement = Payment.objects.filter(is_submitted=True).latest('date_submitted').date_submitted
    current_date = datetime.now()
    deal_statuses = DealStatus.objects.filter(user__in=users, date_created__gt=last_successful_settlement, date_created__lte=current_date, contact__isnull=True, payment_authorization__isnull=False).exclude(payment_authorization="REWARD")
    for deal_status in deal_statuses:
        amount_to_authorize = get_amount_to_authorize(deal_status)
        result = braintree.Transaction.sale({
            "customer_id": str(deal_status.user.id),
            "amount": str(amount_to_authorize)
        })
        if result.is_success:
            deal_status.payment_authorization = result.transaction.id
            deal_status.save()
            print str(deal_status.id) + " authorized with " + result.transaction.id
        else:
            print str(deal_status.id) + " not authorized"


def get_customer_payment(user):
    customer = braintree.Customer.find(str(user.id))
    payment_methods = customer.payment_methods
    if check_if_payment_on_file(user):
        card_info = {}
        for payment_method in payment_methods:
            if payment_method.default:
                card_info['card_type'] = payment_method.card_type
                card_info['last_four'] = payment_method.last_4
                return card_info
    else:
        return None


def charge_user_for_event(user, event_status):
    if get_presale_status(event_status):
        total_amount = event_status.event.presale_item_price + event_status.tip_amount
    else:
        total_amount = event_status.event.item_price + event_status.tip_amount
    result = braintree.Transaction.sale({
            "customer_id": str(user.id),
            "amount": str(total_amount),
            "options": {
                "submit_for_settlement": True
            }
        })
    if result.is_success:
        add_payment_to_db(event_status, user, result)
        return event_status
    else:
        event_status.delete()
        return False


def charge_payment(request_data):
    if 'nonce' and 'full_name' and 'email' and 'event_id' and 'attendees' and 'promo_code' not in request_data:
        return False
    event_id = int(request_data['event_id'])

    if not SponsoredEvent.objects.filter(pk=event_id).exists():
        return False

    print str(request_data)
    event = SponsoredEvent.objects.get(pk=event_id)
    name = request_data['full_name']
    email = request_data['email']
    attendees = int(request_data['attendees'])
    nonce = request_data['nonce']
    promo_code = request_data['promo_code']
    if 'tip' in request_data:
        tip = float(request_data['tip'])
        success = charge_web_user_for_event_with_tip(name, email, event, attendees, nonce, promo_code, tip)
    else:
        success = charge_web_user_for_event(name, email, event, attendees, nonce, promo_code)
    return success


def charge_web_user_for_event(name, email, event, attendees, nonce, promo_code):
    if WebPromo.objects.filter(code__iexact=promo_code, event=event).exists():
        web_promo = WebPromo.objects.get(code__iexact=promo_code, event=event)
        total = web_promo.price * attendees
        code = promo_code
    else:
        total = get_current_web_price(event) * attendees
        code = None
    print "PROMO CODE: " + str(code)
    result = braintree.Transaction.sale({
        "amount": str(total),
        "payment_method_nonce": nonce,
        "options": {
            "submit_for_settlement": True
        }
    })
    print "RESULT: " + str(result.is_success)
    if result.is_success:
        cash_payment = CashPayment(attendees=attendees, event=event, name=name, email=email, total=total, promo_code=code)
        cash_payment.save()
        send_web_order_confirmation(cash_payment)
    return result.is_success


def charge_web_user_for_event_with_tip(name, email, event, attendees, nonce, promo_code, tip):
    if WebPromo.objects.filter(code__iexact=promo_code, event=event).exists():
        web_promo = WebPromo.objects.get(code__iexact=promo_code, event=event)
        total = (web_promo.price * attendees)
        code = promo_code
    elif BrandAmbassador.objects.filter(promo_code__iexact=promo_code).exists():
        total = (15 * attendees)
        code = promo_code
    else:
        total = (get_current_web_price(event) * attendees)
        code = None
    print "PROMO CODE: " + str(code)
    result = braintree.Transaction.sale({
        "amount": str(total + tip),
        "payment_method_nonce": nonce,
        "options": {
            "submit_for_settlement": True
        }
    })
    print "RESULT: " + str(result.is_success)
    if result.is_success:
        cash_payment = CashPayment(attendees=attendees, event=event, name=name, email=email, total=total,
                                   promo_code=code, tip=tip)
        cash_payment.save()
        send_web_order_confirmation(cash_payment)
    return result.is_success
