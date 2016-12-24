from beaconWeb.apps.beacon.models.deal import Deal
from beaconWeb.apps.beacon.models.deal_place import DealPlace
from beaconWeb.apps.beacon.models.employee import Employee
from beaconWeb.apps.beacon.models.tab import Tab
from beaconWeb.apps.beacon.models.tab_item import TabItem
from beaconWeb.apps.beacon.models.deal_hours import DealHours
from beaconWeb.settings import OMNIVORE_DEV_KEY
import requests
import json
from datetime import datetime
from decimal import Decimal, ROUND_HALF_UP
import random
from beaconWeb.geo_timezone import GeoTimeZone
import traceback
from beaconWeb.apps.beacon.retention.emails import send_marketing_email
from beaconWeb.apps.beacon.common.utils.payments import authorize_payment_for_entire_tab

AUTH = {"Api-Key": OMNIVORE_DEV_KEY}
OMNIVORE_BASE_URL = "https://api.omnivore.io/0.1/locations/"
SIMPLICITY_BASE_URL = "http://api.simplicitypos.io/v1/locations/"


def get_active_deal_for_place(place):
    deals_queryset = Deal.objects.filter(active=True, place=place, deal_type="DT")
    deals = list(deals_queryset)
    timezone = GeoTimeZone().get_timezone(latitude=place.latitude, longitude=place.longitude)
    now = datetime.now(tz=timezone)
    weekday = (now.weekday() + 1) % 7
    weekday_bit = [DealHours.days_active.Sunday, DealHours.days_active.Monday, DealHours.days_active.Tuesday,
                   DealHours.days_active.Wednesday, DealHours.days_active.Thursday, DealHours.days_active.Friday,
                   DealHours.days_active.Saturday][weekday]
    now_in_seconds = 60*60*now.hour + 60*now.minute + now.second
    deal_hours = DealHours.objects.filter(deal__in=deals)
    for deal in deals:
        if deal_hours.filter(deal=deal, days_active=weekday_bit, end__gte=now_in_seconds).exists():
            return deal
    return None


def create_tab(user, request_data_dict):
    deal_place_id = int(request_data_dict['place_id'])
    place = DealPlace.objects.get(id=deal_place_id)
    point_of_sale = place.point_of_sale
    api_tab_id = create_simplicity_tab(user, point_of_sale)
    print type(api_tab_id)
    print api_tab_id
    try:
        print int(api_tab_id)
    except ValueError:
        print "create tab failed, pos not active"
        send_marketing_email("info@gethotspotapp.com", "POS ERROR", ['wxu121@gmail.com'], "POS ERROR create_tab failed", "POS ERROR create_tab failed, pos not active", "POS ERROR create_tab failed, pos not active", "test")
        return False
    if int(api_tab_id) < 0:
        print "create tab failed"
        send_marketing_email("info@gethotspotapp.com", "POS ERROR", ['wxu121@gmail.com'], "POS ERROR create_tab failed", "POS ERROR create_tab failed", "POS ERROR create_tab failed", "test")
        return False
    tab = create_tab_object(user, api_tab_id, point_of_sale)
    tab_items = []
    #deal = get_active_deal_for_place(place)
    #if deal:
    #    added_drink_menu_id, added_drink_overall_id, added_drink_name, added_drink_price = add_hotspot_drink_and_return_drink_info(tab, deal)
    #    tab_item = create_tab_item_object(tab, added_drink_menu_id, added_drink_overall_id, added_drink_name, added_drink_price, deal)
    #    tab_item = add_extra_deal_properties(tab_item)
    #    tab_items = [tab_item]
    #else:
    #    tab_items = []
    simplicity_tab_info = return_simplicity_tab_info(tab)
    tab = update_tab_object(tab, simplicity_tab_info)
    return tab, tab_items


def add_extra_deal_properties(tab_item):
    if tab_item.deal:
        tab_item.deal.total_check_ins = None
        tab_item.deal.is_reward_item = None
    return tab_item


def user_has_open_tab(user, point_of_sale):
    if Tab.objects.filter(user=user, point_of_sale=point_of_sale, closed=False, cancelled=False).exists():
        return True
    else:
        return False


