from asyncio import coroutine

from ..sequential.tasks import process_tile as process_tile_seq

process_tile = coroutine(process_tile_seq)
