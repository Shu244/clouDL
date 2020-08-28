#!/bin/bash

# Input arguments are bucket_name and mode

BUCKET_NAME=$1
MODE=$2

if [ "$MODE" == "new" ]; then

  python prep_and_start.py stoked-brand-285120 \
    $BUCKET_NAME \
    --tokenpth ./user_files/access_token \
    --mkbucket \
    --datapth ./user_files/fake_data.tar.gz \
    --hyparams ./user_files/hyperparameters.json \
    --location us-central1 \
    --cluster 2 ./user_files/configs.json ./startup.sh

elif [ "$MODE" = "resume" ]; then

  python prep_and_start.py stoked-brand-285120 \
    $BUCKET_NAME \
    --hyparams ./user_files/hyperparameters.json \
    --cluster 2 ./user_files/configs.json ./startup.sh

elif [ "$MODE" = "manual-test" ]; then

  python prep_and_start.py stoked-brand-285120 \
    $BUCKET_NAME \
    --tokenpth ./user_files/access_token \
    --mkbucket \
    --datapth ./user_files/fake_data.tar.gz \
    --hyparams ./user_files/hyperparameters.json \
    --location us-central1

elif [ "$MODE" = "analyze" ]; then

  python analyze.py stoked-brand-285120-$BUCKET_NAME \
    --errs 10 \
    --best epochs \
    --results epochs \
    --yrange 95 100
fi