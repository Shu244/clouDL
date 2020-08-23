import argparse
import json
from . import gcp_interactions as gcp


def make_bucket(bucket_name, location):
    print(
        '''
        Making a bucket: 
        -bucket name: {0}
        -location: {1}
        '''.format(bucket_name, location))

    gcp.make_bucket(bucket_name, location)


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

    gcp.upload_file(bucket_name, data_path, 'data')


def move_access_token(bucket_name, access_token_pth):
    print(
        '''
        Moving token to bucket: 
        -bucket name: {0}
        -access_token_path: {1}
        '''.format(bucket_name, access_token_pth))

    gcp.upload_file(bucket_name, access_token_pth, 'secrets')


def rmvms(bucket_name):
    folder_name = 'VM-progress'

    print(
        '''
        Removing folder containing VM progress. 
        -bucket name: {0}
        -folder_name: {1}
        '''.format(bucket_name, folder_name))

    gcp.delete_all_prefixes("bucket_name", folder_name)


def validate_workers(project_id, op_zone_pairs):
    invalid_zones = []
    num_workers_failed = 0
    for operation, zone in op_zone_pairs:
        result = gcp.wait_for_operation(project_id, operation, zone)
        if not result:
            invalid_zones.append(zone)
            num_workers_failed += 1

    print('{0} workers failed in zones {1}'.format(num_workers_failed, invalid_zones))
    return num_workers_failed, invalid_zones

def build_cluster_helper(project_id, workers, machine_configs, startup_script, invalid_zones=[]):
    allowed_zones = machine_configs['zones']

    if len(allowed_zones) == len(invalid_zones):
        print('No zones left, {0} workers cannot be created'.format(workers))
        return False

    if workers == 0:
        print('All VMs successfully created')
        return True

    valid-zones
    op_zone_pairs = []
    for i in range(0, workers):
        zone =
        operation = gcp.create_instance(...todo...)

    # Retrying failed workers
    num_workers_failed, invalid_zones = validate_workers(project_id, op_zone_pairs)
    build_cluster(project_id, num_workers_failed, machine_configs, startup_script, invalid_zones)


def build_cluster(project_id, workers, machine_configs_pth, startup_script_pth):
    print(
        '''
        Building cluster for training
        -project_id: {0}
        -workers: {1}
        -machine_configs_pth: {2}
        -startup_script_pth: {3}
        '''.format(project_id, workers, machine_configs_pth, startup_script_pth))

    machine_configs = json.load(open(machine_configs_pth))
    startup_script = open(startup_script_pth, 'r').read()
    build_cluster_helper(project_id, workers, machine_configs. starup_script)

def gen_bucket_name(project_id, bucket_name):
    return project_id + '-' + bucket_name


def hr():
    print('----'*20)


# python local_cleanup.py stoked-brand-285120 test-name config_path startup_path -b -d data_path -c code_path -v -w 2 -l us-central1
if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Prepping buckets and spinning up VMs to train model.")

    parser.add_argument('project_id', help='Project ID')
    parser.add_argument('bucket_name', help='The name of the bucket')
    parser.add_argument('machine_configs_pth', help='The json specifying the configs of the machines used for training')
    parser.add_argument('startup_script_pth', help='The bash start up script to run on the VMs')
    parser.add_argument('token_pth', help='The access_token.py path used to download private repo from GitHub')

    parser.add_argument("-b", "--mkbucket", action="store_true", help="Create the bucket")
    parser.add_argument("-d", "--datapth", help="The path of the data to move into the bucket")
    parser.add_argument("-v", "--rmvms", action="store_true", help="Remove the VM progress reports")
    parser.add_argument("-w", "--workers", type=int, default=1, help="The number of VMs to spin up")
    parser.add_argument("-l", "--location", default="us-central1", help="The location for your bucket")

    args = parser.parse_args()

    pid = args.project_id
    bname = gen_bucket_name(pid, args.bucket_name)

    if args.mkbucket:
        make_bucket(bname, args.location)
        hr()

    if args.access_token:
        move_access_token(bname, args.token_pth)
        hr()

    if args.datapth:
        move_data(bname, args.datapth)
        hr()

    if args.rmvms:
        rmvms(pid)
        hr()

    build_cluster(pid, args.workers, args.machine_configs_pth, args.startup_script_pth)
    hr()
