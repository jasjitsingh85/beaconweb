from django.shortcuts import render_to_response
from django.template import RequestContext
from beaconWeb.apps.beacon.common.utils.encryption import simple_int_hash
from beaconWeb.apps.beacon.models import *
from django.shortcuts import render
from django.http import HttpResponseRedirect
from beaconWeb.apps.beacon.forms import UploadFileForm
from beaconWeb.apps.beacon.common.constants.email_status import EMAIL_STATUS
from beaconWeb.apps.happy_hours.data_dump import process_csv
from beaconWeb.apps.beacon.forms import EventFeedback
from beaconWeb.apps.beacon.common.utils.payments import get_client_token
from django.contrib.auth.models import User
from beaconWeb.apps.beacon.common.common_utils import get_current_web_price, get_current_app_price, get_all_attendee_list, get_attendee_counts, add_email, add_email_with_event, get_market_for_event, get_four_nearest_events


def hotspot(request):
    context_dict = {}
    return render_to_response('beaconWeb/apps/beacon/templates/hotspot.html', context_dict, context_instance=RequestContext(request))


def dashboard(request):
    context_dict = {}
    # context_dict['new_haven_user_number'] = get_users_in_new_haven()
    # context_dict['chart_labels'], context_dict['chart_data'] = get_engagement_labels_and_data(30)
    return render_to_response('beaconWeb/apps/beacon/templates/splashtest.html', context_dict, context_instance=RequestContext(request))


def promo(request):
    context_dict = {}
    # context_dict['new_haven_user_number'] = get_users_in_new_haven()
    # context_dict['chart_labels'], context_dict['chart_data'] = get_engagement_labels_and_data(30)
    return render_to_response('beaconWeb/apps/beacon/templates/promo.html', context_dict, context_instance=RequestContext(request))


def save_feedback(request, user_id, event_id, nps_score):
    context_dict = {}
    context_dict['request'] = request
    user_id_unhashed = simple_int_hash(int(user_id))
    event_id_unhashed = simple_int_hash(int(event_id))
    user = User.objects.get(id=user_id_unhashed)
    sponsored_event = SponsoredEvent.objects.get(id=event_id_unhashed)
    feedback = UserFeedback(user=user, sponsored_event=sponsored_event, nps_score=int(nps_score))
    feedback.save()
    context_dict['feedback_id'] = feedback.id
    if request.method == 'POST':
        form = EventFeedback(request.POST)
        if form.is_valid():
            return HttpResponseRedirect('/submit/')
    else:
        form = EventFeedback(initial={'source':'...', 'frequency':'...'})
        context_dict['form'] = form
    return render_to_response('beaconWeb/apps/beacon/templates/feedback.html', context_dict, context_instance=RequestContext(request))


def submit_comments(request, feedback_id):
    context_dict = {}
    context_dict['request'] = request
    feedback = UserFeedback.objects.get(id=feedback_id)
    if request.method == 'POST':
        form = EventFeedback(request.POST)
        if form.is_valid():
            general = form.cleaned_data['general']
            if general:
                feedback.question1 = general
                feedback.save()
            source = form.cleaned_data['source']
            if source is not u"...":
                feedback.question2 = source
                feedback.save()
            frequency = form.cleaned_data['frequency']
            if frequency is not u"...":
                feedback.question3 = frequency
                feedback.save()
            improvements = form.cleaned_data['improvements']
            if improvements:
                feedback.question4 = improvements
                feedback.save()
    return render_to_response('beaconWeb/apps/beacon/templates/feedback-thanks.html', context_dict, context_instance=RequestContext(request))


def hotspot_deal(request, deal_status_id=None):
    context_dict = {}
    context_dict['request'] = request
    deal_status_id = simple_int_hash(int(deal_status_id))
    context_dict['deal_status_id'] = deal_status_id
    # if DealStatus.objects.filter(id=int(deal_status_id)):
    #     deal_status = DealStatus.objects.get(id=deal_status_id)
    #     if ContactStatus.objects.filter(deal_status=deal_status).exists():
    #         contact_status = ContactStatus.objects.filter(deal_status=deal_status)[0]
    #         contact_status.link_clicked = True
    #         contact_status.save()
    return render_to_response('beaconWeb/apps/beacon/templates/hotspot-deal-redirect.html', context_dict, context_instance=RequestContext(request))


def privacy(request):
    context_dict = {}
    return render_to_response('privacy.html', context_dict, context_instance=RequestContext(request))


def terms(request):
    context_dict = {}
    return render_to_response('terms.html', context_dict, context_instance=RequestContext(request))


def support(request):
    context_dict = {}
    return render_to_response('support.html', context_dict, context_instance=RequestContext(request))


def free_drink_coupon(request):
    context_dict = {}
    return render_to_response('beaconWeb/apps/beacon/templates/officehero.html', context_dict, context_instance=RequestContext(request))


