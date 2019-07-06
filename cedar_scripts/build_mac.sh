#!/bin/bash
#
# Usage:  build_mac.sh [options] filename.mac
# Option:  -n     nevents
#          -s     seed
#          -g     geom
#          -r     dark-rate [kHz]
#          -D     DAQ_mac_file
#          -N     NUANCE_input_file
#          -E     fixed_or_max_KE [MeV]
#          -e     min_KE [MeV]
#          -p     PID
#          -x     x_pos [cm] (for fixed position)
#          -y     y_pos [cm] (for fixed position) or half_y_max (for uniform position)
#          -z     z_pos [cm] (for fixed position)
#          -R     R_max (for uniform position)
#          -d     direction_type [fix|2pi|4pi]
#          -u     x_dir
#          -v     y_dir
#          -w     z_dir
#          -f     output_file.root

#for arg in "$@"; do
#  echo $arg
#done
geom="nuPRISM_mPMT"
darkrate=0.1
daqfile="${WCSIMDIR}/macros/daq.mac"
seed=${SLURM_ARRAY_TASK_ID}
while getopts "n:s:g:r:D:N:E:e:P:p:x:y:z:R:d:u:v:w:f:" flag; do
  case $flag in
    n) nevents="${OPTARG}";;
    s) seed="${OPTARG}";;
    g) geom="${OPTARG}";;
    r) darkrate="${OPTARG}";;
    D) daqfile="$(readlink -f "${OPTARG}")";;
    N) nuance="$(readlink -f "${OPTARG}")";;
    E) Emax="${OPTARG}";;
    e) Emin="${OPTARG}";;
    P) pid="${OPTARG}";;
    p) pos="${OPTARG}";;
    x) xpos="${OPTARG}";;
    y) ypos="${OPTARG}";;
    z) zpos="${OPTARG}";;
    R) rpos="${OPTARG}";;
    d) dir="${OPTARG}";;
    u) xdir="${OPTARG}";;
    v) ydir="${OPTARG}";;
    w) zdir="${OPTARG}";;
    f) rootfile="$(readlink -f "${OPTARG}")";;
  esac
done
shift $((OPTIND - 1))
file="$(readlink -f "$1")"
if [ -z $nevents ]; then echo "Number of events not set"; exit 1; fi
if [ -z $seed ]; then echo "Random seed not set"; exit 1; fi
if [ -z $geom ]; then echo "Geometry not set"; exit 1; fi
if [ -z $darkrate ]; then echo "Dark rate not set"; exit 1; fi
if [ -z $daqfile ]; then echo "DAQ mac file not set"; exit 1; fi
if [ -z $rootfile ]; then echo "Root file not set"; exit 1; fi
if [ -z $file ]; then echo "Output mac file name not set"; exit 1; fi
if [ ! -z $nuance ]; then
  if [ ! -z $Emax ]; then echo "Using nuance file but Emax is set"; exit 1; fi
  if [ ! -z $Emin ]; then echo "Using nuance file but Emin is set"; exit 1; fi
  if [ ! -z $pid  ]; then echo "Using nuance file but PID is set"; exit 1; fi
  if [ ! -z $pos ]; then echo "Using nuance file but pos is set"; exit 1; fi
  if [ ! -z $xpos ]; then echo "Using nuance file but x pos is set"; exit 1; fi
  if [ ! -z $ypos ]; then echo "Using nuance file but y pos is set"; exit 1; fi
  if [ ! -z $zpos ]; then echo "Using nuance file but z pos is set"; exit 1; fi
  if [ ! -z $rpos ]; then echo "Using nuance file but r pos is set"; exit 1; fi
  if [ ! -z $dir  ]; then echo "Using nuance file but dir type is set"; exit 1; fi
  if [ ! -z $xdir ]; then echo "Using nuance file but x dir is set"; exit 1; fi
  if [ ! -z $ydir ]; then echo "Using nuance file but y dir is set"; exit 1; fi
  if [ ! -z $zdir ]; then echo "Using nuance file but z dir is set"; exit 1; fi
