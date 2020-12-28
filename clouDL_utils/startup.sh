#!/bin/bash

echo "------------------------------------------STARTING--------------------------------------------------"
sudo /opt/deeplearning/install-driver.sh to install drivers

export PATH="/opt/conda/bin:$PATH"

BUCKET_NAME=$(curl http://metadata/computeMetadata/v1/instance/attributes/bucket -H "Metadata-Flavor: Google")
echo "The bucket name is $BUCKET_NAME"

mkdir code
cd code
mkdir data

gsutil cp gs://$BUCKET_NAME/data ./data
tar -xvzf data/data.tar.zip -C data

gsutil cp gs://$BUCKET_NAME/secrets/access_token ./data
TOKEN=$(<./data/access_token)

# USER_CODE_GOES_HERE

export NAME=$(curl -X GET http://metadata.google.internal/computeMetadata/v1/instance/name -H 'Metadata-Flavor: Google')
export ZONE=$(curl -X GET http://metadata.google.internal/computeMetadata/v1/instance/zone -H 'Metadata-Flavor: Google')
gcloud --quiet compute instances delete $NAME --zone=$ZONE
echo "------------------------------------------FINISHED--------------------------------------------------"

