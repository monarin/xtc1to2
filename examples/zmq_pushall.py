#!/usr/bin/env python
"""An example that reads in lcls1 experiment and push data to
be saved in lcls2 format via zmq.

Usage: 
    1. Get psana1 environment (source /reg/g/psdm/etc/psconda.sh) and 
    activate py3 env. (conda activate ana-4.0.38-py3)
    export PYTHONPATH=$HOME/xtc1to2:$PYTHONPATH
    2. Set exp, run, mode, and detector name
    3. Set path to geometry file 
"""
from xtc1to2.read_img import PsanaImg, DisplaySPIImg
from xtc1to2.read_photon_energy import PsanaPhotonEnergy
from xtc1to2.read_geometry import PsanaGeometry
from xtc1to2.socket.zmqhelper import ZmqSender
import h5py
import numpy as np
import csv


fl_csv          = "2022_0603_2226_44.auto.label.csv"
label_1hit = '1'

# Specify the dataset and detector...
## exp, run, mode, detector_name = "amo06516", "90", "idx", "pnccdFront"
geom = (
    "/reg/d/psdm/amo/amo06516/calib/PNCCD::CalibV1/Camp.0:pnCCD.0/geometry/38-end.data"
)
# Initialize the geometry
gmt_reader = PsanaGeometry(geom)

# Initialize zmq sender
socket = "tcp://127.0.0.1:5558"
zmq_send = ZmqSender(socket)

# Collect all items from the auto-labeled file...
mode            = "idx" 
detector_name   = "pnccdFront"
event_dict      = {}
img_reader_dict = {}
phe_reader_dict = {}
with open(fl_csv) as csv_handle:
    lines = csv.reader(csv_handle)
    for line in lines:
        # Skip the header...
        next(lines)

        # Go through each line...
        for line in lines:
            exp, run, event_num, label = line

            # Specify the key to dictionaries...
            basename = (exp, run)

            # Collect run info from each exp,run...
            if not basename in event_dict: event_dict[basename] = [event_num]
            else                         : event_dict[basename].append(event_num)

            # Collect img_reader from each exp,run...
            if not basename in img_reader_dict: 
                img_reader_dict[basename] = PsanaImg(exp, run, mode, detector_name)

            # Collect photon energy from each exp,run...
            if not basename in phe_reader_dict:
                phe_reader_dict[basename] = PsanaPhotonEnergy(exp, run, mode)

for i, (basename, event_num_list) in enumerate(event_dict.items()):
    exp, run = basename

    for event_num in event_num_list:
        ts = img_reader_dict[basename].timestamp(event_num)
        if i == 0:
            start_dict = {
                "exp"             : exp,
                "run"             : run,
                "start"           : True,
                "config_timestamp": ts.time() - 10,
                "pixel_position"  : gmt_reader.pixel_position,
                "pixel_index_map" : gmt_reader.pixel_index_map,
            }
            zmq_send.send_zipped_pickle(start_dict)

        img = img_reader_dict[basename].get(event_num, calib = True)
        phe = phe_reader_dict[basename].get(event_num)
        data = {
            "calib"        : img,
            "photon_energy": phe,
            "timestamp"    : ts.time(),
        }

        print(
            f"exp={exp} run={int(run):04d} event_num={int(event_num):06d} ts={ts.time()} img={img.shape} dtype={img.dtype} photon energy:{phe:.3f}"
        )
        print(f"pixel_position={gmt_reader.pixel_position.shape} dtype={gmt_reader.pixel_position.dtype}")
        print(f"pixel_index_map={gmt_reader.pixel_index_map.shape} dtype={gmt_reader.pixel_index_map.dtype}")

        zmq_send.send_zipped_pickle(data)

# Send end message
done_dict = {"end": True}
zmq_send.send_zipped_pickle(done_dict)
