import glob
import pathlib
import os
import time

# Compute Engine client library
import googleapiclient.discovery
# Cloud storage client library
from google.cloud import storage

storage_client = storage.Client()
# using compute engine service, version 1
compute = googleapiclient.discovery.build('compute', 'v1')

def upload_folder_helper(bucket, src, dest):
    '''
    Recursively uploads folder.

    :param bucket: Bucket name
    :param src: To upload
    :param dest: Location to upload
    '''

    assert os.path.isdir(src)
    for local_obj in glob.glob(src + '/**'):
        basename = os.path.basename(local_obj)
        if os.path.isdir(local_obj):
            # local_obj is a folder
            upload_folder_helper(bucket, local_obj, dest + "/" + basename)
        else:
            remote_path = os.path.join(dest, basename)
            blob = bucket.blob(remote_path)
            blob.upload_from_filename(local_obj)
            print('Moved ', remote_path)


def upload_folder(bucket_name, src, dest):
    '''
    Moves the contents of the src folder inside dest folder.
    This function should not be used to push training data.
    Instead, archive and zip training folder so it can be pushed as one file
    For safety, dest be empty

    :param bucket_name: name of bucket
    :param src: source folder
    :param dest: destination folder
    '''
    if not os.path.isdir(src) or len(os.listdir(src)) == 0:
        raise ValueError("src folder must exist and not be empty")

    bucket = storage_client.bucket(bucket_name)

    # Ensuring empty dest folder
    blobs = bucket.list_blobs(prefix=dest)
    for blob in blobs:
        # Ignoring the folder itself
        if blob.name[blob.name.find('/') + 1:] == '':
            continue
        raise ValueError("Dest folder must be empty")

    upload_folder_helper(bucket, src, dest)


def upload_file(bucket_name, src, dest):
    '''
    Upload a file to Google cloud storage

    :param bucket_name: Bucket name
    :param src: Path of the file to upload
    :param dest: Path of the folder of where to upload file
    '''

    bucket = storage_client.bucket(bucket_name)
    remote_path = os.path.join(dest, os.path.basename(src))
    blob = bucket.blob(remote_path)
    blob.upload_from_filename(src)


def download_folder(bucket_name, src, dest):
    '''
    Moves content of src folder in GCP into local dest folder.
    For safety, dest must be empty.

    :param bucket: Bucket name
    :param src: Source folder in GCP storage
    :param dest: local destination folder
    '''

    if not os.path.isdir(dest) or len(os.listdir(dest)) != 0:
        raise ValueError("Dest folder must exists and be empty")

    bucket = storage_client.bucket(bucket_name)
    blobs = bucket.list_blobs(prefix=src)  # Get list of files
    for blob in blobs:
        # name will be in the format of src/folder1/.../folderN/file.ext
        name = blob.name

        # Ignoring the folder itself
        no_src = name[name.find('/') + 1:]
        if no_src == '':
            continue

        path = os.path.join(dest, no_src)
        if name.count('/') > 1:
            # Create nested directories
            pathlib.Path(path[:path.rfind('/')]).mkdir(parents=True, exist_ok=True)

        blob.download_to_filename(path)


def download_file(bucket_name, src, dest):
    '''
    Downloads a file from Google Cloud Storage

    :param bucket_name: Name of the bucket
    :param src: Path of the file
    :param dest: Path of the folder to keep the file.
    '''
    filename = src[src.rfind('/')+1:]
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(src)
    blob.download_to_filename(os.path.join(dest, filename))


def delete_all_prefixes(bucket_name, folder):
    '''
    Delete folder and all of its content in Google Cloud Storage

    :param bucket_name: Bucket name
    :param folder: Folder name in Cloud
    '''

    bucket = storage_client.bucket(bucket_name)
    blobs = bucket.list_blobs(prefix=folder)
    for blob in blobs:
        blob.delete()


def make_bucket(bucket_name, location):
    '''
    Makes a bucket

    :param bucket_name: Name of bucket
    :param location: location to store bucket
    '''

    # Will throw error if bucket already exists
    storage_client.create_bucket(bucket_name, location=location)


