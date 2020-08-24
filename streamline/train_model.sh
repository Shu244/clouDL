#!/bin/bash

gcloud compute ssh vm-0 --zone=us-central1-b --command="python --version"