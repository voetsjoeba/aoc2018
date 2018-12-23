#!/usr/bin/env python
from __future__ import print_function, absolute_import
import sys, os, re
from collections import namedtuple, defaultdict
from math import floor
from pprint import pprint
from copy import copy, deepcopy
from hashlib import sha1

OPEN = 0
TREES = 1
LUMBERYARD = 2

class Tile(object):
	def __init__(self, x, y, char):
		self.x = x
		self.y = y
		self.type = (OPEN if char == "." else (TREES if char == "|" else LUMBERYARD))

	def visualize(self):
		return ("." if self.type == OPEN else ("|" if self.type == TREES else "#"))

def new_type(current_type, counters):
	new_type = current_type
	if current_type == OPEN and counters[TREES] >= 3:
		new_type = TREES
	elif current_type == TREES and counters[LUMBERYARD] >= 3:
		new_type = LUMBERYARD
	elif current_type == LUMBERYARD:
		new_type = LUMBERYARD if (counters[LUMBERYARD] >= 1 and counters[TREES] >= 1) else OPEN
	return new_type

class Map(object):
	def __init__(self, lines):
		height = len(lines)
		width = len(lines[0])
		grid = [[None]*width for i in range(0,height)]
		for y in range(0, height):
			for x in range(0, width):
				char = lines[y][x]
				grid[y][x] = Tile(x, y, char)

		self.width = width
		self.height = height
		self._source = grid
		self._dest = deepcopy(grid)

	def advance(self):
		rolling_counts = [0, 0, 0] # open, trees, lumberyard

		# convolution time (kind of)
		for a,b in ((1,0), (1,1), (0,1)):
			tile = self._source[b][a]
			rolling_counts[tile.type] += 1

		for y in range(0, self.height):
			row_start_counts = rolling_counts[:]

			for x in range(0, self.width):
				current_type = self._source[y][x].type
				self._dest[y][x].type = new_type(current_type, rolling_counts)

				# roll the window one X coordinate to the right; drop N counts from the left (if any), add N from the right (if any)
				# . . .        - . . +
				# . x>n    ->  - + - +
				# . . .        - . . +

				# subtract three on the left
				if x > 0 and y > 0:              rolling_counts[self._source[y-1][x-1].type] -= 1
				if x > 0:                        rolling_counts[self._source[y]  [x-1].type] -= 1
				if x > 0 and y < self.height-1:  rolling_counts[self._source[y+1][x-1].type] -= 1

				# add three on the right
				if x < self.width-2 and y > 0:              rolling_counts[self._source[y-1][x+2].type] += 1
				if x < self.width-2:                        rolling_counts[self._source[y]  [x+2].type] += 1
				if x < self.width-2 and y < self.height-1:  rolling_counts[self._source[y+1][x+2].type] += 1

				# count old center, uncount new center
				rolling_counts[self._source[y][x].type] += 1
				if x < self.width-1: rolling_counts[self._source[y][x+1].type] -= 1

			# finished a row; reset the counters to the ones we had at the beginning of this row,
			# subtract 3 counts from the last one and add 3 from the next, then resume scanning to the right
			# . . .       - - -
			# . y .   ->  . + .
			# . n .       . - .
			#             + + +
			x = 0
			rolling_counts = row_start_counts # no need for a copy here

			# subtract three from the top
			if y > 0 and x > 0:             rolling_counts[self._source[y-1][x-1].type] -= 1
			if y > 0:                       rolling_counts[self._source[y-1][x].type]   -= 1
			if y > 0 and x < self.width-1:  rolling_counts[self._source[y-1][x+1].type] -= 1

			# add three on the bottom
			if y < self.height-2 and x > 0:             rolling_counts[self._source[y+2][x-1].type] += 1
			if y < self.height-2:                       rolling_counts[self._source[y+2][x].type]   += 1
			if y < self.height-2 and x < self.width-1:  rolling_counts[self._source[y+2][x+1].type] += 1

			# count old center, uncount new counter
			rolling_counts[self._source[y][x].type] += 1
			if y < self.height-1: rolling_counts[self._source[y+1][x].type] -= 1

		# swap source and dest for the next iteration
		self._source, self._dest = self._dest, self._source

	def visualize(self):
		result = ""
		vwidth = len(str(self.height-1))
		result += " "*vwidth + " " + "".join("%-2d" % x for x in range(0, self.width)) + "\n"
		for y in range(0, self.height):
			result += (("%"+str(vwidth)+"d") % y) + " "
			for x in range(0, self.width):
				result += self._source[y][x].visualize() + " "
			result += "\n"
		return result

	def tiles(self):
		for y in range(0, self.height):
			for x in range(0, self.width):
				yield self._source[y][x]

class Day18(object):
	def __init__(self, filename):
		with open(filename, "r") as f:
			self.lines = map(str.strip, f.readlines())

	def run_simulation(self, num_ticks):
		# keep hashes of each state reached so we can identify cycles
		hashes = {} # hash -> seen after N ticks were completed
		map = Map(self.lines)

		ticks_completed = 0
		while ticks_completed < num_ticks:
			hash = sha1(map.visualize()).hexdigest()
			if hash in hashes:
				# found a cycle; repeat it as far as we can
				cycle_len = ticks_completed - hashes[hash]
				print("found a cycle of length %d" % cycle_len)
				while ticks_completed + cycle_len <= num_ticks:
					ticks_completed += cycle_len
				hashes = {}
			else:
				hashes[hash] = ticks_completed
				map.advance()
				ticks_completed += 1

		print(map.visualize())
		lumber_tiles = 0
		tree_tiles = 0
		for tile in map.tiles():
			if tile.type == LUMBERYARD: lumber_tiles += 1
			if tile.type == TREES: tree_tiles += 1

		return lumber_tiles * tree_tiles

	def part1(self):
		return self.run_simulation(10)

	def part2(self):
		return self.run_simulation(1000000000)

if __name__ == "__main__":
	day = Day18("day18.txt")
	print(day.part1())
	print(day.part2())