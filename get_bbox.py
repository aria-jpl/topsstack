import json
from math import floor, ceil


def load_context():
    '''loads the context file into a dict'''
    try:
        context_file = '_context.json'
        with open(context_file, 'r') as fin:
            context = json.load(fin)
        return context
    except:
        raise Exception('unable to parse _context.json from work directory')

def main():
    ctx = load_context()
    min_lat, max_lat, min_lon, max_lon = ctx['region_of_interest']
    min_lat_lo = floor(min_lat)
    max_lat_hi = ceil(max_lat)
    min_lon_lo = floor(min_lon)
    max_lon_hi = ceil(max_lon)
    out = ' '.join(str(e) for e in (min_lat, max_lat, min_lon, max_lon,
                                    min_lat_lo, max_lat_hi,
                                    min_lon_lo, max_lon_hi))
    print(out)
    

if __name__ == '__main__':
    main()
