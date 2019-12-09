from typing import Tuple, MutableMapping
from dataclasses import dataclass
import numpy as np


@dataclass(frozen=True)
class Cell:
    x: int
    y: int

    def tile_key(self, tile_shape: Tuple[int, int]) -> Tuple[int, int]:
        return self.x // tile_shape[0], self.y // tile_shape[1]

    def tile_local_index(self, tile_key, tile_shape) -> Tuple[int, int]:
        return self.x - (tile_key[0] * tile_shape[0]), self.y - (tile_key[1] * tile_shape[1])


class GameBoard:
    def __init__(self, tile_size: int, starting_cells: Tuple[Cell, ...]):
        self._tile_shape: Tuple[int, int] = (tile_size, tile_size)
        self._tiles: MutableMapping[Tuple[int, int], np.ndarray] = {}

        self.add_cells(starting_cells)

    def _initialize_tile(self, tile_key: Tuple[int, int]):
        for i in range(-1, 2):
            for j in range(-1, 2):
                key = tile_key[0] + i, tile_key[1] + j
                if key not in self._tiles:
                    self._tiles[key] = np.zeros(self._tile_shape, dtype=np.bool)

    def add_cells(self, cells: Tuple[Cell, ...]):
        """
        Activates cells in the game board.

        Parameters
        ----------
        cells
            Tuple of cells to add.

        Raises
        ------
        RuntimeError
            When the cell to add is already active.

        Returns
        -------
            None
        """
        for cell in cells:
            tile_key = cell.tile_key(self._tile_shape)
            self._initialize_tile(tile_key)

            local_idx, local_idy = cell.tile_local_index(tile_key, self._tile_shape)
            if self._tiles[tile_key][local_idx, local_idy]:
                raise RuntimeError(f"attempted to add cell that already exists: {cell.x, cell.y}")

            self._tiles[tile_key][local_idx, local_idy] = True

    def kill_cells(self, cells: Tuple[Cell, ...]):
        """
        Kills cells in the game board.

        Parameters
        ----------
        cells

        Returns
        -------

        """
        for cell in cells:
            tile_key = cell.tile_key(self._tile_shape)
            if tile_key not in self._tiles:
                raise RuntimeError(f"attempted to kill cell that doesn't exist: {cell.x, cell.y}")
            tile = self._tiles[tile_key]
            local_idx, local_idy = cell.tile_local_index(tile_key, self._tile_shape)
            if not tile[local_idx, local_idy]:
                raise RuntimeError(f"attempted to kill cell that's already dead: {cell.x, cell.y}")
            tile[local_idx, local_idy] = False

        # self.cleanup_tiles()

    def _all_nearby_tiles_empty(self, tile_key):
        for i in range(-1, 2):
            for j in range(-1, 2):
                newkey = tile_key[0] + i, tile_key[1] + j
                if newkey in self._tiles and np.count_nonzero(self._tiles[newkey]) > 0:
                    return False
        return True

    def cleanup_tiles(self):
        keys = [k for k in self._tiles.keys()]
        for tile_key in keys:
            if self._all_nearby_tiles_empty(tile_key):
                del self._tiles[tile_key]

    def _build_halo(self, tile_key, halo_shape):
        ret = np.zeros(halo_shape, dtype=np.bool)

        # this code is trippy, don't look too hard at it

        # There are 8 other tiles we have to partially pull from
        up_left = (tile_key[0] - 1, tile_key[1] + 1)
        if up_left in self._tiles:
            ret[0, -1] = self._tiles[up_left][-1, 0]

        up_mid = (tile_key[0], tile_key[1] + 1)
        if up_mid in self._tiles:
            ret[1:ret.shape[0]-1, -1] = self._tiles[up_mid][:, 0]

        up_right = (tile_key[0] + 1, tile_key[1] + 1)
        if up_right in self._tiles:
            ret[-1, -1] = self._tiles[up_right][0, 0]

        mid_left = (tile_key[0] - 1, tile_key[1])
        if mid_left in self._tiles:
            ret[0, 1:ret.shape[1]-1] = self._tiles[mid_left][-1, :]

        mid_right = (tile_key[0] + 1, tile_key[1])
        if mid_right in self._tiles:
            ret[-1, 1:ret.shape[1]-1] = self._tiles[mid_right][0, :]

        down_left = (tile_key[0] - 1, tile_key[1] - 1)
        if down_left in self._tiles:
            ret[0, 0] = self._tiles[down_left][-1, -1]

        down_mid = (tile_key[0], tile_key[1] - 1)
        if down_mid in self._tiles:
            ret[1:ret.shape[0]-1, 0] = self._tiles[down_mid][:, -1]

        down_right = (tile_key[0] + 1, tile_key[1] - 1)
        if down_right in self._tiles:
            ret[-1, 0] = self._tiles[down_right][0, -1]

        return ret

    def tiles(self, with_halo=True):
        """
        Generates tiles for processing.

        Parameters
        ----------
        with_halo
            When True, will modify the generated ndarrays to add halo data
            "around" the original tile. Tile size will be original size + 2 in
            each dimension.

        Returns
        -------
        Generator of ndarrays
        """
        for tile_key, tile in self._tiles.items():
            if with_halo:
                new_shape = (tile.shape[0] + 2, tile.shape[1] + 2)
                halo = self._build_halo(tile_key, new_shape)
                halo[1: tile.shape[0] + 1, 1: tile.shape[1] + 1] = tile
            else:
                halo = tile
            yield tile_key, halo

    def for_display(self):
        keys = self._tiles.keys()

        minx = min(k[0] for k in keys)
        miny = min(k[1] for k in keys)

        maxx = max(k[0] for k in keys)
        maxy = max(k[1] for k in keys)

        xshift_factor = 0 - minx
        yshift_factor = 0 - miny

        xrange = (maxx - minx + 1) * self._tile_shape[0]
        yrange = (maxy - miny + 1) * self._tile_shape[1]
        ret = np.zeros(shape=(xrange, yrange), dtype=np.bool)

        for key, tile in self.tiles(with_halo=False):
            xmin, ymin = (key[0] + xshift_factor) * self._tile_shape[0], \
                         (key[1] + yshift_factor) * self._tile_shape[1]
            xmax, ymax = xmin + self._tile_shape[0], ymin + self._tile_shape[1]
            ret[xmin:xmax, ymin:ymax] = tile

        return ret
