#!/bin/bash

sudo /opt/deeplearning/install-driver.sh to install drivers

RANK=$(curl http://metadata/computeMetadata/v1/instance/attributes/rank -H "Metadata-Flavor: Google")
BUCKET_NAME=$(curl http://metadata/computeMetadata/v1/instance/attributes/bucket -H "Metadata-Flavor: Google")

mkdir code
cd code

gsutil cp gs://$BUCKET_NAME/secrets/access_token .
token=$(<access_token)
git clone https://shu244:$token@github.com/shu244/GCP_AI.git

cd GCP_AI/streamline
python manager.py RANK BUCKET_NAME
