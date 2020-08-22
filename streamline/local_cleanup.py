
"""
Example of using the Compute Engine API to create and delete instances.
Creates a new compute engine instance and uses it to apply a caption to
an image.
    https://cloud.google.com/compute/docs/tutorials/python-guide
For more information, see the README.md under /compute.
"""

import argparse
import os
import time
import glob
import pathlib

# Compute Engine client library
import googleapiclient.discovery
# Cloud storage client library
from google.cloud import storage

from six.moves import input

storage_client = storage.Client()


def list_instances(compute, project, zone):
    result = compute.instances().list(project=project, zone=zone).execute()
    return result['items'] if 'items' in result else None


def create_instance(compute, project, zone, name, bucket):
    # Get the latest Debian Jessie image.
    image_response = compute.images().getFromFamily(
        project='debian-cloud', family='debian-9').execute()
    source_disk_image = image_response['selfLink']

    # Configure the machine
    machine_type = "zones/%s/machineTypes/n1-standard-1" % zone
    startup_script = open(
        os.path.join(
            os.path.dirname(__file__), 'startup-script.sh'), 'r').read()
    image_url = "http://storage.googleapis.com/gce-demo-input/photo.jpg"
    image_caption = "Ready for dessert?"

    config = {
        'name': name,
        'machineType': machine_type,

        # Specify the boot disk and the image to use as a source.
        'disks': [
            {
                'boot': True,
                'autoDelete': True,
                'initializeParams': {
                    'sourceImage': source_disk_image,
                }
            }
        ],

        # Specify a network interface with NAT to access the public internet.
        'networkInterfaces': [{
            'network': 'global/networks/default',
            'accessConfigs': [
                {'type': 'ONE_TO_ONE_NAT', 'name': 'External NAT'}
            ]
        }],

        # Allow the instance to access cloud storage and logging.
        'serviceAccounts': [{
            'email': 'default',
            'scopes': [
                'https://www.googleapis.com/auth/devstorage.read_write',
                'https://www.googleapis.com/auth/logging.write'
            ]
        }],

        # Metadata is readable from the instance and allows you to
        # pass configuration from deployment scripts to instances.
        'metadata': {
            'items': [{
                # Startup script is automatically executed by the
                # instance upon startup.
                'key': 'startup-script',
                'value': startup_script
            }, {
                'key': 'url',
                'value': image_url
            }, {
                'key': 'text',
                'value': image_caption
            }, {
                'key': 'bucket',
                'value': bucket
            }]
        }
    }

    return compute.instances().insert(
        project=project,
        zone=zone,
        body=config).execute()



def delete_instance(compute, project, zone, name):
    return compute.instances().delete(
        project=project,
        zone=zone,
        instance=name).execute()


def wait_for_operation(compute, project, zone, operation):
    print('Waiting for operation to finish...')
    while True:
        result = compute.zoneOperations().get(
            project=project,
            zone=zone,
            operation=operation).execute()

        if result['status'] == 'DONE':
            print("done.")
            if 'error' in result:
                raise Exception(result['error'])
            return result

        time.sleep(1)


def main(project, bucket, zone, instance_name, wait=True):
    compute = googleapiclient.discovery.build('compute', 'v1')

    print('Creating instance.')

    operation = create_instance(compute, project, zone, instance_name, bucket)
    wait_for_operation(compute, project, zone, operation['name'])

    instances = list_instances(compute, project, zone)

    print('Instances in project %s and zone %s:' % (project, zone))
    for instance in instances:
        print(' - ' + instance['name'])

    print("""
Instance created.
It will take a minute or two for the instance to complete work.
Check this URL: http://storage.googleapis.com/{}/output.png
Once the image is uploaded press enter to delete the instance.
""".format(bucket))

    if wait:
        input()

    print('Deleting instance.')

    operation = delete_instance(compute, project, zone, instance_name)
    wait_for_operation(compute, project, zone, operation['name'])


def upload_folder_helper(bucket, src, dest):
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
    :return: None
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


def download_folder(bucket_name, src, dest):
    '''
    Moves content of src folder in GCP into local dest folder.
    For safety, dest must be empty.

    :param bucket: Bucket name
    :param src: Source folder in GCP storage
    :param dest: local destination folder
    :return: None
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


def make_bucket(bucket_name, location):
    print(
        '''
        Making a bucket: 
        -bucket name: {0}
        -location: {1}
        '''.format(bucket_name, location))

    # Will throw error if bucket already exists
    storage_client.create_bucket(bucket_name, location=location)


def move_data(bucket_name, data_path):
    print(
        '''
        Moving data to bucket: 
        -bucket name: {0}
        -data_path: {1}
        '''.format(bucket_name, data_path))

    exts_list = data_path.split('.')
    if len(exts_list) < 3 or exts_list[-1] != 'zip' or exts_list[-2] != 'tar':
        raise ValueError("Data path must be archived (.tar) and compressed (.zip)")

    upload_folder(bucket_name, data_path, 'data/')


def rmvms(project_id):
    print('removing VMs ', project_id)


def build_cluster(project_id, workers, machine_configs_pth, startup_script_pth, location, zone):
    print('building cluster ', project_id, workers, machine_configs_pth, startup_script_pth, location, zone)


def gen_gcp_pth(project_id, *args):
    pth = 'gs://' + project_id
    for arg in args:
        pth += '/' + arg
    return pth


def gen_bucket_name(project_id, bucket_name):
    return project_id + '-' + bucket_name


def hr():
    print('----'*20)


# python local_cleanup.py stoked-brand-285120 test-name config_path startup_path -b -d data_path -c code_path -v -w 2 -l us-central1 -z aZone
if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Prepping buckets and spinning up VMs to train model.")

    parser.add_argument('project_id', help='Project ID')
    parser.add_argument('bucket_name', help='The name of the bucket')
    parser.add_argument('machine_configs_pth', help='The json specifying the configs of the machines used for training')
    parser.add_argument('startup_script_pth', help='The bash start up script to run on the VMs')

    parser.add_argument("-b", "--mkbucket", action="store_true", help="Create the bucket")
    parser.add_argument("-d", "--datapth", help="The path of the data to move into the bucket")
    parser.add_argument("-c", "--codepth", help="The path of the code to move into the bucket")
    parser.add_argument("-v", "--rmvms", action="store_true", help="Remove the VM progress reports")
    parser.add_argument("-w", "--workers", type=int, default=1, help="The number of VMs to spin up")
    parser.add_argument("-l", "--location", default="us-central1", help="The location for your bucket and VMs")
    parser.add_argument("-z", "--zone", default="us-central1-b", help="The recommended zone to add your bucket and VMs")

    args = parser.parse_args()

    pid = args.project_id
    bname = gen_bucket_name(pid, args.bucket_name)

    if args.mkbucket:
        make_bucket(bname, args.location)
        hr()

    if args.datapth:
        move_data(bname, args.datapth)
        hr()

    if args.rmvms:
        rmvms(pid)
        hr()

    build_cluster(pid, args.workers, args.machine_configs_pth, args.startup_script_pth, args.location, args.zone)
    hr()
