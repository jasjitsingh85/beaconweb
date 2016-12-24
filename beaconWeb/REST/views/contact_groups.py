from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import authentication
from rest_framework.authtoken.models import Token
from beaconWeb.apps.beacon.common.utils.friends import *
from beaconWeb.apps.beacon.common.utils.friends import contacts_from_data, create_contact_group, edit_contact_group
from rest_framework import status
from beaconWeb.REST.serializers import ContactGroupSerializer


class ContactGroupAPI(APIView):

    authentication_classes = (authentication.TokenAuthentication,)

    def post(self, request, format=None):
        response = {}
        auth_token = request.auth
        token = Token.objects.get(key=auth_token)
        user = token.user
        contact_list = request.DATA.getlist('contact[]')
        contacts = contacts_from_data(user, contact_list)
        name = request.DATA['name']
        group = create_contact_group(user, contacts, name)
        response['group'] = ContactGroupSerializer(group).data
        return Response(response, status.HTTP_200_OK)

    def put(self, request, format=None):
        response = {}
        auth_token = request.auth
        token = Token.objects.get(key=auth_token)
        user = token.user
        group_id = request.DATA['group_id']
        group = ContactGroup.objects.get(pk=group_id)
        if token.user != group.user:
            return Response(response, status=status.HTTP_401_UNAUTHORIZED)
        remove = request.DATA.getlist('remove[]')
        remove_contacts = contacts_from_data(user, remove)
        add = request.DATA.getlist('add[]')
        add_contacts = contacts_from_data(user, add)
        group = edit_contact_group(group, add_contacts, remove_contacts)
        if 'name' in request.DATA:
            group.name = request.DATA['name']
            group.save()
        response['group'] = ContactGroupSerializer(group).data
        return Response(response, status=status.HTTP_200_OK)

    def get(self, request, format=None):
        response = {}
        auth_token = request.auth
        token = Token.objects.get(key=auth_token)
        user = token.user
        groups = user.contact_groups.exclude(deleted=True).select_related('members')
        response['groups'] = ContactGroupSerializer(groups, many=True).data
        return Response(response, status.HTTP_200_OK)

    def delete(self, request, format=None):
        response = {}
        auth_token = request.auth
        token = Token.objects.get(key=auth_token)
        print request.QUERY_PARAMS
        group_id = request.QUERY_PARAMS['group_id']
        group = ContactGroup.objects.get(pk=group_id)
        if token.user != group.user:
            return Response(response, status=status.HTTP_401_UNAUTHORIZED)
        group.deleted = True
        group.save()
        return Response(response, status=status.HTTP_200_OK)
