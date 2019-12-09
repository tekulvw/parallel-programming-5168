from .celeryapp import app
from ..sequential.tasks import process_tile as process_tile_seq

process_tile = app.task(process_tile_seq)
