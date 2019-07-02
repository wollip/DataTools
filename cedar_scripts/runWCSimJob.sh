#!/bin/bash
#SBATCH --account=rpp-tanaka-ab
#SBATCH --time=1:00:00
#SBATCH --mem-per-cpu=2000
#SBATCH --output=%x-%a.out
#SBATCH --error=%x-%a.err
#SBATCH --cpus-per-task=1

# usage:   runWCSimJob.sh name data_dir [options] 
#          name is used in the output directory and filenames to identify this production run
#          data_dir is the top directory where simulated data will be stored
# Options: -n nevents            number of events
#          -s seed               WCSim random seed, default is set from SLURM_ARRAY_TASK_ID)
#          -g geom               WCSim geometry default is nuPRISM_mPMT)
#          -r dark-rate          dark rate [kHz] (default is 0.1 kHz)
#          -D DAQ_mac_file       WCSim daq mac file (default is [data_dir]/[name]/WCSim/macros/daq.mac
#          -E fixed_or_max_Evis  fixed or maximum energy [MeV]
#         [-e min_Evis]          minumum energy [MeV]
#          -P PID                particle type
#          -p pos_type           position type [fix|unif]
#         [-x x_pos]             fixed x position (for pos_type=fix) [cm]
#          -y y_pos              fixed y position (for pos_type=fix) or maximum half-y (for pos_type=unif) [cm]
#         [-z z_pos]             fixed z position (for pos_type=fix) [cm]
#         [-R R_pos]             fixed R position (for pos_type=fix) or max R (for pos_type=unif) [cm]
#          -d dir_type           direction type [fix|2pi|4pi]
#          -u x_dir              x direction (for dir_type=fix)
#          -v y_dir              y direction (for dir_type=fix)
#          -w z_dir              z direction (for dir_type=fix)
#          -F                    also run fiTQun on output

ulimit -c 0

module load python/3.6.3
module load scipy-stack

submittime=${JOBTIME:-`date`}
starttime=`date`

# Get positional parameters
name=$1
data_dir=`readlink -f $2`
if [ -z "${name}" ] || [[ "${name}" == "-[nsgrDNEePpxyzRduvw]" ]]; then echo "Run name not set"; exit; fi
if [ -z "${data_dir}" ] || [[ "${data_dir}" == "-[nsgrDNEePpxyzRduvw]"  ]]; then echo "Data directory not set"; exit; fi
shift 2

# Set default options
data_dir="${data_dir}/${name}"
seed=${SLURM_ARRAY_TASK_ID}
geom="nuPRISM_mPMT"
darkrate=0.1
daqfile="${WCSIMDIR}/macros/daq.mac"

# Get options
while getopts "n:s:g:r:D:N:E:e:P:p:x:y:z:R:d:u:v:w:F" flag; do
  case ${flag} in
    n) nevents="${OPTARG}";;
    s) seed="${OPTARG}";;
    g) geom="${OPTARG}";;
    r) darkrate="${OPTARG}";;
    D) daqfile="${OPTARG}";;
    N) nuance="${OPTARG}";;
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
    F) run_fiTQun=1;;
  esac
done

echo "[${submittime}] Job ${name}, output to ${data_dir}, submitted with options $@"
echo "[${starttime}] Starting job"

# Validate options
if [ -z "${nevents}" ]; then echo "Number of events not set"; exit ; fi
if [ -z "${seed}" ]; then echo "Random seed not set"; exit ; fi
if [ ! -f "${daqfile}" ]; then echo "DAQ mac file $daqfile not found"; exit ; fi
if [ -z "${Emax}" ]; then echo "Energy not set"; exit ; fi
if [ -z "${pid}"  ]; then echo "PID not set"; exit ; fi
if [ -z "${dir}"  ]; then echo "Direction type not set"; exit ; fi
if [ "${dir}" == "fix" ]; then
  if [ -z "${xdir}" ]; then echo "Dir is fix but x dir not set"; exit ; fi
  if [ -z "${ydir}" ]; then echo "Dir is fix but y dir not set"; exit ; fi
  if [ -z "${zdir}" ]; then echo "Dir is fix but z dir not set"; exit ; fi
else
  if [[ "${dir}" != [24]pi ]]; then echo "Unrecognised direction type"; exit; fi
  if [ ! -z "${xdir}" ]; then echo "Dir is ${dir} but x dir set"; exit; fi
  if [ ! -z "${ydir}" ]; then echo "Dir is ${dir} but y dir set"; exit; fi
  if [ ! -z "${zdir}" ]; then echo "Dir is ${dir} but z dir set"; exit; fi
fi
if [ "${pos}" == "unif" ]; then
  if [ ! -z "${xpos}" ]; then echo "Pos is unif but x pos set"; exit ; fi
  if [ ! -z "${zpos}" ]; then echo "Pos is unif but z pos set"; exit ; fi
  if [ -z "${ypos}" ]; then echo "Pos is unif but max half-y not set"; exit; fi
  if [ -z "${rpos}" ]; then echo "Pos is unif but max R not set"; exit; fi
elif [ "${pos}" == "fix" ]; then
  if [ ! -z "${rpos}" ]; then
    if [ ! -z "${xpos}" ]; then echo "Both R pos and x pos set"; exit; fi
    if [ ! -z "${zpos}" ]; then echo "Both R pos and z pos set"; exit; fi
  else
    if [ -z "${xpos}" ]; then echo "Neither R pos nor x pos set"; exit ; fi
    if [ -z "${zpos}" ]; then echo "Neither R pos not z pos set"; exit ; fi
  fi
  if [ -z "${ypos}" ]; then echo "y pos not set"; exit ; fi
fi

