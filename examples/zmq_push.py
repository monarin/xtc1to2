"""An example that reads in lcls1 experiment and push data to
be saved in lcls2 format via zmq.

Usage: 
    1. Get psana1 environment (source /reg/g/psdm/etc/psconda.sh) and 
    activate py3 env. (conda activate ana-4.0.36-py3)
    2. Set exp, run, mode, and detector name
    3. Set path to geometry file 
"""
from read_img import PsanaImg, DisplaySPIImg
from read_photon_energy import PsanaPhotonEnergy
from read_geometry import PsanaGeometry

# Specify the dataset and detector...
exp, run, mode, detector_name = 'amo06516', '90', 'idx', 'pnccdFront'
geom = "/reg/d/psdm/amo/amo06516/calib/PNCCD::CalibV1/Camp.0:pnCCD.0/geometry/38-end.data"

# Initialize all readers
img_reader = PsanaImg(exp, run, mode, detector_name)
phe_reader = PsanaPhotonEnergy(exp, run, mode)
gmt_reader = PsanaGeometry(geom)

# Access an image (e.g. event 796)...
event_num = 796
img = img_reader.get(event_num, calib=True)
photon_energy = phe_reader.get(event_num)
ts = img_reader.timestamp(event_num)


print(f'event_num={event_num} ts={ts.time()} {img.shape} photon energy:{photon_energy:.3f}')
print(f'pixel_position={gmt_reader.pixel_position.shape}')
print(f'pixel_index_map={gmt_reader.pixel_index_map.shape}')


