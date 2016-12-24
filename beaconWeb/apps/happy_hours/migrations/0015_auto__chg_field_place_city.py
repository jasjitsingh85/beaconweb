# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):

        # Changing field 'Place.city'
        db.alter_column(u'happy_hours_place', 'city_id', self.gf('django.db.models.fields.related.ForeignKey')(null=True, to=orm['happy_hours.City']))

    def backwards(self, orm):

        # Changing field 'Place.city'
        db.alter_column(u'happy_hours_place', 'city_id', self.gf('django.db.models.fields.related.ForeignKey')(default=None, to=orm['happy_hours.City']))

    models = {
        u'happy_hours.city': {
            'Meta': {'object_name': 'City'},
            'gt_id': ('django.db.models.fields.IntegerField', [], {'unique': 'True', 'db_index': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'state_name': ('django.db.models.fields.CharField', [], {'max_length': '128'})
        },
        u'happy_hours.happyhour': {
            'Meta': {'object_name': 'HappyHour'},
            'days': ('django.db.models.fields.CharField', [], {'max_length': '7'}),
            'days_active': ('django.db.models.fields.BigIntegerField', [], {'default': 'None', 'null': 'True', 'blank': 'True'}),
            'description': ('django.db.models.fields.TextField', [], {}),
            'end': ('django.db.models.fields.FloatField', [], {'default': 'None', 'null': 'True', 'blank': 'True'}),
            'gt_id': ('django.db.models.fields.IntegerField', [], {'default': 'None', 'unique': 'True', 'null': 'True', 'db_index': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'place': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'happy_hours'", 'to': "orm['happy_hours.Place']"}),
            'start': ('django.db.models.fields.FloatField', [], {'default': 'None', 'null': 'True', 'blank': 'True'})
        },
        u'happy_hours.neighborhood': {
            'Meta': {'object_name': 'Neighborhood'},
            'city': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'neighborhoods'", 'to': u"orm['happy_hours.City']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '128'})
        },
        'happy_hours.place': {
            'Meta': {'object_name': 'Place'},
            'city': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'places'", 'null': 'True', 'to': u"orm['happy_hours.City']"}),
            'foursquare_id': ('django.db.models.fields.CharField', [], {'max_length': '128', 'null': 'True', 'blank': 'True'}),
            'gt_id': ('django.db.models.fields.IntegerField', [], {'db_index': 'True', 'unique': 'True', 'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'image_url': ('django.db.models.fields.CharField', [], {'max_length': '128', 'null': 'True', 'blank': 'True'}),
            'latitude': ('django.db.models.fields.FloatField', [], {'db_index': 'True'}),
            'longitude': ('django.db.models.fields.FloatField', [], {'db_index': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'neighborhood': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'places'", 'null': 'True', 'to': u"orm['happy_hours.Neighborhood']"}),
            'phone': ('django.db.models.fields.CharField', [], {'max_length': '20', 'null': 'True', 'blank': 'True'}),
            'street_address': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'yelp_id': ('django.db.models.fields.CharField', [], {'max_length': '128', 'null': 'True', 'blank': 'True'}),
            'zip_code': ('django.db.models.fields.CharField', [], {'max_length': '10'})
        }
    }

    complete_apps = ['happy_hours']