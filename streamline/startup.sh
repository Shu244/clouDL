#!/bin/bash

echo "------------------------------------------STARTING--------------------------------------------------"
sudo /opt/deeplearning/install-driver.sh to install drivers

# The y flag installs without prompts
conda install -y pathlib

## Takes a while for user to get created. So I may need to sleep. This is acutually not necessary though
#cd home
#cd shuhaolai18

export PATH="/opt/conda/bin:$PATH"

RANK=$(curl http://metadata/computeMetadata/v1/instance/attributes/rank -H "Metadata-Flavor: Google")
BUCKET_NAME=$(curl http://metadata/computeMetadata/v1/instance/attributes/bucket -H "Metadata-Flavor: Google")
echo "The rank is $RANK"
echo "The bucket name is $BUCKET_NAME"

mkdir code
cd code
mkdir data

gsutil cp gs://$BUCKET_NAME/secrets/access_token ./data
token=$(<./data/access_token)
git clone https://shu244:$token@github.com/shu244/GCP_AI.git

#cd GCP_AI
#python base.py
cd GCP_AI/streamline
mkdir tmp
python manager.py $RANK $BUCKET_NAME

#export NAME=$(curl -X GET http://metadata.google.internal/computeMetadata/v1/instance/name -H 'Metadata-Flavor: Google')
#export ZONE=$(curl -X GET http://metadata.google.internal/computeMetadata/v1/instance/zone -H 'Metadata-Flavor: Google')
#gcloud --quiet compute instances delete $NAME --zone=$ZONE
echo "------------------------------------------FINISHED--------------------------------------------------"

