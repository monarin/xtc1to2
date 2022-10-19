"""Receives data from zmq and save in xtc2 format.

Usage:
    1. ssh to the same node that you are running zmq_push.py
    2. Activate psana2 and xtc1to2 environment
       source lcls2/setup_env.sh
       export PYTHONPATH=$HOME/xtc1to2/:$PYTHONPATH
    2. Receive data from zmq
"""
from xtc1to2.socket.zmqhelper import ZmqReceiver
from psana.dgramedit import DgramEdit, AlgDef, DetectorDef
from psana.psexp import TransitionId
import numpy as np
import h5py
from psana import DataSource


def test_output():
    """Compares known data (saved to hdf5 by the push process) with read data."""
    f = h5py.File('out.hdf5', 'r')
    pixel_position = f['pixel_position']
    pixel_index_map = f['pixel_index_map']
    data = f['data']
    photon_energy = f['photon_energy']

    ds = DataSource(files='out.xtc2')
    run = next(ds.runs())
    det = run.Detector('amopnccd')
    pp_det = run.Detector('pixel_position')
    pim_det = run.Detector('pixel_index_map')
    data_array = np.zeros([3,4,512,512], dtype=np.float32)
    photon_array = np.zeros(3, dtype=np.float64)
    for i,evt in enumerate(run.events()):
        data_array[i,:,:,:] = det.raw.calib(evt)
        photon_array[i] = det.raw.photon_energy(evt)
        pixel_position_array = pp_det(evt)
        pixel_index_map_array = pim_det(evt)

    assert np.array_equal(data,data_array)
    assert np.array_equal(photon_energy, photon_array)
    assert np.array_equal(pixel_position, pixel_position_array)
    assert np.array_equal(pixel_index_map, pixel_index_map_array)


def save_dgramedit(dg_edit, outbuf, outfile):
    """ Save dgram edit to output buffer and write to file"""
    dg_edit.save(outbuf)
    outfile.write(outbuf[:dg_edit.size])


if __name__ == "__main__":
    flag_test = True

    # NameId setup
    nodeId = 1 
    namesId = {
        "amopnccd": 0,
        "runinfo": 1,
        "scan": 2,
    }


    # Setup socket for zmq connection
    socket = "tcp://127.0.0.1:5557"
    zmq_recv = ZmqReceiver(socket)


    # Allocating memory for DgramEdit output buffer
    memsize = 64000000
    outbuf = bytearray(memsize)

    
    # Open output file for writing
    ofname = 'out.xtc2'
    xtc2file = open(ofname, "wb")

    
    # Create config, algorithm, and detector
    config = DgramEdit(transition_id=TransitionId.Configure)
    alg = AlgDef("raw", 1, 2, 3)
    det = DetectorDef("amopnccd", "pnccd", "detnum1234")

    runinfo_alg = AlgDef("runinfo", 0, 0, 1)
    runinfo_det = DetectorDef("runinfo", "runinfo", "")

    scan_alg = AlgDef("raw", 2, 0, 0)
    scan_det = DetectorDef("scan", "scan", "detnum1234")


    # Define data formats
    datadef = {
        "calib": (np.float32, 3),
        "photon_energy": (np.float64, 0),
    }

    runinfodef = {
        "expt": (str, 1),
        "runnum": (np.uint32, 0),
    }

    scandef = {
        "pixel_position": (np.float32, 4),
        "pixel_index_map": (np.int16, 4),
    }


    # Create detetors
    pnccd = config.Detector(det, alg, datadef, nodeId=nodeId, namesId=namesId["amopnccd"])
    runinfo = config.Detector(runinfo_det, 
                              runinfo_alg, 
                              runinfodef, 
                              nodeId=nodeId, 
                              namesId=namesId["runinfo"]
                             )
    scan = config.Detector(scan_det,
                           scan_alg,
                           scandef,
                           nodeId=nodeId,
                           namesId=namesId["scan"]
                          )



    # Start saving data
    while True:
        obj = zmq_recv.recv_zipped_pickle()

        # Begin timestamp is needed (we calculate this from the first L1Accept)
        # to set the correct timestamp for all transitions prior to the first L1.
        if "start" in obj:
            config_timestamp = obj["config_timestamp"]
            config.updatetimestamp(config_timestamp)
            save_dgramedit(config, outbuf, xtc2file)

            beginrun = DgramEdit(transition_id=TransitionId.BeginRun, config=config, ts=config_timestamp + 1)
            runinfo.runinfo.expt = "amo06516"
            runinfo.runinfo.runnum = 90
            beginrun.adddata(runinfo.runinfo)
            scan.raw.pixel_position = obj['pixel_position']
            scan.raw.pixel_index_map = obj['pixel_index_map']
            beginrun.adddata(scan.raw)
            save_dgramedit(beginrun, outbuf, xtc2file)
            
            beginstep = DgramEdit(transition_id=TransitionId.BeginStep, config=config, ts=config_timestamp + 2)
            save_dgramedit(beginstep, outbuf, xtc2file)
            
            enable = DgramEdit(transition_id=TransitionId.Enable, config=config, ts=config_timestamp + 3)
            save_dgramedit(enable, outbuf, xtc2file)
            current_timestamp = config_timestamp + 3

        elif "end" in obj:
            disable = DgramEdit(transition_id=TransitionId.Disable, config=config, ts=current_timestamp + 1)
            save_dgramedit(disable, outbuf, xtc2file)
            current_timestamp = config_timestamp + 3
            endstep = DgramEdit(transition_id=TransitionId.EndStep, config=config, ts=current_timestamp + 2)
            save_dgramedit(endstep, outbuf, xtc2file)
            endrun = DgramEdit(transition_id=TransitionId.EndRun, config=config, ts=current_timestamp + 3)
            save_dgramedit(endrun, outbuf, xtc2file)
            break

        else:
            # Create L1Accept
            d0 = DgramEdit(transition_id=TransitionId.L1Accept, config=config, ts=obj["timestamp"])
            pnccd.raw.calib = obj["calib"]
            pnccd.raw.photon_energy = obj["photon_energy"]
            d0.adddata(pnccd.raw)
            save_dgramedit(d0, outbuf, xtc2file)
            current_timestamp = obj["timestamp"]



    xtc2file.close()

    if flag_test:
        test_output()
