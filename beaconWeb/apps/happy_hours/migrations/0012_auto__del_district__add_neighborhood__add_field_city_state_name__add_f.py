# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Deleting model 'District'
        db.delete_table(u'happy_hours_district')

        # Adding model 'Neighborhood'
        db.create_table(u'happy_hours_neighborhood', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=128)),
            ('city', self.gf('django.db.models.fields.related.ForeignKey')(related_name='Neighborhoods', to=orm['happy_hours.City'])),
        ))
        db.send_create_signal(u'happy_hours', ['Neighborhood'])

        # Adding field 'City.state_name'
        db.add_column(u'happy_hours_city', 'state_name',
                      self.gf('django.db.models.fields.CharField')(default='?', max_length=128),
                      keep_default=False)

        # Adding field 'Place.neighborhood'
        db.add_column(u'happy_hours_place', 'neighborhood',
                      self.gf('django.db.models.fields.related.ForeignKey')(blank=True, related_name='places', null=True, to=orm['happy_hours.Neighborhood']),
                      keep_default=False)


    def backwards(self, orm):
        # Adding model 'District'
        db.create_table(u'happy_hours_district', (
            ('city', self.gf('django.db.models.fields.related.ForeignKey')(related_name='districts', to=orm['happy_hours.City'])),
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('gt_id', self.gf('django.db.models.fields.IntegerField')(unique=True, db_index=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=128)),
        ))
        db.send_create_signal(u'happy_hours', ['District'])

        # Deleting model 'Neighborhood'
        db.delete_table(u'happy_hours_neighborhood')

        # Deleting field 'City.state_name'
        db.delete_column(u'happy_hours_city', 'state_name')

        # Deleting field 'Place.neighborhood'
        db.delete_column(u'happy_hours_place', 'neighborhood_id')


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
            'gt_id': ('django.db.models.fields.IntegerField', [], {'unique': 'True', 'db_index': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'place': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'happy_hours'", 'to': "orm['happy_hours.Place']"}),
            'start': ('django.db.models.fields.FloatField', [], {'default': 'None', 'null': 'True', 'blank': 'True'})
        },
        u'happy_hours.neighborhood': {
            'Meta': {'object_name': 'Neighborhood'},
            'city': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'Neighborhoods'", 'to': u"orm['happy_hours.City']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '128'})
        },
        'happy_hours.place': {
            'Meta': {'object_name': 'Place'},
            'city': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'places'", 'to': u"orm['happy_hours.City']"}),
            'foursquare_id': ('django.db.models.fields.CharField', [], {'max_length': '128', 'null': 'True', 'blank': 'True'}),
            'gt_id': ('django.db.models.fields.IntegerField', [], {'unique': 'True', 'db_index': 'True'}),
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