#!/bin/bash

#python local_cleanup.py stoked-brand-285120 \
#    beta \
#    --mkbucket \
#    --tokenpth ./user_files/access_token \
#    --mkbucket \
#    --datapth ./user_files/fake_data.tar.gz \
#    --hyparams ./user_files/hyperparameters.json \
#    --location us-central1
##    --cluster 1 ./user_files/machine_configs_pth.json ./startup.sh \

python local_cleanup.py stoked-brand-285120 \
    beta \
    --hyparams ./user_files/hyperparameters.json \
