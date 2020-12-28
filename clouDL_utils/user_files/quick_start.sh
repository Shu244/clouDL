#!/bin/bash

# Input arguments are mode and project_id and bucket_name
# Flag to move data.tar.zip to cloud storage: --datapth $BASE/data.tar.gz

WORKERS=1 # Spin up 1 worker
ARCHIVE=3 # Store only the top 3 in the archive

MODE=$1
PROJECT_ID=$2
BUCKET_NAME=$3

BASE="./user_files"

if [ "$MODE" == "new" ]; then

  clouDL $PROJECT_ID \
    $BUCKET_NAME \
    --mkbucket \
    --archive $ARCHIVE \
    --hyparams $BASE/hyperparameters.json \
    --location us-central1 \
    --cluster $WORKERS $BASE/configs.json $BASE/user_startup.sh

elif [ "$MODE" = "resume" ]; then

  clouDL $PROJECT_ID \
    $BUCKET_NAME \
    --archive $ARCHIVE \
    --hyparams $BASE/hyperparameters.json \
    --cluster $WORKERS $BASE/configs.json $BASE/user_startup.sh

elif [ "$MODE" = "manual" ]; then

  clouDL $PROJECT_ID \
    $BUCKET_NAME \
    --tokenpth $BASE/access_token \
    --mkbucket \
    --archive $ARCHIVE \
    --hyparams $BASE/hyperparameters.json \
    --location us-central1

elif [ "$MODE" = "analyze" ]; then

  clouDL_analyze $PROJECT_ID-$BUCKET_NAME \
    --errs 10 \
    --best epochs \
    --archive epochs $ARCHIVE \
    --results epochs \
    --yrange 95 100
fi
