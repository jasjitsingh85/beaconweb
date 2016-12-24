#!/bin/bash   

STAGING_NAME='staging'
PROD_NAME='heroku'
STAGING_APP_NAME='hotspotapp-staging'
echo -n "Are you sure you want to restore $STAGING_NAME? This is destructive [y/n]:"
read -n 1 confirm
echo

if [ "$confirm" == "y" ]; then
echo Backing up staging
heroku pgbackups:capture --expire -r $STAGING_NAME
echo Resetting staging
heroku pg:reset DATABASE -r $STAGING_NAME --confirm $STAGING_APP_NAME
PROD_DB_URL=$(heroku pgbackups:url -r $PROD_NAME)
echo Restoring staging from latest prod backup
heroku pgbackups:restore DATABASE $PROD_DB_URL -r $STAGING_NAME --confirm $STAGING_APP_NAME
else
echo "OK, database will not be restored"
fi
