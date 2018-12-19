#!/usr/bin/env python
from __future__ import print_function, absolute_import
import sys, os, re
from collections import namedtuple, defaultdict
from math import floor
from pprint import pprint
from copy import copy

def digits_of(n):
	if n == 0:
		return [0]
	digits = []
	while n != 0:
		digits.append(n%10)
		n = int(floor(n/10))
	digits.reverse()
	return digits

class Day14(object):
	def visualize(self, state, cursor1=None, cursor2=None):
		result = ""
		for i,n in enumerate(self.state):
			entry = " %d " % (n,)
			if cursor1 and i == cursor1: entry = "(" + entry[1] + ")"
			if cursor2 and i == cursor2: entry = "[" + entry[1] + "]"
			result += entry
		return result
		
	def part1(self):
		state = [3,7]
		cursor1 = 0
		cursor2 = 1
		
		num_recipes = 293801
		while len(state) < num_recipes + 10:
			seed = state[cursor1] + state[cursor2]
			state.extend(digits_of(seed))
			
			state_len = len(state)
			cursor1 = (cursor1 + 1 + state[cursor1]) % state_len
			cursor2 = (cursor2 + 1 + state[cursor2]) % state_len
		
		return "".join("%d" % n for n in state[num_recipes:num_recipes+10])
	
	def part2(self):
		state = [3,7]
		cursor1 = 0
		cursor2 = 1
		
		pattern = [2,9,3,8,0,1]
		pattern_len = len(pattern)
		while True:
			seed = state[cursor1] + state[cursor2]
			seed_digits = digits_of(seed)
			state.extend(seed_digits)
			
			# we added len(seed) digits at the end of the state, so see if the pattern
			# matches at any of the last len(seed) positions
			state_len = len(state)
			for i in range(0, len(seed_digits)):
				if state[state_len -(i+pattern_len) : state_len -i ] == pattern:
					# found a match ending at state[-i]
					return state_len - pattern_len - i
			
			cursor1 = (cursor1 + 1 + state[cursor1]) % state_len
			cursor2 = (cursor2 + 1 + state[cursor2]) % state_len

if __name__ == "__main__":
	day = Day14()
	print(day.part1())
	print(day.part2())