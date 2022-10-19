<h2>Description</h2>
Converts xtc1 to xtc2 file

<h2>Installation</h2>
git clone --recurse-submodules git@github.com:monarin/xtc1to2.git $HOME/xtc1to2    

<h2>Running</h2>
This example (flag_test=True) converts three events from lcls1 to lcls2 format. The output is ./out.xtc2.

Push Side:
```bash
ssh psana
source /reg/g/psdm/etc/psconda.sh
export PYTHONPATH=$HOME/xtc1to2:$PYTHONPATH
cd $HOME/xtc1to2/examples
python zmq_push.py
```
Pull Side:
```bash
ssh <same node as the push side>
source /cds/sw/ds/ana/conda2/manage/bin/psconda.sh
export PYTHONPATH=$HOME/xtc1to2:$PYTHONPATH
cd $HOME/xtc1to2/examples
python zmq_pull.py
```
<h2>Notes</h2>
There are many experiment-specific parameters (exp code, run number, detector names, etc.) that need to be changed in both zmq_push.py and zmq_pull.py. For this example, we need Photon Energy information. The python example below shows how we can obtain Photon Energy per shot in lcls1 environment. 

Obtaining Photon Energy:
```python
es = ps.ds.env().epicsStore()  
try:  
    md.small.wavelength = es.value('SIOC:SYS0:ML00:AO192')  
except:  
    md.small.wavelength = 0  
ebeamDet = psana.Detector('EBeam')  
ebeam = ebeamDet.get(ps.evt)  
try:  
    photonEnergy = ebeam.ebeamPhotonEnergy()  
    pulseEnergy = ebeam.ebeamL3Energy()  # MeV  
except:  
    photonEnergy = 0  
    pulseEnergy = 0  
    if md.small.wavelength > 0:  
        h = 6.626070e-34  # J.m  
        c = 2.99792458e8  # m/s  
        joulesPerEv = 1.602176621e-19  # J/eV  
        photonEnergy = (h / joulesPerEv * c) / (md.small.wavelength * 1e-9)  
```

 
