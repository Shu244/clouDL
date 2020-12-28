import pathlib
import glob
import json
import time
import os

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
            upload_folder_helper(bucket, local_obj, os.path.join(dest, basename))
        else:
            remote_path = os.path.join(dest, basename)
            blob = bucket.blob(remote_path)
            blob.upload_from_filename(local_obj)


def upload_folder(bucket_name, src, dest):
    '''
    Moves the contents of the src folder inside dest folder.
    This function should not be used to push training data.
    Instead, archive and zip training folder so it can be pushed as one file
    For safety, dest must be empty
    Raises FileNotFoundError when src file(s) does not exists.

    :param bucket_name: name of bucket
    :param src: source folder
    :param dest: destination folder
    '''
    if not os.path.isdir(src) or len(os.listdir(src)) == 0:
        raise ValueError("src folder must exist and not be empty")

    bucket = storage_client.bucket(bucket_name)

    if dest[-1] != '/':
        dest = dest + '/'

    # Ensuring empty dest folder
    blobs = bucket.list_blobs(prefix=dest)
    for blob in blobs:
        # Ignoring the folder itself
        if not blob.name[len(dest):]:
            continue
        raise ValueError("Dest folder must be empty")

    upload_folder_helper(bucket, src, dest)


def upload_file(bucket_name, src, dest):
    '''
    Upload a file to Google cloud storage
    Raises FileNotFoundError if source file does not exists.

    :param bucket_name: Bucket name
    :param src: Path of the file to upload
    :param dest: Path of the folder of where to upload file
    '''

    bucket = storage_client.bucket(bucket_name)
    remote_path = os.path.join(dest, os.path.basename(src))
    blob = bucket.blob(remote_path)
    blob.upload_from_filename(src)


def download_folder(bucket_name, src, dest, ignore_filename=None):
    '''
    Moves content of src folder in GCP into local dest folder.
    For safety, dest must be empty.

    :param bucket: Bucket name
    :param src: Source folder in GCP storage
    :param dest: local destination folder
    :param ignore_filename: files to not move in the src folder
    '''

    # if not os.path.isdir(dest) or len(os.listdir(dest)) != 0:
    #     raise ValueError("Dest folder must exists and be empty")

    if src[-1] != '/':
        src = src + '/'

    bucket = storage_client.bucket(bucket_name)
    blobs = bucket.list_blobs(prefix=src)  # Get list of files
    for blob in blobs:
        # name will be in the format of src/folder1/.../folderN/file.ext
        name = blob.name

        if ignore_filename and os.path.basename(name) == ignore_filename:
            continue

        # Ignoring the path to the src folder
        no_path = name[len(src):]
        if not no_path:
            continue

        local_path = os.path.join(dest, no_path)
        if no_path.count('/') > 0:
            # Create nested directories
            only_dir = local_path[:local_path.rfind('/')]
            if not os.path.isdir(only_dir):
                pathlib.Path(only_dir).mkdir(parents=True, exist_ok=True)

        # The blob is a folder in the cloud
        if os.path.isdir(local_path):
            continue

        blob.download_to_filename(local_path)


def download_file(bucket_name, src, dest):
    '''
    Downloads a file from Google Cloud Storage.
    Raises FileNotFoundError when necessary.

    :param bucket_name: Name of the bucket
    :param src: Path of the file
    :param dest: Path of the folder to keep the file.
    '''
    filename = os.path.basename(src)
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(src)
    blob.download_to_filename(os.path.join(dest, filename))


def move_cloud_folder(bucket_name, src, dest, ignore_filename=None):
    '''
    Moves the contents of the src cloud folder to the dest Cloud folder by
    renaming each blob in the src folder.

    :param bucket_name: Bucket name
    :param src: Source folder
    :param dest: Destination folder
    :param ignore_filename: files to not move in the src folder
    '''

    if src[-1] != '/':
        src = src + '/'

    bucket = storage_client.bucket(bucket_name)
    blobs = bucket.list_blobs(prefix=src)  # Get list of files
    for blob in blobs:
        # name will be in the format of src/folder1/.../folderN/file.ext
        name = blob.name

        if ignore_filename and os.path.basename(name) == ignore_filename:
            continue

        # Ignoring the path to the src folder
        no_src = name[len(src):]
        if not no_src:
            continue

        new_name = os.path.join(dest, no_src)
        bucket.rename_blob(blob, new_name)


def get_folder_names(bucket_name, src):
    '''
    Gets all the folder names in the first level of the src folder
    :param bucket_name: Bucket name
    :param src: Source folder
    '''

    if src[-1] != '/':
        src = src + '/'

    bucket = storage_client.bucket(bucket_name)
    blobs = bucket.list_blobs(prefix=src)  # Get list of files
    folder_names = set({})
    for blob in blobs:
        name = blob.name
        no_src = name[len(src):]
        folder_delimiter_index = no_src.find('/')
        if folder_delimiter_index == -1:
            continue
        folder_name = no_src[:folder_delimiter_index]
        if folder_name:
            folder_names.add(folder_name)
    return folder_names


def stream_download_str(bucket_name, src):
    '''
    Download a blob from GCP as a string object

    :param bucket_name: Bucket name
    :param src: Source to download from
    '''

    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(src)
    return blob.download_as_string()


def stream_download_json(bucket_name, src):
    '''
    Download a blob from GCP as a json/dict object

    :param bucket_name: Bucket name
    :param src: Source to download from
    '''

    str = stream_download_str(bucket_name, src)
    return json.loads(str)


def stream_upload_str(bucket_name, src, dest):
    '''
    Upload a string object to GCP

    :param bucket_name: Bucket name
    :param src: Source string
    :param dest: Destination to save file (ex: vm-progress/filename.json)
    '''

    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(dest)
    blob.upload_from_string(src)


def delete_all_prefixes(bucket_name, prefix):
    '''
    Delete folder and all of its content in Google Cloud Storage

    :param bucket_name: Bucket name
    :param folder: Folder name in Cloud
    '''

    bucket = storage_client.bucket(bucket_name)
    blobs = bucket.list_blobs(prefix=prefix)
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
    machine_type = "zones/%s/machineTypes/n1-standard-%d" % (zone, configs["cpu_count"])
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
                    'sourceImage': configs['sourceImage'],
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

    if configs["gpu_count"] > 0:
        config["guestAccelerators"] = [
            {
                "acceleratorCount": configs["gpu_count"],
                "acceleratorType": accelerator_type
            }
        ],

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
    def __init__(self, bucket_name):
        self.bucket_name = bucket_name

    def send(self, filename, msg, folder):
        file_path = os.path.join(folder, filename)
        stream_upload_str(self.bucket_name, msg, file_path)
