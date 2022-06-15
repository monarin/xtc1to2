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

expected_label1_events = 1669
def get_run_info():
    """Returns a dictionary of run and selected events.
    
    Open csv with each line containing 'exp', 'run', 'event_num', 'label'
    Total evt: 5059 - 1 (header) = 5058
    label 0: 2697
    label 1: 1669
    label 2: 681
    """
    fl_csv     = "2022_0603_2226_44.auto.label.diagnosis.csv"
    label_1hit = '1'

    # This is a dictionary with a key as run number. Each pointing
    # to a list of event number that will be selected.
    run_info = {}
    with open(fl_csv) as csv_handle:
        lines = csv.reader(csv_handle)
        
        #skip header
        next(lines)
        for line in lines:
            exp, run, evt_no, label, ts = line
            if label != label_1hit: continue
            run = int(run)
            run_data = (int(evt_no), int(ts))
            if run in run_info:
                run_info[run].append(run_data)
            else:
                run_info[run] = [run_data]

    # Check run_info
    cn_label1 = 0
    for run, evt_list in run_info.items():
        n_events = len(evt_list)
        print(run, n_events)
        cn_label1 += n_events
    print(f'Total label 1 events: {cn_label1}')
    assert cn_label1 == expected_label1_events
    return run_info


if __name__ == "__main__":
    # Specify the dataset and detector...
    exp, mode, detector_name = "amo06516", "idx", "pnccdFront"
    geom = (
        "/reg/d/psdm/amo/amo06516/calib/PNCCD::CalibV1/Camp.0:pnCCD.0/geometry/38-end.data"
    )
    # Initialize the geometry
    gmt_reader = PsanaGeometry(geom)

    # Initialize zmq sender
    socket = "tcp://127.0.0.1:5558"
    zmq_send = ZmqSender(socket)

    # Get event no. list per run
    run_info = get_run_info()
    n_runs = len(run_info.keys())
    cn_runs = 0

    # Start sending data by looping through runs
    cn_events = 0
    for run, run_data in run_info.items(): 
        img_reader = PsanaImg(exp, run, mode, detector_name)
        phe_reader = PsanaPhotonEnergy(exp, run, mode)

        for i_evt, run_item in enumerate(run_data):
            event_num, chk_ts = run_item
            img = img_reader.get(event_num, calib=True)
            photon_energy = phe_reader.get(event_num)
            ts = img_reader.timestamp(event_num)
            assert ts.time() == chk_ts

            if i_evt == 0 and cn_runs == 0:
                # Send beginning timestamp - this will create config, beginrun,
                # beginstep, and enable on the client.
                start_dict = {
                    "start": True, 
                    "exp": exp,
                    "run": run,
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
                f"run={run} event_num={event_num} ts={ts.time()} img={img.shape} dtype={img.dtype} photon energy:{photon_energy:.3f}"
            )

            # Send the dataset
            zmq_send.send_zipped_pickle(data)
            cn_events += 1

        # end for i_evt, ...
        cn_runs += 1

    # end for run, ...

    # Send end message
    done_dict = {"end": True}
    zmq_send.send_zipped_pickle(done_dict)
    
    print(f"Send total: {cn_events} events in {cn_runs} runs")
