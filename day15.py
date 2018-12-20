#!/usr/bin/env python
from __future__ import print_function, absolute_import
import sys, os, re
from collections import namedtuple, defaultdict
from math import floor
from pprint import pprint
from copy import copy
from contextlib import contextmanager

Pos = namedtuple("Pos", "y x") # y coord first for easy grid order comparison

DEBUG = False
def dprint(s=""):
	if DEBUG: print(s)
def dwrite(s="", flush=False):
	if DEBUG:
		sys.stdout.write(s)
		if flush: sys.stdout.flush()

GOBLIN = 0
ELF = 1
FLOOR = 2
WALL = 3

class EndOfCombat(Exception):
	pass

@contextmanager
def debug(on_or_off):
	global DEBUG
	prev_value = DEBUG
	DEBUG = on_or_off
	try:
		yield
	finally:
		DEBUG = prev_value

def manhattan(a, b):
	return abs(b.x-a.x) + abs(b.y-a.y)

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

class Unit(object):
	__slots__ = ["pos", "team", "hp", "attack_power", "map"]
	def __init__(self, x, y, team, map):
		self.pos = Pos(x, y)
		self.team = team
		self.hp = 200
		self.attack_power = 0
		self.map = map

	def move_to(self, pos):
		old_pos = self.pos
		self.pos = pos
		self.map.unit_moved(self, old_pos)

	def attack(self, other):
		other.hp -= self.attack_power
		if other.hp <= 0:
			other.hp = 0
			self.map.unit_died(other)
			other.pos = None

	def is_alive(self):
		return self.hp > 0
	def team_name(self):
		return ("G" if self.team == GOBLIN else "E")
	def visualize(self):
		return self.team_name()
	def __str__(self):
		return "%s(%d,%d)" % (self.team_name(), self.pos.x, self.pos.y)

class Tile(object):
	__slots__ = ["pos", "type", "unit"]
	def __init__(self, x, y, type):
		self.pos = Pos(x, y)
		self.type = type
		self.unit = None # unit currently on this tile, or None

	@contextmanager
	def temporary_typechange(self, new_type):
		old_type = self.type
		self.type = new_type
		try:
			yield
		finally:
			self.type = old_type

	def visualize(self):
		return ("." if self.type == FLOOR else "#")
	def __str__(self):
		return self.visualize()

class Map(object):
	__slots__ = ["width", "height", "tiles"]
	def __init__(self):
		self.width = 0
		self.height = 0
		self.tiles = []

	def populate(self, ascii_lines):
		self.height = len(ascii_lines)
		self.width = len(ascii_lines[0])
		self.tiles = [[None]*self.width for n in range(0, self.height)]

		units = []
		for y, line in enumerate(ascii_lines):
			for x, char in enumerate(line):
				tile = Tile(x, y, (FLOOR if char in ("G", "E", ".") else WALL))
				self.tiles[y][x] = tile

				if char in ("G", "E"):
					unit = Unit(x, y, (GOBLIN if char == "G" else ELF), self)
					tile.unit = unit
					units.append(unit)
		return units

	def tile_at(self, pos):
		return self.tiles[pos.y][pos.x]
	def unit_at(self, pos):
		return self.tile_at(pos).unit

	def unit_moved(self, unit, old_pos):
		self.tile_at(old_pos).unit = None
		self.tile_at(unit.pos).unit = unit
	def unit_died(self, unit):
		self.tile_at(unit.pos).unit = None

	def neighbours_of(self, tile_or_unit):
		return self.neighbours_at(tile_or_unit.pos)

	def neighbours_at(self, p):
		assert isinstance(p, Pos)
		result = []
		if p.x > 0: result.append(self.tiles[p.y][p.x-1])
		if p.y > 0: result.append(self.tiles[p.y-1][p.x])
		if p.x < self.width-1: result.append(self.tiles[p.y][p.x+1])
		if p.y < self.height-1: result.append(self.tiles[p.y+1][p.x])
		return result

	def visualize(self, include_units=True):
		vwidth = len(str(self.height))
		result = " "*vwidth + " " + "".join("%-2d" % i for i in range(0,self.width)) + "\n"
		for y in range(0, self.height):
			unit_hps = []
			result += ("%"+str(vwidth)+"d ") % y
			for x in range(0, self.width):
				tile = self.tile_at(Pos(x, y))
				if tile.unit and include_units:
					result += tile.unit.visualize() + " "
					unit_hps.append("%s(%d)" % (tile.unit.team_name(), tile.unit.hp))
				else:
					result += tile.visualize() + " "

			result += "   " + ", ".join(unit_hps)
			result += "\n"
		return result

	def shortest_path(self, start, goal):
		with debug(False):
			return self._shortest_path(start, goal)

	def _shortest_path(self, start, goal):
		assert isinstance(start, Pos) and isinstance(goal, Pos)
		dprint("    computing shortest path from %s to %s" % (start, goal))
		closed = set()
		open = set([start])
		distance_fn = manhattan
		distance_heuristic = manhattan

		parents = {} # tile -> parent tile along path
		g_scores = {start: 0} # tile -> g score
		f_scores = {start: distance_heuristic(start, goal)} # tile -> f score

		while open:
			# take node from open list with lowest F score, and move it to the closed list
			pos = min(open, key=lambda p: f_scores[p]) # explore along lower grid order tiles first

			dprint("      evaluating node %s" % pos)
			closed.add(pos)
			open.remove(pos)

			if pos == goal:
				# reconstruct the path
				path = [pos]
				while pos in parents:
					parent = parents[pos]
					path.append(parent)
					pos = parent
				path.reverse()
				return path

			# expand open list with accessible adjacent tiles (that are not yet in the open list),
			# and calculate their f/g scores
			adjacent_tiles = [t for t in self.neighbours_at(pos) if (t.type == FLOOR and not t.unit)]
			adjacent_positions = [t.pos for t in adjacent_tiles]

			dprint("      considering non-closed adjacent tiles:")
			for nbpos in adjacent_positions:
				if nbpos in closed:
					dprint("        %s: on closed list, skipping" % nbpos)
					continue

				gscore_via_here = g_scores[pos] + distance_fn(pos, nbpos)
				if nbpos in open:
					gscore_current  = g_scores[nbpos]
					gscore_improved = gscore_via_here < gscore_current

					dprint("        %s: on open list" % nbpos)
					dprint("                 can we improve on it through G score? %s" % ("yes" if gscore_improved else "no"))
					if gscore_improved:
						dprint("          updating parent of %s to %s" % (nbpos, pos))
						pass
					else:
						continue
				else:
					# not yet seen before, just add it
					dprint("        %s: added to open list with G=%2d F=%2d parent=%s" % (nbpos, gscore_via_here, gscore_via_here+distance_heuristic(nbpos, goal), pos))
					open.add(nbpos)

				parents[nbpos] = pos
				g_scores[nbpos] = gscore_via_here
				f_scores[nbpos] = gscore_via_here + distance_heuristic(nbpos, goal)

			dprint("      -------------------------------")
		dprint()
		return None # no path found


