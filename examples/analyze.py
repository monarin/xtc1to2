from psana import DataSource


# Start datasource
xtc_dir= '/cds/home/m/monarin/tmp/amo06516'
ds = DataSource(exp='amo06516', run=85, dir=xtc_dir)
run = next(ds.runs())


# Obtain detectors
det = run.Detector('amopnccd')
pp_det = run.Detector('pixel_position')
pim_det = run.Detector('pixel_index_map')


# Access events
for evt in run.events():
    calib = det.raw.calib(evt)
    photon_energy = det.raw.photon_energy(evt)
    pixel_position = pp_det(evt)
    pixel_index_map = pim_det(evt)
    print(evt.timestamp, photon_energy, calib.shape, pixel_position.shape, pixel_index_map.shape)
