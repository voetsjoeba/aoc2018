#!/usr/bin/env python
from __future__ import print_function, absolute_import
import sys, os, re
from collections import namedtuple, defaultdict
from pprint import pprint

class Bounds(object):
	def __init__(self):
		self.xmin = None
		self.xmax = None
		self.ymin = None
		self.ymax = None
	
	def update(self, x, y):
		self.xmin = (x if self.xmin is None else min(self.xmin, x))
		self.xmax = (x if self.xmax is None else max(self.xmax, x))
		self.ymin = (y if self.ymin is None else min(self.ymin, y))
		self.ymax = (y if self.ymax is None else max(self.ymax, y))
	
	w = property(lambda self: 1 + self.xmax - self.xmin)
	h = property(lambda self: 1 + self.ymax - self.ymin)
	area = property(lambda self: self.w * self.h)

class Sky(object):
	def __init__(self):
		self.lights = []
		self._bounds = None
		
	def add_light(self, light):
		self.lights.append(light)
		
	def advance(self, timestep=1):
		for light in self.lights:
			light.advance(timestep=timestep)
		self._bounds = None # invalidate bounds
	
	def bounds(self):
		if self._bounds is None:
			self._bounds = Bounds()
			for L in self.lights:
				self._bounds.update(L.px, L.py)
		return self._bounds
		
	def diagram(self):
		bounds = self.bounds()
		lines = ["."*bounds.w]*bounds.h
		for light in self.lights:
			iy = light.py - bounds.ymin
			ix = light.px - bounds.xmin
			line = lines[iy]
			lines[iy] = line[:ix] + "#" + line[ix+1:]
		return "\n".join(lines)

class Light(object):
	def __init__(self, px, py, vx, vy):
		self.px = px
		self.py = py
		self.vx = vx
		self.vy = vy
	
	def advance(self, timestep=1):
		self.px += timestep * self.vx
		self.py += timestep * self.vy
	
	@classmethod
	def parse(cls, s):
		match = re.match(r"^position=<\s*(-?\d+),\s*(-?\d+)> velocity=<\s*(-?\d+),\s*(-?\d+)>$", s)
		if not match: raise ValueError("bad input line")
		
		px = int(match.group(1))
		py = int(match.group(2))
		vx = int(match.group(3))
		vy = int(match.group(4))
		return Light(px, py, vx, vy)

class Day10(object):
	def __init__(self, input_file):
		with open(input_file, "r") as f:
			lines = [line.strip() for line in f.readlines()]
		
		sky = Sky()
		for line in lines:
			light = Light.parse(line)
			sky.add_light(light)
		self.sky = sky
	
	def part1(self):
		t = 0
		min_area = self.sky.bounds().area
		
		# iterate time until we reach a minimum bounding box; assume that's when the message is displayed
		while True:
			t += 1
			self.sky.advance(1)
			
			area = self.sky.bounds().area
			if area < min_area:
				min_area = area
			else:
				# area stopped decreasing, assume we hit the message (revert one step to display it)
				self.sky.advance(-1)
				print(self.sky.diagram())
				return t-1

if __name__ == "__main__":
	day = Day10("day10.txt")
	print(day.part1())