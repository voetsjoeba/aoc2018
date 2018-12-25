#!/usr/bin/env python
from __future__ import print_function, absolute_import
import sys, os, re
from collections import namedtuple, defaultdict
from math import floor, ceil
from pprint import pprint
from copy import copy

ROCKY = 0
WET = 1
NARROW = 2
TORCH = 3
CLIMBING_GEAR = 4
NO_TOOL = 5

class Region(object):
	def __init__(self, x, y, cave_depth):
		self.x = x
		self.y = y
		self.cave_depth = cave_depth
		self.geologic_index = None
		self._erosion_level = None
		self._valid_tools = None
		self._type = None

	@property
	def type(self):
		if self._type is None:
			self._type = self.erosion_level % 3
		return self._type

	@property
	def erosion_level(self):
		assert self.geologic_index is not None
		if self._erosion_level is None:
			self._erosion_level = (self.geologic_index + self.cave_depth) % 20183
		return self._erosion_level

	@property
	def valid_tools(self):
		if self._valid_tools is None:
			if   self.type == ROCKY:  self._valid_tools = set([TORCH, CLIMBING_GEAR])
			elif self.type == WET:    self._valid_tools = set([CLIMBING_GEAR, NO_TOOL])
			elif self.type == NARROW: self._valid_tools = set([TORCH, NO_TOOL])
			else: raise ValueError()
		return self._valid_tools

	def visualize(self):
		return ("." if self.type == ROCKY else ("=" if self.type == WET else "|"))

	def __str__(self):
		return "(%d,%d)" % (self.x, self.y)

class Cave(object):
	def __init__(self, depth, target_x, target_y):
		self.depth = depth
		self.width = target_x + 1
		self.height = target_y + 1

		self.start = Region(0, 0, self.depth)
		self.target = Region(target_x, target_y, self.depth)
		self.start.geologic_index = 0
		self.target.geologic_index = 0

		self._regions = {}
		self._regions[(self.start.x, self.start.y)] = self.start
		self._regions[(self.target.x, self.target.y)] = self.target

		self._path_nodes = {}

		x = 1
		y = 0
		while y < self.height:
			while x < self.width:
				if not (x == self.target.x and y == self.target.y):
					self.get_or_add_region(x, y)
				x += 1
			x = 0
			y += 1

	def get_region(self, x, y):
		return self._regions.get((x,y), None)

	def get_or_add_region(self, x, y):
		region = self._regions.get((x,y), None)
		if not region:
			region = Region(x, y, self.depth)
			if y == 0:
				region.geologic_index = (x*16807)
			elif x == 0:
				region.geologic_index = (y*48271)
			else:
				up   = self.get_or_add_region(x, y-1)
				left = self.get_or_add_region(x-1, y)
				region.geologic_index = left.erosion_level * up.erosion_level
			self._regions[(x,y)] = region
		return region

	def regions(self, width=None, height=None):
		for y in range(0, (self.height or height)):
			for x in range(0, (self.width or width)):
				yield self.get_region(x, y)

	def visualize(self):
		result = ""
		for y in range(0, self.height):
			for x in range(0, self.width):
				char = self.get_region(x, y).visualize()
				if   x==0 and y==0: char = "M"
				elif x==self.target.x and y==self.target.y: char = "T"
				result += char
			result += "\n"
		return result

class PathNode(object):
	def __init__(self, region, tool):
		self.region = region
		self.tool = tool

	def __eq__(self, other):
		return hash(self) == hash(other)
	def __hash__(self):
		return hash((self.region.x, self.region.y, self.tool))


class Pathfinder(object):
	def __init__(self, cave):
		self.cave = cave

	def shortest_path(self, start, goal):

		def neighbours(cave, node):
			# return neighbouring PathNodes and the cost to reach them
			x, y, current_tool = node.region.x, node.region.y, node.tool

			regions = []
			if x > 0:             regions.append(cave.get_region(x-1, y)) # any regions left or up from us should already exist
			if y > 0:             regions.append(cave.get_region(x, y-1))
			regions.append(cave.get_or_add_region(x+1, y))
			regions.append(cave.get_or_add_region(x, y+1))

			nb_nodes = [] # node, cost pairs

			# we can always switch to the other tool(s) allowed on this node
			other_tools = node.region.valid_tools - set([current_tool])
			for other_tool in other_tools:
				change_tool = PathNode(node.region, other_tool)
				nb_nodes.append((change_tool, 7))

			# we can move to neighbouring regions if our current tool is also valid on it
			for nb_region in regions:
				if current_tool in nb_region.valid_tools:
					move_region = PathNode(nb_region, current_tool)
					nb_nodes.append((move_region, 1))

			return nb_nodes

		def cost_heuristic(node1, node2):
			return abs(node2.region.x - node1.region.x) + abs(node2.region.y - node1.region.y) + (7 if node1.tool != node2.tool else 0)

		closed = set()
		open = set([start])

		parents = {} # node -> parent node along path
		g_scores = {start: 0} # tile -> g score
		f_scores = {start: cost_heuristic(start, goal)} # tile -> f score

		while open:
			# take node from open list with lowest F score, and move it to the closed list
			node = min(open, key=lambda p: f_scores[p]) # explore along lower grid order tiles first
			closed.add(node)
			open.remove(node)

			if node == goal:
				# reconstruct the path
				total_cost = g_scores[node]
				path = [(node, g_scores[node])]
				while node in parents:
					parent = parents[node]
					path.append((parent, g_scores[parent]))
					node = parent
				path.reverse()
				return path

			# expand open list with accessible adjacent nodes (that are not yet in the open list),
			# and calculate their f/g scores
			adjacent_nodes = neighbours(self.cave, node)

			for nnode, ncost in adjacent_nodes:
				if nnode in closed: continue

				gscore_via_here = g_scores[node] + ncost
				if nnode in open:
					gscore_current  = g_scores[nnode]
					gscore_improved = gscore_via_here < gscore_current
					if gscore_improved:
						pass
					else:
						continue
				else:
					# not yet seen before, just add it
					open.add(nnode)

				parents[nnode] = node
				g_scores[nnode] = gscore_via_here
				f_scores[nnode] = gscore_via_here + cost_heuristic(nnode, goal)

		return None # no path found

class Day22(object):
	def __init__(self, filename):
		with open(filename, "r") as f:
			lines = map(str.strip, f.readlines())

		depth  = int(lines[0][len("depth: "):])
		target = map(int, lines[1][len("target: "):].split(","))
		self.cave = Cave(depth, target[0], target[1])

	def part1(self):
		return sum(region.type for region in self.cave.regions())

	def part2(self):
		# run an A* search, but against an expanded graph that combines both cave regions and the current tool at that point.
		# start node = ((0,0), torch), target node = ((t,t), torch)
		start_node  = PathNode(self.cave.start,  TORCH)
		target_node = PathNode(self.cave.target, TORCH)
		pf = Pathfinder(self.cave)
		path = pf.shortest_path(start_node, target_node)
		if path is not None:
			return path[-1][1]

if __name__ == "__main__":
	day = Day22("day22.txt")
	print(day.part1())
	print(day.part2())