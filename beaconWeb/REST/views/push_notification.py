from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import authentication
from rest_framework.authtoken.models import Token
from rest_framework import status
from beaconWeb.apps.push_notifications.models import AndroidDevice


class PUSHAPI(APIView):

    """
    To register an android device to receive push notifications
    POST - Required params: registration_id, device_id
    registration_id -- registration id from android phone
    device_id -- device id of android phone
    """

    authentication_classes = (authentication.TokenAuthentication,)

    def post(self, request, format=None):
        response = {}
        auth_token = request.auth
        if Token.objects.filter(key=auth_token).exists():
            token = Token.objects.get(key=auth_token)
            reg_id = request.DATA['registration_id']
            dev_id = request.DATA['device_id']
            if AndroidDevice.objects.filter(dev_id=dev_id).exists():
                existing_device = AndroidDevice.objects.get(dev_id=dev_id)
                existing_device.reg_id = reg_id
                existing_device.user = token.user
                existing_device.save()
                response['message'] = 'Device has been updated'
                return Response(response, status=status.HTTP_200_OK)
            else:
                AndroidDevice.objects.create(user=token.user, reg_id=reg_id, dev_id=dev_id)
                response['message'] = 'Device successfully added'
                return Response(response, status=status.HTTP_200_OK)
        else:
            response['message'] = "No user associated with token found"
            return Response(response, status=status.HTTP_401_UNAUTHORIZED)
