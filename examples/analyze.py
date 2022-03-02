from psana import DataSource


# Start datasource
xtc_dir = "/cds/home/m/monarin/tmp/amo06516"
ds = DataSource(exp="amo06516", run=85, dir=xtc_dir)
run = next(ds.runs())


# Obtain detectors
det = run.Detector("amopnccd")
pp_det = run.Detector("pixel_position")
pim_det = run.Detector("pixel_index_map")


# Access events
for nevt, evt in enumerate(run.events()):
    # Save images in a list
    calibs.append(det.raw.calib(evt))

    # Per run variables
    photon_energy = det.raw.photon_energy(evt)
    pixel_position = pp_det(evt)
    pixel_index_map = pim_det(evt)

    # Ideal world spinifel
    if nevt == N_images_per_rank:
        solve_ac(calibs, photon_energy, pixel_position, pixel_index_map)

    print(
        evt.timestamp,
        photon_energy,
        calib.shape,
        pixel_position.shape,
        pixel_index_map.shape,
    )
