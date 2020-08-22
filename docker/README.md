# Considerations

The resulting docker image is several GBs, and deploying it to GCP takes a nontrivial time.
Another option is to use a prebuilt notebook from AI Platform, but that only allows 1 GPU. 
Prebuilt Compute Engines do not exists yet. Though tedious, this is currently
the best option.

# Docker build
From the root of the repo: 

<code>docker build --tag gcp_ai --file deploy/dockerfile .</code>

# Docker run
<code>docker run --name aicontainer --gpus all gcp_ai</code>