else
  if [ -z $Emax ]; then echo "Energy not set"; exit 1; fi
  if [ -z $pid  ]; then echo "PID not set"; exit 1; fi
  if [ -z $dir  ]; then echo "Direction type not set"; exit 1; fi
  if [ "$dir" == "fix" ]; then
    if [ -z $xdir ]; then echo "Dir is fix but x dir not set"; exit 1; fi
    if [ -z $ydir ]; then echo "Dir is fix but y dir not set"; exit 1; fi
    if [ -z $zdir ]; then echo "Dir is fix but z dir not set"; exit 1; fi
  else
    if [[ "$dir" != [24]pi ]]; then echo "Unrecognised direction type"; exit; fi
    if [ ! -z $xdir ]; then echo "Dir is $dir but x dir set"; exit; fi
    if [ ! -z $ydir ]; then echo "Dir is $dir but y dir set"; exit; fi
    if [ ! -z $zdir ]; then echo "Dir is $dir but z dir set"; exit; fi
  fi
  if [ "$pos" == "unif" ]; then
    if [ ! -z $xpos ]; then echo "Pos is unif but x pos set"; exit 1; fi
    if [ ! -z $zpos ]; then echo "Pos is unif but z pos set"; exit 1; fi
    if [ -z $ypos ]; then echo "Pos is unif but max half-y not set"; exit; fi
    if [ -z $rpos ]; then echo "Pos is unif but max R not set"; exit; fi
  elif [ "$pos" == "fix" ]; then
    if [ ! -z $rpos ]; then
      if [ ! -z $xpos ]; then echo "Both R pos and x pos set"; exit; fi
      if [ ! -z $zpos ]; then echo "Both R pos and z pos set"; exit; fi
      xpos=$rpos
      zpos=0
    else
      if [ -z $xpos ]; then echo "Neither R pos nor x pos set"; exit 1; fi
      if [ -z $zpos ]; then echo "Neither R pos not z pos set"; exit 1; fi
    fi
    if [ -z $ypos ]; then echo "y pos not set"; exit 1; fi
  fi
fi

echo     "/run/verbose                           1"                    > $file
echo     "/tracking/verbose                      0"                    >> $file
echo     "/hits/verbose                          0"                    >> $file
echo     "/random/setSeeds                       $seed $seed"          >> $file
echo     "/WCSim/WCgeom                          $geom"                >> $file
echo     "/WCSim/Construct"                                            >> $file
echo     "/WCSim/PMTQEMethod                     Stacking_Only"        >> $file
echo     "/WCSim/PMTCollEff                      on"                   >> $file
echo     "/WCSim/SavePi0                         false"                >> $file
echo     "/DAQ/Digitizer                         SKI"                  >> $file
echo     "/DAQ/Trigger                           NDigits"              >> $file
echo     "/control/execute                       $daqfile"             >> $file
echo     "/DarkRate/SetDarkRate                  $darkrate kHz"        >> $file
echo     "/DarkRate/SetDarkMode                  1"                    >> $file
echo     "/DarkRate/SetDarkHigh                  100000"               >> $file
echo     "/DarkRate/SetDarkLow                   0"                    >> $file
echo     "/DarkRate/SetDarkWindow                4000"                 >> $file
if [ ! -z $nuance ]; then
  echo   "/mygen/generator                       muline"               >> $file
  echo   "/mygen/vecfile                         $nuance"              >> $file
else
  echo   "/mygen/generator                       gps"                  >> $file
  echo   "/gps/particle                          $pid"                 >> $file
  if [ ! -z $Emin ]; then
    echo "/gps/ene/type                          Lin"                  >> $file
    echo "/gps/ene/intercept                     1"                    >> $file
    echo "/gps/ene/min                           $Emin MeV"            >> $file
    echo "/gps/ene/max                           $Emax MeV"            >> $file
  else
    echo "/gps/energy                            $Emax MeV"            >> $file
  fi
  if [ "$dir" == "fix" ]; then
    echo "/gps/direction                         $xdir $ydir $zdir"    >> $file
  elif [ "$dir" == "2pi" ]; then
    echo "/gps/ang/type                          iso"                  >> $file
    echo "/gps/ang/rot1                          1 0 0"                >> $file
    echo "/gps/ang/rot2                          0 0 1"                >> $file
    echo "/gps/ang/mintheta                      90  deg"              >> $file
    echo "/gps/ang/maxtheta                      90  deg"              >> $file
    echo "/gps/ang/minphi                        0   deg"              >> $file
    echo "/gps/ang/maxphi                        360 deg"              >> $file
  elif [ "$dir" == "4pi" ]; then
    echo "/gps/ang/type                          iso"                  >> $file
  fi
  if [ "$pos" == "unif" ]; then
    echo "/gps/pos/type                          Volume"               >> $file
    echo "/gps/pos/shape                         Cylinder"             >> $file
    echo "/gps/pos/rot1                          1 0 0"                >> $file
    echo "/gps/pos/rot2                          0 0 1"                >> $file
    echo "/gps/pos/radius                        $rpos cm"             >> $file
    echo "/gps/pos/halfz                         $ypos cm"             >> $file
  else
    echo "/gps/position                          $xpos $ypos $zpos cm" >> $file
  fi
fi
echo     "/Tracking/fractionOpticalPhotonsToDraw 0.0"                  >> $file
echo     "/WCSimIO/RootFile                      $rootfile"            >> $file
echo     "/WCSimIO/SaveRooTracker                0"                    >> $file
echo     "/run/beamOn                            $nevents"             >> $file

