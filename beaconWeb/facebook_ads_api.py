from facebookads.api import FacebookAdsApi
from facebookads import objects
from datetime import datetime, timedelta
from django.conf import settings
from django.contrib.auth.models import User
from beaconWeb.apps.beacon.models import SponsoredEvent
from beaconWeb.apps.beacon.common.common_utils import get_all_new_users_in_markets, get_all_new_users_in_markets_emails, get_new_submitted_emails
from facebookads.objects import AdUser
from facebookads.adobjects.campaign import Campaign
from facebookads.objects import AdAccount


class HotspotFacebookAds(object):
    user = User.objects.get(username="5413359388")
    access_token = "EAAKijrdivowBADr6SJGcYKFfpnc8ZAHJEoYnMPnjJEAyZClbL0vZA62ZAt6MFoQ8ZBokTZCjmH6Xce6Qs9VVeKkFrLm8L6bemKRxtx9Ch0v9loFqNPPXSzrjpMr64LQFKXAPFwMLFTE1CmCTawCXZBK"
    ads_api = FacebookAdsApi.init(settings.FACEBOOK_APP_ID, settings.FACEBOOK_APP_SECRET, access_token)
    me = objects.AdUser(fbid='me')
    my_accounts = list(me.get_ad_accounts())
    def get_total_ad_spending(self, min_date=datetime.now()-timedelta(weeks=1), max_date=datetime.now()):
        ad_spending = 0
        formatted_min_date = self.convert_date(min_date+timedelta(days=1))
        formatted_max_date = self.convert_date(max_date)
        for account in self.my_accounts:
            account_obj = account.get_insights(params={"time_range":{'since':formatted_min_date, 'until':formatted_max_date}})
            if account_obj:
                ad_spending = ad_spending + float(account_obj[0]['spend'])
        return ad_spending
    def get_emails_for_markets(self, min_date=datetime.now()-timedelta(weeks=1), max_date=datetime.now(), market=None):
        user_emails = get_all_new_users_in_markets_emails(min_date, max_date)
        submitted_emails = get_new_submitted_emails(min_date, max_date)
        print "User Emails: "+ str(len(user_emails))
        print "Submitted Emails: " + str(len(submitted_emails))
        cash_payment_emails = []
        all_emails = list(user_emails) + list(submitted_emails) + list(cash_payment_emails)
        return set(all_emails)
    def get_users_for_markets(self, min_date=datetime.now()-timedelta(weeks=1), max_date=datetime.now(), market=None):
        all_users = get_all_new_users_in_markets(min_date, max_date)
        print "Users: "+ str(len(all_users))
        return all_users
    def cost_per_email(self, min_date=datetime.now()-timedelta(weeks=1), max_date=datetime.now()):
        emails = self.get_emails_for_markets(min_date, max_date)
        ad_spending = self.get_total_ad_spending(min_date, max_date)
        cost_per_email = ad_spending/len(emails)
        print "Spending: " + str(ad_spending)
        print "Emails: " + str(len(emails))
        print "Cost/Email: " + str(cost_per_email)
    def cost_per_user(self, min_date=datetime.now()-timedelta(weeks=1), max_date=datetime.now()):
        users = self.get_users_for_markets(min_date, max_date)
        ad_spending = self.get_total_ad_spending(min_date, max_date)
        cost_per_user = ad_spending/len(users)
        print "Spending: " + str(ad_spending)
        print "Users: " + str(len(users))
        print "Cost/User: " + str(cost_per_user)
    def get_last_ten_weeks(self):
        for i in range(10):
            current_date = datetime.now()-timedelta(weeks=i)
            previous_date = datetime.now()-timedelta(weeks=i+1)
            self.cost_per_email(previous_date, current_date)
            print ""
    def get_last_ten_weeks_users(self):
        for i in range(10):
            current_date = datetime.now()-timedelta(weeks=i)
            previous_date = datetime.now()-timedelta(weeks=i+1)
            self.cost_per_user(previous_date, current_date)
            print ""
    def convert_date(self, date):
        return date.strftime("%Y-%m-%d")
    def spent_on_event(self, event):
        fields = ['campaign_name', 'campaign_id', 'spend']
        params = {"date_preset":"lifetime"}
        if event.facebook_campaign_id:
            # my_account = objects.AdAccount('act_19596279')
            campaign_id = event.facebook_campaign_id
            campaign = Campaign(campaign_id)
            insights = campaign.get_insights(fields=fields, params=params)
            if len(insights) > 0:
                return insights[0]['spend']
            else:
                return None
        else:
            return None
    def update_campaign_ids(self):
        fields = ['campaign_name', 'campaign_id', 'spend']
        my_account = objects.AdAccount('act_19596279')
        campaigns = my_account.get_campaigns()
        facebook_event_ids = SponsoredEvent.objects.all().values_list('facebook_event_id', flat=True)
        for campaign in campaigns:
            c = campaign.get_insights(fields=fields)
            name = c[0]['campaign_name']
            print name
            for fb_id in facebook_event_ids:
                if fb_id in name:
                    event = SponsoredEvent.objects.get(facebook_event_id=fb_id)
                    event.facebook_campaign_id = c[0]['campaign_id']
                    event.save()



