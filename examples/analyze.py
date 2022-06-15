from psana import DataSource
import os

# Need to increase smd0's chunk size for step data
os.environ['PS_SMD_CHUNKSIZE'] = '128000000'

# No. of events to read
max_events = 0

# Start datasource
#xtc_dir = '/cds/data/drpsrcf/users/monarin/spinifel_3iyf'
xtc_dir = '/reg/d/psdm/xpp/xpptut15/scratch/mona/amo06516'
ds = DataSource(exp="amo06516", run=90, dir=xtc_dir, max_events=max_events)
run = next(ds.runs())


# Obtain detectors
det = run.Detector("amopnccd")

# Obtain pixel_position and pixel_index_map from BeginRun dgram
if ds.exp=="amo06516":
    pixel_position = run.beginruns[0].scan[0].raw.pixel_position
else:
    pixel_position = run.beginruns[0].scan[0].raw.pixel_position_reciprocal
pixel_index_map = run.beginruns[0].scan[0].raw.pixel_index_map

# Access events
for nevt, evt in enumerate(run.events()):
    calib = det.raw.calib(evt)

    print(
        evt.timestamp,
        calib.shape,
        pixel_position.shape,
        pixel_index_map.shape,
    )

print(f'found {nevt+1} events')
