import os
import shutil
import json
import hashlib
import re
from osgeo import ogr, osr


def read_context():
    with open('_context.json', 'r') as f:
        cxt = json.load(f)
        return cxt


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
    gets all SLC senes for the stack
    :param cxt: contents for _context.json
    :return: list of scenes
    """
    localize_urls = cxt['localize_urls']
    all_scenes = []
    for localize_url in localize_urls:
        local_path = localize_url['local_path']
        slc_id = local_path.split('/')[0]
        all_scenes.append(slc_id)
    return all_scenes


def get_min_max_timestamps(scenes_ls):
    """
    returns the min timestamp and max timestamp of the stack
    :param scene_ls: list[str] all slc scenes in stack
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
    return min(timestamps), max(timestamps)


"""
steps: 
    1. coregistered_slcs
    2. create datasets.json
        {
          "version": "v1.0",
          "label": "Sacramento Valley",
          "location": {
            "type": "polygon",
            "coordinates": [
              [
                [-122.9059682940358,40.47090915967475],
                [-121.6679748715316,37.84406528996276],
                [-120.7310161872557,38.28728069813177],
                [-121.7043611684245,39.94137004454238],
                [-121.9536916840953,40.67097860759095],
                [-122.3100379696548,40.7267890636145],
                [-122.7640648263371,40.5457010812299],
                [-122.9059682940358,40.47090915967475]
              ]
            ]
          },
          "starttime": "1970-01-01T00:00:00",
          "endtime": "2016-01-01T00:00:00"
        }
    3. create met.json
"""


if __name__ == '__main__':
    from pprint import pprint

    VERSION = 'v1.0'
    DATASET_NAMING_TEMPLATE = 'coregistered_slcs_{min_timestamp}_{max_timestamp}'

    context_json = read_context()
    dataset_json_files, met_json_files = get_dataset_met_json_files(context_json)
    pprint(dataset_json_files)
    pprint(met_json_files)

    test_geojson, image_corners = get_union_polygon(dataset_json_files)
    pprint(test_geojson)
    pprint(image_corners)

    slc_scenes = get_scenes(context_json)
    pprint(slc_scenes)

    min_timestamp, max_timestamp = get_min_max_timestamps(slc_scenes)

    dataset_name = DATASET_NAMING_TEMPLATE.format(min_timestamp=min_timestamp, max_timestamp=max_timestamp)
    if not os.path.exists(dataset_name):
        os.mkdir(dataset_name)

    # move merged/ master/ slaves/ directory to dataset directory
    move_directories = ['merged', 'master', 'slaves']
    for directory in move_directories:
        shutil.move(directory, dataset_name)

    # generate .dataset.json and .met.json
