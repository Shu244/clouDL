import argparse
import json
import gcp_interactions as gcp
import strings


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
    if len(exts_list) < 3 or exts_list[-1] != 'gz' or exts_list[-2] != 'tar':
        raise ValueError("Data path must be archived (.tar) and compressed (.zip)")

    gcp.upload_file(bucket_name, data_path, strings.data)


def move_access_token(bucket_name, access_token_pth):
    print(
        '''
        Moving token to bucket: 
        -bucket name: {0}
        -access_token_path: {1}
        '''.format(bucket_name, access_token_pth))

    gcp.upload_file(bucket_name, access_token_pth, strings.secrets)


def rmvms(bucket_name, folder_name):
    folder_name = 'VM-progress'

    print(
        '''
        Removing folder containing VM progress. 
        -bucket name: {0}
        -folder_name: {1}
        '''.format(bucket_name, folder_name))

    gcp.delete_all_prefixes(bucket_name, folder_name)


def hyperparamters(bucket_name, hyparams_path, quick_send):
    print(
        '''
        Removes error and recreates progress folder to hold new hyperparamters. 
        -bucket name: {0}
        -hyparams_pth: {1}
        '''.format(bucket_name, hyparams_path))

    print("Removing the vm-progress folder in bucket %s" % bucket_name)
    gcp.delete_all_prefixes(bucket_name, strings.vm_progress)

    print("Removing the shared-errors folder in bucket %s" % bucket_name)
    gcp.delete_all_prefixes(bucket_name, strings.shared_errors)

    hyparam_configs = json.load(open(hyparams_path))
    iters = hyparam_configs["iterations"]
    params = hyparam_configs["params"]
    for index, param in enumerate(params):
        wrapper = {}
        wrapper["param"] = param
        wrapper["current_iter"] = 0
        wrapper["max_iter"] = iters
        quick_send.send(strings.vm_progress_file, json.dumps(wrapper), strings.vm_progress + '/' + str(index))


def build_cluster(project_id, bucket_name, workers, machine_configs_pth, startup_script_pth, quick_send):
    print(
        '''
        Building cluster for training
        -project_id: {0}
        -workers: {1}
        -machine_configs_pth: {2}
        -startup_script_pth: {3}
        -bucket_name: {4}
        '''.format(project_id, workers, machine_configs_pth, startup_script_pth, bucket_name))

    max_workers = workers
    machine_configs = json.load(open(machine_configs_pth))
    startup_script = open(startup_script_pth, 'r').read()

    valid_zones = machine_configs['zones']
    remaining_ranks = list(range(0, workers))

    '''
    Builds VM according to configs with given startup script.
    If VM fails to build, then the zone is removed and we try a different zone. 
    Cycle continues until there are no more zones or all workers have been built
    '''
    while workers > 0 and len(valid_zones) > 0:
        unused_ranks = []
        operations = []
        for idx, rank in enumerate(remaining_ranks):
            zone = valid_zones[idx % len(valid_zones)]
            try:
                operation = gcp.create_instance(project_id, machine_configs, startup_script,
                                                zone, rank, bucket_name)
                operation['vm-rank'] = rank
                operation['testing-zone'] = zone
                operations.append(operation)
            except Exception:
                print("Failed to build a worker in zone %s, trying a different zone" % zone)
                unused_ranks.append(rank)
                valid_zones.remove(zone)

        for op in operations:
            zone = op['testing-zone']
            rank = op['vm-rank']
            passed = gcp. wait_for_operation(project_id, op['name'], zone)
            if passed:
                workers -= 1
            else:
                print("Failed to build a worker in zone %s, trying a different zone" % zone)
                unused_ranks.append(rank)
                valid_zones.remove(zone)
        remaining_ranks = unused_ranks

    # Writing errors to bucket
    if workers != 0:
        print("Writing error to shared errors in the cloud")
        msg = "%d/%d workers built. All desired hyperparemters could not be explored" % \
              (max_workers - len(remaining_ranks), max_workers)
        quick_send.send(strings.cluster_error, msg, strings.shared_errors)

    print("%d/%d workers built" % (max_workers - len(remaining_ranks), max_workers))


def gen_bucket_name(project_id, bucket_name):
    return project_id + '-' + bucket_name


def hr():
    print('----'*20)


# Example:
# python local_cleanup.py stoked-brand-285120 bucket-name1 ./configs.jso  ./startup.sh ./access_token  -b -d ./fake_data.tar.gz -w 2 -l us-central1
if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Prepping buckets and spinning up VMs to train model.")

    parser.add_argument('project_id', help='Project ID')
    parser.add_argument('bucket_name', help='The name of the bucket')
    parser.add_argument('machine_configs_pth', help='The json specifying the configs of the machines used for training')
    parser.add_argument('startup_script_pth', help='The bash start up script to run on the VMs')

    parser.add_argument("-t", '--tokenpth', help='The access_token path is used to download private repo from GitHub')
    parser.add_argument("-b", "--mkbucket", action="store_true", help="Create the bucket")
    parser.add_argument("-d", "--datapth", help="The path of the data to move into the bucket")
    parser.add_argument("-p", "--hyparams", help="The path for the hyperparameter json")
    parser.add_argument("-w", "--workers", type=int, default=1, help="The number of VMs to spin up")
    parser.add_argument("-l", "--location", default="us-central1", help="The location for your bucket")
    parser.add_argument("-m", '--tmppth', default="./tmp", help='The folder to store temporary files before moving to gcloud')

    args = parser.parse_args()

    pid = args.project_id
    bname = gen_bucket_name(pid, args.bucket_name)
    quick_send = gcp.QuickSend(args.tmppth, bname)

    if args.mkbucket:
        make_bucket(bname, args.location)
        hr()

    if args.tokenpth:
        move_access_token(bname, args.tokenpth)
        hr()

    if args.datapth:
        move_data(bname, args.datapth)
        hr()

    if args.hyparams:
        hyperparamters(bname, args.hyparams, quick_send)
        hr()

    build_cluster(pid, bname, args.workers, args.machine_configs_pth, args.startup_script_pth, quick_send)
    hr()
