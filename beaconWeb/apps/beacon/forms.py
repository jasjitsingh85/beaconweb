from django import forms

class UploadFileForm(forms.Form):
    title = forms.CharField(max_length=50)
    file  = forms.FileField()

SOURCE_CHOICES = (
    ("Facebook",u'Facebook'),
    ("Email",u'Email'),
    ("From a friend",u'From a friend'),
    ("Notification on my phone",u'Notification on my phone'),
    ("Saw in the app",u'Saw in the app'),
    ("Found out at the venue",u'Found out at the venue'),
    ("Other",u'Other'),
    ("...",u"...")
)

FREQUENCY_CHOICES = (
    ("Never",u'Never'),
    ("A couple times a year",u'A couple times a year'),
    ("Once a month",u'Once a month'),
    ("A couple times a month",u'A couple times a month'),
    ("Once a week",u'Once a week'),
    ("...",u"...")
)

class EventFeedback(forms.Form):
    general = forms.CharField(required=False,
                              widget=forms.Textarea(attrs={'class':'form-control','placeholder':'feedback','rows':3}))
    source = forms.CharField(required=False,
                              widget=forms.Select(choices=SOURCE_CHOICES, attrs={'class':'form-control'}))
    frequency = forms.CharField(required=False,
                                 widget=forms.Select(choices=FREQUENCY_CHOICES, attrs={'class':'form-control'}))
    improvements = forms.CharField(required=False,
                                    widget=forms.Textarea(attrs={'class':'form-control','placeholder':'feedback','rows':3}))