def create_omnivore_tab(user, point_of_sale):
    open_tab_parameters = return_omnivore_open_tab_parameters(user, point_of_sale)
    response = requests.post(OMNIVORE_BASE_URL + point_of_sale.location_id + "/tickets", headers=AUTH, data=open_tab_parameters)
    return response.json()['id']


def return_omnivore_open_tab_parameters(user, point_of_sale):
    tab_parameters = {}
    tab_parameters['order_type'] = point_of_sale.default_order_type_id
    tab_parameters['revenue_center'] = point_of_sale.default_revenue_center
    tab_parameters['table_id'] = point_of_sale.default_table_id
    tab_parameters['employee_id'] = point_of_sale.default_employee.employee_id
    tab_parameters['guest_count'] = 1
    tab_parameters['name'] = return_tab_name(user)
    tab_parameters['auto_send'] = True
    return json.dumps(tab_parameters)


def return_tab_name(user):
    long_name = user.first_name + " " + user.last_name
    if len(long_name) > 16:
        standard_name = long_name[:16]
    else:
        standard_name = long_name
    return standard_name


def increment_ticket_name(x, old_name):
    new_name = old_name[:14] + " " + str(x)
    return new_name


def add_hotspot_drink(point_of_sale, omnivore_tab_id, deal):
    order_item_parameters = return_omnivore_add_drink_parameters(deal)
    response = requests.post(OMNIVORE_BASE_URL + point_of_sale.default_location_id + "/tickets/" + omnivore_tab_id + "/items", headers=AUTH, data=order_item_parameters)
    added_drink_id = response.json()['_embedded']['items'][0]['id']
    name = response.json()['_embedded']['items'][0]['name']
    price = response.json()['_embedded']['items'][0]['price']
    return added_drink_id, name, price


def return_omnivore_add_drink_parameters(deal):
    add_drink_parameters = {}
    add_drink_parameters['menu_item'] = deal.pos_item_id
    add_drink_parameters['quantity'] = 1
    add_drink_parameters['price_level'] = deal.pos_price_id
    return json.dumps(add_drink_parameters)


def tab_claimed(point_of_sale, omnivore_tab_id):
    response = requests.get(OMNIVORE_BASE_URL + point_of_sale.location_id + "/tickets/" + omnivore_tab_id, headers=AUTH)
    employee_dict = response.json()['_embedded']['employee']
    if employee_dict['id'] == point_of_sale.default_employee.employee_id:
        return False
    else:
        return employee_dict


def check_if_tab_claimed(user, deal_place_id, omnivore_tab_id, item_id):
    place = DealPlace.objects.get(id=deal_place_id)
    point_of_sale = place.point_of_sale
    employee_dict = tab_claimed(point_of_sale, omnivore_tab_id)
    if employee_dict:
        employee = create_employee_object(employee_dict)
        tab = create_tab_object(user, omnivore_tab_id, point_of_sale, employee)
        create_tab_item_object(tab, item_id, omnivore_tab_id, point_of_sale)
        return True
    else:
        return False


def create_employee_object(employee_dict):
    if Employee.objects.filter(employee_id=employee_dict['id']).exists():
        return Employee.objects.get(employee_id=employee_dict['id'])
    else:
        employee = Employee(employee_id=employee_dict['id'], first_name=employee_dict['first_name'], last_name=employee_dict['last_name'])
        employee.save()
        return employee


def create_tab_object(user, api_tab_id, point_of_sale):
    tab = Tab(user=user, point_of_sale=point_of_sale, api_tab_id=api_tab_id, employee=point_of_sale.default_employee, order_type_id=point_of_sale.default_order_type_id, revenue_center_id=point_of_sale.default_revenue_center_id, table_id=point_of_sale.default_table_id)
    tab.save()
    return tab


def create_tab_item_object(tab, menu_id, overall_id, item_name, item_price, deal):
    price_decimal = Decimal(str(item_price))
    tab_item = TabItem(tab=tab, menu_item_id=menu_id, overall_item_id=overall_id, name=item_name, price=price_decimal, deal=deal)
    tab_item.save()
    return tab_item