class Simulation(object):
	def __init__(self, lines, elf_attack=0, goblin_attack=0):
		self.map = Map()
		self.units = self.map.populate(lines)
		self.rounds_completed = 0
		self.casualties = defaultdict(int) # team ID => number of units who died
		
		for u in self.units:
			u.attack_power = (elf_attack if u.team == ELF else goblin_attack)

	def round(self):
		queue = sorted(self.units, key=lambda u: u.pos) # in grid order
		while len(queue) > 0:
			unit, queue = queue[0], queue[1:]
			self.take_turn(unit)
			dprint(self.visualize())

		self.rounds_completed += 1
		
	def best_path(self, start, goal):
		# finds the best path from a given starting node to a goal, preferring those with an initial step
		# through neighbouring tiles of lower grid order if multiple paths of the same length are possible
		
		# compute the shortest path starting from each of the starting point's neighbouring positions, and see
		# how they compare relative to each other. if any have the same length, prefer the one started from a neighbour
		# with lower grid order
		neighbours = [t.pos for t in self.map.neighbours_at(start) if (not t.unit) and (t.type == FLOOR)]
		paths = []
		for n in neighbours:
			path = self.map.shortest_path(n, goal)
			if not path: continue
			paths.append((n, [start] + path))
		
		if len(paths) == 0:
			return None
		
		paths = sorted(paths, key=lambda pair: (len(pair[1]), pair[0]))
		best_path = paths[0][1]
		assert best_path[0] == start
		assert best_path[-1] == goal
		return best_path

	def take_turn(self, unit):
		# unit may have been killed on a previous unit's turn this round (already removed from the map and from self.units if so)
		if not unit.is_alive():
			return
		
		dprint("unit %s starts its turn:" % (unit,))

		enemy_units = [u for u in self.units if u.is_alive() and u.team != unit.team]
		if not enemy_units:
			dprint("  no more enemies, end of combat")
			raise EndOfCombat()

		# find open tiles next to enemy units
		move_targets = set()
		for e in enemy_units:
			for tile in self.map.neighbours_of(e):
				if tile.type == FLOOR and (tile.unit is None or tile.unit == unit):
					move_targets.add(tile.pos)

		# we may already be on one of the targets; if so, we don't need to move
		needs_move = (unit.pos not in move_targets)
		move_targets.discard(unit.pos)

		if needs_move:
			dprint("  considers moving to one of %d positions next to enemies:" % (len(move_targets)))

			# which target is the closest reachable one? if multiple are equally far away, pick the target with lowest grid order
			paths = []
			for target in move_targets:
				path = self.best_path(unit.pos, target)
				#if not path:
				#	dprint("    %s: unreachable" % (target,))
				#	continue
				#dprint("    %7s: in %d steps:  %s" % (target, len(path)-1, " -> ".join(str(x) for x in path)))
				paths.append((target, path))
			
			for target, path in sorted(paths, key=lambda tp: (len(tp[1]), tp[0]) if tp[1] else (float("inf"), tp[0])):
				if path is None: dprint("    %7s: unreachable" % (target,))
				else:            dprint("    %7s: in %2d steps:  %s" % (target, len(path)-1, " -> ".join("%7s" % str(x) for x in path)))

			paths = [p for t,p in paths if p is not None]
			if not paths:
				dprint("  no enemies reachable, ending turn")
				return # needs to move but can't, ends turn

			path_to_target = min(paths, key=lambda p: (len(p), p[-1])) # disambiguate paths with same length using grid order of the destination
			target = path_to_target[-1]
			dprint("  best target: %s" % (target,))

			# can we find an alternate path to the same target with smaller or equal cost,
			# that makes a different initial step to a tile with lower grid order?
			#with self.map.tile_at(path_to_target[1]).temporary_typechange(WALL):
			#	alternate_path = self.map.shortest_path(unit.pos, target)
			#	if alternate_path and len(alternate_path) <= len(path_to_target) and alternate_path[1] < path_to_target[1]:
			#		dprint("    found a better path:  %s" % (" -> ".join(str(x) for x in alternate_path)))
			#		path_to_target = alternate_path
			#	else:
			#		dprint("    no better path found")

			#shortest_path = paths[0]
			dprint("  takes 1 step along best path to %s" % (path_to_target[-1],))
			dprint("  now at %s" % (path_to_target[1],))
			unit.move_to(path_to_target[1])
		else:
			dprint("  is already next to an enemy")

		# if there are any enemies adjacent to us, attack the one with lowest hp
		adjacent_enemies = [tile.unit for tile in self.map.neighbours_of(unit) if tile.unit and tile.unit.team != unit.team]
		dprint("  has %d enemies adjacent to it" % len(adjacent_enemies))

		if adjacent_enemies:
			enemy = min(adjacent_enemies, key=lambda e: (e.hp, e.pos)) # break HP ties by grid order of the enemy position
			dprint("    attacks weakest adjacent enemy %s for %d damage" % (enemy, unit.attack_power))
			dprint("    enemy %s has %d remaining health" % (enemy, max(0, enemy.hp - unit.attack_power)))
			unit.attack(enemy)
			if not enemy.is_alive():
				self.units.remove(enemy)
				self.casualties[enemy.team] += 1

		dprint()

	def visualize(self):
		return self.map.visualize()

