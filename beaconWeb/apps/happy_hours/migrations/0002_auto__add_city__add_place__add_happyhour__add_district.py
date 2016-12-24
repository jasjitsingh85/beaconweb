# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'City'
        db.create_table(u'happy_hours_city', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('gt_id', self.gf('django.db.models.fields.IntegerField')(unique=True, db_index=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=128)),
        ))
        db.send_create_signal(u'happy_hours', ['City'])

        # Adding model 'Place'
        db.create_table(u'happy_hours_place', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('gt_id', self.gf('django.db.models.fields.IntegerField')(unique=True, db_index=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=128)),
            ('street_address', self.gf('django.db.models.fields.CharField')(max_length=128)),
            ('zip_code', self.gf('django.db.models.fields.CharField')(max_length=10)),
            ('longitude', self.gf('django.db.models.fields.FloatField')(db_index=True)),
            ('latitude', self.gf('django.db.models.fields.FloatField')(db_index=True)),
            ('city', self.gf('django.db.models.fields.related.ForeignKey')(related_name='places', to=orm['happy_hours.City'])),
        ))
        db.send_create_signal(u'happy_hours', ['Place'])

        # Adding model 'HappyHour'
        db.create_table(u'happy_hours_happyhour', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('description', self.gf('django.db.models.fields.CharField')(max_length=128)),
            ('start', self.gf('django.db.models.fields.FloatField')()),
            ('end', self.gf('django.db.models.fields.FloatField')()),
            ('days', self.gf('django.db.models.fields.CharField')(max_length=7)),
            ('place', self.gf('django.db.models.fields.related.ForeignKey')(related_name='happy_hours', to=orm['happy_hours.Place'])),
        ))
        db.send_create_signal(u'happy_hours', ['HappyHour'])

        # Adding model 'District'
        db.create_table(u'happy_hours_district', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('gt_id', self.gf('django.db.models.fields.IntegerField')(unique=True, db_index=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=128)),
            ('city', self.gf('django.db.models.fields.related.ForeignKey')(related_name='districts', to=orm['happy_hours.City'])),
        ))
        db.send_create_signal(u'happy_hours', ['District'])


    def backwards(self, orm):
        # Deleting model 'City'
        db.delete_table(u'happy_hours_city')

        # Deleting model 'Place'
        db.delete_table(u'happy_hours_place')

        # Deleting model 'HappyHour'
        db.delete_table(u'happy_hours_happyhour')

        # Deleting model 'District'
        db.delete_table(u'happy_hours_district')


    models = {
        u'happy_hours.city': {
            'Meta': {'object_name': 'City'},
            'gt_id': ('django.db.models.fields.IntegerField', [], {'unique': 'True', 'db_index': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '128'})
        },
        u'happy_hours.district': {
            'Meta': {'object_name': 'District'},
            'city': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'districts'", 'to': u"orm['happy_hours.City']"}),
            'gt_id': ('django.db.models.fields.IntegerField', [], {'unique': 'True', 'db_index': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '128'})
        },
        u'happy_hours.happyhour': {
            'Meta': {'object_name': 'HappyHour'},
            'days': ('django.db.models.fields.CharField', [], {'max_length': '7'}),
            'description': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'end': ('django.db.models.fields.FloatField', [], {}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'place': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'happy_hours'", 'to': u"orm['happy_hours.Place']"}),
            'start': ('django.db.models.fields.FloatField', [], {})
        },
        u'happy_hours.place': {
            'Meta': {'object_name': 'Place'},
            'city': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'places'", 'to': u"orm['happy_hours.City']"}),
            'gt_id': ('django.db.models.fields.IntegerField', [], {'unique': 'True', 'db_index': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'latitude': ('django.db.models.fields.FloatField', [], {'db_index': 'True'}),
            'longitude': ('django.db.models.fields.FloatField', [], {'db_index': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'street_address': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'zip_code': ('django.db.models.fields.CharField', [], {'max_length': '10'})
        }
    }

    complete_apps = ['happy_hours']