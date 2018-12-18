#!/usr/bin/env python
from __future__ import print_function, absolute_import
import sys, os, re
from collections import namedtuple, defaultdict
from math import floor
from pprint import pprint
from copy import copy

def hundreds_digit(n):
	return int(floor(n/100.0)) % 10

class Cell(object):
	def __init__(self, x, y, grid_serial):
		self.x = x
		self.y = y
		
		rack_id = self.x + 10
		self.power_level = rack_id * self.y + grid_serial
		self.power_level = hundreds_digit(self.power_level * rack_id) - 5
	
	def __repr__(self):
		return "(x=%3d, y=%3d, p=%d)" % (self.x, self.y, self.power_level)

class Grid(object):
	def __init__(self, width, height, serial):
		self.width = width
		self.height = height
		self.serial = serial
		
		self._cells = None
		self._row_sums = None # cumulative sums of each row
		
		self.build()
	
	def build(self):
		self._cells    = [[None]*self.width for n in range(0, self.height)]
		self._row_sums = []
		
		for iy in range(0, self.height):
			cumulative_sums = [0] # insert left sentinel value 0 for easier indexing later
			cumulative_sum = 0
			for ix in range(0, self.width):
				cell = Cell(ix+1, iy+1, self.serial)
				cumulative_sum += cell.power_level
				self._cells[iy][ix] = cell
				cumulative_sums.append(cumulative_sum)
			self._row_sums.append(cumulative_sums)
	
	def window_sum(self, ixbase, iybase, window_size):
		# returns the sum of the cell powerlevels within the square window with top left corners at indices (ix,iy) and of size window_size
		sum = 0
		for iy in range(iybase, iybase + window_size):
			sum += self._row_sums[iy][ixbase+window_size] - self._row_sums[iy][ixbase]
		return sum
	
	def at_index(self, ix, iy):
		return self._cells[iy][ix]
		
class Day11(object):
	def __init__(self):
		self.grid = Grid(300, 300, 3999)
	
	def scan_grid(self, window_size):
		# take initial 3 window sum at (1,1), then update it as the window moves across the grid
		max_seen = (None, None, None) # (x,y,value)
		
		for iy in range(0, self.grid.height - (window_size-1)):
			for ix in range(0, self.grid.width - (window_size-1)):
				window_sum = self.grid.window_sum(ix, iy, window_size)
				if (max_seen[2] is None) or window_sum > max_seen[2]:
					cell = self.grid.at_index(ix, iy)
					max_seen = (cell.x, cell.y, window_sum)
		
		return max_seen
	
	def part1(self):
		x, y, sum = self.scan_grid(window_size=3)
		return "%d,%d" % (x, y)
	
	def part2(self):
		max_seen = (0,0,0,0) # (x,y,winsize,value)
		for window_size in range(1, 300+1):
			sys.stdout.write("X" if window_size % 10 == 0 else (".\n" if window_size % 100 == 0 else "."))
			x, y, sum = self.scan_grid(window_size=window_size)
			if sum > max_seen[3]:
				max_seen = (x, y, window_size, sum)
		
		sys.stdout.write("\n")
		return "%d,%d,%d" % (max_seen[0], max_seen[1], max_seen[2])

if __name__ == "__main__":
	day = Day11()
	print(day.part1())
	print(day.part2())