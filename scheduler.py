from rq_scheduler import Scheduler
from rq import use_connection
import django_rq
from django_rq import job
from datetime import datetime, timedelta


def print_chron_statements():
    print "CHRON JOB IS WORKING!"

scheduler = Scheduler('default', connection=django_rq.get_connection('high'))

# scheduler.schedule(
#     scheduled_time=datetime.now(), # Time for first execution, in UTC timezone
#     func=print_chron_statements,                     # Function to be queued
#     args=[],                    # Keyword arguments passed into function when executed
#     interval=1,                   # Time before the function is called again, in seconds
#     repeat=None                      # Repeat this number of times (None means repeat forever)
# )