#!/usr/bin/env python
from __future__ import print_function, absolute_import
import sys, os, re
from collections import namedtuple, defaultdict
from math import floor
from pprint import pprint
from copy import copy

Pos = namedtuple("Pos", "x y")

def clamp(value, min_value, max_value):
	if value < min_value: return min_value
	if value > max_value: return max_value
	return value

SAND = 0
CLAY = 1
DOWN = 2
HORIZONTAL = 3
LEFT = 4
RIGHT = 5
class Tile(object):
	def __init__(self, x, y, type):
		self.x = x
		self.y = y
		self.type = type
		self.visited = False # has any water touched this tile?
		self.drop_directions = set() # does this tile have a drop in either direction? (LEFT, RIGHT or both)

	def type_name(self):
		return "Clay" if self.type == CLAY else "Sand"

class WaterFront(object):
	def __init__(self, x, y, map):
		self.queue = [(x, y, DOWN)] # pending flow expansion points
		self.map = map

	def flow(self, stop_at=0, skim_overflow=False):
		num_iters = 0
		while self.queue:
			if stop_at > 0 and num_iters >= stop_at:
				if num_iters == stop_at: print("breaking after %d iterations" % (num_iters,))
				self.visualize_img()
				raw_input()
			num_iters += 1

			# expand the front of the water flow outwards, taking into account the flow direction at each position.
			expansion_point, queue = self.queue[0], self.queue[1:]
			self.queue = queue

			x = expansion_point[0]
			y = expansion_point[1]
			direction = expansion_point[2]

			if direction == DOWN:
				self.map.tile_at(x,y).visited = (not skim_overflow)

				# visit tiles downwards until we hit clay or the edge of the map
				while y < self.map.max_y:
					tile_down = self.map.tile_at(x, y+1)
					if tile_down.type == CLAY:
						self.queue.append((x, y, HORIZONTAL))
						break
					y += 1
					tile_down.visited = tile_down.visited or (not skim_overflow)

				# we hit the bottom of the map, no further expansions needed
			else:
				# scan outwards to the left and right, and see if at any point we would drop down.
				# if so, record a drop marker at the tile immediately prior to the drop (in that direction), and queue up a new downwards expansion point at the drop location.
				#
				# if during the scan we encounter a drop marker in our current direction, then we know that someone else has already taken the drop, and we need not repeat it.
				# conversely, if we encounter a drop marker in the OTHER direction, then that means that drop was not a proper drop down to a lower level,
				# but instead a local one within a basin that we ran into an edge of later and are now filling from the other side. hence, these can be removed.
				#
				# otherwise, if we hit walls on both sides, then we know that our scan line is fully contained, and we can move up on y coordinate and repeat another
				# horizontal scan to see if we fall off at that level.
				assert y < self.map.max_y
				self.map.tile_at(x, y).visited = True
				contained = {LEFT: False, RIGHT: False}

				for step, direction in [(-1, LEFT), (1, RIGHT)]:
					scan_x = x
					while scan_x > self.map.min_x and scan_x < self.map.max_x:
						tile = self.map.tile_at(scan_x + step, y)
						below = self.map.tile_at(scan_x + step, y + 1)
						if tile.type == CLAY: # we hit a wall
							contained[direction] = True
							break

						# discard any drop markers made in the other direction, we're back up to their level from the other side.
						# but if we have one in the current direction, we can stop because someone else has already taken the drop
						tile.drop_directions.intersection_update(set([direction]))
						if direction in tile.drop_directions:
							break

						if below.type != CLAY and (not below.visited):
							# found a new drop; queue up a downward expansion at the drop point, and record a marker at the tile immediately preceding it
							assert (not tile.visited) # otherwise we should have encountered a drop marker
							self.queue.append((tile.x, tile.y, DOWN))
							self.map.tile_at(tile.x - step, tile.y).drop_directions.add(direction)
							tile.visited = True
							break

						tile.visited = True
						scan_x += step

				if contained[LEFT] and contained[RIGHT]:
					self.queue.append((x, y-1, HORIZONTAL))
				elif skim_overflow:
					# this line overflows on one or both sides; if we're not counting overflow, mark them all as unvisited again
					scan_x = x
					while True:
						scan_tile = self.map.tile_at(scan_x, y)
						self.map.tile_at(scan_x, y).visited = False
						if (LEFT in scan_tile.drop_directions or scan_tile.type) == CLAY:
							break
						scan_x -= 1

					scan_x = x
					while True:
						scan_tile = self.map.tile_at(scan_x, y)
						self.map.tile_at(scan_x, y).visited = False
						if (RIGHT in scan_tile.drop_directions or scan_tile.type) == CLAY:
							break
						scan_x += 1

	def visualize(self):
		return self.visualize_ascii()

	def visualize_ascii(self):
		result = ""
		for y in range(self.map.min_y, self.map.max_y + 1):
			for x in range(self.map.min_x, self.map.max_x + 1):
				tile = self.map.tile_at(x, y)
				char = "#"
				if tile.type != CLAY:
					char = " " if tile.wet else "."
				result += char
			result += "\n"
		return result

	def visualize_img(self):
		COLOR_WATER = (0,0,255)
		COLOR_SAND  = (255,255,255)
		COLOR_CLAY  = (0,0,0)
		COLOR_EXPANSION_HORIZONTAL = (0,255,0)
		COLOR_EXPANSION_DOWN = (255,0,255)
		COLOR_DROP_MARKER = (200,200,255)

		rgb_data = []
		for tile in self.map.tiles():
			expands_horizontal = ((tile.x, tile.y, HORIZONTAL) in self.queue)
			expands_down = ((tile.x, tile.y, DOWN) in self.queue)

			if tile.visited:         color = COLOR_WATER
			elif tile.type == CLAY:  color = COLOR_CLAY
			else:                    color = COLOR_SAND

			if len(tile.drop_directions) != 0: color = COLOR_DROP_MARKER

			if expands_horizontal:   color = COLOR_EXPANSION_HORIZONTAL
			elif expands_down:       color = COLOR_EXPANSION_DOWN

			rgb_data.append(color)

		from PIL import Image
		img = Image.new('RGB', (self.map.width, self.map.height))
		img.putdata(rgb_data)
		img.save("day17.png", "PNG")

