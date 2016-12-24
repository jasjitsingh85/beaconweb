# Beacon Web


# Requirements

*Postgres.app

*virtualenv: pip install virtualenv


#Setup

Setup virtual environment and download dependencies

$ virtualenv ENV

$ source ENV/bin/activate

$ pip install -r requirements.txt


Create database and extend it with postgis

$ createdb beacons

Run syncdb and migrate
