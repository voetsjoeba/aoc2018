#!/usr/bin/env python
from __future__ import print_function, absolute_import
import sys, os, re
from collections import namedtuple, defaultdict
from math import floor
from pprint import pprint
from copy import copy

class Pos(object):
	__slots__ = ["x", "y"]
	def __init__(self, x, y):
		self.x = x
		self.y = y
	def __str__(self):
		return "(%d,%d)" % (self.x, self.y)

	__lt__ = lambda s,o: (s.y, s.x) < (o.y, o.x) # grid order: lower rows win, then lower columns
	__gt__ = lambda s,o: o < s
	__eq__ = lambda s,o: (not s < o) and (not o < s)
	__ne__ = lambda s,o: (s < o) or (o < s)
	__ge__ = lambda s,o: not s < o
	__le__ = lambda s,o: not o < s
	__neg__ = lambda s: Pos(-s.x, -s.y)
	__hash__ = lambda s: hash((s.x, s.y))

NORTH = ( 0,-1)
EAST  = ( 1, 0)
SOUTH = ( 0, 1)
WEST  = (-1, 0)

class Node(object):
	def __init__(self, x, y):
		self.x = x
		self.y = y
		self.north = None
		self.east = None
		self.south = None
		self.west = None

	def __str__(self):
		return "(%d,%d)" % (self.x, self.y)

class Graph(object):
	def __init__(self, root=None):
		self.nodes = {} # (x,y) -> Node
		self.min_x = None
		self.max_x = None
		self.min_y = None
		self.max_y = None
		self.root=root

	def add_node(self, n):
		self.nodes[(n.x, n.y)] = n
		self.min_x = min(n.x, n.x if (self.min_x is None) else self.min_x)
		self.max_x = max(n.x, n.x if (self.max_x is None) else self.max_x)
		self.min_y = min(n.y, n.y if (self.min_y is None) else self.min_y)
		self.max_y = max(n.y, n.y if (self.max_y is None) else self.max_y)

	def get_node(self, x, y):
		return self.nodes.get((x,y), None)

	def get_or_add_node(self, x, y):
		node = self.get_node(x, y)
		if not node:
			node = Node(x, y)
			self.add_node(node)
		return node

	def visualize(self, marked_nodes_1=None, marked_nodes_2=None):
		vdoor = "\033[1;30m%s\033[0;m" % "|"   # dark gray
		hdoor = "\033[1;30m%s\033[0;m" % "-"   # dark gray
		wall  = "\033[1;37m%s\033[0;m" % "#"   # bright white
		room_center = " "

		marked_nodes_1 = marked_nodes_1 or []
		marked_nodes_2 = marked_nodes_2 or []
		format_mark_1 = "\033[33;1m%s\033[0;m" # bright yellow
		format_mark_2 = "\033[36;1m%s\033[0;m" # bright cyan

		numbercol_fmt = "%2s  "
		numbercol_width = max(len(numbercol_fmt % self.max_y), len(numbercol_fmt % self.min_y))

		result = (numbercol_fmt % "")  + "".join(" %2d " % x for x in range(self.min_x, self.max_x+1)) + "\n"
		for y in range(self.min_y, self.max_y+1):
			lines     = [numbercol_fmt % "", numbercol_fmt % y]
			last_line = (numbercol_fmt % "") if y == self.max_y else None

			for x in range(self.min_x, self.max_x+1):
				node = self.get_node(x, y)

				center_char = room_center
				if   node in marked_nodes_1: center_char = format_mark_1 % "1"
				elif node in marked_nodes_2: center_char = format_mark_2 % "2"

				lines[0] += "%s%s"    % (wall, hdoor*3 if (node and node.north) else wall*3)
				lines[1] += "%s %s "  % (vdoor if (node and node.west) else wall, center_char)
				if last_line is not None:
					last_line += "%s%s" % (wall, hdoor*3 if node and node.south else wall*3)

				if x == self.max_x:
					lines[0] += wall
					lines[1] += (vdoor if node and node.east else wall)
					if last_line is not None:
						last_line += wall

			result += "\n".join(lines) + "\n"
			if last_line is not None:
				result += last_line + "\n"

		return result

	def build(self, start_node, regex):
		pos = self._build(start_node, regex, 0)
		assert pos == len(regex)
		return start_node

	def _build(self, current_node, regex, pos, depth=0):
		start_node = current_node
		prefix = "  " * depth

		while pos < len(regex):
			#print(regex[:pos])
			#print(self.visualize(marked_nodes_1=[self.root], marked_nodes_2=[current_node]))
			#raw_input()
			x = current_node.x
			y = current_node.y
			c = regex[pos]

			if c in ("N", "E", "S", "W"):
				if c == "N":
					north = self.get_or_add_node(x, y-1)
					north.south, current_node.north, current_node = current_node, north, north
				elif c == "E":
					east = self.get_or_add_node(x+1, y)
					east.west, current_node.east, current_node = current_node, east, east
				elif c == "S":
					south = self.get_or_add_node(x, y+1)
					south.north, current_node.south, current_node = current_node, south, south
				elif c == "W":
					west = self.get_or_add_node(x-1, y)
					west.east, current_node.west, current_node = current_node, west, west
				pos += 1

			elif c == "(":
				pos = self._build(current_node, regex, pos+1, depth+1)
			elif c == "|":
				current_node = start_node
				pos += 1
			elif c == ")":
				pos += 1
				break
			else:
				raise ValueError("unexpected character: %s" % (c,))

		return pos

	def shortest_paths(self, start_node):
		# find shortest paths from a given starting node to all other nodes
		queue = []

		distances = {}
		parents = {}
		for node in self.nodes.values():
			distances[node] = float("inf")
			parents[node] = None
			queue.append(node)

		distances[start_node] = 0
		while queue:
			u = min(queue, key=lambda n: distances[n])
			queue.remove(u)

			for neighbour in [u.north, u.east, u.south, u.west]:
				if (not neighbour) or (neighbour not in queue): continue
				alt_distance = distances[u] + 1
				if alt_distance < distances[neighbour]:
					distances[neighbour] = alt_distance
					parents[neighbour] = u

		return distances, parents

	def reconstruct_path(self, node, parents):
		path = [node]
		current = node
		while current in parents:
			current = parents[current]
			path.append(current)
		path.reverse()
		return path

class Day20(object):
	def __init__(self, filename):
		with open(filename, "r") as f:
			self.regex = f.read().strip()

		root = Node(0,0)
		g = Graph(root=root)

		g.add_node(root)
		g.build(root, self.regex[1:-1]) # don't need the ^ and $ bits
		assert root in g.nodes.values()

		# run dijkstra on the graph to find the distance from the root to all other nodes
		distances, parents = g.shortest_paths(root)

		self.graph = g
		self.distances = distances
		self.parents = parents

	def part1(self):
		farthest_room = max(self.distances.keys(), key=lambda node: self.distances[node])
		path = self.graph.reconstruct_path(farthest_room, self.parents)

		print("farthest room = %s (%d doors away)" % (farthest_room, self.distances[farthest_room]))
		return self.distances[farthest_room]

	def part2(self):
		return len([d for d in self.distances.values() if d >= 1000])

if __name__ == "__main__":
	day = Day20("day20.txt")
	print(day.part1())
	print(day.part2())