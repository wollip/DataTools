#!/bin/bash

# usage: setup_jobs.sh name data_dir

# exit when any command fails if being run in subshell
if [[ "${BASH_SOURCE[0]}" == "$0" ]]; then
  set -e
  EXIT=exit
else
  EXIT=return
fi

name="$1"
data_dir="$(readlink -m "$2")"

start_dir="$(pwd)"
cd "$(dirname "${BASH_SOURCE[0]}")"
cd ..
export DATATOOLS="$(pwd)"
if [ "$(git status --porcelain --untracked-files=no)" ]; then
  echo "DataTools git repository not clean, commit or stash changes first so that version can be traced"
  $EXIT 1
fi

mkdir -p "$data_dir/$name"
git describe --always --long --tags > "$data_dir/$name/DataTools-git-describe"

export G4WORKDIR="$data_dir/$name/WCSim/build"
mkdir -p "$G4WORKDIR"
if [ ! -w "$G4WORKDIR" ]; then
  echo "$G4WORKDIR is not writeable. Trying to overwrite previous run? Delete or make directory writable before running this script if you really want to do that."
  $EXIT 1
fi

echo "Compiling WCSim, source $WCSIMDIR, destination $G4WORKDIR"
cd "$WCSIMDIR"
if [ "$(git status --porcelain --untracked-files=no)" ]; then
  echo "WCSim git repository not clean, commit or stash changes first so that version can be traced"
  $EXIT 1
fi
make clean
make rootcint
make -j16
cp -r "$WCSIMDIR/macros/" "$G4WORKDIR"
cp -r "$WCSIMDIR/mPMT-configfiles" "$G4WORKDIR"
cp "$WCSIMDIR/libWCSimRoot.so" "$G4WORKDIR"
cp "$WCSIMDIR/libWCSim.a" "$G4WORKDIR"
git describe --always --long --tags > "$G4WORKDIR/WCSim-git-describe"
export WCSIMDIR="$G4WORKDIR"
# make read-only to prevent accidental write
chmod -R a-w "$G4WORKDIR"

if [[ "${BASH_SOURCE[0]}" != "$0" ]]; then
# script has been sourced
  echo "Finished setting up. Environment variables set. Just run jobs:"
else
  echo "Finished setting up. Export environment variables and run jobs (or source this script instead of running in subshell):"
  echo "export WCSIMDIR=${WCSIMDIR}"
  echo "export G4WORKDIR=${G4WORKDIR}"
  echo "export DATATOOLS=${DATATOOLS}"
fi
echo "run_WCSim_job.sh $name $data_dir [options]"

cd $start_dir