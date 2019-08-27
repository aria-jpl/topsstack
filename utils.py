import os
import sys
import shutil
import json
import re

from datetime import datetime
from osgeo import ogr, osr


# copied from stitch_ifgs.get_union_polygon()
def get_union_polygon(ds_files):
    """
    Get GeoJSON polygon of union of IFGs.
    :param ds_files: list of .dataset.json files, which have the 'location' key
    :return: geojson of merged bbox
    """

    geom_union = None
    for ds_file in ds_files:
        f = open(ds_file)
        ds = json.load(f)
        geom = ogr.CreateGeometryFromJson(json.dumps(ds['location'], indent=2, sort_keys=True))
        if geom_union is None:
            geom_union = geom
        else:
            geom_union = geom_union.Union(geom)
    return json.loads(geom_union.ExportToJson()), geom_union.GetEnvelope()


def get_dataset_met_json_files(cxt):
    """
    returns 2 lists: file paths for dataset.json files and met.json files
    :param cxt: json from _context.json
    :return: list[str], list[str]
    """
    pwd = os.getcwd()
    localize_urls = cxt['localize_urls']

    met_files, ds_files = [], []
    for localize_url in localize_urls:
        local_path = localize_url['local_path']
        slc_id = local_path.split('/')[0]
        slc_path = os.path.join(pwd, slc_id, slc_id)

        ds_files.append(slc_path + '.dataset.json')
        met_files.append(slc_path + '.met.json')
    return ds_files, met_files


def get_scenes(cxt):
    """
    gets all SLC scenes for the stack
    :param cxt: contents for _context.json
    :return: list of scenes
    """
    localize_urls = cxt['localize_urls']
    all_scenes = set()
    for localize_url in localize_urls:
        local_path = localize_url['local_path']
        slc_id = local_path.split('/')[0]
        all_scenes.add(slc_id)
    return sorted(list(all_scenes))


def get_min_max_timestamps(scenes_ls):
    """
    returns the min timestamp and max timestamp of the stack
    :param scenes_ls: list[str] all slc scenes in stack
    :return: (str, str) 2 timestamp strings, ex. 20190518T161611
    """
    timestamps = set()

    regex_pattern = r'(\d{8}T\d{6}).(\d{8}T\d{6})'
    for scene in scenes_ls:
        matches = re.search(regex_pattern, scene)
        if not matches:
            raise Exception("regex %s was unable to match with SLC id %s" % (regex_pattern, scene))

        slc_timestamps = (matches.group(1), matches.group(2))
        timestamps = timestamps.union(slc_timestamps)

    min_timestamp = min(timestamps)
    max_timestamp = max(timestamps)
    return min_timestamp.replace('T', ''), max_timestamp.replace('T', '')


def create_list_from_keys_json_file(json_files, *args):
    """
    gets all key values in each .json file and returns a sorted array of values
    :param json_files: list[str]
    :return: list[]
    """
    values = set()
    for json_file in json_files:
        f = open(json_file)
        data = json.load(f)
        for arg in args:
            value = data[arg]
            values.add(value)
    return sorted(list(values))


def camelcase_to_underscore(name):
    s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
    return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()


def get_key_and_convert_to_underscore(json_file_paths, key):
    """
    read through all the json files in file paths, get the first occurrence of key and convert it to underscore
    :param json_file_paths: list[str]
    :param key: str
    :return: key and value
    """
    for json_file in json_file_paths:
        f = open(json_file)
        data = json.load(f)
        if key in data.keys():
            underscore_key = camelcase_to_underscore(key)
            return underscore_key, data[key]
    return None, None


def generate_dataset_json_data(dataset_json_files, version):
    """
    :param cxt: _context.json file
    :param dataset_json_files: list[str] all file paths of SLC's .dataset.json files
    :param version: str: version, ex. v1.0
    :return: dict
    """
    dataset_json_data = dict()
    dataset_json_data['version'] = version

    sensing_timestamps = create_list_from_keys_json_file(dataset_json_files, 'starttime', 'endtime')
    dataset_json_data['starttime'] = min(sensing_timestamps)
    dataset_json_data['endtime'] = max(sensing_timestamps)

    geojson, image_corners = get_union_polygon(dataset_json_files)
    dataset_json_data['location'] = geojson

    return dataset_json_data


def generate_met_json_data(cxt, met_json_file_paths, dataset_json_files, version):
    """
    :param cxt: _context.json file
    :param met_json_file_paths: list[str] all file paths of SLC's .met.json files
    :param dataset_json_files: list[str] all file paths of SLC's .dataset.json files
    :param version: str: version, ex. v1.0
    :return: dict
    """
    met_json_data = {
        'processing_start': os.environ['PROCESSING_START'],
        'processing_stop': datetime.now().strftime('%Y-%m-%dT%H:%M:%S'),
        'version': version
    }

    first_occurrence_keys = [
        'direction',
        'orbitNumber',
        'trackNumber',
        'sensor',
        'platform'
    ]
    for key in first_occurrence_keys:
        key, value = get_key_and_convert_to_underscore(met_json_file_paths, key)
        met_json_data[key] = value

    orbit_cycles = create_list_from_keys_json_file(met_json_file_paths, 'orbitCycle')
    met_json_data['orbit_cycles'] = orbit_cycles

    # generating bbox
    geojson, image_corners = get_union_polygon(dataset_json_files)
    coordinates = geojson['coordinates'][0]
    for coordinate in coordinates:
        coordinate[0], coordinate[1] = coordinate[1], coordinate[0]
    met_json_data['bbox'] = coordinates

    # list of SLC scenes
    scenes = get_scenes(cxt)
    met_json_data['scenes'] = scenes
    met_json_data['scene_count'] = len(scenes)

    # getting timestamps
    sensing_timestamps = create_list_from_keys_json_file(dataset_json_files, 'starttime', 'endtime')
    met_json_data['sensing_start'] = min(sensing_timestamps)
    met_json_data['sensing_stop'] = max(sensing_timestamps)
    met_json_data['timesteps'] = sensing_timestamps

    # additional information
    met_json_data['dataset_type'] = 'stack'

    return met_json_data
