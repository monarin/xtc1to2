#!/bin/bash
# source /cds/sw/ds/ana/conda2/manage/bin/psconda.sh -py3
# source ~monarin/lcls2/setup_env.sh 
source ~smarches/git/lcls2/setup_env.sh 

#source /reg/g/psdm/etc/psconda.sh -py3 

echo $PYTHONPATH
#export PYTHONPATH=$HOME/git/xtc1to2:$PYTHONPATH
export PYTHONPATH=..:$PYTHONPATH
# cd $HOME/git/xtc1to2/examples

# python zmq_pull.py


python zmq_pull_SFX.py 
#-e mfxp22820 -r 13 -d Rayonix -o /cds/data/psdm/txi/txisfx00121/xtc/txisfx00121-r0013-s000-c000_test.xtc2 -b 256000000