# Calculate visible Ekin from Evis
declare -A Eth
Eth[e-]=0.786
Eth[e+]=0.786
Eth[mu-]=158.7
Eth[mu+]=158.7
Eth[gamma]=`python -c "print(2*${Eth[e-]})"`
Eth[pi-]=209.7
Eth[pi+]=209.7
Eth[pi0]=`python -c "print(2*${Eth[gamma]})"`
EkinMax=`python -c "print(${Emax}+${Eth[${pid}]:-0})"`
[ ! -z "${Emin}" ] && EkinMin=`python -c "print(${Emin}+${Eth[${pid}]:-0})"`

log_dir="/scratch/${USER}/log/${name}"
pos_string="${pos}-pos-${xpos:+x${xpos}}${rpos:+R${rpos}}-y${ypos}${zpos:+-z${zpos}}cm"
dir_string="${dir}-dir${xdir:+-x${xdir}-y${ydir}-z${zdir}}"
E_string="E${Emin:+${Emin}to}${Emax}MeV"
directory="${pid}/${E_string}/${pos_string}/${dir_string}"
filename="${name}_${pid}_${E_string}_${pos_string}_${dir_string}_${nevents}evts_${seed}"
fullname="${directory}/${filename}"

# Get args to pass to build_mac.sh 
# For gammas, set position to (0,0,0) and double number of events, to simulate enough gamma conversions
args=()
if [ "${pid}" == "gamma" ]; then
  gamma_ext="_gamma-conversion"
  for arg in "$@"; do
    if [[ "${skip}" == 1 ]]; then
      unset skip
    elif [ "${arg}" == "-p" ]; then
      args+=( "-p" "fix" )
      skip=1
    elif [ "${arg}" == "-n" ]; then
      nevents2=`python -c "print(${nevents}*2)"`
      args+=( "-n" "${nevents2}" )
      skip=1
    elif [[ "${arg}" == "-[xyzR]" ]]; then
      args+=( "${arg}" 0 )
      skip=1
    else
      args+=( "${arg}" )
    fi
  done
else
  gamma_ext=""
  args=( "$@" )
fi

# Create mac file
macfile="${data_dir}/mac${gamma_ext}/${fullname}.mac"
rootfile="${data_dir}/WCSim${gamma_ext}/${fullname}.root"
mkdir -p "${data_dir}/mac${gamma_ext}/${directory}"
echo "[`date`] Creating mac file ${macfile}"
./build_mac.sh "${args[@]}" -f "${rootfile}" "${macfile}"

# Run WCSim
logfile="${log_dir}/WCSim${gamma_ext}/${fullname}.log"
echo "[`date`] Running WCSim on ${macfile} output to ${rootfile} log to ${logfile}"
mkdir -p "${data_dir}/WCSim${gamma_ext}/${directory}"
mkdir -p "${log_dir}/WCSim${gamma_ext}/${directory}"
cd ${WCSIMDIR}
${G4WORKDIR}/bin/${G4SYSTEM}/WCSim "${macfile}" &> "${logfile}"

# For gammas, dump gamma conversion results to nuance file and run on that
if [ "${pid}" == "gamma" ]; then
  nuancefile="${data_dir}/nuance/${fullname}.txt"
  posargs="\"${pos}\", ${xpos}${rpos}, ${ypos}, ${zpos:-0}"
  echo "[`date`] Dumping gamma conversion products to ${nuancefile}"
  root -l -b -q "DumpGammaConvProducts.C+(\"${rootfile/.root/_flat.root}\", \"${nuancefile}\", ${nevents}, \"${dir}\", ${posargs})"
  
  # Create mac file
  macfile="${data_dir}/mac_nuance/${fullname}.mac"
  rootfile="${data_dir}/WCSim/${fullname}.root"
  mkdir -p "${data_dir}/mac_nuance/${directory}"
  echo "[`date`] Creating mac file ${macfile}"
  ./build_mac.sh -n "${nevents}" -s "${seed}" -g "${geom}" -r "${darkrate}" -D "${daqfile}" -N "${nuancefile}" -f "${rootfile}" "${macfile}"
  
  # Run WCSim
  logfile="${log_dir}/WCSim/${fullname}.log"
  echo "[`date`] Running WCSim on ${macfile} output to ${rootfile} log to ${logfile}"
  mkdir -p "${data_dir}/WCSim/${directory}"
  mkdir -p "${log_dir}/WCSim/${directory}"
  cd ${WCSIMDIR}
  ${G4WORKDIR}/bin/${G4SYSTEM}/WCSim "${macfile}" &> "${logfile}"
fi

npzfile="${data_dir}/numpy/${fullname}.npz"
mkdir -p "${data_dir}/numpy/${directory}"
mkdir -p "${log_dir}/numpy/${directory}"
echo "[`date`] Converting to numpy file ${npzfile} log to ${log_dir}/numpy/${fullname}.log"
python /project/rpp-tanaka-ab/machine_learning/production_software/DataTools/root_utils/event_dump.py "${rootfile}" -d "${data_dir}/numpy/${directory}" &> "${log_dir}/numpy/${fullname}.log"

if [ ! -z "${runfiTQun}" ]; then
  echo "[`date`] Running fiTQun on ${rootfile}"
  mkdir -p "${data_dir}/fiTQun/${directory}"
  mkdir -p "${log_dir}/fiTQun/${directory}"
#  ./runfiTQun.sh "${rootfile}" ${nevents} &> "${log_dir}/fiTQun/${fullname}.log"
fi

endtime=`date`
echo "[${endtime}] Completed"
echo -e "${submittime}\t${starttime}\t${endtime}\t${pid}\t${E_string}\t${pos_string}\t${dir_string}\t${nevents}\t${seed}" >> "${log_dir}.log"
