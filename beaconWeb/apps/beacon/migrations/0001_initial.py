# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'Beacon'
        db.create_table(u'beacon_beacon', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('creator', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.User'])),
            ('description', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('address', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('time', self.gf('django.db.models.fields.DateTimeField')()),
            ('private', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('longitude', self.gf('django.db.models.fields.FloatField')(db_index=True)),
            ('latitude', self.gf('django.db.models.fields.FloatField')(db_index=True)),
            ('facebook_place_id', self.gf('django.db.models.fields.BigIntegerField')(null=True, blank=True)),
            ('date_created', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('date_updated', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
            ('isActivated', self.gf('django.db.models.fields.BooleanField')(default=True)),
        ))
        db.send_create_signal('beacon', ['Beacon'])

        # Adding model 'Contact'
        db.create_table(u'beacon_contact', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('user', self.gf('django.db.models.fields.related.ForeignKey')(related_name='contact_for', to=orm['auth.User'])),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=50)),
            ('phone_number', self.gf('django.db.models.fields.CharField')(max_length=20)),
            ('normalized_phone', self.gf('django.db.models.fields.CharField')(max_length=20, db_index=True)),
            ('date_created', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
        ))
        db.send_create_signal('beacon', ['Contact'])

        # Adding model 'BeaconFollow'
        db.create_table(u'beacon_beaconfollow', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('user', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.User'], null=True, blank=True)),
            ('contact', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['beacon.Contact'], null=True, blank=True)),
            ('beacon', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['beacon.Beacon'])),
            ('state', self.gf('django.db.models.fields.CharField')(default='N', max_length=10)),
            ('date_created', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('date_updated', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
        ))
        db.send_create_signal('beacon', ['BeaconFollow'])

        # Adding model 'Friendship'
        db.create_table(u'beacon_friendship', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('user', self.gf('django.db.models.fields.related.ForeignKey')(related_name='friend_to', to=orm['auth.User'])),
            ('friend', self.gf('django.db.models.fields.related.ForeignKey')(blank=True, related_name='friend_from', null=True, to=orm['auth.User'])),
            ('contact', self.gf('django.db.models.fields.related.ForeignKey')(blank=True, related_name='contact_from', null=True, to=orm['beacon.Contact'])),
            ('state', self.gf('django.db.models.fields.CharField')(default='ACCEPTED', max_length=10)),
            ('date_created', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('date_updated', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
        ))
        db.send_create_signal('beacon', ['Friendship'])

        # Adding model 'BeaconInvite'
        db.create_table(u'beacon_beaconinvite', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('user', self.gf('django.db.models.fields.related.ForeignKey')(blank=True, related_name='user_notified', null=True, to=orm['auth.User'])),
            ('contact', self.gf('django.db.models.fields.related.ForeignKey')(blank=True, related_name='contact_notified', null=True, to=orm['beacon.Contact'])),
            ('beacon', self.gf('django.db.models.fields.related.ForeignKey')(related_name='notified_beacon', to=orm['beacon.Beacon'])),
            ('invited_by', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.User'], null=True, blank=True)),
            ('date_created', self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime(2013, 9, 11, 0, 0), auto_now_add=True, blank=True)),
        ))
        db.send_create_signal('beacon', ['BeaconInvite'])

        # Adding model 'Profile'
        db.create_table(u'beacon_profile', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('user', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.User'], unique=True)),
            ('phone_number', self.gf('django.db.models.fields.CharField')(max_length=20)),
            ('normalized_phone', self.gf('django.db.models.fields.CharField')(max_length=20, db_index=True)),
            ('activated', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('activation_code', self.gf('django.db.models.fields.CharField')(max_length=5)),
            ('gender', self.gf('django.db.models.fields.CharField')(max_length=1, null=True, blank=True)),
            ('push_notification_device', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['ios_notifications.Device'], null=True)),
            ('date_updated', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
        ))
        db.send_create_signal('beacon', ['Profile'])

        # Adding model 'Location'
        db.create_table(u'beacon_location', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('user', self.gf('django.db.models.fields.related.ForeignKey')(related_name='last_location', to=orm['auth.User'])),
            ('longitude', self.gf('django.db.models.fields.FloatField')(db_index=True)),
            ('latitude', self.gf('django.db.models.fields.FloatField')(db_index=True)),
            ('date_created', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
        ))
        db.send_create_signal('beacon', ['Location'])

        # Adding model 'Image'
        db.create_table(u'beacon_image', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('image_key', self.gf('django.db.models.fields.CharField')(max_length=60)),
            ('beacon', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['beacon.Beacon'])),
            ('user', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.User'])),
            ('date_created', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
        ))
        db.send_create_signal('beacon', ['Image'])

        # Adding model 'Message'
        db.create_table(u'beacon_message', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('user', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.User'], null=True, blank=True)),
            ('beacon', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['beacon.Beacon'])),
            ('message', self.gf('django.db.models.fields.CharField')(max_length=255, null=True, blank=True)),
            ('image', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['beacon.Image'], null=True, blank=True)),
            ('date_created', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
        ))
        db.send_create_signal('beacon', ['Message'])


    def backwards(self, orm):
        # Deleting model 'Beacon'
        db.delete_table(u'beacon_beacon')

        # Deleting model 'Contact'
        db.delete_table(u'beacon_contact')

        # Deleting model 'BeaconFollow'
        db.delete_table(u'beacon_beaconfollow')

        # Deleting model 'Friendship'
        db.delete_table(u'beacon_friendship')

        # Deleting model 'BeaconInvite'
        db.delete_table(u'beacon_beaconinvite')

        # Deleting model 'Profile'
        db.delete_table(u'beacon_profile')

        # Deleting model 'Location'
        db.delete_table(u'beacon_location')

        # Deleting model 'Image'
        db.delete_table(u'beacon_image')

        # Deleting model 'Message'
        db.delete_table(u'beacon_message')


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
            'creator': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['auth.User']"}),
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
            'beacon': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['beacon.Beacon']"}),
            'contact': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['beacon.Contact']", 'null': 'True', 'blank': 'True'}),
            'date_created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'date_updated': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'state': ('django.db.models.fields.CharField', [], {'default': "'N'", 'max_length': '10'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['auth.User']", 'null': 'True', 'blank': 'True'})
        },
        'beacon.beaconinvite': {
            'Meta': {'object_name': 'BeaconInvite'},
            'beacon': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'notified_beacon'", 'to': "orm['beacon.Beacon']"}),
            'contact': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'contact_notified'", 'null': 'True', 'to': "orm['beacon.Contact']"}),
            'date_created': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime(2013, 9, 11, 0, 0)', 'auto_now_add': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'invited_by': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['auth.User']", 'null': 'True', 'blank': 'True'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'user_notified'", 'null': 'True', 'to': u"orm['auth.User']"})
        },
        'beacon.contact': {
            'Meta': {'object_name': 'Contact'},
            'date_created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'}),
            'normalized_phone': ('django.db.models.fields.CharField', [], {'max_length': '20', 'db_index': 'True'}),
            'phone_number': ('django.db.models.fields.CharField', [], {'max_length': '20'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'contact_for'", 'to': u"orm['auth.User']"})
        },
        'beacon.friendship': {
            'Meta': {'object_name': 'Friendship'},
            'contact': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'contact_from'", 'null': 'True', 'to': "orm['beacon.Contact']"}),
            'date_created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'date_updated': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'friend': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'friend_from'", 'null': 'True', 'to': u"orm['auth.User']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'state': ('django.db.models.fields.CharField', [], {'default': "'ACCEPTED'", 'max_length': '10'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'friend_to'", 'to': u"orm['auth.User']"})
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
            'user': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'last_location'", 'to': u"orm['auth.User']"})
        },
        'beacon.message': {
            'Meta': {'object_name': 'Message'},
            'beacon': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['beacon.Beacon']"}),
            'date_created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'image': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['beacon.Image']", 'null': 'True', 'blank': 'True'}),
            'message': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
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
            'push_notification_device': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['ios_notifications.Device']", 'null': 'True'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['auth.User']", 'unique': 'True'})
        },
        u'contenttypes.contenttype': {
            'Meta': {'ordering': "('name',)", 'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        u'ios_notifications.apnservice': {
            'Meta': {'unique_together': "(('name', 'hostname'),)", 'object_name': 'APNService'},
            'certificate': ('django.db.models.fields.TextField', [], {}),
            'hostname': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'passphrase': ('django_fields.fields.EncryptedCharField', [], {'max_length': '101', 'null': 'True', 'cipher': "'AES'", 'blank': 'True'}),
            'private_key': ('django.db.models.fields.TextField', [], {})
        },
        u'ios_notifications.device': {
            'Meta': {'unique_together': "(('token', 'service'),)", 'object_name': 'Device'},
            'added_at': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'deactivated_at': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'display': ('django.db.models.fields.CharField', [], {'max_length': '30', 'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'last_notified_at': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'os_version': ('django.db.models.fields.CharField', [], {'max_length': '20', 'null': 'True', 'blank': 'True'}),
            'platform': ('django.db.models.fields.CharField', [], {'max_length': '30', 'null': 'True', 'blank': 'True'}),
            'service': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['ios_notifications.APNService']"}),
            'token': ('django.db.models.fields.CharField', [], {'max_length': '64'}),
            'users': ('django.db.models.fields.related.ManyToManyField', [], {'blank': 'True', 'related_name': "'ios_devices'", 'null': 'True', 'symmetrical': 'False', 'to': u"orm['auth.User']"})
        }
    }

    complete_apps = ['beacon']