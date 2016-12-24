from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework import permissions
from beaconWeb.apps.twilio_sms.utils import sync_sms
from beaconWeb.apps.beacon.common.utils.sms_reply import received_twilio_sms_from_staffer
from beaconWeb.apps.twilio_sms.models import TwilioSMS
from time import sleep


class StafferReplyAPI(APIView):

    permission_classes = (permissions.AllowAny,)

    def post(self, request, format=None):
        data = request.DATA
        response = {}
        sms = TwilioSMS.objects.create(twilio_sid=data['SmsSid'], to_number=data['To'], from_number=data['From'],
                                       body=data['Body'], status=data['SmsStatus'], direction='inbound')
        received_twilio_sms_from_staffer(sms)
        return Response(response, status=status.HTTP_200_OK)
