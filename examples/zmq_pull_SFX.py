"""Receives data from zmq and save in xtc2 format.

Usage:
    1. ssh to the same node that you are running zmq_push.py
    2. Activate psana2 and xtc1to2 environment
       source lcls2/setup_env.sh
       export PYTHONPATH=$HOME/xtc1to2/:$PYTHONPATH
    2. Receive data from zmq

to add a variable, add a definition in datadef = {}

"""
from xtc1to2.socket.zmqhelper import ZmqReceiver
from psana.dgramedit import DgramEdit, AlgDef, DetectorDef
from psana.psexp import TransitionId
import numpy as np
import h5py
from psana import DataSource

verbosity = 1
#flag_test = True
flag_test = False

############

detector_name  = 'rayonix'

def test_output(ofname, data_shape, nevts):
    """Compares known data (saved to hdf5 by the push process) with read data."""
    print('testing...')
    f = h5py.File('out.hdf5', 'r')
    pixel_position = f['pixel_position']
    pixel_index_map = f['pixel_index_map']
    data = f['data']
    photon_energy = f['photon_energy']
    seg = f['seg']
    row = f['row']
    col = f['col']
    npix = f['npix']
    amax = f['amax']
    atot = f['atot']
    h5npeaks = f['npeaks']

    h5mask = f['mask']
    h5dict = f['peak_finder'].asstr()[()] # for strings

    ds = DataSource(files=ofname)
    run = next(ds.runs())
    det = run.Detector(detector_name)

    pp_det = run.Detector('pixel_position')
    pim_det = run.Detector('pixel_index_map')
    msk = run.Detector('mask')    
    ppf_dict =  run.Detector('pf_dict')

    max_npeaks = 2048
    data_array = np.zeros(([nevts]+data_shape), dtype=np.float32)

    photon_array = np.zeros(nevts, dtype=np.float64)

    npeaks_array = np.zeros(nevts , dtype=np.uint16)
    seg_array = np.zeros((nevts, max_npeaks) , dtype=np.uint16)
    row_array = np.zeros((nevts, max_npeaks) , dtype=np.uint16)
    col_array = np.zeros((nevts, max_npeaks) , dtype=np.uint16)
    npix_array = np.zeros((nevts, max_npeaks) , dtype=np.uint16)
    amax_array = np.zeros((nevts, max_npeaks) , dtype=np.float32)
    atot_array = np.zeros((nevts, max_npeaks) , dtype=np.float32)
    

    for i,evt in enumerate(run.events()):
        data_array[i,:,:,:] = det.raw.calib(evt)
        photon_array[i] = det.raw.photon_energy(evt)

        pixel_position_array = pp_det(evt)
        pixel_index_map_array = pim_det(evt)
        mask = msk(evt)
        pf_dict = ppf_dict(evt)

        npeaks = det.raw.npeaks(evt)
        npeaks_array[i] = npeaks
        if npeaks >0:
           row_array[i,0:npeaks] = det.raw.row(evt)
           col_array[i,0:npeaks] = det.raw.col(evt)
           npix_array[i,0:npeaks] = det.raw.npix(evt)
           amax_array[i,0:npeaks] = det.raw.amax(evt)
           atot_array[i,0:npeaks] = det.raw.atot(evt)



    assert np.array_equal(h5npeaks,npeaks_array)
    assert np.array_equal(h5dict, pf_dict)

    assert np.array_equal(row,row_array)
    assert np.array_equal(col,col_array)
    assert np.array_equal(npix,npix_array)
    assert np.array_equal(amax,amax_array)
    assert np.array_equal(atot,atot_array)
    assert np.array_equal(data,data_array)
    assert np.array_equal(photon_energy, photon_array)
    assert np.array_equal(pixel_position, pixel_position_array)
    assert np.array_equal(pixel_index_map, pixel_index_map_array)
    print("test passed (!)")


def save_dgramedit(dg_edit, outbuf, outfile):
    """ Save dgram edit to output buffer and write to file"""
    dg_edit.save(outbuf)
    outfile.write(outbuf[:dg_edit.size])


