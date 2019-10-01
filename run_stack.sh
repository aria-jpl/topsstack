#!/usr/bin/env bash

# Saving the processing start time for .met.json file
export PROCESSING_START=$(date +%FT%T)

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
dem.py -a stitch -b $MINLAT_LO $MAXLAT_HI $MINLON_LO $MAXLON_HI -r -s 1 -c -f


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
if [[ -f $WGS84 ]]; then
    echo fixImageXml.py -f -i $WGS84
    fixImageXml.py -f -i $WGS84
else
    echo $WGS84 does not exist!
    exit 1
fi


# Getting MASTER_DATE environment variable
export MASTER_DATE=$(python get_master_date.py)

# Create stack processor run scripts (after checking for MASTER DATE)
if [[ "$MASTER_DATE" ]]; then
	echo "MASTER_DATE exists: ${MASTER_DATE}"
	echo stackSentinel.py -s zip/ -d $WGS84 -a AuxDir/ -m $MASTER_DATE -o Orbits -b "$MINLAT $MAXLAT $MINLON $MAXLON" -W slc
	stackSentinel.py -s zip/ -d $WGS84 -a AuxDir/ -m $MASTER_DATE -o Orbits -b "$MINLAT $MAXLAT $MINLON $MAXLON" -W slc
else
	echo "MASTER_DATE DOES NOT EXIST"
	echo stackSentinel.py -s zip/ -d $WGS84 -a AuxDir/ -o Orbits -b "$MINLAT $MAXLAT $MINLON $MAXLON" -W slc
	stackSentinel.py -s zip/ -d $WGS84 -a AuxDir/ -o Orbits -b "$MINLAT $MAXLAT $MINLON $MAXLON" -W slc
fi


# allowing use of the gdal_translate command
export PATH="$PATH:/opt/conda/bin/"

# Process stack processor run scripts in order
nprocs=8
for (( i=1 ; i <= 10 ; i++ )) ; do
    echo run.py -i ./run_files/run_${i}_* -p $nprocs
    run.py -i ./run_files/run_${i}_* -p $nprocs
done

# Publishing dataset after stack processor completes
python /home/ops/verdi/ops/topsstack/create_dataset.py
