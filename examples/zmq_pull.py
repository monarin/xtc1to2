"""Receives data from zmq and save in xtc2 format.

Usage:
    1. Activate psana2 and xtc1to2 environment
       source lcls2/setup_env.sh
       export PYTHONPATH=$HOME/xtc1to2/:$PYTHONPATH
    2. Receive data from zmq
"""
from xtc1to2.socket.zmqhelper import ZmqReceiver
import dgrampy as dp
from psana.psexp import TransitionId


# NameId setup
nodeId = 0
namesId = {
    "amopnccd": 0,
    "runinfo": 1,
}


# Setup socket for zmq connection
socket = "tcp://127.0.0.1:5557"
zmq_recv = ZmqReceiver(socket)


# Create config, algorithm, and detector
config = dp.config()
alg = dp.alg("raw", 1, 2, 3)
det = dp.det("amopnccd", "pnccd", "detnum1234")

runinfo_alg = dp.alg("runinfo", 0, 0, 1)
runinfo_det = dp.det("runinfo", "runinfo", "")


# Define data formats
datadef_dict = {
    "calib": (dp.DataType.FLOAT, 3),
    "photon_energy": (dp.DataType.DOUBLE, 0),
}
datadef = dp.datadef(datadef_dict)

runinfodef_dict = {
    "expt": (dp.DataType.CHARSTR, 1),
    "runnum": (dp.DataType.UINT32, 0),
}
runinfodef = dp.datadef(runinfodef_dict)


# Create Names
data_names = dp.names(
    config, det, alg, datadef, nodeId=nodeId, namesId=namesId["amopnccd"], segment=0
)
runinfo_names = dp.names(
    config,
    runinfo_det,
    runinfo_alg,
    runinfodef,
    nodeId=nodeId,
    namesId=namesId["runinfo"],
    segment=0,
)


# Start saving data
while True:
    obj = zmq_recv.recv_zipped_pickle()

    # Begin timestamp is needed (we calculate this from the first L1Accept)
    # to set the correct timestamp for all transitions prior to the first L1.
    if "start" in obj:
        config_timestamp = obj["config_timestamp"]
        dp.updatetimestamp(config, config_timestamp)
        dp.save(config)

        beginrun = dp.dgram(transid=TransitionId.BeginRun, ts=config_timestamp + 1)
        beginrun_data = {"expt": "amo06516", "runnum": 90}
        dp.adddata(beginrun, runinfo_names, runinfodef, beginrun_data)
        dp.save(beginrun)

        beginstep = dp.dgram(transid=TransitionId.BeginStep, ts=config_timestamp + 2)
        dp.save(beginstep)

        enable = dp.dgram(transid=TransitionId.Enable, ts=config_timestamp + 3)
        dp.save(enable)
    elif "end" in obj:
        disable = dp.dgram(transid=TransitionId.Disable, ts=current_timestamp + 1)
        dp.save(disable)

        endstep = dp.dgram(transid=TransitionId.EndStep, ts=current_timestamp + 2)
        dp.save(disable)

        endrun = dp.dgram(transid=TransitionId.EndRun, ts=current_timestamp + 3)
        dp.save(endrun)

        break
    else:
        # Create L1Accept
        d0 = dp.dgram(ts=obj["timestamp"])
        data = {
            "calib": obj["calib"],
            "photon_energy": obj["photon_energy"],
        }
        dp.adddata(d0, data_names, datadef, data)
        dp.save(d0)
        current_timestamp = obj["timestamp"]


# Write out dgrampy buffer to xtc2 file
with open("out.xtc2", "wb") as f:
    f.write(dp.get_buf())
