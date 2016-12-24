from django.db import models
from deal_place import DealPlace


class PlacePhotos(models.Model):
    place = models.ForeignKey(DealPlace)
    source_image_url = models.CharField(max_length=400)
    like_count = models.IntegerField(null=True, blank=True)
    comment_count = models.IntegerField(null=True, blank=True)
    tag_count = models.IntegerField(null=True, blank=True)
    image_date = models.DateTimeField(null=True, blank=True)

    class Meta:
        app_label = 'beacon'