if __name__ == "__main__":

    # NameId setup
    nodeId = 1 
    namesId = {
        detector_name: 0,
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
    #ofname = 'out.xtc2'
    #xtc2file = open(ofname, "wb")

    
    # Create config, algorithm, and detector
    config = DgramEdit(transition_id=TransitionId.Configure)
    alg = AlgDef("raw", 1, 2, 3)
    det = DetectorDef(detector_name, detector_name, "detnum1234")

    runinfo_alg = AlgDef("runinfo", 0, 0, 1)
    runinfo_det = DetectorDef("runinfo", "runinfo", "")

    scan_alg = AlgDef("raw", 2, 0, 0)
    scan_det = DetectorDef("scan", "scan", "detnum1234")


    # Define data formats
    datadef = {
        "calib": (np.float32, 3),
        "photon_energy": (np.float64, 0),
	"npeaks": (np.uint16, 0),
	"seg": (np.uint16, 1),
	"row": (np.uint16, 1),
	"col": (np.uint16, 1),
	"npix": (np.uint16, 1),
	"amax": (np.float32, 1),
	"atot": (np.float32, 1),
    }

    runinfodef = {
        "expt": (str, 1),
        "runnum": (np.uint32, 0),
    }

    scandef = {
        "pixel_position": (np.float32, 4),
        "pixel_index_map": (np.int16, 4),
	"mask": (np.uint16, 3), 
        "pf_dict": (str,1),
    }


    # Create detetors
    det = config.Detector(det, alg, datadef, nodeId=nodeId, namesId=namesId[detector_name])

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


    nevts = 0

    # Start saving data
    while True:
        obj = zmq_recv.recv_zipped_pickle()

        # Begin timestamp is needed (we calculate this from the first L1Accept)
        # to set the correct timestamp for all transitions prior to the first L1.
        if "start" in obj:
            data_shape = obj["data_shape"]
            config_timestamp = obj["config_timestamp"]
            config.updatetimestamp(config_timestamp)

	    ##
            runinfo.runinfo.expt = obj["exp"] 
            runinfo.runinfo.runnum = obj["run"]
            
            ofname = 'converted/'+obj["exp"]+'_'+str(obj["run"])+'.xtc2'
            print("saving to:", ofname)

            xtc2file = open(ofname, "wb")
            ##

            save_dgramedit(config, outbuf, xtc2file)

            beginrun = DgramEdit(transition_id=TransitionId.BeginRun, config=config, ts=config_timestamp + 1)
            '''
	    ##
            runinfo.runinfo.expt = obj["exp"] 
            runinfo.runinfo.runnum = obj["run"]
            
            ofname = obj["exp"]+'.xtc2'
            print("saving to:", ofname)

            xtc2file = open(ofname, "wb")
            ##
            '''
            beginrun.adddata(runinfo.runinfo)
            scan.raw.pixel_position = obj['pixel_position']
            scan.raw.pixel_index_map = obj['pixel_index_map']

            scan.raw.mask = obj['mask']
            scan.raw.pf_dict = obj['pf_dict']

            beginrun.adddata(scan.raw)
            save_dgramedit(beginrun, outbuf, xtc2file)
            
            beginstep = DgramEdit(transition_id=TransitionId.BeginStep, config=config, ts=config_timestamp + 2)
            save_dgramedit(beginstep, outbuf, xtc2file)
            
            enable = DgramEdit(transition_id=TransitionId.Enable, config=config, ts=config_timestamp + 3)
            save_dgramedit(enable, outbuf, xtc2file)
            current_timestamp = config_timestamp + 3



        elif "end" in obj:
            print("received end")
            disable = DgramEdit(transition_id=TransitionId.Disable, config=config, ts=current_timestamp + 1)
            save_dgramedit(disable, outbuf, xtc2file)
            current_timestamp = config_timestamp + 3
            endstep = DgramEdit(transition_id=TransitionId.EndStep, config=config, ts=current_timestamp + 2)
            save_dgramedit(endstep, outbuf, xtc2file)
            endrun = DgramEdit(transition_id=TransitionId.EndRun, config=config, ts=current_timestamp + 3)
            save_dgramedit(endrun, outbuf, xtc2file)
            break

        else:
            nevts+=1
            # Create L1Accept
            d0 = DgramEdit(transition_id=TransitionId.L1Accept, config=config, ts=obj["timestamp"])
            det.raw.calib = obj["calib"]
            det.raw.photon_energy = obj["photon_energy"]

            det.raw.npeaks = obj["npeaks"]


            if verbosity == 1:
               print('++++++++++++++++++++++')
               print('npeaks', obj['npeaks'])
               print('row',obj['row'])
               print('++++++++++++++++++++++')

            if type(obj['seg'])==type(None):
               det.raw.seg = np.empty(1,dtype=np.uint16)
               det.raw.row = np.empty(1,dtype=np.uint16)
               det.raw.col = np.empty(1,dtype=np.uint16)
               det.raw.npix = np.empty(1,dtype=np.uint16)
               det.raw.amax = np.empty(1,dtype=np.float32)
               det.raw.atot = np.empty(1,dtype=np.float32)

            else:
               det.raw.seg = obj['seg'] 
               det.raw.row = obj['row']
               det.raw.col = obj['col']
               det.raw.npix = obj['npix']
               det.raw.amax = obj['amax']
               det.raw.atot = obj['atot']

            d0.adddata(det.raw)
            save_dgramedit(d0, outbuf, xtc2file)
            current_timestamp = obj["timestamp"]



    xtc2file.close()

    if flag_test:
        #pass
        test_output(ofname, data_shape, nevts)
