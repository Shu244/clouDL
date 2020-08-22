#!/bin/bash

nflag="false"
bflag="false"
dflag="false"
cflag="false"
vflag="false"
wflag=1

usage () {
  echo "bash local_cleanup.sh -n <bucket_name> [-b] [-d <data_path>] [-c <code_path>] [-v] [-w <num_workers>]"
  echo "Use the b flag to make the bucket and v flag to clear the VMs' progress"
  echo "Google Cloud SDK must be install to use this script"
}

hr () {
  echo "------------------------------------------------------------------------------"
}

options=':n:bd:c:vh'
while getopts $options option
do
    case "$option" in
      n  ) nflag=$OPTARG;;
      b  ) bflag=$OPTARG;;
      d  ) dflag=$OPTARG;;
      c  ) cflag=$OPTARG;;
      v  ) vflag=$OPTARG;;
      w  ) wflag=$OPTARG;;
      h  ) usage; exit;;
      \? ) echo "Unknown option: -$OPTARG" >&2; exit 1;;
      :  ) echo "Missing option argument for -$OPTARG" >&2; exit 1;;
      *  ) echo "Unimplemented option: -$OPTARG" >&2; exit 1;;
    esac
done

# bucket_name, make_bucket, move_data, code_path, clear_vm_progress
PROJECT_ID=$(gcloud config list project --format "value(core.project)")

if  [[ $nflag == "false" ]]
then
  echo "Please specify the n flag. Use -h for help."
  exit 1
fi

if  [[ $bflag != "false" ]]
then
  echo "Making bucket named $nflag in us-central1 and creating folders"
  gsutil mb -l us-central1 gs://$PROJECT_ID-$nflag
  hr
fi

if  [[ $dflag != "false" ]]
then
  echo "Moving data from $dflag to bucket"
  gsutil cp $dflag gs://$PROJECT_ID-$nflag/data/
  hr
fi

if  [[ $cflag != "false" ]]
then
  echo "Moving code from $cflag to bucket"
  gsutil cp $cflag gs://$PROJECT_ID-$nflag/code/
  hr
fi

if  [[ $vflag != "false" ]]
then
  echo "Clearing the virtual machine progress reports"
  gsutil rm -r gs://$PROJECT_ID-$nflag/vm-progress
  hr
fi

for ((i=1;i<=wflag;i++))
do
  echo ""
#  gcloud beta compute instances create-with-container image-test --zone=us-central1-a \
#    --machine-type=n1-standard-1 \
#    --subnet=default \
#    --network-tier=PREMIUM \
#    --metadata="google-logging-enabled=true,startup-script=docker run --name aicontainer --gpus all gcp_ai" \
#    --no-restart-on-failure \
#    --maintenance-policy=TERMINATE \
#    --preemptible \
#    --service-account=871526703212-compute@developer.gserviceaccount.com \
#    --scopes=https://www.googleapis.com/auth/devstorage.read_only,https://www.googleapis.com/auth/logging.write,https://www.googleapis.com/auth/monitoring.write,https://www.googleapis.com/auth/servicecontrol,https://www.googleapis.com/auth/service.management.readonly,https://www.googleapis.com/auth/trace.append \
#    --accelerator=type=nvidia-tesla-t4,count=1 \
#    --image=cos-stable-81-12871-1185-0 \
#    --image-project=cos-cloud \
#    --boot-disk-size=10GB \
#    --boot-disk-type=pd-standard \
#    --boot-disk-device-name=image-test \
#    --no-shielded-secure-boot \
#    --shielded-vtpm \
#    --shielded-integrity-monitoring \
#    --container-image=gcr.io/integral-accord-270805/gcp_ai:latest \
#    --container-restart-policy=always \
#    --labels=container-vm=cos-stable-81-12871-1185-0 \
#    --reservation-affinity=any
done
