#!/bin/bash

echo "------------------------------------------STARTING--------------------------------------------------"
sudo /opt/deeplearning/install-driver.sh to install drivers

export PATH="/opt/conda/bin:$PATH"

# The y flag installs without prompts
conda install -y pathlib

mkdir code
cd code
mkdir data

gsutil cp gs://$BUCKET_NAME/secrets/access_token ./data
TOKEN=$(<./data/access_token)
git clone https://shu244:$TOKEN@github.com/shu244/GCP_AI.git

cd GCP_AI
git pull origin package
git checkout package

python MNIST_test.py

export NAME=$(curl -X GET http://metadata.google.internal/computeMetadata/v1/instance/name -H 'Metadata-Flavor: Google')
export ZONE=$(curl -X GET http://metadata.google.internal/computeMetadata/v1/instance/zone -H 'Metadata-Flavor: Google')
gcloud --quiet compute instances delete $NAME --zone=$ZONE
echo "------------------------------------------FINISHED--------------------------------------------------"

