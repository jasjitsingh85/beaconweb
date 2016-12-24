from django.utils.encoding import smart_str
from math import radians, cos, sin, asin, sqrt


def safe_bulk_create(objs):
    """Wrapper to overcome the size limitation of standard bulk_create()"""
    if objs:
        BULK_SIZE = 900/len(objs[0].__class__._meta.fields)
        for i in range(0,len(objs),BULK_SIZE):
            objs[0].__class__.objects.bulk_create(objs[i:i+BULK_SIZE])


def refetch_model_instance(instance):
    """refetch object in the database in case cache is outdated"""
    return instance.__class__.objects.get(pk=instance.pk)


def smart_format(format_string, *args):
    smart_args = ()
    for arg in args:
        smart_args = smart_args + (smart_str(arg),)
    return format_string.format(*smart_args)


def normalize_phone_number(phone):
    removeList = ["(", ")", "+", "-", " "]
    for remove in removeList:
        phone = phone.replace(remove, "")
    phone = phone.rstrip()
    phone = phone.lstrip()
    if len(phone) > 0:
        if phone[0] == "1":
            phone = phone[1:len(phone)]
    phone = remove_non_ascii(phone)
    return phone


def prettify_phone_number(phone):
    normalized_phone = normalize_phone_number(phone)
    pretty = "({0}) {1}-{2}".format(normalized_phone[0:3], normalized_phone[3:6], normalized_phone[6:])
    return pretty



#http://stackoverflow.com/questions/1342000/how-to-make-the-python-interpreter-correctly-handle-non-ascii-characters-in-stri
def remove_non_ascii(s):
    return "".join(i for i in s if ord(i) < 128)


def distance_between_two_points(lat1, lon1, lat2, lon2):
    """
    Calculate the great circle distance between two points
    on the earth (specified in decimal degrees)
    """
    # convert decimal degrees to radians
    lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])
    # haversine formula
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * asin(sqrt(a))
    km = 6367 * c
    return km