def upload(request):
    if request.method == 'POST': # If the form has been submitted...
        # ContactForm was defined in the previous section
        #delete old objects
        file_name = request.FILES['file']
        process_csv(file_name)
        return HttpResponseRedirect('/admin/')
    else:
        form = UploadFileForm() # An unbound form

    return render(request, 'beaconWeb/apps/beacon/templates/upload.html', {
        'form': form,
    })


def load_payment(request, event_id=None):
    context_dict = {}
    context_dict['request'] = request
    event_id = int(event_id)
    context_dict['client_token'] = get_client_token()
    if SponsoredEvent.objects.filter(pk=event_id).exists():
        event = SponsoredEvent.objects.get(pk=event_id)
        context_dict['event'] = event
        context_dict['current_price'] = '{:,.2f}'.format(get_current_web_price(event))
        context_dict['app_price'] = '{:,.2f}'.format(get_current_app_price(event))
    # else:
    #     context_dict['event'] = None
        return render_to_response('beaconWeb/apps/beacon/templates/payment.html', context_dict, context_instance=RequestContext(request))


def checkout(request):
    context_dict = {}
    context_dict['request'] = request
    return render_to_response('beaconWeb/apps/beacon/templates/checkout.html', context_dict, context_instance=RequestContext(request))


def load_event_staffer(request, event_staffer_id=None):
    context_dict = {}
    context_dict['request'] = request
    event_staffer_id = int(event_staffer_id)
    if EventStaffer.objects.filter(pk=event_staffer_id).exists():
        event_staffer_obj = EventStaffer.objects.get(pk=event_staffer_id)
        context_dict['current_app_price'] = '{:,.2f}'.format(get_current_app_price(event_staffer_obj.event))
        context_dict['current_price'] = '{:,.2f}'.format(get_current_web_price(event_staffer_obj.event))
        context_dict['event_id'] = event_staffer_obj.event.id
        context_dict['event_staffer'] = event_staffer_obj
        context_dict['web_attendee_list'] = list(CashPayment.objects.filter(event=event_staffer_obj.event, name__isnull=False))
        context_dict['all_attendee_list'] = get_all_attendee_list(event_staffer_obj.event)
        context_dict['unredeemed_attendees'], context_dict['redeemed_attendees'], context_dict['web_reservations'], context_dict['total_attendees'] = get_attendee_counts(event_staffer_obj.event)
        return render_to_response('beaconWeb/apps/beacon/templates/event-staffer.html', context_dict, context_instance=RequestContext(request))



def load_email_response(request, email=None, event_id=None, response_boolean=None):
    context_dict = {}
    context_dict['request'] = request
    email = str(email)
    event_id = int(event_id)
    if bool(int(response_boolean)):
        status = EMAIL_STATUS.INTERESTED_IN_EVENT
    else:
        status = EMAIL_STATUS.NOT_INTERESTED_IN_EVENT
    event = SponsoredEvent.objects.get(pk=event_id)
    email_response_obj = EmailResponse(email=email, event=event, status=status)
    email_response_obj.save()
    return render_to_response('beaconWeb/apps/beacon/templates/response-captured.html', context_dict, context_instance=RequestContext(request))


def load_unsubscribe_form(request, email=None, event_id=None):
    context_dict = {}
    context_dict['request'] = request
    context_dict['email'] = str(email)
    context_dict['event_id'] = int(event_id)
    context_dict['event'] = SponsoredEvent.objects.get(pk=int(event_id))
    campaign = EmailStatus.objects.filter(email__iexact=str(email), event="open").latest('date_created')
    if request.method == 'POST':
        selection = request.POST['unsubscribe-option']
        if int(selection) == 0:
            email_response_obj = EmailResponse(email=email, event=context_dict['event'],
                                               status=EMAIL_STATUS.EVENT_UNSUBSCRIBE, campaign=campaign)
            email_response_obj.save()
            return render_to_response('beaconWeb/apps/beacon/templates/unsubscribe-complete.html', context_dict,
                                  context_instance=RequestContext(request))
        elif int(selection) == 1:
            email_response_obj = EmailResponse(email=email, event=context_dict['event'],
                                               status=EMAIL_STATUS.UNSUBSCRIBE, campaign=campaign)
            email_response_obj.save()
            return render_to_response('beaconWeb/apps/beacon/templates/unsubscribe-complete.html', context_dict,
                                  context_instance=RequestContext(request))
    else:
        email_response_obj = EmailResponse(email=email, event=context_dict['event'], status=EMAIL_STATUS.PAGE_VISITED, campaign=campaign)
        email_response_obj.save()
        return render_to_response('beaconWeb/apps/beacon/templates/unsubscribe.html', context_dict, context_instance=RequestContext(request))


def load_ticket_page(request, ticket_id=None):
    context_dict = {}
    event_id = simple_int_hash(int(ticket_id))
    event = SponsoredEvent.objects.get(pk=event_id)
    context_dict['event'] = event
    context_dict['client_token'] = get_client_token()
    context_dict['current_price'] = '{:,.2f}'.format(get_current_web_price(event))
    context_dict['app_price'] = '{:,.2f}'.format(get_current_app_price(event))
    context_dict['market'] = get_market_for_event(event)
    # context_dict['reviews'] = []
    context_dict['nearby_events'] = get_four_nearest_events(event)
    #page type static or #page type dynamic
    return render_to_response('beaconWeb/apps/beacon/templates/ticket.html', context_dict,
                              context_instance=RequestContext(request))


