from PSCalib.GeometryAccess import GeometryAccess
import numpy as np


class PsanaGeometry:
    """A getter that reads in lcls1-style geometry file.

    Use this access info from  geometry file (*-end.data).
    Available info is set as class attributes.
    """

    pixel_position = None
    pixel_index_map = None

    def __init__(self, geom):
        """Sets coordinate in real space (convert to m)."""
        cframe = 0  # fixed to psana style (1 is for lab conventions)
        geometry = GeometryAccess(geom, cframe=cframe)

        # Stores a tuple of x,y, and z coordinate arrays
        pixel_coords = geometry.get_pixel_coords(cframe=cframe)
        pixel_coord_indexes = geometry.get_pixel_coord_indexes(cframe=cframe)

        # Converts to metre unit for pixel coordinates
        temp = [np.asarray(t) * 1e-6 for t in pixel_coords]
        temp_index = [np.asarray(t) for t in pixel_coord_indexes]

        # The shape of each axis is represented by five numbers (for this det)
        # e.g. (1,2,2,512,512). We calculate no. of panels by multiplying
        # all numbers except the last two (#pixel_x, #pixel_y).
        panel_num = np.prod(temp[0].shape[:-2])

        shape = (panel_num, temp[0].shape[-2], temp[0].shape[-1])
        pixel_position = np.zeros(shape + (3,))  # x,y,z
        pixel_index_map = np.zeros(shape + (2,))  # x,y

        for n in range(3):
            pixel_position[..., n] = temp[n].reshape(shape)

        for n in range(2):
            pixel_index_map[..., n] = temp_index[n].reshape(shape)
        pixel_index_map = pixel_index_map.astype(np.int64)

        self.pixel_position = pixel_position
        self.pixel_index_map = pixel_index_map
