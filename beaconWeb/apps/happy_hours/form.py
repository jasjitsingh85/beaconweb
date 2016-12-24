from django import forms
from beaconWeb.apps.happy_hours.models import City

DAY_CHOICES = (
    ('Sunday','Sunday'),
    ('Monday','Monday'),
    ('Tuesday', 'Tuesday'),
    ('Wednesday', 'Wednesday'),
    ('Thursday', 'Thursday'),
    ('Friday', 'Friday'),
    ('Saturday', 'Saturday'),
)

TIME_CHOICES = (
    ('Afternoon', 'Afternoon'),
    ('Evening', 'Evening'),
    ('Night', 'Night'),
)

NEIGHBORHOOD_CHOICES = (
    ('Any', 'Select'),
)


class SelectForm(forms.Form):
    city = forms.ModelChoiceField(City.objects.all())
    neighborhood = forms.ChoiceField()
    day = forms.ChoiceField(choices=DAY_CHOICES)
    time = forms.ChoiceField(choices=TIME_CHOICES)

    def __init__(self, *args, **kwargs):
        super(SelectForm, self).__init__(*args, **kwargs)
        self.fields['city'].queryset = City.objects.order_by('name')