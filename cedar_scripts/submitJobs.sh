#!/bin/bash
# Example script to set up and submit batch jobs

# exit when any command fails
set -e

export DATATOOLS=/project/rpp-tanaka-ab/machine_learning/production_software/DataTools
cd $DATATOOLS/cedar_scripts

source sourceme.sh

name=IWCDmPMT_test
data_dir=/project/rpp-tanaka-ab/machine_learning/data

source setupJobs.sh "$name" "$data_dir"

# set WCSim directory to where the data will also go (setup script will compile it there to be reused if needed)
export WCSIMDIR="$data_dir/$name/WCSim"
export G4WORKDIR="$data_dir/$name/WCSim"

# set directory where log files will be saved
export LOGDIR="/scratch/$USER/log/$name/"
mkdir -p "$LOGDIR"
# cd to this directory so SLURM puts its logs there too
cd "$LOGDIR"

JOBTIME=`date` sbatch --time=0:59:00 --array=0-9 --job-name=e "$DATATOOLS/cedar_scripts/runWCSimJob.sh" "$name" "$data_dir" -n 100 -e 100 -E 1000 -P e- -d 2pi -p fix -x 0 -y 0 -z 0
JOBTIME=`date` sbatch --time=0:59:00 --array=0-9 --job-name=mu "$DATATOOLS/cedar_scripts/runWCSimJob.sh" "$name" "$data_dir" -n 100 -e 100 -E 1000 -P mu- -d 2pi -p fix -x 0 -y 0 -z 0
JOBTIME=`date` sbatch --time=0:59:00 --array=0-9 --job-name=gamma "$DATATOOLS/cedar_scripts/runWCSimJob.sh" "$name" "$data_dir" -n 100 -e 100 -E 1000 -P gamma -d 2pi -p fix -x 0 -y 0 -z 0
