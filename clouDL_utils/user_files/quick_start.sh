#!/bin/bash

# Input arguments are mode and project_id and bucket_name
# Flag to move data.tar.zip to cloud storage: --datapth $BASE/data.tar.gz

WORKERS=1 # Spin up 1 worker
ARCHIVE=3 # Store only the top 3 in the archive

MODE=$1
PROJECT_ID=$2
BUCKET_NAME=$3

# This allows us to use relative imports by calling python with m flag and specifying package level
cd ../..
BASE="./clouDL/user_files"

if [ "$MODE" == "new" ]; then

  python -m clouDL.prep_and_start $PROJECT_ID \
    $BUCKET_NAME \
    --tokenpth $BASE/access_token \
    --mkbucket \
    --archive $ARCHIVE \
    --hyparams $BASE/hyperparameters.json \
    --location us-central1 \
    --cluster $WORKERS $BASE/configs.json $BASE/startup.sh

elif [ "$MODE" = "resume" ]; then

  python -m clouDL.prep_and_start $PROJECT_ID \
    $BUCKET_NAME \
    --archive $ARCHIVE \
    --hyparams $BASE/hyperparameters.json \
    --cluster $WORKERS $BASE/configs.json $BASE/startup.sh

elif [ "$MODE" = "manual" ]; then

  python -m clouDL.prep_and_start $PROJECT_ID \
    $BUCKET_NAME \
    --tokenpth $BASE/access_token \
    --mkbucket \
    --archive $ARCHIVE \
    --hyparams $BASE/hyperparameters.json \
    --location us-central1

elif [ "$MODE" = "analyze" ]; then

  python -m clouDL.analyze $PROJECT_ID-$BUCKET_NAME \
    --errs 10 \
    --best epochs \
    --archive epochs $ARCHIVE \
    --results epochs \
    --yrange 95 100
fi
