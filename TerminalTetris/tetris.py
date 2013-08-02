#!/usr/bin/env python

import logging
import numpy as np


class BaseSprite(object):

    matrix = (())

    def __init__(self, id_=1):
        self.logger = logging.getLogger(type(self).__name__)
        self.matrix = np.array(self.matrix, dtype=int) * id_
        self.logger.debug('\n' + str(self))

    @property
    def height(self):
        return self.matrix.shape[0]

    @property
    def width(self):
        return self.matrix.shape[1]

    def rotate(self, nb=1):
        self.matrix = np.rot90(self.matrix, nb)
        self.logger.debug('\n' + str(self))

    def unrotate(self, nb=1):
        self.rotate(-nb)

    def __str__(self):
        msg = '\n'.join([str(row) for row in self.matrix])
        return msg


class ISprite(BaseSprite):

     matrix = (
        (0, 1, 0, 0),
        (0, 1, 0, 0),
        (0, 1, 0, 0),
        (0, 1, 0, 0),
    )


class OSprite(BaseSprite):

    matrix = (
        (1, 1),
        (1, 1),
    )


class TSprite(BaseSprite):

    matrix = (
        (0, 0, 0),
        (1, 1, 1),
        (0, 1, 0),
    )


class LSprite(BaseSprite):

    matrix = (
        (0, 1, 0),
        (0, 1, 0),
        (0, 1, 1),
    )


class JSprite(BaseSprite):

    matrix = (
        (0, 1, 0),
        (0, 1, 0),
        (1, 1, 0),
    )


class ZSprite(BaseSprite):

    matrix = (
        (0, 0, 0),
        (1, 1, 0),
        (0, 1, 1),
    )


class SSprite(BaseSprite):

    matrix = (
        (0, 0, 0),
        (0, 1, 1),
        (1, 1, 0),
    )


sprite_types = [
    ISprite,
    OSprite,
    TSprite,
    LSprite,
    JSprite,
    ZSprite,
    SSprite,
]


import random


class TetrisError(Exception):
    pass


class Collision(TetrisError):
    pass


class GameOver(TetrisError):
    pass


class  Controller(object):

    def __init__(self, gamearea):
        self.logger = logging.getLogger(type(self).__name__)
        self.gamearea = gamearea
        self.sprite_count = 0

    def _prepare_new_sprite(self):
        self.sprite_count += 1
        sprite = random.choice(sprite_types)(self.sprite_count)
        sprite.rotate(random.randint(0, 3))
        return sprite

    def _compute_initial_position(self, sprite):
        #XXX compute starting row (how ugly!)
        row = 0
        for x in np.packbits(sprite.matrix, 1).flatten():
            if x > 0:
                break
            row -= 1
        hcenter = round((self.gamearea.width - self.sprite.width) / 2)
        position = np.array((row, hcenter))
        return position

    def start(self):
        self.next_sprite = self._prepare_new_sprite()
        self.next()

    def next(self):
        self.logger.info('next')
        self.sprite, self.next_sprite = self.next_sprite, self._prepare_new_sprite()
        self.position = self._compute_initial_position(self.sprite)
        self.logger.debug(self)
        try:
            self.gamearea.check_collision(self.sprite, self.position)
        except Collision:
            self.gamearea.freeze_sprite(self.sprite, self.position)
            self.logger.info('game over')
            raise GameOver('gamearea filled')

    def rotate(self):
        self.logger.info('rotate')
        self.sprite.rotate()
        try:
            self.gamearea.check_collision(self.sprite, self.position)
        except Collision:
            self.logger.debug('rewind')
            self.sprite.unrotate()

    def left(self):
        self.logger.info('left')
        try:
            self._move(np.array((0, -1)))
        except Collision:
            pass

    def right(self):
        self.logger.info('right')
        try:
            self._move(np.array((0, +1)))
        except Collision:
            pass

    def down(self):
        self.logger.info('down')
        try:
            self._move(np.array((+1, 0)))
        except Collision:
            # sprite is back to previous position already
            self.gamearea.freeze_sprite(self.sprite, self.position)
            self.next()

    def _move(self, vector):
        previous_position = self.position.copy()
        self.position += vector
        self.logger.debug(self)
        try:
            self.gamearea.check_collision(self.sprite, self.position)
        except Collision:
            self.logger.debug('rewind')
            self.position = previous_position
            self.logger.debug(self)
            raise  # 'down' needs to know about the collision

    def __str__(self):
        msg = '%s at %s' % (type(self.sprite).__name__, self.position)
        return msg