def load_promo_ticket_page(request, ticket_id=None):
    context_dict = {}
    event_id = simple_int_hash(int(ticket_id))
    event = SponsoredEvent.objects.get(pk=event_id)
    context_dict['event'] = event
    context_dict['client_token'] = get_client_token()
    context_dict['current_price'] = '{:,.2f}'.format(get_current_web_price(event))
    context_dict['app_price'] = '{:,.2f}'.format(get_current_app_price(event))
    context_dict['market'] = get_market_for_event(event)
    # context_dict['reviews'] = []
    context_dict['nearby_events'] = get_four_nearest_events(event)
    # page type static or #page type dynamic
    return render_to_response('beaconWeb/apps/beacon/templates/ticket-referral.html', context_dict,
                              context_instance=RequestContext(request))


def load_early_access_page(request, ticket_id=None):
    context_dict = {}
    event_id = simple_int_hash(int(ticket_id))
    event = SponsoredEvent.objects.get(pk=event_id)
    context_dict['event'] = event
    context_dict['client_token'] = get_client_token()
    context_dict['current_price'] = '{:,.2f}'.format(get_current_web_price(event))
    context_dict['app_price'] = '{:,.2f}'.format(get_current_app_price(event))
    context_dict['market'] = get_market_for_event(event)
    # context_dict['reviews'] = []
    context_dict['nearby_events'] = get_four_nearest_events(event)
    if request.method == 'POST':
        email = request.POST['email']
        add_email_with_event(email, event.market, event)
        return render_to_response('beaconWeb/apps/beacon/templates/submit-email-early-access.html', context_dict,context_instance=RequestContext(request))
    #page type static or #page type dynamic
    return render_to_response('beaconWeb/apps/beacon/templates/promo-tickets-early-access.html', context_dict,
                              context_instance=RequestContext(request))


def load_early_access_subscribe_page(request, ticket_id=None):
    context_dict = {}
    event_id = simple_int_hash(int(ticket_id))
    event = SponsoredEvent.objects.get(pk=event_id)
    context_dict['event'] = event
    # context_dict['client_token'] = get_client_token()
    context_dict['current_price'] = '{:,.2f}'.format(get_current_web_price(event))
    context_dict['app_price'] = '{:,.2f}'.format(get_current_app_price(event))
    context_dict['market'] = event.market
    # context_dict['reviews'] = []
    # context_dict['nearby_events'] = get_four_nearest_events(event)
    if request.method == 'POST':
        email = request.POST['email']
        add_email_with_event(email, event.market, event)
        return render_to_response('beaconWeb/apps/beacon/templates/submit-email-early-access-subscribe.html', context_dict,context_instance=RequestContext(request))
    #page type static or #page type dynamic
    return render_to_response('beaconWeb/apps/beacon/templates/promo-tickets-early-access-subscribe.html', context_dict,
                              context_instance=RequestContext(request))


def load_email_capture_for_event(request, ticket_id=None):
    context_dict = {}
    event_id = simple_int_hash(int(ticket_id))
    event = SponsoredEvent.objects.get(pk=event_id)
    context_dict['event'] = event
    # context_dict['client_token'] = get_client_token()
    context_dict['current_price'] = '{:,.2f}'.format(get_current_web_price(event))
    context_dict['app_price'] = '{:,.2f}'.format(get_current_app_price(event))
    context_dict['market'] = event.market.name
    if request.method == 'POST':
        email = request.POST['email']
        add_email_with_event(email, event.market, event)
        return render_to_response('beaconWeb/apps/beacon/templates/submit-email-complete.html', context_dict,context_instance=RequestContext(request))
    return render_to_response('beaconWeb/apps/beacon/templates/email-capture.html', context_dict, context_instance=RequestContext(request))


def load_email_capture(request, market_name=None):
    context_dict = {}
    context_dict['request'] = request
    context_dict['market'] = market_name.title()
    if Market.objects.filter(name__iexact=market_name).exists():
        market = Market.objects.get(name__iexact=market_name)
        if request.method == 'POST':
            email = request.POST['email']
            add_email(email, market)
            return render_to_response('beaconWeb/apps/beacon/templates/submit-email-complete.html', context_dict,context_instance=RequestContext(request))
        return render_to_response('beaconWeb/apps/beacon/templates/email-capture.html', context_dict, context_instance=RequestContext(request))


def load_facebook_share(request, event_id_hash=None):
    context_dict = {}
    # event_id = simple_int_hash(int(event_id_hash))
    # event = SponsoredEvent.objects.get(pk=event_id)
    # context_dict['event'] = event
    return render_to_response('beaconWeb/apps/beacon/templates/facebook-share.html', context_dict,
                              context_instance=RequestContext(request))
