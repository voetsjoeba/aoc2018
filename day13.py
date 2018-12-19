#!/usr/bin/env python
from __future__ import print_function, absolute_import
import sys, os, re
from collections import namedtuple, defaultdict
from math import floor
from pprint import pprint
from copy import copy

UP = 0
DOWN = 1
LEFT = 2
RIGHT = 3
STRAIGHT = 4
VERTICAL = 5
HORIZONTAL = 6

class CrashException(Exception):
	def __init__(self, x, y, train1, train2):
		self.x = x
		self.y = y
		self.train1 = train1
		self.train2 = train2

def constant_name(c):
	if c == UP: return "UP"
	if c == DOWN: return "DOWN"
	if c == LEFT: return "LEFT"
	if c == RIGHT: return "RIGHT"
	if c == STRAIGHT: return "STRAIGHT"
	if c == VERTICAL: return "VERTICAL"
	if c == HORIZONTAL: return "HORIZONTAL"

class Train(object):
	def __init__(self, x, y, facing):
		self.x = x
		self.y = y
		self.facing = facing
		self.num_intersections = 0 # no intersections taken yet
	
	def advance(self, track):
		# moves this train by 1 step along the track, checking for collisions before moving
		next_piece = None
		next_facing = None
		
		train_id = "train (%d,%d)" % (self.x, self.y)
		
		current_piece = track.piece_at(self.x, self.y)
		if isinstance(current_piece, StraightPiece):
			#print("%s is facing %s on a straight piece" % (train_id, constant_name(self.facing)))
			new_x, new_y, facing = self.take_intersection(STRAIGHT)
			next_piece = track.piece_at(new_x, new_y)
			next_facing = facing
		
		elif isinstance(current_piece, CornerPiece):
			#print("%s is facing %s on a corner piece" % (train_id, constant_name(self.facing)))
			new_x, new_y, facing = self.take_corner(current_piece)
			next_piece = track.piece_at(new_x, new_y)
			next_facing = facing
			
		elif isinstance(current_piece, Intersection):
			#print("%s is facing %s on an intersection" % (train_id, constant_name(self.facing)))
			turn_sequence = [LEFT, STRAIGHT, RIGHT]
			turn = turn_sequence[self.num_intersections % len(turn_sequence)]
			self.num_intersections += 1
			
			new_x, new_y, facing = self.take_intersection(turn)
			next_piece = track.piece_at(new_x, new_y)
			next_facing = facing
		
		else:
			raise NotImplementedError()
		
		if not next_piece:
			raise RuntimeError("could not determine next piece for train at (x=%d,y=%d)" % (self.x, self.y))
		
		# is there another train already at the new position?
		other_train = track.train_at(next_piece.x, next_piece.y)
		if other_train:
			raise CrashException(next_piece.x, next_piece.y, other_train, self)
		
		self.x = next_piece.x
		self.y = next_piece.y
		self.facing = next_facing
	
	def take_intersection(self, turn_direction):
		# turn_map[turn_direction][current_facing] = (x_incr, y_incr, new_facing)
		turn_map = {
			LEFT: {
				LEFT:  ( 0,  1, DOWN),
				RIGHT: ( 0, -1, UP),
				UP:    (-1,  0, LEFT),
				DOWN:  ( 1,  0, RIGHT),
			},
			RIGHT: {
				LEFT:  ( 0, -1, UP),
				RIGHT: ( 0,  1, DOWN),
				UP:    ( 1,  0, RIGHT),
				DOWN:  (-1,  0, LEFT),
			},
			STRAIGHT: {
				LEFT:  (-1,  0, LEFT),
				RIGHT: ( 1,  0, RIGHT),
				UP:    ( 0, -1, UP),
				DOWN:  ( 0,  1, DOWN),
			}
		}
		turn_info = turn_map[turn_direction][self.facing]
		return (self.x + turn_info[0], self.y + turn_info[1], turn_info[2])
	
	def take_corner(self, corner_piece):
		# corner_map[corner_orientation][current_facing] = (x_incr, y_incr, new_facing)
		corner_map = {
			LEFT: { # "\" corner
				LEFT:  ( 0, -1, UP),
				RIGHT: ( 0,  1, DOWN),
				UP:    (-1,  0, LEFT),
				DOWN:  ( 1,  0, RIGHT),
			},
			RIGHT: { # "/" corner
				LEFT:  ( 0,  1, DOWN),
				RIGHT: ( 0, -1, UP),
				UP:    ( 1,  0, RIGHT),
				DOWN:  (-1,  0, LEFT),
			}
		}
		corner_info = corner_map[corner_piece.orientation][self.facing]
		return (self.x + corner_info[0], self.y + corner_info[1], corner_info[2])
	
	def visualize(self):
		if self.facing == LEFT:    char = "<"
		elif self.facing == RIGHT: char = ">"
		elif self.facing == UP:    char = "^"
		elif self.facing == DOWN:  char = "v"
		
		return "\033[33;1m%s\033[0;m" % char

