#!/bin/bash

# Input arguments are mode and bucket_name

MODE=$1
BUCKET_NAME=$2
WORKERS=1 # Spin up 1 worker
ARCHIVE=3 # Store only the top 3 in the archive


# This allows us to use relative imports by calling python with m flag and specifying package level
cd ..

# Flag to move data.tar.zip to cloud storage: --datapth ./GCP_AI/user_files/data.tar.gz \

if [ "$MODE" == "new" ]; then

  python -m GCP_AI.prep_and_start stoked-brand-285120 \
    $BUCKET_NAME \
    --tokenpth ./GCP_AI/user_files/access_token \
    --mkbucket \
    --archive $ARCHIVE \
    --hyparams ./GCP_AI/user_files/hyperparameters.json \
    --location us-central1 \
    --cluster $WORKERS ./GCP_AI/user_files/configs.json ./GCP_AI/startup.sh

elif [ "$MODE" = "resume" ]; then

  python -m GCP_AI.prep_and_start stoked-brand-285120 \
    $BUCKET_NAME \
    --archive $ARCHIVE \
    --hyparams ./GCP_AI/user_files/hyperparameters.json \
    --cluster $WORKERS ./GCP_AI/user_files/configs.json ./GCP_AI/startup.sh

elif [ "$MODE" = "manual" ]; then

  python -m GCP_AI.prep_and_start stoked-brand-285120 \
    $BUCKET_NAME \
    --tokenpth ./GCP_AI/user_files/access_token \
    --mkbucket \
    --archive $ARCHIVE \
    --hyparams ./GCP_AI/user_files/hyperparameters.json \
    --location us-central1

elif [ "$MODE" = "analyze" ]; then

  python -m GCP_AI.analyze stoked-brand-285120-$BUCKET_NAME \
    --errs 10 \
    --best epochs \
    --archive epochs $ARCHIVE \
    --results epochs \
    --yrange 95 100
fi
