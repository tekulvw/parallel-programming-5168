import asyncio
import time
import random
from typing import List

from celery import group
import click
from matplotlib import pyplot as plt
import matplotlib.animation as animation
import numpy as np

from lifegame.board import GameBoard, Cell
from lifegame.sequential.tasks import process_tile as process_tile_seq
from lifegame.celeryapp.tasks import process_tile as process_tile_celery
from lifegame.coroutine.tasks import process_tile as process_tile_coroutine


def execute_tile_results(board, group_result):
    cell_add = {Cell(*to_add) for task_result in group_result for to_add in task_result[0]}
    cell_kill = {Cell(*to_kill) for task_result in group_result for to_kill in task_result[1]}

    assert any(kill_cell in cell_add for kill_cell in cell_kill) is False
    assert any(add_cell in cell_kill for add_cell in cell_add) is False

    board.kill_cells(tuple(cell_kill))
    board.add_cells(tuple(cell_add))


def run_game_sync(use_celery: bool, starting_cells, iterations: int, tile_size: int):
    if iterations < 0:
        raise ValueError("iteration count cannot be 0")

    board = GameBoard(tile_size, starting_cells)

    fig, ax = plt.subplots()
    matrice = ax.matshow(board.for_display())

    '''for _ in range(iterations):
        if use_celery:
            g = group(process_tile_celery.s(key, tile) for key, tile in board.tiles())()
            group_result = g.get()
        else:
            group_result = [process_tile_seq(key, tile) for key, tile in board.tiles()]
        execute_tile_results(board, group_result)'''

    def anifunc(*args):
        if use_celery:
            g = group(process_tile_celery.s(key, tile) for key, tile in board.tiles())()
            group_result = g.get()
        else:
            group_result = [process_tile_seq(key, tile) for key, tile in board.tiles()]
        execute_tile_results(board, group_result)

        matrice.set_array(board.for_display())

    ani = animation.FuncAnimation(fig, anifunc, frames=iterations, interval=200)
    plt.show()


async def run_game_async(starting_cells, iterations: int, tile_size: int):
    if iterations < 0:
        raise ValueError("iteration count cannot be 0")

    board = GameBoard(tile_size, starting_cells)

    for _ in range(iterations):
        tasks = [asyncio.create_task(process_tile_coroutine(key, tile)) for key, tile in board.tiles()]
        group_result = await asyncio.gather(*tasks)
        execute_tile_results(board, group_result)


def get_cells(tile_size: int) -> List[Cell]:
    xs = list(range(0, tile_size * 4))
    ys = list(range(0, tile_size * 4))

    random.shuffle(xs)
    random.shuffle(ys)

    cells = [Cell(x, y) for x, y in zip(xs, ys)]
    print(len(cells))
    # return cells[:round(len(cells) * 0.9)]
    return [
        Cell(0, 1),
        Cell(1, 0),
        Cell(2, 0),
        Cell(2, 1),
        Cell(2, 2),
    ]


def time_func(func, *args, **kwargs):
    start = time.time()
    func(*args, **kwargs)
    end = time.time()

    print(f"Run time: {end - start} seconds")


@click.group()
def cli():
    pass


@cli.command()
@click.argument("iterations", type=int)
@click.argument("tile_size", type=int)
def sequential(iterations: int, tile_size: int):
    time_func(
        run_game_sync,
        use_celery=False,
        starting_cells=get_cells(tile_size),
        iterations=iterations,
        tile_size=tile_size,
    )


@cli.command()
@click.argument("iterations", type=int)
@click.argument("tile_size", type=int)
def celery(iterations: int, tile_size: int):
    time_func(
        run_game_sync,
        use_celery=True,
        starting_cells=get_cells(tile_size),
        iterations=iterations,
        tile_size=tile_size,
    )


@cli.command()
@click.argument("iterations", type=int)
@click.argument("tile_size", type=int)
def coroutine(iterations: int, tile_size: int):
    time_func(
        asyncio.run,
        run_game_async(get_cells(tile_size), iterations, tile_size),
    )


if __name__ == "__main__":
    cli()
