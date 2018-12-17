from __future__ import print_function,absolute_import
import sys, os, re
from collections import namedtuple, defaultdict
from pprint import pprint
from math import sqrt, atan2, degrees, pi
from random import shuffle

def manhattan(p1, p2):
	return abs(p2.x-p1.x) + abs(p2.y-p1.y)

class Point(object):
	ORIGIN = None
	def __init__(self, x, y, name=None):
		self.x = x
		self.y = y
		self.name = name
		self.data = None # arbitrary data associated with this point
	def __str__(self):
		if self.name: return self.name
		return "(x=%d,y=%d)" % (self.x, self.y)
	def __repr__(self):
		return "Point(x=%d, y=%d, name=%s)" % (self.x, self.y, self.name)

Point.ORIGIN = Point(0,0)

class Vector(Point):
	@classmethod
	def between_points(cls, from_, to, **kwargs):
		if ("name" not in kwargs and from_.name and to.name):
			kwargs["name"] = "%s%s" % (from_.name, to.name)
		return Vector(to.x - from_.x, to.y - from_.y, **kwargs)
	@classmethod
	def to_point(cls, to, **kwargs):
		return Vector(to.x, to.y, **kwargs)
	
	def __init__(self, x, y, name=None):
		super(Vector, self).__init__(x, y)
		self.name = name
		
	def __sub__(self, v):
		return Vector(self.x - v.x, self.y - v.y)
	def __add__(self, v):
		return Vector(self.x + v.x, self.y + v.y)

	def normalized(self):
		L = sqrt(self.x**2 + self.y**2)
		return Vector(self.x/L, self.y/L)
	def xy(self):
		return (self.x, self.y)

	def signed_angle_to(self, other):
		# returns a signed anti-clockwise angle in radians, between -pi and pi, from this vector to the given vector
		x1, y1 = self.normalized().xy()
		x2, y2 = other.normalized().xy()
		return atan2(x1*y2 - y1*x2, x1*x2 + y1*y2)
		
	def __str__(self):
		if self.name: return self.name
		return "(%.2f,%.2f)" % (self.x, self.y)
		
class Grid(object):
	def __init__(self, min_x, max_x, min_y, max_y):
		self.min_x = min_x
		self.max_x = max_x
		self.min_y = min_y
		self.max_y = max_y
		assert self.width >= 1 and self.height >= 1
		
		points = [] # indexed as (y,x)
		for y in range(0, self.height):
			row = []
			for x in range(0, self.width):
				p = Point(self.min_x + x, self.min_y + y)
				row.append(p)
			points.append(row)
		self._points = points
	
	def at(self, x, y):
		return self._points[y-self.min_y][x-self.min_x]
	
	def x_range(self):
		return range(self.min_x, self.max_x+1)
	def y_range(self):
		return range(self.min_y, self.max_y+1)
		
	def __iter__(self):
		for y in range(0, self.height):
			for x in range(0, self.width):
				yield self._points[y][x]
	
	def __getitem__(self, y):
		return self._points[y]
	
	width  = property(lambda self: self.max_x - self.min_x + 1)
	height = property(lambda self: self.max_y - self.min_y + 1)
	
	TL = property(lambda self: Point(self.min_x, self.max_y))
	TR = property(lambda self: Point(self.max_x, self.max_y))
	BL = property(lambda self: Point(self.min_x, self.min_y))
	BR = property(lambda self: Point(self.max_x, self.min_y))
	
class Day6(object):
	def __init__(self, input_file):
		with open(input_file, "r") as f:
			lines = map(lambda L: L.strip(), f.readlines())
		
		coords = []
		for i, line in enumerate(lines):
			x, y = map(int, line.split(", "))
			p = Point(x,y)
			p.name = chr(ord("A")+i)
			coords.append(p)
		
		self.coords = coords

	def part1(self):
		# for each coordinate X on the plane, see if we can identify a line in the plane so that all other coordinates
		# lie on the same side of the line. if so, then the area of this coordinate will extend infinitely, because
		# infinitely many points from X outwards perpendicular to this line will have X as its closest coordinate.
		
		finite_coords = []
		for X in self.coords:
			# pick any initial other coordinate A, and construct the vector XA.
			# then iterate over all remaining coordinates C, taking the signed angle between XA and XC,
			# and keeping track of the highest and lowest values seen (i.e. the biggest angles anti-clockwise resp. clockwise relative to XA).
			#
			# the angular span in X that contains all other points is then found as the sum of the largest anti-clockwise rotation
			# and the largest clockwise rotation. if this span exceeds 180 degrees, then some points lie "behind" X, and it cannot extend infinitely
			
			others = [p for p in self.coords if p != X]
			
			v = Vector.between_points(X, others[0])
			max_angle_seen = 0
			min_angle_seen = 0
			
			has_infinite_area = True
			for C in others[1:]:
				v2 = Vector.between_points(X, C)
				angle = v.signed_angle_to(v2)
				max_angle_seen = max(max_angle_seen, angle)
				min_angle_seen = min(min_angle_seen, angle)
			
			if max_angle_seen - min_angle_seen > pi:
				finite_coords.append(X)
		
		# find the bounding area of the place containing all coords
		min_x = min(p.x for p in self.coords)
		max_x = max(p.x for p in self.coords)
		min_y = min(p.y for p in self.coords)
		max_y = max(p.y for p in self.coords)
		
		grid = Grid(min_x, max_x, min_y, max_y)
		
		# now populate the grid with distances to each coordinate, keep tracking of the distance
		# to all coordinates in each point (since we need to eliminate cases where two or more distances)
		# are the same. keep track of the coordinate with the largest area along the way.
		coord_areas = defaultdict(int) # coord -> area size
		for p in grid:
			distances = sorted((manhattan(p,c), c) for c in self.coords) # (distance, coord) pairs
			if distances[0][0] == distances[1][0]:
				# disregard, has no shortest distance to any singular coordinate
				continue
			
			p.data = distances[0]
			distance, coord = tuple(distances[0])
			if coord in finite_coords:
				coord_areas[coord] += 1
		
		return max(coord_areas.values())
	
	def part2(self):
		# find the bounding area of the place containing all coords
		min_x = min(p.x for p in self.coords)
		max_x = max(p.x for p in self.coords)
		min_y = min(p.y for p in self.coords)
		max_y = max(p.y for p in self.coords)
		
		grid = Grid(min_x, max_x, min_y, max_y)
		
		# now populate the grid with distances to each coordinate, keep tracking of the distance
		# to all coordinates in each point
		area = 0
		for p in grid:
			distances = [manhattan(p,c) for c in self.coords]
			if sum(distances) < 10000:
				area += 1
		
		return area

if __name__ == "__main__":
	day = Day6("day6.txt")
	print(day.part1())
	print(day.part2())