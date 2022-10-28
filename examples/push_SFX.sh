#!/bin/bash

##SBATCH -p psfehq 
##SBATCH -t 3:00:00
##SBATCH --job-name push_sfx
##SBATCH --ntasks=1
##SBATCH --nodelist=psana1519
##SBATCH --output=push.out


source /reg/g/psdm/etc/psconda.sh -py3
#export PYTHONPATH=$HOME/git/xtc1to2:$PYTHONPATH
export PYTHONPATH=..:$PYTHONPATH

# cd $HOME/git/xtc1to2/examples

python zmq_push_SFX.py #-e mfxp22820 -r 13 -d Rayonix --max_events 6000



#source /reg/g/psdm/etc/psconda.sh -py3  
#export PYTHONPATH="${PYTHONPATH}:/cds/home/a/apeck/btx_exafel"

#cd /cds/home/a/apeck/btx_exafel/btx_exafel/conversion
# cd /cds/home/s/smarches/git/btx/btx/conversion

#/cds/sw/ds/ana/conda1/inst/envs/ana-4.0.38-py3/bin/python zmq_push.py -e mfxp22820 -r 13 -d Rayonix --max_events 6000

#/cds/sw/ds/ana/conda1/inst/envs/ana-4.0.38-py3/bin/python /cds/home/s/smarches/git/btx/btx/conversion/zmq_push1.py -e mfxp22820 -r 13 -d Rayonix --max_events 6000


