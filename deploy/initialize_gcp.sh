gcloud beta compute --project=integral-accord-270805 instances create-with-container image-test --zone=us-central1-a \
  --machine-type=n1-standard-1 \
  --subnet=default \
  --network-tier=PREMIUM \
  --metadata="google-logging-enabled=true,startup-script=docker run --name aicontainer --gpus all gcp_ai" \
  --no-restart-on-failure \
  --maintenance-policy=TERMINATE \
  --preemptible \
  --service-account=871526703212-compute@developer.gserviceaccount.com \
  --scopes=https://www.googleapis.com/auth/devstorage.read_only,https://www.googleapis.com/auth/logging.write,https://www.googleapis.com/auth/monitoring.write,https://www.googleapis.com/auth/servicecontrol,https://www.googleapis.com/auth/service.management.readonly,https://www.googleapis.com/auth/trace.append \
  --accelerator=type=nvidia-tesla-t4,count=1 \
  --image=cos-stable-81-12871-1185-0 \
  --image-project=cos-cloud \
  --boot-disk-size=10GB \
  --boot-disk-type=pd-standard \
  --boot-disk-device-name=image-test \
  --no-shielded-secure-boot \
  --shielded-vtpm \
  --shielded-integrity-monitoring \
  --container-image=gcr.io/integral-accord-270805/gcp_ai:latest \
  --container-restart-policy=always \
  --labels=container-vm=cos-stable-81-12871-1185-0 \
  --reservation-affinity=any


  gcloud beta compute --project=stoked-brand-285120 instances create-with-container gcp-ai --zone=us-central1-a --machine-type=n1-standard-1 --subnet=default --network-tier=PREMIUM --metadata="google-logging-enabled=true,startup-script=docker run --name aicontainer --gpus all gcr.io/stoked-brand-285120/gcp_ai" --no-restart-on-failure --maintenance-policy=TERMINATE --preemptible --service-account=873973865900-compute@developer.gserviceaccount.com --scopes=https://www.googleapis.com/auth/devstorage.read_only,https://www.googleapis.com/auth/logging.write,https://www.googleapis.com/auth/monitoring.write,https://www.googleapis.com/auth/servicecontrol,https://www.googleapis.com/auth/service.management.readonly,https://www.googleapis.com/auth/trace.append --accelerator=type=nvidia-tesla-t4,count=1 --image=cos-stable-81-12871-1185-0 --image-project=cos-cloud --boot-disk-size=10GB --boot-disk-type=pd-standard --boot-disk-device-name=gcp-ai --no-shielded-secure-boot --shielded-vtpm --shielded-integrity-monitoring --container-image=gcr.io/stoked-brand-285120/gcp_ai:latest --container-restart-policy=always --labels=container-vm=cos-stable-81-12871-1185-0 --reservation-affinity=any