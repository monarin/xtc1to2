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
import h5py
import numpy as np


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
start_evt = 796
data_array = np.zeros([3,4,512,512], dtype=np.float32)
photon_array = np.zeros(3, dtype=np.float64)
for i, event_num in enumerate(range(start_evt, start_evt + 3)):
    img = img_reader.get(event_num, calib=True)
    photon_energy = phe_reader.get(event_num)
    ts = img_reader.timestamp(event_num)
    data_array[i,:,:,:] = img
    photon_array[i] = photon_energy

    if event_num == start_evt:
        # Send beginning timestamp - this will create config, beginrun,
        # beginstep, and enable on the client.
        start_dict = {
            "start": True, 
            "config_timestamp": ts.time() - 10,
            "pixel_position": gmt_reader.pixel_position,
            "pixel_index_map": gmt_reader.pixel_index_map,
        }
        zmq_send.send_zipped_pickle(start_dict)
        
    data = {
        "calib": img,
        "photon_energy": photon_energy,
        "timestamp": ts.time(),
    }

    print(
        f"event_num={event_num} ts={ts.time()} img={img.shape} dtype={img.dtype} photon energy:{photon_energy:.3f}"
    )
    print(f"pixel_position={gmt_reader.pixel_position.shape} dtype={gmt_reader.pixel_position.dtype}")
    print(f"pixel_index_map={gmt_reader.pixel_index_map.shape} dtype={gmt_reader.pixel_index_map.dtype}")

    # Send the dataset
    zmq_send.send_zipped_pickle(data)

# Send end message
done_dict = {"end": True}
zmq_send.send_zipped_pickle(done_dict)

print(f'photon_array={photon_array}')
with h5py.File("out.hdf5", "w") as f:
    f.create_dataset("pixel_position", data=gmt_reader.pixel_position)
    f.create_dataset("pixel_index_map", data=gmt_reader.pixel_index_map)
    f.create_dataset("data", data=data_array)
    f.create_dataset("photon_energy", data=photon_array)

