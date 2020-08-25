#!/bin/bash

python local_cleanup.py stoked-brand-285120 \
    test1 \
    ./user_files/configs.json \
    ./startup.sh \
    --hyparams ./user_files/hyperparameters.json \
#    --tokenpth ./user_files/access_token \
#    --mkbucket \
#    --datapth ./user_files/fake_data.tar.gz \
#    --workers 1 \
#    --location us-central1