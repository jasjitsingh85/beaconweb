# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'DealHours'
        db.create_table(u'beacon_dealhours', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('deal', self.gf('django.db.models.fields.related.ForeignKey')(related_name='hours', to=orm['beacon.Deal'])),
            ('start', self.gf('django.db.models.fields.FloatField')()),
            ('end', self.gf('django.db.models.fields.FloatField')()),
            ('open_hours', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('days_active', self.gf('django.db.models.fields.BigIntegerField')(default=None)),
        ))
        db.send_create_signal('beacon', ['DealHours'])

        # Adding model 'DealStatus'
        db.create_table(u'beacon_dealstatus', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('deal', self.gf('django.db.models.fields.related.ForeignKey')(related_name='deal_statuses', to=orm['beacon.Deal'])),
            ('beacon', self.gf('django.db.models.fields.related.ForeignKey')(related_name='deal_statuses', to=orm['beacon.Beacon'])),
            ('hours', self.gf('django.db.models.fields.related.ForeignKey')(related_name='deal_statuses', to=orm['beacon.DealHours'])),
            ('date_time', self.gf('django.db.models.fields.DateTimeField')()),
            ('user', self.gf('django.db.models.fields.related.ForeignKey')(blank=True, related_name='deal_statuses', null=True, to=orm['auth.User'])),
            ('contact', self.gf('django.db.models.fields.related.ForeignKey')(blank=True, related_name='deal_statuses', null=True, to=orm['beacon.Contact'])),
            ('deal_link', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('date_created', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
        ))
        db.send_create_signal('beacon', ['DealStatus'])

        # Adding model 'Deal'
        db.create_table(u'beacon_deal', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('place', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['beacon.DealPlace'])),
            ('deal_description', self.gf('django.db.models.fields.TextField')()),
            ('bonus_description', self.gf('django.db.models.fields.TextField')(null=True, blank=True)),
            ('invite_description', self.gf('django.db.models.fields.TextField')()),
        ))
        db.send_create_signal('beacon', ['Deal'])

        # Adding model 'DealPlace'
        db.create_table(u'beacon_dealplace', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('longitude', self.gf('django.db.models.fields.FloatField')(db_index=True)),
            ('latitude', self.gf('django.db.models.fields.FloatField')(db_index=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=128)),
            ('street_address', self.gf('django.db.models.fields.CharField')(max_length=128)),
            ('phone', self.gf('django.db.models.fields.CharField')(max_length=20, null=True, blank=True)),
            ('image_url', self.gf('django.db.models.fields.CharField')(max_length=128, null=True, blank=True)),
            ('yelp_id', self.gf('django.db.models.fields.CharField')(max_length=128, null=True, blank=True)),
            ('foursquare_id', self.gf('django.db.models.fields.CharField')(max_length=128, null=True, blank=True)),
        ))
        db.send_create_signal('beacon', ['DealPlace'])


    def backwards(self, orm):
        # Deleting model 'DealHours'
        db.delete_table(u'beacon_dealhours')

        # Deleting model 'DealStatus'
        db.delete_table(u'beacon_dealstatus')

        # Deleting model 'Deal'
        db.delete_table(u'beacon_deal')

        # Deleting model 'DealPlace'
        db.delete_table(u'beacon_dealplace')


    models = {
        u'auth.group': {
            'Meta': {'object_name': 'Group'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '80'}),
            'permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'})
        },
        u'auth.permission': {
            'Meta': {'ordering': "(u'content_type__app_label', u'content_type__model', u'codename')", 'unique_together': "((u'content_type', u'codename'),)", 'object_name': 'Permission'},
            'codename': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['contenttypes.ContentType']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        },
        u'auth.user': {
            'Meta': {'object_name': 'User'},
            'date_joined': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75', 'blank': 'True'}),
            'first_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'groups': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['auth.Group']", 'symmetrical': 'False', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'is_staff': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_superuser': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'last_login': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'last_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'user_permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'}),
            'username': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '30'})
        },
        'beacon.beacon': {
            'Meta': {'object_name': 'Beacon'},
            'address': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'cancelled': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'creator': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'created_hotspots'", 'to': u"orm['auth.User']"}),
            'date_created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'date_updated': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'description': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'facebook_place_id': ('django.db.models.fields.BigIntegerField', [], {'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'isActivated': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'latitude': ('django.db.models.fields.FloatField', [], {'db_index': 'True'}),
            'longitude': ('django.db.models.fields.FloatField', [], {'db_index': 'True'}),
            'private': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'time': ('django.db.models.fields.DateTimeField', [], {})
        },
        'beacon.beaconfollow': {
            'Meta': {'object_name': 'BeaconFollow'},
            'beacon': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'beacon_follows'", 'to': "orm['beacon.Beacon']"}),
            'checked_in_by': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'check_ins'", 'null': 'True', 'to': u"orm['auth.User']"}),
            'contact': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['beacon.Contact']", 'null': 'True', 'blank': 'True'}),
            'date_created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'date_updated': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'invited_by': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'sent_invites'", 'null': 'True', 'to': u"orm['auth.User']"}),
            'saw_invite': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'state': ('django.db.models.fields.CharField', [], {'default': "'I'", 'max_length': '10'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'received_invites'", 'null': 'True', 'to': u"orm['auth.User']"})
        },
        'beacon.contact': {
            'Meta': {'object_name': 'Contact'},
            'date_created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'}),
            'normalized_phone': ('django.db.models.fields.CharField', [], {'max_length': '20', 'db_index': 'True'}),
            'phone_number': ('django.db.models.fields.CharField', [], {'max_length': '20'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'contacts'", 'to': u"orm['auth.User']"})
        },
        'beacon.contactgroup': {
            'Meta': {'object_name': 'ContactGroup'},
            'date_created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'deleted': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '256'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'contact_groups'", 'to': u"orm['auth.User']"})
        },
        'beacon.contentoption': {
            'Meta': {'object_name': 'ContentOption'},
            'content_option': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'display_location': ('django.db.models.fields.CharField', [], {'max_length': '2'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'})
        },
        'beacon.deal': {
            'Meta': {'object_name': 'Deal'},
            'bonus_description': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'deal_description': ('django.db.models.fields.TextField', [], {}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'invite_description': ('django.db.models.fields.TextField', [], {}),
            'place': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['beacon.DealPlace']"})
        },
        'beacon.dealhours': {
            'Meta': {'object_name': 'DealHours'},
            'days_active': ('django.db.models.fields.BigIntegerField', [], {'default': 'None'}),
            'deal': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'hours'", 'to': "orm['beacon.Deal']"}),
            'end': ('django.db.models.fields.FloatField', [], {}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'open_hours': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'start': ('django.db.models.fields.FloatField', [], {})
        },
        'beacon.dealplace': {
            'Meta': {'object_name': 'DealPlace'},
            'foursquare_id': ('django.db.models.fields.CharField', [], {'max_length': '128', 'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'image_url': ('django.db.models.fields.CharField', [], {'max_length': '128', 'null': 'True', 'blank': 'True'}),
            'latitude': ('django.db.models.fields.FloatField', [], {'db_index': 'True'}),
            'longitude': ('django.db.models.fields.FloatField', [], {'db_index': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'phone': ('django.db.models.fields.CharField', [], {'max_length': '20', 'null': 'True', 'blank': 'True'}),
            'street_address': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'yelp_id': ('django.db.models.fields.CharField', [], {'max_length': '128', 'null': 'True', 'blank': 'True'})
        },
        'beacon.dealstatus': {
            'Meta': {'object_name': 'DealStatus'},
            'beacon': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'deal_statuses'", 'to': "orm['beacon.Beacon']"}),
            'contact': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'deal_statuses'", 'null': 'True', 'to': "orm['beacon.Contact']"}),
            'date_created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'date_time': ('django.db.models.fields.DateTimeField', [], {}),
            'deal': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'deal_statuses'", 'to': "orm['beacon.Deal']"}),
            'deal_link': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'hours': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'deal_statuses'", 'to': "orm['beacon.DealHours']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'deal_statuses'", 'null': 'True', 'to': u"orm['auth.User']"})
        },
        'beacon.groupmember': {
            'Meta': {'object_name': 'GroupMember'},
            'contact': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['beacon.Contact']"}),
            'date_created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'group': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'members'", 'to': "orm['beacon.ContactGroup']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'})
        },
        'beacon.image': {
            'Meta': {'object_name': 'Image'},
            'beacon': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['beacon.Beacon']"}),
            'date_created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'image_key': ('django.db.models.fields.CharField', [], {'max_length': '60'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['auth.User']"})
        },
        'beacon.location': {
            'Meta': {'object_name': 'Location'},
            'date_created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'latitude': ('django.db.models.fields.FloatField', [], {'db_index': 'True'}),
            'longitude': ('django.db.models.fields.FloatField', [], {'db_index': 'True'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'locations'", 'to': u"orm['auth.User']"})
        },
        'beacon.message': {
            'Meta': {'object_name': 'Message'},
            'avatar_url': ('django.db.models.fields.CharField', [], {'max_length': '100', 'null': 'True'}),
            'beacon': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['beacon.Beacon']"}),
            'chat_type': ('django.db.models.fields.CharField', [], {'default': "'UM'", 'max_length': '10'}),
            'contact': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['beacon.Contact']", 'null': 'True', 'blank': 'True'}),
            'date_created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'image': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['beacon.Image']", 'null': 'True', 'blank': 'True'}),
            'message': ('django.db.models.fields.CharField', [], {'max_length': '500', 'null': 'True', 'blank': 'True'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['auth.User']", 'null': 'True', 'blank': 'True'})
        },
        'beacon.profile': {
            'Meta': {'object_name': 'Profile'},
            'activated': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'activation_code': ('django.db.models.fields.CharField', [], {'max_length': '5'}),
            'date_updated': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'gender': ('django.db.models.fields.CharField', [], {'max_length': '1', 'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'normalized_phone': ('django.db.models.fields.CharField', [], {'max_length': '20', 'db_index': 'True'}),
            'phone_number': ('django.db.models.fields.CharField', [], {'max_length': '20'}),
            'user': ('django.db.models.fields.related.OneToOneField', [], {'to': u"orm['auth.User']", 'unique': 'True'})
        },
        'beacon.recommendation': {
            'Meta': {'object_name': 'Recommendation'},
            'date_created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'foursquare_venue_id': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'message_text': ('django.db.models.fields.CharField', [], {'max_length': '256'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'recommendations'", 'to': u"orm['auth.User']"})
        },
        u'contenttypes.contenttype': {
            'Meta': {'ordering': "('name',)", 'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        }
    }

    complete_apps = ['beacon']