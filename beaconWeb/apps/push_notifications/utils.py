from django.conf import settings
from json import dumps
from beaconWeb.apps.push_notifications.models import AndroidDevice
from ios_notifications.models import Device as APSDevice
from ios_notifications.models import APNService, Notification
from gcm.api import send_gcm_message
from raven.contrib.django.models import client


def update_badge_number(user, badge_number):
    send_push_notification_to_users([user], None, None, badge_number, None)


def send_push_notification_to_users(users, message=None, title=None, badge=None, content_available=False, sound=None, extras=None):
    send_gcm_notification_to_users(users, message=message, title=title, extras=extras)
    send_aps_notification_to_users(users, message=message, badge=badge, sound=sound,
                                   content_available=content_available, extras=extras)


def send_gcm_notification_to_users(users, **kwargs):
    regs_ids = list(AndroidDevice.objects.filter(user__in=users).values_list('reg_id', flat=True))
    data = gcm_data(**kwargs)
    return send_gcm_message(api_key=settings.GCM_APIKEY, regs_id=regs_ids, data=data, collapse_key="message")


def send_aps_notification_to_users(users, **kwargs):
    apns = APNService.objects.filter(hostname=settings.APNS_HOSTNAME)[0]
    print str(apns)
    devices = APSDevice.objects.filter(users__in=users, service=apns)
    print str(devices)
    payload_json = dumps(aps_payload(**kwargs))
    try:
        payload_json = payload_json[0:239]
        notification = Notification.objects.create(custom_payload=payload_json, service=apns)
        #seems like something goes wrong if there's a bad device. just send to one device at a time for now
        #apns.push_notification_to_devices(notification, devices, chunk_size=200)
        for device in devices:
            apns.push_notification_to_devices(notification, [device], chunk_size=200)
    except:
        print "Failed to send push"
        print str(client.captureException())
        client.captureException()


def gcm_data(**kwargs):
    message = kwargs.get('message')
    title = kwargs.get('title')
    extras = kwargs.get('extras')
    payload = {}
    if message:
        payload['message'] = message
    if title:
        payload['title'] = title
    if extras:
        for key in extras.keys():
            payload[key] = extras[key]
    return payload


def aps_payload(**kwargs):
    message = kwargs.get('message')
    badge = kwargs.get('badge')
    content_available = kwargs.get('content_available')
    sound = kwargs.get('sound')
    extras = kwargs.get('extras')
    aps = {}
    if message:
        aps['alert'] = message
    if badge is not None:
        aps['badge'] = badge
    if content_available:
        aps['content-available'] = 1
    if sound:
        aps['sound'] = sound

    payload = {'aps': aps}
    if extras:
        for key in extras.keys():
            payload[key] = extras[key]
    return payload