def gen_gcp_pth(root, *args):
    '''
    Generates a path of the form: gs://root/arg1/arg2/arg3/...
    :param project_id: Project id
    :param args: Paths
    :return: Generated path
    '''

    pth = 'gs://' + root
    for arg in args:
        pth += '/' + arg
    return pth


def list_instances(project_id, zone):
    result = compute.instances().list(project=project_id, zone=zone).execute()
    return result['items'] if 'items' in result else None


def create_instance(project_id, configs, startup_script, zone, rank, bucket_name):
    name = configs["name_prefix"] + ("-%d" % rank)

    image_response = compute.images().getFromFamily(
        project='deeplearning-platform-release',
        family=configs['family']).execute()
    source_image = image_response['selfLink']

    machine_type = "zones/%s/machineTypes/n1-standard-2" % zone
    accelerator_type = "zones/%s/acceleratorTypes/%s" % (zone, configs['gpu'])

    subnetwork = "regions/%s/subnetworks/default" % zone[:zone.rfind('-')]

    config = {
        "name": name,
        "machineType": machine_type,

        "disks": [
            {
                "boot": True,
                "autoDelete": True,
                "initializeParams": {
                    'sourceImage': source_image,
                    "diskSizeGb": configs["diskSizeGb"],
                }
            }
        ],

        "networkInterfaces": [
            {
                "kind": "compute#networkInterface",
                "subnetwork": subnetwork,
                "accessConfigs": [
                    {
                        "kind": "compute#accessConfig",
                        "name": "External NAT",
                        "type": "ONE_TO_ONE_NAT",
                        "networkTier": "PREMIUM"
                    }
                ],
                "aliasIpRanges": []
            }
        ],

        "guestAccelerators": [
            {
                "acceleratorCount": configs["gpu_count"],
                "acceleratorType": accelerator_type
            }
        ],

        "scheduling": {
            "preemptible": configs["preemptible"],
            "onHostMaintenance": "TERMINATE",
        },

        # Allow the instance to access cloud storage and logging.
        'serviceAccounts': [
            {
                'email': 'default',
                'scopes': [
                    # Read and write to cloud storage
                    'https://www.googleapis.com/auth/devstorage.read_write',
                    # Write logs
                    'https://www.googleapis.com/auth/logging.write',
                    # Manage compute engine instances (needed for self deleting)
                    'https://www.googleapis.com/auth/compute'
                ]
            }
        ],

        # Metadata is readable from the instance and allows you to
        # pass configuration from deployment scripts to instances.
        'metadata': {
            'items': [
                {
                    # Startup script is automatically executed by the
                    # instance upon startup.
                    'key': 'startup-script',
                    'value': startup_script
                },
                {
                    'key': 'rank',
                    'value': rank
                },
                {
                    'key': 'bucket',
                    'value': bucket_name
                }
            ]
        }
    }

    return compute.instances().insert(
        project=project_id,
        zone=zone,
        body=config).execute()


def wait_for_operation(project_id, operation, zone):
    '''
    Waits for an operation in GCP to finish then report its status

    :param project_id: Project id the operation took place in
    :param operation: Operation name
    :param zone: Zone of the operation
    :return: True if successful, false otherwise
    '''

    while True:
        result = compute.zoneOperations().get(
            project=project_id,
            zone=zone,
            operation=operation).execute()

        if result['status'] == 'DONE':
            if 'error' in result:
                return False
            return True

        time.sleep(1)


def delete_instance(project_id, zone, name):
    return compute.instances().delete(
        project=project_id,
        zone=zone,
        instance=name).execute()


class QuickSend:
    def __init__(self, temp_path, bucket_name):
        self.temp_path = temp_path
        self.bucket_name = bucket_name

    def send(self, filename, msg, folder):
        '''
        Writes the msg to the filename in the tmp folder then sends it
        to google cloud storage in the folder specified by the arg.

        :param filename: Name of the file of for the msg
        :param msg: Message to send
        :param folder: Folder to store the file in cloud storage
        '''

        file_path = os.path.join(self.temp_path, filename)
        f = open(file_path, 'w')
        f.write(msg)
        f.close()
        upload_file(self.bucket_name, file_path, folder)