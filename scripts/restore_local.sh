#!/bin/bash   

echo 'Dropping and creating database beacons'
psql -c "DROP DATABASE beacons"
psql -c "CREATE DATABASE beacons"
PROD_NAME='heroku'
PROD_URL=$(heroku pgbackups:url -r $PROD_NAME)
LOCAL_DUMP='latest.dump'
echo Downloading latest backup and storing in $LOCAL_DUMP
curl -o $LOCAL_DUMP $PROD_URL
pg_restore --verbose --clean --no-acl --no-owner -h localhost -U $USER -d beacons $LOCAL_DUMP
echo Restore complete. Cleaning up $LOCAL_DUMP
rm $LOCAL_DUMP
