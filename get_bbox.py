import os
import json
from math import floor, ceil


def load_context():
    """loads the context file into a dict"""
    try:
        context_file = '_context.json'
        with open(context_file, 'r') as fin:
            context = json.load(fin)
        return context
    except Exception as e:
        raise Exception('unable to parse _context.json from work directory: %s' % e)


def get_user_input_bbox(ctx_file):
    """
    :param ctx_file: dictionary from cxt file
    :return: void
    """
    min_lat = ctx_file['min_lat']
    max_lat = ctx_file['max_lat']
    min_lon = ctx_file['min_lon']
    max_lon = ctx_file['max_lon']

    min_lat_lo = floor(min_lat)
    max_lat_hi = ceil(max_lat)
    min_lon_lo = floor(min_lon)
    max_lon_hi = ceil(max_lon)

    return min_lat, max_lat, min_lon, max_lon, min_lat_lo, max_lat_hi, min_lon_lo, max_lon_hi


def get_minimum_bounding_rectangle():
    cwd = os.getcwd()
    slc_ids = [x for x in os.listdir('.') if os.path.isdir(x) and '_SLC__' in x]

    all_lats = []
    all_lons = []
    for slc in slc_ids:
        slc_met_json = slc + '.met.json'

        with open(os.path.join(cwd, slc, slc_met_json), 'r') as f:
            data = json.load(f)
            bbox = data['bbox']
            for coord in bbox:
                all_lats.append(coord[0])
                all_lons.append(coord[1])

    min_lat = min(all_lats) + 0.2
    max_lat = max(all_lats) - 0.1
    min_lon = min(all_lons)
    max_lon = max(all_lons)

    min_lat_lo = floor(min_lat)
    max_lat_hi = ceil(max_lat)
    min_lon_lo = floor(min_lon)
    max_lon_hi = ceil(max_lon)

    return min_lat, max_lat, min_lon, max_lon, min_lat_lo, max_lat_hi, min_lon_lo, max_lon_hi


def main():
    ctx = load_context()
    # min_lat, max_lat, min_lon, max_lon = ctx['region_of_interest']

    if ctx['min_lat'] != "" or ctx['max_lat'] != "" or ctx['min_lon'] != "" or ctx['max_lon'] != "":
        # if any values are present in _context.json we can assume user put them in manually
        bbox_data = get_user_input_bbox(ctx)
    else:
        # if user did not define ANY lat lons
        bbox_data = get_minimum_bounding_rectangle()

    out = ' '.join(str(e) for e in bbox_data)
    print(out)


# TODO: take master date as user input
if __name__ == '__main__':
    main()