def compute_matrix_intersection_slices(a, b, position):
    return (
        slice(max(position[0], 0), position[0] + b.shape[0]),
        slice(max(position[1], 0), position[1] + b.shape[1]),
        slice(abs(min(position[0], 0)), min(a.shape[0] - position[0], b.shape[0])),
        slice(abs(min(position[1], 0)), min(a.shape[1] - position[1], b.shape[1])),
    )


def get_matrix_intersections(a, b, position):
    slices = compute_matrix_intersection_slices(a, b, position)
    a = a[slices[0], slices[1]]
    b = b[slices[2], slices[3]]
    return a, b


def merge_matrices(a, b, position):
    slices = compute_matrix_intersection_slices(a, b, position)
    a[slices[0], slices[1]] += b[slices[2], slices[3]]
    return a


class GameArea(object):

    shape = (20, 10)

    def __init__(self):
        self.logger = logging.getLogger(type(self).__name__)
        self.matrix = np.zeros(self.shape, dtype=int)

    @property
    def height(self):
        return self.matrix.shape[0]

    @property
    def width(self):
        return self.matrix.shape[1]

    def check_collision(self, sprite, position):
        bgmatrix, fgmatrix = get_matrix_intersections(self.matrix, sprite.matrix, position)
        bgmatrix, fgmatrix = np.sign(bgmatrix),  np.sign(fgmatrix)
        self.logger.debug('checking collision\n' + '\n'.join([' '.join(map(str, rows))
            for rows in zip(fgmatrix, bgmatrix, fgmatrix + bgmatrix)]))
        if np.sum(fgmatrix) != np.sum(np.sign(sprite.matrix)):
            self.logger.info('out of bound!')
            raise Collision('out of bound')
        if np.bitwise_and(fgmatrix, bgmatrix).any():
            self.logger.info('collision!')
            raise Collision('collision')
        self.logger.info('no collision')

    def freeze_sprite(self, sprite, position):
        merge_matrices(self.matrix, sprite.matrix, position)
        self.logger.info('shape freezed')


import itertools
import os
import termcolor

from termcolor import colored


color_names = termcolor.COLORS.keys()


class Display(object):

    def __init__(self, gamearea, controller):
        self.gamearea = gamearea
        self.controller = controller

    def _render_row(self, row):
        render_bloc = lambda n: colored('#', color_names[n % len(color_names)])
        line = ' '.join([render_bloc(cell) if cell else ' ' for cell in row])
        return line

    def _render_sprite(self, sprite):
        yield ''
        for row in sprite.matrix:
            line = self._render_row(row)
            yield line

    def _render_gamearea(self):
        matrix = self.gamearea.matrix.copy()
        merge_matrices(matrix, self.controller.sprite.matrix, self.controller.position)
        for row in matrix:
            line = '| %s |' % self._render_row(row)
            yield line

    def refresh(self):
        os.system('clear')
        next_sprite_renderer = self._render_sprite(self.controller.next_sprite)
        gamearea_renderer = self._render_gamearea()
        for lines in itertools.izip_longest(gamearea_renderer, next_sprite_renderer, fillvalue=''):
            line = (' ' * 4).join(lines)
            print line


import time


def main():
    #logging.basicConfig(level=logging.DEBUG)
    gamearea = GameArea()
    controller = Controller(gamearea)
    display = Display(gamearea, controller)

    controller.start()
    display.refresh()
    while True:
        try:
            controller.down()
            random.choice([
                controller.left,
                controller.right,
                controller.rotate,
            ])()
        except GameOver:
            break
        display.refresh()
        time.sleep(0.05)
    display.refresh()


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        pass