def get_tab_and_tab_items(user, query_parameters_dict):
    if 'place_id' not in query_parameters_dict:
        return False
    deal_place_id = int(query_parameters_dict['place_id'])
    print str(deal_place_id)
    place = DealPlace.objects.get(id=deal_place_id)
    point_of_sale = place.point_of_sale
    tab = Tab.objects.get(user=user, point_of_sale=point_of_sale, closed=False, cancelled=False)
    tab, tab_items = update_tab_and_tab_item_objects(tab)
    final_tab_items = []
    for tab_item in tab_items:
        final_tab_item = add_extra_deal_properties(tab_item)
        final_tab_items.append(final_tab_item)
    return tab, final_tab_items


def close_tab(user, request_data_dict):
    if 'place_id' and "tip" not in request_data_dict:
        return False
    deal_place_id = int(request_data_dict['place_id'])
    place = DealPlace.objects.get(id=deal_place_id)
    point_of_sale = place.point_of_sale
    tab = Tab.objects.get(user=user, point_of_sale=point_of_sale, closed=False, cancelled=False)
    tip = Decimal(request_data_dict['tip'])
    tab = add_amount_paid_to_tab(tab, tip)
    if not authorize_payment_for_entire_tab(tab):
        return tab
    tab = close_tab_in_object(tab, tip)
    response = close_simplicity_tab(tab)
    if response != 1:
        print "close tab failed"
        send_marketing_email("info@gethotspotapp.com", "POS ERROR", ['wxu121@gmail.com'], "POS ERROR close_tab failed", "POS ERROR close_tab failed", "POS ERROR close_tab failed", "test")
        return False
    return tab


def add_amount_paid_to_tab(tab, tip):
    tab.amount_paid = return_simplicity_amount_due(tab) + tip
    tab.save()
    return tab


def close_tab_in_object(tab, tip):
    tab.closed = True
    tab.tip = tip
    tab.total = calculate_total(tab)
    tab.date_closed = datetime.now()
    tab.save()
    return tab


def calculate_convenience_fee(tab):
    subtotal = tab.subtotal
    percentage_convenience_fee = Decimal('0.03') * subtotal
    flat_convenience_fee = Decimal('0.50')
    if percentage_convenience_fee > flat_convenience_fee:
        return percentage_convenience_fee
    else:
        return flat_convenience_fee


def calculate_total(tab):
    subtotal = tab.subtotal
    other_charges = tab.other_charges
    tax = tab.tax
    discount = tab.discount
    convenience_fee = tab.convenience_fee
    tip = tab.tip
    total = subtotal + other_charges + tax + convenience_fee + tip - discount
    print total
    return total


def return_simplicity_amount_due(tab):
    simplicity_tab_info = return_simplicity_tab_info(tab)
    simplicity_total = Decimal(simplicity_tab_info['amount_due'])
    return simplicity_total


def calculate_simplicity_total(tab):
    total = tab.total
    convenience_fee = tab.convenience_fee
    simplicity_total = total - convenience_fee
    return simplicity_total


def return_simplicity_open_tab_parameters(user, point_of_sale):
    tabs = Tab.objects.filter(user=user)
    open_tab_parameters = {}
    open_tab_parameters['revctrid'] = point_of_sale.default_revenue_center_id
    open_tab_parameters['employee_id'] = point_of_sale.default_employee.employee_id
    open_tab_parameters['order_type_id'] = point_of_sale.default_order_type_id
    open_tab_parameters['ticket_name'] = return_tab_name(user)
    return open_tab_parameters


def create_simplicity_tab(user, point_of_sale):
    open_tab_parameters = return_simplicity_open_tab_parameters(user, point_of_sale)
    url = SIMPLICITY_BASE_URL + point_of_sale.location_id + "/tickets/create"
    response = requests.post(url, data=open_tab_parameters)
    increment = 0
    while response.json() == -11:
        new_ticket_name = increment_ticket_name(increment, open_tab_parameters['ticket_name'])
        open_tab_parameters['ticket_name'] = new_ticket_name
        response = requests.post(url, data=open_tab_parameters)
        increment += 1
    return response.json()


