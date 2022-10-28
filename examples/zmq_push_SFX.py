"""An example that reads in lcls1 experiment and selects events (as 
listed in csv file) then pushes data to be saved in lcls2 format via zmq.

Usage: 
    1. Get psana1 environment (source /reg/g/psdm/etc/psconda.sh)
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
from psalgos.pypsalgos import PyAlgos

'''
### mfx
exp, run, mode, detector_name = "mfxp22820", "13", "idx", "Rayonix"
data_shape = [1, 1920, 1920]
# mask = np.load('/reg/data/ana03/scratch/smarches/temp/mfxp22820/smarches/psocake/r0013/mask.npy')
geom = ('/reg/d/psdm/mfx/mfxp22820/calib/Camera::CalibV1/MfxEndstation.0:Rayonix.0/geometry/0-end.data') 
### 
'''

### cxi
exp, run, mode, detector_name = "cxic0415", "101", "idx", "DscCsPad"
data_shape = [32,185,388]
mask=np.ones((data_shape), dtype=np.uint16)
geom = ( "/reg/d/psdm/cxi/cxic0415/calib/CsPad::CalibV1/CxiDs1.0:Cspad.0/geometry/14-end.data" )
##################################

pf_dict={"type":'v3r3', "rank":3, "r0":3.0, "dr":2.0, "nsigm":10, "npix_min":2, "npix_max":30, "amax_thr":300, "atot_thr": 600, "son_min":10}

##################################


alg = PyAlgos()
alg.set_peak_selection_pars(npix_min=pf_dict["npix_min"], npix_max=pf_dict["npix_max"], amax_thr=pf_dict["amax_thr"], atot_thr=pf_dict["atot_thr"], son_min=pf_dict["son_min"])

peak_finder = lambda img: alg.peak_finder_v3r3(img, rank=pf_dict['rank'], r0=pf_dict['r0'], dr=pf_dict['dr'], nsigm=pf_dict['nsigm'], mask=mask )

###################################



# Set test flag for selecting out event 796 - 798 and run assert test
test_flag = True
test_flag = False

verbosity = 0.5


# Initialize all readers
img_reader = PsanaImg(exp, run, mode, detector_name)
phe_reader = PsanaPhotonEnergy(exp, run, mode)
gmt_reader = PsanaGeometry(geom)

#######
"""
##
event_num_list = list(range(10000))
for i, event_num in enumerate(event_num_list):
    print("i", i, "event_num", event_num)    
    img = img_reader.get(event_num, calib=True)
    photon_energy = phe_reader.get(event_num)
    ts = img_reader.timestamp(event_num)
##  
"""

# Initialize zmq sender
socket = "tcp://127.0.0.1:5557"
zmq_send = ZmqSender(socket)

# Get list of images by event no. otherwise use 796, 797, 798
if test_flag:
    event_num_list = [0,1,2,3, 4, 797]
    data_array = np.zeros(([len(event_num_list)]+data_shape), dtype=np.float32)
    photon_array = np.zeros(len(event_num_list), dtype=np.float64)
    # max 2048 peaks, all 0s = no peaks, get the number of peaks
    #seg_list = []
    npeaks_array = np.zeros(len(event_num_list) , dtype=np.uint16)
    max_npeaks = 2048
    seg_array = np.zeros((len(event_num_list), max_npeaks) , dtype=np.uint16)
    row_array = np.zeros((len(event_num_list), max_npeaks) , dtype=np.uint16)
    col_array = np.zeros((len(event_num_list), max_npeaks) , dtype=np.uint16)
    npix_array = np.zeros((len(event_num_list), max_npeaks) , dtype=np.uint16)
    amax_array = np.zeros((len(event_num_list), max_npeaks) , dtype=np.float32)
    atot_array = np.zeros((len(event_num_list), max_npeaks) , dtype=np.float32)


else:
    event_num_list = []
    with open('amo06516_r90_single_hits.csv') as csvfile:
        csvreader = csv.reader(csvfile, delimiter=',')
        for row in csvreader:
            event_num_list += list(map(int, row))

# print(event_num_list)

event_num_list = list(range(84))

# event_num_list = list(range(100000))
event_num_list = range(100000)


for i, event_num in enumerate(event_num_list):
    # print("i", i, "event_num", event_num)
    try:
       img = img_reader.get(event_num, calib=True)
       photon_energy = phe_reader.get(event_num)
       ts = img_reader.timestamp(event_num)
    except:
       break

    ##############################3

    seg, row, col, npix, amax, atot = None, None, None, None, None, None
    npeaks = np.uint16(0)

    peaks = peak_finder(img)

    npeaks = np.uint16(peaks.shape[0])
    # get the number of peaks

    if peaks.size>0:       
       seg = np.uint16(peaks[:,0])
       row = np.uint16(peaks[:,1])
       col = np.uint16(peaks[:,2])
       npix = np.uint16(peaks[:,3])
       amax = np.float32(peaks[:,4])
       atot = np.float32(peaks[:,5]) 

    if verbosity >= 1:
       print('++++++++++++++++++++++')
       print('npeaks', npeaks)
       print('row',row)
       print('++++++++++++++++++++++')

    if test_flag:
        data_array[i,:,:,:] = img
        photon_array[i] = photon_energy
        # seg_list.append(seg)
        npeaks_array[i] = npeaks

        if npeaks >0:
           seg_array[i,0:npeaks] = seg
           row_array[i,0:npeaks] = row
           col_array[i,0:npeaks] = col
           npix_array[i,0:npeaks] = npix
           amax_array[i,0:npeaks] = amax
           atot_array[i,0:npeaks] = atot

    if i == 0:
        # Send beginning timestamp - this will create config, beginrun,
        # beginstep, and enable on the client.
        start_dict = {
            "start": True, 
            "config_timestamp": ts.time() - 10,
            "pixel_position": gmt_reader.pixel_position,
            "pixel_index_map": gmt_reader.pixel_index_map,
        }
        start_dict.update({"mask":mask, 'pf_dict': str(pf_dict), 'data_shape':data_shape}) 
        start_dict.update({"exp":exp, 'run': int(run)}) 

        zmq_send.send_zipped_pickle(start_dict)
        
    data = {
        "calib": img,
        "photon_energy": photon_energy,
        "timestamp": ts.time(),
        "npeaks": npeaks,
	"seg": seg,
	"row": row,
	"col": col,
	"npix": npix,
	"amax": amax,
	"atot": atot,
    }
    if verbosity > 0:
       print(
            f"event_num={event_num} ts={ts.time()} img={img.shape} dtype={img.dtype} photon energy:{photon_energy:.3f}"
       )

    # Send the dataset
    zmq_send.send_zipped_pickle(data)

# Send end message

done_dict = {"end": True}
#done_dict = {"end": False}
zmq_send.send_zipped_pickle(done_dict)

if test_flag:
    print("writing file")
    with h5py.File("out.hdf5", "w") as f:
        f.create_dataset("pixel_position", data=gmt_reader.pixel_position)
        f.create_dataset("pixel_index_map", data=gmt_reader.pixel_index_map)
        f.create_dataset("data", data=data_array)
        f.create_dataset("photon_energy", data=photon_array)

        f.create_dataset("mask", data = mask)
        f.create_dataset("npeaks", data = npeaks_array)
        f.create_dataset("seg", data = seg_array)
        f.create_dataset("row", data = row_array)
        f.create_dataset("col", data = col_array)
        f.create_dataset("npix", data = npix_array)
        f.create_dataset("amax", data = amax_array)
        f.create_dataset("atot", data = atot_array)
        f.create_dataset("peak_finder", data = str(pf_dict))
       

