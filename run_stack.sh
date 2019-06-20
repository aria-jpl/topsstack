#!/usr/bin/env bash

set -e 
PGE_BASE=$(cd `dirname ${BASH_SOURCE}`; pwd)

# Get user's bounding box coordinates and outer box with integer coordinates
TOKENS=$(python ${PGE_BASE}/get_bbox.py _context.json)
IFS=" "
read MINLAT MAXLAT MINLON MAXLON MINLAT_LO MAXLAT_HI MINLON_LO MAXLON_HI <<< $TOKENS

echo "Coords:"
echo $MINLAT $MAXLAT $MINLON $MAXLON $MINLAT_LO $MAXLAT_HI $MINLON_LO $MAXLON_HI

# Prep SLCs
mkdir zip
mv S1*/*.zip zip

# Get DEM
echo dem.py -a stitch -b $MINLAT_LO $MAXLAT_HI $MINLON_LO $MAXLON_HI -r -s 1 -c -f


# Fix DEM
if [[ $MINLAT_LO < 0 ]]; then
    MINLAT_LO=$(( -$MINLAT_LO ))
    NS_LO=S
else
    NS_LO=N
fi
if [[ $MAXLAT_HI < 0 ]]; then
    MAXLAT_HI=$(( -$MAXLAT_HI ))
    NS_HI=S
else
    NS_HI=N
fi
if [[ $MINLON_LO < 0 ]]; then
    MINLON_LO=$(( -$MINLON_LO ))
    EW_LO=W
else
    EW_LO=E
fi
if [[ $MAXLON_HI < 0 ]]; then
    MAXLON_HI=$(( -$MAXLON_HI ))
    EW_HI=W
else
    EW_LO=E
fi
WGS84=demLat_${NS_LO}${MINLAT_LO}_${NS_HI}${MAXLAT_HI}_Lon_${EW_LO}${MINLON_LO}_${EW_HI}${MAXLON_HI}.dem.wgs84
if [[ -z $WGS84 ]]; then
    echo fixImageXml.py -f -i $WGS84
else
    echo $WGS84 does not exist!
    exit 1
fi
# Create stack processor run scripts
echo stackSentinel.py -s zip/ -d $WGS84 -a AuxDir/ -o Orbits -b \'$MINLAT $MAXLAT $MINLON $MAXLON\' -W slc

# Process stack processor run scripts in order
# Do the following in a loop?  
exit 0
source ./run_files/run_1_unpack_slc_topo_master
source ./run_files/run_2_average_baseline
source ./run_files/run_3_extract_burst_overlaps
source ./run_files/run_4_overlap_geo2rdr_resample
source ./run_files/run_5_pairs_misreg
source ./run_files/run_6_timeseries_misreg
source ./run_files/run_7_geo2rdr_resample
source ./run_files/run_8_extract_stack_valid_region
source ./run_files/run_9_merge
source ./run_files/run_10_grid_baseline