class Map(object):
	@classmethod
	def parse(cls, lines):
		# the inputs may specify the same tile multiple times, so keep track of them by position so we don't duplicate any
		min_y = None
		min_x = None
		max_y = None
		max_x = None

		clay_tiles = {}
		for line in lines:
			m = re.match(r"(x|y)=(\d+), (x|y)=(\d+)..(\d+)", line)

			xy = (m.group(1) == "x")
			fixed_coord = int(m.group(2))
			range_start = int(m.group(4))
			range_end = int(m.group(5))

			for i in range(range_start, range_end+1):
				pos = Pos(x=fixed_coord, y=i) if xy else Pos(x=i, y=fixed_coord)
				if pos not in clay_tiles:
					clay_tiles[pos] = Tile(pos.x, pos.y, CLAY)
					min_x = min(min_x if min_x is not None else pos.x, pos.x)
					max_x = max(max_x if max_x is not None else pos.x, pos.x)
					min_y = min(min_y if min_y is not None else pos.y, pos.y)
					max_y = max(max_y if max_y is not None else pos.y, pos.y)


		# expand min_x and max_x by one to allow water to flow down on the extremes
		min_x -= 1
		max_x += 1

		top_left = Pos(min_x, min_y)
		bottom_right = Pos(max_x, max_y)
		return Map(top_left, bottom_right, clay_tiles)

	def tile_at(self, x, y):
		return self.grid[y-self.min_y][x-self.min_x]

	def __init__(self, top_left, bottom_right, clay_tiles):
		self.min_x = top_left.x
		self.min_y = top_left.y
		self.max_x = bottom_right.x
		self.max_y = bottom_right.y
		self.width  = (self.max_x - self.min_x + 1)
		self.height = (self.max_y - self.min_y + 1)
		self.grid = [[None]*self.width for i in range(0, self.height)]

		for pos, clay_tile in clay_tiles.items():
			self.grid[pos.y - self.min_y][pos.x - self.min_x] = clay_tile
		for yi in range(0, self.height):
			for xi in range(0, self.width):
				if not self.grid[yi][xi]:
					self.grid[yi][xi] = Tile(self.min_x + xi, self.min_y + yi, SAND)

	def tiles(self):
		for yi in range(0, self.height):
			for xi in range(0, self.width):
				yield self.grid[yi][xi]

class Day17(object):
	def __init__(self, filename):
		with open(filename, "r") as f:
			self.lines = map(str.strip, f.readlines())

	def solve(self, stop_at=0, skim_overflow=False):
		map = Map.parse(self.lines)
		source = WaterFront(500, clamp(0, map.min_y, map.max_y), map)
		source.flow(stop_at=stop_at, skim_overflow=skim_overflow)
		source.visualize_img()
		return len([tile for tile in map.tiles() if tile.visited])

	def part1(self, stop_at=0):
		return self.solve(stop_at=stop_at, skim_overflow=False)

	def part2(self):
		return self.solve(skim_overflow=True)

if __name__ == "__main__":
	day = Day17("day17.txt")
	print(day.part1(stop_at=(int(sys.argv[1]) if len(sys.argv) >= 2 else 0)))
	print(day.part2())