class Day15(object):
	def __init__(self, filename):
		with open(filename, "r") as f:
			self.lines = [line.strip() for line in f.readlines()]
	
	def run_simulation(self, elf_attack, goblin_attack):
		self.simulation = Simulation(self.lines, elf_attack=elf_attack, goblin_attack=goblin_attack)
		dprint(self.simulation.visualize())
		try:
			while True:
				self.simulation.round()
				if DEBUG:
					dprint(self.simulation.visualize())
					dprint("%d rounds were completed" % self.simulation.rounds_completed)
					#raw_input()
				else:
					sys.stdout.write(".")
					sys.stdout.flush()
		except EndOfCombat as e:
			if not DEBUG: sys.stdout.write("\n")
		
	def part1(self):
		self.run_simulation(elf_attack=3, goblin_attack=3)
		
		hp_sum = sum(u.hp for u in self.simulation.units)
		winning_team = "Goblins" if self.simulation.units[0].team == GOBLIN else "Elves"
		dprint()
		print(self.simulation.visualize())
		print()
		print("Combat ends after %d full rounds" % self.simulation.rounds_completed)
		print("%s win with %d total hit points left" % (winning_team, hp_sum))
		print("Outcome: %d * %d = %d" % (self.simulation.rounds_completed, hp_sum, self.simulation.rounds_completed*hp_sum))
		return self.simulation.rounds_completed * hp_sum

	def part2(self, elf_attack):
		self.run_simulation(elf_attack=elf_attack, goblin_attack=3)
	
		hp_sum = sum(u.hp for u in self.simulation.units)
		winning_team = "Goblins" if self.simulation.units[0].team == GOBLIN else "Elves"
		
		dprint()
		print(self.simulation.visualize())
		print()
		print("Combat ends after %d full rounds" % self.simulation.rounds_completed)
		print("%s win with %d total hit points left" % (winning_team, hp_sum))
		print("Outcome: %d * %d = %d" % (self.simulation.rounds_completed, hp_sum, self.simulation.rounds_completed*hp_sum))
		print("Elves attack power was %d" % elf_attack)
		print("Casualties:")
		print("  Elves: %d" % (self.simulation.casualties[ELF]))
		print("  Goblins: %d" % (self.simulation.casualties[GOBLIN]))
		return self.simulation.rounds_completed*hp_sum

if __name__ == "__main__":
	day = Day15(sys.argv[1] if len(sys.argv) > 1 else "day15.txt")
	print(day.part1())
	print(day.part2(elf_attack=(int(sys.argv[2]) if len(sys.argv) > 2 else 3)))