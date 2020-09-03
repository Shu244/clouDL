#!/bin/bash

# Input arguments are bucket_name and mode

BUCKET_NAME=$1
MODE=$2
WORKERS=1
ARCHIVE=3

if [ "$MODE" == "new" ]; then

  python prep_and_start.py stoked-brand-285120 \
    $BUCKET_NAME \
    --tokenpth ./user_files/access_token \
    --mkbucket \
    --datapth ./user_files/fake_data.tar.gz \
    --archive $ARCHIVE \
    --hyparams ./user_files/hyperparameters.json \
    --location us-central1 \
    --cluster $WORKERS ./user_files/configs.json ./startup.sh

elif [ "$MODE" = "resume" ]; then

  python prep_and_start.py stoked-brand-285120 \
    $BUCKET_NAME \
    --archive $ARCHIVE \
    --hyparams ./user_files/hyperparameters.json \
    --cluster $WORKERS ./user_files/configs.json ./startup.sh

elif [ "$MODE" = "manual-test" ]; then

  python prep_and_start.py stoked-brand-285120 \
    $BUCKET_NAME \
    --tokenpth ./user_files/access_token \
    --mkbucket \
    --datapth ./user_files/fake_data.tar.gz \
    --archive $ARCHIVE \
    --hyparams ./user_files/hyperparameters.json \
    --location us-central1

elif [ "$MODE" = "analyze" ]; then

  python analyze.py stoked-brand-285120-$BUCKET_NAME \
    --errs 10 \
    --best epochs \
    --archive epochs $ARCHIVE \
    --results epochs \
    --yrange 95 100
fi