from psana import DataSource
import os

# Need to increase smd0's chunk size for step data
os.environ['PS_SMD_CHUNKSIZE'] = '268435456'


# Start datasource
#xtc_dir = '/cds/home/m/monarin/xtc1to2/examples/data'
xtc_dir = '/cds/data/drpsrcf/users/monarin/amo06516/'
ds = DataSource(exp="amo06516", run=90, dir=xtc_dir)
run = next(ds.runs())


# Obtain detectors
det = run.Detector("amopnccd")
pp_det = run.Detector("pixel_position")
pim_det = run.Detector("pixel_index_map")


# Access events
for nevt, evt in enumerate(run.events()):
    calib = det.raw.calib(evt)

    # Per run variables
    photon_energy = det.raw.photon_energy(evt)
    pixel_position = pp_det(evt)
    pixel_index_map = pim_det(evt)

    print(
        evt.timestamp,
        photon_energy,
        calib.shape,
        pixel_position.shape,
        pixel_index_map.shape,
    )
