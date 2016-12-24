# from scheduler import scheduler
#
# scheduler.run()
# import logging

from apscheduler.schedulers.blocking import BlockingScheduler

sched = BlockingScheduler()

# logging.basicConfig()

from beaconWeb.apps.beacon.common.chron import daily_chron_job, close_chat_lines
from beaconWeb.apps.beacon.common.utils.event_staffer import check_to_send_initial_staffer_notifications, check_to_send_first_reminder_staffer_notifications, check_to_send_second_reminder_staffer_notifications, check_to_send_final_reminder_staffer_notifications, send_daily_event_staffer_email_to_general_manager
# from beaconWeb.apps.beacon.data.instagram_scraper import get_media_and_cache
from beaconWeb.apps.beacon.common.utils.tracker import store_event_numbers
from beaconWeb.apps.beacon.common.utils.sponsored_events import event_chron_job
from beaconWeb.apps.beacon.common.utils.swipe_and_match import check_for_dating_queue
from beaconWeb.apps.beacon.common.utils.email_campaign import check_and_run_day_of_email
# from beaconWeb.apps.beacon.common.utils.event_staffer import run_event_staffing
# from beaconWeb.settings import RQ_THREAD
# from django_rq import job


# @sched.scheduled_job('interval', minutes=60)
# def timed_job():
#     print "Started newsfeed cache job"
#     update_newsfeed_cache.delay()


#@sched.scheduled_job('interval', minutes=30)
#def timed_job():
#    print "checking for unclaimed tabs to cancel"
#    check_for_unclaimed_tabs_to_cancel()


#@sched.scheduled_job('interval', minutes=60)
#def timed_job():
#    print "checking for open tabs to close"
#    check_for_open_tabs_to_close()


# @sched.scheduled_job('cron', day_of_week='*',  hour=4)
# def update_photos_job():
#     print "Started get media and cache job"
#     get_media_and_cache.delay()


@sched.scheduled_job('cron', day_of_week='*',  hour=0)
def update_event_tracking_one():
    print "Started event tracking"
    store_event_numbers.delay()


@sched.scheduled_job('cron', day_of_week='*',  hour=12)
def update_event_tracking_two():
    print "Started event tracking"
    store_event_numbers.delay()


@sched.scheduled_job('interval', minutes=5)
def event_management_check():
    print "Started event chron job"
    event_chron_job.delay()


@sched.scheduled_job('cron', day_of_week='*',  hour=4)
def scheduled_job():
    print "Daily Chron Job"
    daily_chron_job.delay()


@sched.scheduled_job('cron', day_of_week='*',  hour=19)
def check_swipe_and_match():
    print "Checked Swipe and Match"
    check_for_dating_queue.delay()

# @sched.scheduled_job('cron', day_of_week='*',  hour=15)
# def event_staffing():
#     print "Started Run Event Staffing"
#     run_event_staffing.delay()


@sched.scheduled_job('cron', day_of_week='*',  hour=4)
def close_lines():
    close_chat_lines.delay()


@sched.scheduled_job('cron', day_of_week='*',  hour=8)
def initial_staffer_notifications():
    check_to_send_initial_staffer_notifications.delay()


@sched.scheduled_job('cron', day_of_week='*',  hour=19)
def send_first_reminder():
    print "send first staffer reminder check"
    check_to_send_first_reminder_staffer_notifications.delay()


@sched.scheduled_job('cron', day_of_week='*',  hour=12)
def send_second_reminder():
    print "send second staffer reminder check"
    check_to_send_second_reminder_staffer_notifications.delay()


@sched.scheduled_job('cron', day_of_week='*',  minute=15)
def send_final_reminder():
    print "send final staffer reminder check"
    check_to_send_final_reminder_staffer_notifications.delay()


@sched.scheduled_job('cron', day_of_week='*',  hour=23)
def daily_event_staffer_email():
    print "send daily email about staffers to gm"
    send_daily_event_staffer_email_to_general_manager.delay()


# @sched.scheduled_job('cron', day_of_week=1,  hour=15)
# def weekly_email_campaign():
#     check_and_run_weekly_email.delay()


# @sched.scheduled_job('cron', day_of_week='*',  hour=8)
# def day_before_email_campaign():
#     check_and_run_day_of_email.delay()


sched.start()