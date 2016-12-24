from beaconWeb.apps.beacon.models.beacon import Beacon
from storages.backends.s3boto import S3BotoStorage
from boto.s3.connection import S3Connection
from django.conf import settings
from boto.s3.key import Key
from beaconWeb.apps.beacon.models.image import Image
from beaconWeb.apps.beacon.models.message import Message
from beaconWeb.apps.beacon.models.deal_status import DealStatus
from beaconWeb.apps.beacon.common.common_utils import generate_image_url, users_to_notify
from beaconWeb.apps.beacon.tasks import send_hotspot_message
from beaconWeb.apps.beacon.common.utils.friends import get_friends
from beaconWeb.apps.beacon.common.constants.message_type import MESSAGE_TYPE
import hashlib
import datetime
from beaconWeb.apps.beacon.common.constants.notification_types import NOTIFICATION_TYPE
from django.contrib.auth.models import User
from beaconWeb.apps.beacon.common.utils.tracker import track_notification
#from sorl.thumbnail import get_thumbnail

#Helper Functions
StaticRootS3BotoStorage = lambda: S3BotoStorage(location='static')
MediaRootS3BotoStorage = lambda: S3BotoStorage(location='media')


def upload_image(bucket, key, image):
    s3Connection = S3Connection(settings.AWS_ACCESS_KEY_ID, settings.AWS_SECRET_ACCESS_KEY)
    bucket = s3Connection.get_bucket(bucket)
    newImageKey = Key(bucket)
    newImageKey.key = key
    newImageKey.set_contents_from_file(image)


def send_image_notification(deal_status, sending_user):
    message = "{0} added a picture at {1}".format(sending_user.first_name, deal_status.deal.place.name)
    user_ids, blocked_user_ids = get_friends(sending_user)
    users = User.objects.filter(pk__in=user_ids)
    for user in users:
        send_hotspot_message([user], message, message_type=MESSAGE_TYPE.NEWSFEED, silent=True)
        track_notification(user, NOTIFICATION_TYPE.IMAGE_ADDED, message, sending_user)


def send_saw_picture_notification(deal_status, friend_who_saw_picture):
    message = "{0} saw your picture at {1}".format(friend_who_saw_picture.get_full_name(), deal_status.deal.place.name)
    send_hotspot_message([deal_status.user], message, message_type=MESSAGE_TYPE.GENERAL, silent=True)
    track_notification(deal_status.user, NOTIFICATION_TYPE.IMAGE_SEEN, message, friend_who_saw_picture)


def upload_image_to_s3(user, bucket, image):
    key = hashlib.sha224(str(user.first_name) + str(datetime.datetime.now())).hexdigest()
    upload_image(bucket, key, image)
    #uploadThumbnail(key, image)
    uploadedImage = Image.objects.create(user=user, image_key=key)
    return uploadedImage


#Main functions
def store_image(user, file_request):
    image = file_request['image']
    bucket = "hotspot-photo"
    imageObject = upload_image_to_s3(user, bucket, image)
    return imageObject


def get_image(user, request):
    beacon_id = request['beacon']
    beacon = Beacon.objects.get(pk=beacon_id)
    image = Image.objects.filter(beacon=beacon).order_by('date_created')[0]
    return generate_image_url(image)