def close_simplicity_tab(tab):
    point_of_sale = tab.point_of_sale
    close_tab_parameters = return_simplicity_close_tab_parameters(tab)
    url = SIMPLICITY_BASE_URL + point_of_sale.location_id + "/tickets/" + tab.api_tab_id + "/paid"
    response = requests.post(url, data=close_tab_parameters)
    print "RESPONSE: " + str(response.json())
    return response.json()


def return_simplicity_close_tab_parameters(tab):
    point_of_sale = tab.point_of_sale
    close_tab_parameters = {}
    close_tab_parameters['amount'] = str(tab.amount_paid)
    close_tab_parameters['tip'] = str(tab.tip)
    close_tab_parameters['tender_type'] = point_of_sale.tender_type_id
    close_tab_parameters['discount_desired'] = '0'
    close_tab_parameters['discount_amount'] = '0'
    close_tab_parameters['discount_object'] = '0'
    close_tab_parameters['employee_id'] = tab.employee.employee_id
    return close_tab_parameters


def add_hotspot_drink_and_return_drink_info(tab, deal):
    response = add_hotspot_drink_to_simplicity_tab(tab, deal)
    if response != 1:
        print "add drink failed"
        send_marketing_email("info@gethotspotapp.com", "POS ERROR", ['wxu121@gmail.com'], "POS ERROR add_hotspot_drink failed", "POS ERROR add_hotspot_drink failed", "POS ERROR add_hotspot_drink failed", "test")
        return False
    simplicity_tab_info = return_simplicity_tab_info(tab)
    added_drink_menu_id = simplicity_tab_info['items'][0]['dtl_id']
    added_drink_overall_id = simplicity_tab_info['items'][0]['item_id']
    added_drink_name = simplicity_tab_info['items'][0]['name']
    added_drink_price = simplicity_tab_info['items'][0]['price']
    return added_drink_menu_id, added_drink_overall_id, added_drink_name, added_drink_price



def add_hotspot_drink_to_simplicity_tab(tab, deal):
    point_of_sale = tab.point_of_sale
    pos_item_id = deal.pos_item_id
    add_drink_parameters = return_simplicity_add_drink_parameters(tab, pos_item_id)
    url = SIMPLICITY_BASE_URL + point_of_sale.location_id + "/tickets/add"
    response = requests.post(url, data=add_drink_parameters)
    return response.json()


def return_simplicity_add_drink_parameters(tab, menu_item_id):
    add_drink_parameters = {}
    add_drink_parameters['ticket_id'] = tab.api_tab_id
    add_drink_parameters['menu_item_id'] = menu_item_id
    add_drink_parameters['menu_level_id'] = '1'
    add_drink_parameters['menu_item_reference'] = 'Hotspot Drink Special'
    add_drink_parameters['cond_item_1'] = '0'
    add_drink_parameters['cond_item_1_reference'] = '0'
    add_drink_parameters['employee_id'] = tab.employee.employee_id
    add_drink_parameters['cond_desired'] = '0'
    return add_drink_parameters


def return_simplicity_tab_info(tab):
    point_of_sale = tab.point_of_sale
    url = SIMPLICITY_BASE_URL + point_of_sale.location_id + "/tickets/" + tab.api_tab_id
    response = requests.get(url)
    return response.json()


def update_tab_and_tab_item_objects(tab):
    simplicity_tab_info = return_simplicity_tab_info(tab)
    if simplicity_tab_info == -1:
        print "update_tab_and_tab_item_objects failed"
        send_marketing_email("info@gethotspotapp.com", "POS ERROR", ['wxu121@gmail.com'], "POS ERROR get tab failed", "POS ERROR get tab failed", "POS ERROR get tab failed", "test")
        return False
    tab = update_tab_object(tab, simplicity_tab_info)
    tab_items = update_tab_item_objects(tab, simplicity_tab_info)
    return tab, tab_items


