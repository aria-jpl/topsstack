#!/usr/bin/env bash

source $HOME/.bash_profile

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
dem.py -a stitch -b $MINLAT_LO $MAXLAT_HI $MINLON_LO $MAXLON_HI -r -s 1 -c -f >&1 | tee dem.txt

if [[ -f dem.txt ]]; 
then
    WGS84=`awk '/wgs84/ {print $NF;exit}' dem.txt`
    if [[ -f "${WGS84}" ]]; 
    then
	echo "Found wgs84 file: ${WGS84}"
        echo "fixImageXml.py -f -i ${WGS84}"
        fixImageXml.py -f -i ${WGS84}
    else
        echo "NO WGS84 FILE FOUND" 
        exit 1
    fi
fi


## Fix DEM
#if [[ $MINLAT_LO < 0 ]]; then
#    MINLAT_LO=$(( -$MINLAT_LO ))
#    NS_LO=S
#else
#    NS_LO=N
#fi
#if [[ $MAXLAT_HI < 0 ]]; then
#    MAXLAT_HI=$(( -$MAXLAT_HI ))
#    NS_HI=S
#else
#    NS_HI=N
#fi
#if [[ $MINLON_LO < 0 ]]; then
#    MINLON_LO=$(( -$MINLON_LO ))
#    EW_LO=W
#else
#    EW_LO=E
#fi
#if [[ $MAXLON_HI < 0 ]]; then
#    MAXLON_HI=$(( -$MAXLON_HI ))
#    EW_HI=W
#else
#    EW_LO=E
#fi
#WGS84=demLat_${NS_LO}${MINLAT_LO}_${NS_HI}${MAXLAT_HI}_Lon_${EW_LO}${MINLON_LO}_${EW_HI}${MAXLON_HI}.dem.wgs84
#if [[ -f $WGS84 ]]; then
#    echo fixImageXml.py -f -i $WGS84
#    fixImageXml.py -f -i $WGS84
#else
#    echo $WGS84 does not exist!
#    exit 1
#fi


# Getting MASTER_DATE environment variable
export MASTER_DATE=$(python ${PGE_BASE}/get_master_date.py)

# Create stack processor run scripts (after checking for MASTER DATE)
if [[ "$MASTER_DATE" ]]; then
	echo "MASTER_DATE exists: ${MASTER_DATE}"
	echo stackSentinel.py -s zip/ -d ${WGS84} -a AuxDir/ -m ${MASTER_DATE} -o Orbits -b "${MINLAT} ${MAXLAT} ${MINLON} ${MAXLON}" -W slc
	stackSentinel.py -s zip/ -d $WGS84 -a AuxDir/ -m $MASTER_DATE -o Orbits -b "$MINLAT $MAXLAT $MINLON $MAXLON" -W slc
else
	echo "MASTER_DATE DOES NOT EXIST"
	echo stackSentinel.py -s zip/ -d $WGS84 -a AuxDir/ -o Orbits -b "$MINLAT $MAXLAT $MINLON $MAXLON" -W slc
	stackSentinel.py -s zip/ -d $WGS84 -a AuxDir/ -o Orbits -b "$MINLAT $MAXLAT $MINLON $MAXLON" -W slc
fi


# allowing use of the gdal_translate command
export PATH="$PATH:/opt/conda/bin/"


# Jungkyo's GNU parallel for running all steps
###########################################################################
## STEP 1 ##
start=`date +%s`
cat run_files/run_1_unpack_slc_topo_master |head -1 | sh
Num=`cat run_files/run_1_unpack_slc_topo_master | wc | awk '{print $1}'`
echo $Num
echo "cat run_files/run_1_unpack_slc_topo_master | tail -$Num | parallel -j+10 --eta --load 100%"
cat run_files/run_1_unpack_slc_topo_master | tail -$Num | parallel -j+10 --eta --load 100%
end=`date +%s`
runtime1=$((end-start))
echo $runtime1

## STEP 2 ##
start=`date +%s`
echo "cat run_files/run_2_average_baseline | parallel -j+10 --eta --load 100%"
cat run_files/run_2_average_baseline | parallel -j+10 --eta --load 100%
end=`date +%s`

runtime2=$((end-start))
echo $runtime2

## STEP 3 ##
start=`date +%s`
echo "sh run_files/run_3_extract_burst_overlaps"
sh run_files/run_3_extract_burst_overlaps
end=`date +%s`
runtime3=$((end-start))
echo $runtime3

## STEP 4 ##
start=`date +%s`
echo "cat run_files/run_4_overlap_geo2rdr_resample  | parallel -j+10 --eta --load 100%"
cat run_files/run_4_overlap_geo2rdr_resample  | parallel -j+10 --eta --load 100%
end=`date +%s`
runtime4=$((end-start))
echo $runtime4

## STEP 5 ##
start=`date +%s`
echo "cat run_files/run_5_pairs_misreg  | parallel -j+10 --eta --load 100%"
cat run_files/run_5_pairs_misreg  | parallel -j+10 --eta --load 100%
end=`date +%s`
runtime5=$((end-start))
echo $runtime5

## STEP 6 ##
start=`date +%s`
echo "sh run_files/run_6_timeseries_misreg"
sh run_files/run_6_timeseries_misreg
end=`date +%s`
runtime6=$((end-start))
echo $runtime6

## STEP 7 ##
start=`date +%s`
echo "cat run_files/run_7_geo2rdr_resample   | parallel -j+10 --eta --load 100%"
cat run_files/run_7_geo2rdr_resample   | parallel -j+10 --eta --load 100%
end=`date +%s`
runtime7=$((end-start))
echo $runtime7

## STEP 8##
start=`date +%s`
echo "sh run_files/run_8_extract_stack_valid_region"
sh run_files/run_8_extract_stack_valid_region
end=`date +%s`
runtime8=$((end-start))
echo $runtime8


## STEP 9 ##
start=`date +%s`
echo "cat run_files/run_9_merge  | parallel -j+10 --eta --load 100%"
cat run_files/run_9_merge  | parallel -j+10 --eta --load 100%
end=`date +%s`
runtime9=$((end-start))
echo $runtime9

## STEP 9 ##
start=`date +%s`
echo "cat run_files/run_10_grid_baseline  | parallel -j+10 --eta --load 100%"
cat run_files/run_10_grid_baseline  | parallel -j+10 --eta --load 100%
end=`date +%s`
runtime10=$((end-start))
echo $runtime10

## SUMMARY ##
echo "@@@@ SUMMARY  @@@@@@"
echo "@ Step 1:  $runtime1"
echo "@ Step 2:  $runtime2"
echo "@ Step 3:  $runtime3"
echo "@ Step 4:  $runtime4"
echo "@ Step 5:  $runtime5"
echo "@ Step 6:  $runtime6"
echo "@ Step 7:  $runtime7"
echo "@ Step 8:  $runtime8"
echo "@ Step 9:  $runtime9"
echo "@ Step 10:  $runtime10"
###########################################################################


# Publishing dataset after stack processor completes
python /home/ops/verdi/ops/topsstack/create_dataset.py
