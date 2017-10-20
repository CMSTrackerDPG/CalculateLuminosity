#!/usr/bin/env bash

#--------------------------------------------------
# Instructions 
#--------------------------------------------------

if [[ $# -eq 0 ]]; then 
    printf "NAME\n\tcomputeLuminosity.sh - Compute integrated luminosity for GOOD and BAD runs set by the tracker in a given range of runs (min and max included)\n"
    printf "\nSYNOPSIS\n"
    printf "\n\t%-5s\n" "./computeLuminosity.sh [RUNMIN] [RUNMAX] [BEAM_TYPE]"
    printf "\n\t%-5s\n" "[BEAM_TYPE] can be 'pp' or 'HI'. This will change the beam energy threshold in the script, putting 6500 GeV for 'pp' and 4000 GeV for 'HI'. In some cases, LHC runs at not standard energy and therefore one should put the energy wanted, in GeV, in this parameter (example: 2000). If nothing is specified it will be pp (6500) by default"
    printf "\nEXAMPLES OF USE\n"
    printf "\n\t%-5s\n" "./computeLuminosity.sh 270000 280000  --  compute luminosity between run 270000 and 280000 (both included) in pp collisions mode (i.e. beam energy threshold of 6500 GeV)"
    printf "\n\t%-5s\n" "./computeLuminosity.sh 270000 280000 pp  --  same as above"
    printf "\n\t%-5s\n" "./computeLuminosity.sh 270000 280000 HI  --  same as above but in HI collisions mode (i.e. beam energy threshold of 4000 GeV)"
    printf "\n\t%-5s\n" "./computeLuminosity.sh 270000 280000 2000  --  same as above but with a beam energy threshold of 2000"
fi

#--------------------------------------------------
# Script 
#--------------------------------------------------

if [[ $# -eq 2 || $# -eq 3 || $# -eq 4 ]]; then #check if we have two or three arguments

    RUNMIN=$1
    RUNMAX=$2
    BEAMENERGY=$3
    INPUTFILE=$4
    #Put the correct run range in the template
    sed s/RUNMIN/${RUNMIN}/g TRK_Collisions15_template.cfg | sed s/RUNMAX/${RUNMAX}/g > tmpA.cfg
    sed s/RUNMIN/${RUNMIN}/g TRK_Collisions15_template.cfg | sed s/RUNMAX/${RUNMAX}/g > tmpB.cfg

    if [[ $INPUTFILE == "" ]]  ; then #if empty then we are in normal pp energy collisions
        echo "Taking List Of Runs Directly"
    else
        echo "Applying run file ${INPUTFILE}"
	#echo "INPUTFILE=test.txt" > tmp.cfg
	sed s/INPUTFILE/${INPUTFILE}/g tmpB.cfg > tmpA.cfg 
    fi

    if [[ -z "$BEAMENERGY" || $BEAMENERGY == "pp" ]] ; then #if empty then we are in normal pp energy collisions
        sed s/BEAMENERGY/6500/g tmpA.cfg > tmp.cfg
    elif [ $BEAMENERGY == "HI" ] ; then
        sed s/BEAMENERGY/4000/g tmpA.cfg > tmp.cfg
    else
        echo "No normal mode specified, use a beam energy of ${BEAMENERGY}"
        sed s/BEAMENERGY/${BEAMENERGY}/g tmpA.cfg > tmp.cfg
    fi

    #produce the no-flags configuration and run it
    sed s/QFLAGS_OPTIONS/'NONE:NONE'/g tmp.cfg | sed s/JSON_OPTIONS/JSONFILENQ=JSON_TRK_Collisions2015_weekly_NO_QUALITY.txt/g > TRK_Collisions15_NO_QUALITY.cfg
    python dataCertTRK.py TRK_Collisions15_NO_QUALITY.cfg

    #produce the configuration with flags on and run it 
    sed s/QFLAGS_OPTIONS/'Strip:GOOD,Pix:GOOD,Track:GOOD'/g tmp.cfg | sed s/JSON_OPTIONS/JSONFILE=JSON_TRK_Collisions2015_weekly.txt/g > TRK_Collisions15_WITH_QUALITY.cfg
    python dataCertTRK.py TRK_Collisions15_WITH_QUALITY.cfg
 
    #Set environment
    export PATH=$HOME/.local/bin:/afs/cern.ch/cms/lumi/brilconda-1.0.3/bin:$PATH

    #compute integrated luminosity for NO QUALITY
    allLumi=$(brilcalc lumi  -i JSON_TRK_Collisions2015_weekly_NO_QUALITY.txt | grep totrecorded -A 2 | tail -1 | awk '{print $12}')
    goodLumi=$(brilcalc lumi  -i JSON_TRK_Collisions2015_weekly.txt | grep totrecorded -A 2 | tail -1 | awk '{print $12}')

    if [[ -z $BEAMENERGY || $BEAMENERGY == "pp" ]] ; then
        allLumi=$(echo "scale=1; $allLumi / 1000000." | bc)
        goodLumi=$(echo "scale=1; $goodLumi / 1000000." | bc)
        badLumi=$(echo "scale=1; $allLumi - $goodLumi" | bc)
        unit="pb^-1"
    elif [ $BEAMENERGY == "HI" ] ; then
        badLumi=$(echo "scale=1; $allLumi - $goodLumi" | bc)
        unit="ub^-1"
    else
        badLumi=$(echo "scale=1; $allLumi - $goodLumi" | bc)
        unit="ub^-1"
    fi

    echo "======================================="
    echo "||   RANGE OF RUNS: $RUNMIN - $RUNMAX" 
    echo "||   Total luminosity : $allLumi $unit"
    echo "||   GOOD luminosity : $goodLumi $unit"
    echo "||   BAD luminosity : $badLumi $unit"
    echo "========================================"

    #clean the temp config files
    rm tmpA.cfg
    rm tmpB.cfg
    rm tmp.cfg
    rm TRK_Collisions15_NO_QUALITY.cfg
    rm TRK_Collisions15_WITH_QUALITY.cfg
    rm JSON_TRK_Collisions2015_weekly_NO_QUALITY.txt
    rm JSON_TRK_Collisions2015_weekly.txt

    exit 1
fi
