import numpy as np


def process_tile(tile_key, halo_tile: np.ndarray):
    to_add = []
    to_kill = []

    tile_shape = halo_tile.shape[0] - 2, halo_tile.shape[1] - 2

    for i in range(1, tile_shape[0] + 1):
        for j in range(1, tile_shape[1] + 1):
            world_index = tile_shape[0] * tile_key[0] + (i - 1), tile_shape[1] * tile_key[1] + (j - 1)
            submatrix = halo_tile[i - 1:i + 2, j - 1:j + 2]
            nonzero_count = np.count_nonzero(submatrix)

            if halo_tile[i][j] and nonzero_count not in (3, 4):
                # any live cell with 2 or 3 neighbors survives, must add one for current cell
                to_kill.append(world_index)
            elif not halo_tile[i][j] and nonzero_count == 3:
                # any dead cell with 3 neighbors becomes live
                to_add.append(world_index)
    return [to_add, to_kill]