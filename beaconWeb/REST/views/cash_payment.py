from rest_framework.views import APIView
from rest_framework import status
from rest_framework.response import Response
from rest_framework.authtoken.models import Token
from rest_framework import permissions
from beaconWeb.apps.beacon.common.utils.payments import charge_payment


class CashPaymentAPI(APIView):

    """
    When any user wants to invite more friends to an existing deal, use /invite/
    POST - Required params: phone_number (Token not required with this)
    phone_number -- User's phone number
    PUT - Required params: activation_code (four digit activation code that is texted once user puts in phone_number)
    activation_code -- four digit activation code sent after user types in phone number
    """

    permission_classes = (permissions.AllowAny,)

    def post(self, request):
        response = {}
        payment_successful = charge_payment(request.DATA)
        if payment_successful:
            return Response(response, status=status.HTTP_200_OK)
        else:
            return Response(response, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