class TrackPiece(object):
	@classmethod
	def create(cls, x, y, char):
		if char == "|":
			return StraightPiece(x, y, VERTICAL)
		elif char == "-":
			return StraightPiece(x, y, HORIZONTAL)
		elif char == "/":
			return CornerPiece(x, y, RIGHT)
		elif char == "\\":
			return CornerPiece(x, y, LEFT)
		elif char == "+":
			return Intersection(x, y)
		else:
			return None
	
	def __init__(self, x, y):
		self.x = x
		self.y = y

class StraightPiece(TrackPiece):
	def __init__(self, x, y, orientation):
		super(StraightPiece, self).__init__(x, y)
		self.orientation = orientation
	
	def visualize(self):
		return "|" if self.orientation == VERTICAL else "-"

class CornerPiece(TrackPiece):
	def __init__(self, x, y, orientation):
		super(CornerPiece, self).__init__(x, y)
		self.orientation = orientation
		
	def visualize(self):
		return ("/" if self.orientation == RIGHT else "\\")

class Intersection(TrackPiece):
	def __init__(self, x, y):
		super(Intersection, self).__init__(x, y)
	
	def visualize(self):
		return "+"

class Track(object):
	def __init__(self, lines):
		h = len(lines)
		w = max(len(line) for line in lines)
		pieces = [[None]*w for n in range(0, h)] # (y,x) indexing
		trains = []
		
		for y, line in enumerate(lines):
			for x, char in enumerate(line):
				train = None
				piece = None
				if char in ["<", ">"]:
					train = Train(x, y, (LEFT if char == "<" else RIGHT))
					piece = TrackPiece.create(x, y, "-")
				elif char in ["^", "v"]:
					train = Train(x, y, (UP if char == "^" else DOWN))
					piece = TrackPiece.create(x, y, "|")
				else:
					piece = TrackPiece.create(x, y, char)
				
				if train: trains.append(train)
				if piece: pieces[y][x] = piece
				
		self.width = w
		self.height = h
		self._pieces = pieces
		self._trains = trains
	
	def tick(self, resolve_crashes=False):
		queue = sorted(self._trains, key=lambda t: (t.y, t.x)) # sort vertically first, horizontally second
		while len(queue) > 0:
			train, queue = queue[0], queue[1:]
			try:
				train.advance(self) # throws when there is a crash
			except CrashException as c:
				if not resolve_crashes:
					raise
				
				# delete the two trains from the track and from the queue as well (the one that was crashed into may still be queued for moving),
				# and reorder the queue since the order of the remaining trains might have changed now
				self._trains.remove(c.train1)
				self._trains.remove(c.train2)
				queue = [t for t in queue if t not in (c.train1, c.train2)]
				queue = sorted(queue, key=lambda t: (t.y, t.y))
	
	def visualize(self):
		result = ""
		for y in range(0, self.height):
			for x in range(0, self.width):
				char = " "
				train = self.train_at(x, y)
				if train:
					char = train.visualize()
				else:
					piece = self.piece_at(x, y)
					if piece: char = piece.visualize()
				
				result += char
			result += "\n"
		
		return result
	
	def piece_at(self, x, y):
		return self._pieces[y][x]
	def train_at(self, x, y):
		trains = self.trains_at(x, y)
		return (trains[0] if len(trains) > 0 else None)
	def trains_at(self, x, y):
		return [t for t in self._trains if t.x == x and t.y == y]
	def num_trains(self):
		return len(self._trains)
	def train(self, idx):
		return self._trains[idx]
		
	def __getitem__(self, y):
		return self._grid[y]

class Day13(object):
	def __init__(self, filename):
		with open(filename, "r") as f:
			lines = [line for line in f.readlines()]
		
		self.track = Track(lines)
	
	def run_simulation(self, resolve_crashes=False):
		while self.track.num_trains() > 1:
			#print(self.track.visualize())
			self.track.tick(resolve_crashes=resolve_crashes) # throws when there is a crash
			#print("\n")
			#print("\033[33;1m%s\033[0;m" % ("=" * self.track.width))
			#print("\n\n")
		last_train = self.track.train(0)
		return "%d,%d" % (last_train.x, last_train.y)
	
	def part1(self):
		try:
			self.run_simulation(False)
		except CrashException as c:
			return "%d,%d" % (c.x, c.y)
	
	def part2(self):
		return self.run_simulation(True)

if __name__ == "__main__":
	day = Day13("day13.txt")
	print(day.part1())
	print(day.part2())