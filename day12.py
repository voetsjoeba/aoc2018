#!/usr/bin/env python
from __future__ import print_function, absolute_import
import sys, os, re
from collections import namedtuple, defaultdict
from math import floor
from pprint import pprint
from copy import copy

def str_replace_char(s, idx, char):
	return s[:idx] + char + s[idx+1:]

class Rule(object):
	def __init__(self, pattern, result_state):
		self.pattern = pattern
		self.result_state = result_state

class Generation(object):
	def __init__(self, state, center_index=0):
		# the 'plants' extend to infinity in either direction, and any changes at any point
		# can cause additional changes to propagate outwards in either direction.
		#
		# we're ultimately only interested in the amount of slots with a plant,
		# so at any generation we need only consider the extent of the slots line from the
		# leftmost one with a plant to the rightmost one with a slot, with an additional 2 slots
		# on either end for matching.
		
		assert state.startswith("#") and state.endswith("#") # no need for extra .'s on either side
		self.state = state
		self.center = center_index
	
	def apply_rules(self, rules):
		max_pattern_size = 5
		padding = "."*(max_pattern_size-1)
		
		cur_state_expanded = padding + self.state + padding
		new_state_expanded = padding + self.state + padding
		new_center = self.center + len(padding)
		
		# the first character of self.state might match the last character of a pattern
		# that matches 2 spaces in front of it, and analogously for the last character.
		# (the first and last pairs of ".." are only there to serve as sentinel values
		#  for those extreme matches and do not need to be evaluated themselves)
		for i in range(2, len(cur_state_expanded)-2):
			matched_replacement = None
			for rule in rules:
				pattern = rule.pattern
				if cur_state_expanded[i-2:i-2+len(pattern)] == pattern:
					matched_replacement = rule.result_state
					break # we know each pattern is unique, so we can stop after a match
			
			if matched_replacement is None:
				pass
			new_state_expanded = str_replace_char(new_state_expanded, i, (matched_replacement or "."))
		
		new_state = new_state_expanded
		while new_state[0] == ".":
			new_state = new_state[1:]
			new_center -= 1
		new_state = new_state.rstrip(".") # doesn't affect the center position
		return Generation(new_state, new_center)
	
	def pot_numbers_sum(self):
		result = 0
		for i in range(0, len(self.state)):
			pot_number = i - self.center
			if self.state[i] == "#":
				result += pot_number
		return result
	
	def visual(self, center_offset=0):
		result = "%s%s" % ("."*(center_offset-self.center), self.state)
		return result

class Day12(object):
	def __init__(self, filename):
		with open(filename, "r") as f:
			lines = [line.strip() for line in f.readlines()]
		
		initial_state = lines[0][len("initial state: "):]
		
		rules = []
		for line in lines[2:]:
			match = re.match("^([\.#]{5}) => ([\.#])$", line)
			if not match: raise ValueError("bad input line")
			rule = Rule(match.group(1), match.group(2))
			rules.append(rule)

		# make sure each pattern is unique
		assert len(rules) == len(set(r.pattern for r in rules))
		
		self.state = Generation(initial_state)
		self.rules = rules

	def part1(self):
		state = self.state
		for n in range(0, 20):
			state = state.apply_rules(self.rules)
		return state.pot_numbers_sum()
	
	def part2(self):
		center_offset = 10
		# after 101 generations, the pattern stays the same and just moves along by 1 to the right each generation.
		# the pattern is this:
		#   '#..##..#..#..##..#..#..##..#..#..##..#..#..##..#..#..##..#..#..##..#..#..##..#..#..##..#..#..##..#..#..##..##....#..##..##..##..#..#..##....#..##'
		#
		# and has its first # at offset 56.
		
		# after 101 iterations, the pot numbers were 56 + [0,3,4,...]
		# so after 50 billion iterations, they will be 56 + (50 billion - 101) + [0,3,4,...]
		# so the answer will be the sum of that array.
		pattern = '#..##..#..#..##..#..#..##..#..#..##..#..#..##..#..#..##..#..#..##..#..#..##..#..#..##..#..#..##..#..#..##..##....#..##..##..##..#..#..##....#..##'
		pot_indices_relative = [i for i,c in enumerate(pattern) if c == "#"]
		pot_indices = [56 + 50000000000 - 101 + i for i in pot_indices_relative]
		return sum(pot_indices)

if __name__ == "__main__":
	day = Day12("day12.txt")
	print(day.part1())
	print(day.part2())