"""An example that reads in lcls1 experiment and push data to
be saved in lcls2 format via zmq.

Usage: 
    1. Get psana1 environment (source /reg/g/psdm/etc/psconda.sh) and 
    activate py3 env. (conda activate ana-4.0.36-py3)
    2. Set exp, run, mode, and detector name
    3. Set path to geometry file 
"""
from xtc1to2.read_img import PsanaImg, DisplaySPIImg
from xtc1to2.read_photon_energy import PsanaPhotonEnergy
from xtc1to2.read_geometry import PsanaGeometry
from xtc1to2.socket.zmqhelper import ZmqSender

# Specify the dataset and detector...
exp, run, mode, detector_name = "amo06516", "90", "idx", "pnccdFront"
geom = (
    "/reg/d/psdm/amo/amo06516/calib/PNCCD::CalibV1/Camp.0:pnCCD.0/geometry/38-end.data"
)

# Initialize all readers
img_reader = PsanaImg(exp, run, mode, detector_name)
phe_reader = PsanaPhotonEnergy(exp, run, mode)
gmt_reader = PsanaGeometry(geom)

# Initialize zmq sender
socket = "tcp://127.0.0.1:5557"
zmq_send = ZmqSender(socket)

# Access an image (e.g. event 796)...
event_num = 796
img = img_reader.get(event_num, calib=True)
photon_energy = phe_reader.get(event_num)
ts = img_reader.timestamp(event_num)

data = {
    "calib": img,
    "photon_energy": photon_energy,
    "ts": ts.time(),
    "pixel_position": gmt_reader.pixel_position,
    "pixel_index_map": gmt_reader.pixel_index_map,
}

print(
    f"event_num={event_num} ts={ts.time()} {img.shape} photon energy:{photon_energy:.3f}"
)
print(f"pixel_position={gmt_reader.pixel_position.shape}")
print(f"pixel_index_map={gmt_reader.pixel_index_map.shape}")

# Send the dataset