def update_tab_object(tab, simplicity_tab_info):
    subtotal, tax, service_charges, table_id, revenue_center_id, tab_open, closed_datetime = get_tab_info(simplicity_tab_info)
    employee = get_tab_employee_info(tab, simplicity_tab_info)
    tab.employee = employee
    tab.subtotal = subtotal
    tab.tax = Decimal(tax).quantize(Decimal('.01'), rounding=ROUND_HALF_UP)
    tab.convenience_fee = calculate_convenience_fee(tab).quantize(Decimal('.01'), rounding=ROUND_HALF_UP)
    tab.total = calculate_total(tab).quantize(Decimal('.01'), rounding=ROUND_HALF_UP)
    tab.service_charges = service_charges
    tab.table = table_id
    tab.revenue_center = revenue_center_id
    if not tab_open:
        tab.closed = True
        tab.date_closed = datetime.strptime(closed_datetime, '%Y-%m-%d %H:%M:%S')
    tab.save()
    return tab


def get_tab_info(simplicity_tab_info):
    subtotal = Decimal(simplicity_tab_info['subtotal'])
    tax = Decimal(simplicity_tab_info['tax'])
    print str(simplicity_tab_info['service_charges'])
    if simplicity_tab_info['service_charges'] != 'None':
        service_charges = Decimal(simplicity_tab_info['service_charges'])
    else:
        service_charges = Decimal("0.00")
    table_id = simplicity_tab_info['table']
    if simplicity_tab_info['revenue_center']:
        revenue_center_id = simplicity_tab_info['revenue_center']['id']
    else:
        revenue_center_id = None
    tab_open = simplicity_tab_info['open']
    closed_datetime = simplicity_tab_info['closed_datetime']
    return subtotal, tax, service_charges, table_id, revenue_center_id, tab_open, closed_datetime


def get_tab_employee_info(tab, simplicity_tab_info):
    employee_dict = simplicity_tab_info['server']
    employee = check_if_employee_changed(tab, employee_dict)
    if employee.employee_id != tab.point_of_sale.default_employee.employee_id:
        tab.tab_claimed = True
        tab.save()
    return employee


def update_tab_item_objects(tab, simplicity_tab_info):
    items = simplicity_tab_info['items']
    tab_items = []
    for item in items:
        tab_item = check_if_tab_item_object_exists(tab, item)
        tab_items.append(tab_item)
    delete_extra_tab_item_objects(tab, tab_items)
    return tab_items


def check_if_tab_item_object_exists(tab, item):
    menu_id = item['dtl_id']
    if TabItem.objects.filter(tab=tab, menu_item_id=menu_id).exists():
        return TabItem.objects.get(tab=tab, menu_item_id=menu_id)
    else:
        overall_id = item['item_id']
        item_name = item['name']
        item_price = item['price']
        tab_item = create_tab_item_object(tab, menu_id, overall_id, item_name, item_price, None)
        return tab_item


def delete_extra_tab_item_objects(tab, tab_items):
    tab_item_objects = TabItem.objects.filter(tab=tab)
    if len(tab_item_objects) != len(tab_items):
        for tab_item_object in tab_item_objects:
            if tab_item_object not in tab_items:
                tab_item_object.delete()


def check_if_employee_changed(tab, employee_dict):
    old_employee = tab.employee
    if old_employee.employee_id == employee_dict['id']:
        return old_employee
    else:
        new_employee = create_employee_object(employee_dict)
        return new_employee


def cancel_tab(tab):
    response = cancel_tab_on_simplicity(tab)
    if response != 1:
        print "cancel tab failed"
        return False
    tab = cancel_tab_in_object(tab)


def cancel_tab_on_simplicity(tab):
    point_of_sale = tab.point_of_sale
    url = SIMPLICITY_BASE_URL + point_of_sale.location_id + "/tickets/" + tab.api_tab_id + "/cancel"
    response = requests.put(url)
    return response.json()


def cancel_tab_in_object(tab):
    tab.cancelled = True
    tab.save()
    return tab


def add_menu_item(tab, menu_item_id='2005'):
    add_drink_parameters = return_simplicity_add_drink_parameters(tab, menu_item_id)
    url = SIMPLICITY_BASE_URL + tab.point_of_sale.location_id + "/tickets/add"
    response = requests.post(url, data=add_drink_parameters)
    if response.json() == 1:
        print "succeeded"
    else:
        print "failed"


def tab_was_manually_closed(tab):
    simplicity_tab_info = return_simplicity_tab_info(tab)
    if not simplicity_tab_info['open']:
        return True
    else:
        return False



