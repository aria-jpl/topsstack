from utils import *


def read_context():
    with open('_context.json', 'r') as f:
        cxt = json.load(f)
        return cxt


if __name__ == '__main__':
    VERSION = 'v1.0'
    DATASET_NAMING_TEMPLATE = 'coregistered_slcs-{min_timestamp}-{max_timestamp}'
    PWD = os.getcwd()

    # creating list of all SLC .dataset.json and .met.json files
    context_json = read_context()
    dataset_json_files, met_json_files = get_dataset_met_json_files(context_json)

    # getting list of SLC scenes and extracting min max timestamp
    slc_scenes = get_scenes(context_json)
    min_timestamp, max_timestamp = get_min_max_timestamps(slc_scenes)

    # creatin dataset directory
    dataset_name = DATASET_NAMING_TEMPLATE.format(min_timestamp=min_timestamp, max_timestamp=max_timestamp)
    if not os.path.exists(dataset_name):
        os.mkdir(dataset_name)

    # move merged/ master/ slaves/ directory to dataset directory
    move_directories = ['merged', 'master', 'slaves']
    for directory in move_directories:
        shutil.move(directory, dataset_name)

    # move _stdout.txt log file to dataset
    shutil.copyfile('_stdout.txt', os.path.join(dataset_name, '_stdout.txt'))

    # generate .dataset.json data
    dataset_json_data = generate_dataset_json_data(dataset_json_files, VERSION)
    dataset_json_data['label'] = dataset_name
    print(json.dumps(dataset_json_data, indent=2))

    # generate .met.json data
    met_json_data = generate_met_json_data(context_json, met_json_files, dataset_json_files, VERSION)
    print(json.dumps(met_json_data, indent=2))

    # writing .dataset.json to file
    dataset_json_filename = os.path.join(PWD, dataset_name, dataset_name + '.dataset.json')
    with open(dataset_json_filename, 'w') as f:
        json.dump(dataset_json_data, f, indent=2)

    # writing .met.json to file
    met_json_filename = os.path.join(PWD, dataset_name, dataset_name + '.met.json')
    with open(met_json_filename, 'w') as f:
        json.dump(met_json_data, f, indent=2)
