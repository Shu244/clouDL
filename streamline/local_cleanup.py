
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

import googleapiclient.discovery
from six.moves import input

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


def make_bucket(bucket_pth, location, zone):
    print('Making a bucket ', bucket_pth, location, zone)


def cp(src, dest):
    print('Copying to bucket ', src, dest)


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


if __name__ == '__main__':
    # bash local_cleanup.sh -n <bucket_name> [-b] [-d <data_path>] [-c <code_path>] [-v] [-w <num_workers>]
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
        make_bucket(gen_gcp_pth(bname), args.location, args.zone)

    if args.datapth:
        cp(args.datapth, gen_gcp_pth(bname, "data/"))

    if args.codepth:
        cp(args.codepth, gen_gcp_pth(bname, "code/"))

    if args.rmvms:
        rmvms(pid)

    build_cluster(pid, args.workers, args.machine_configs_pth, args.startup_script_pth, args.location, args.zone)
