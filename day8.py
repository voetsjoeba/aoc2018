from __future__ import print_function, absolute_import
import sys, os, re
from collections import namedtuple, defaultdict
from pprint import pprint

class Node(object):
	@classmethod
	def parse(cls, data):
		node, ptr = cls._parse(data, 0)
		assert ptr == len(data)
		return node
	
	@classmethod
	def _parse(cls, data, ptr):
		result = Node()
		num_children = data[ptr]; ptr += 1
		num_metadata = data[ptr]; ptr += 1
		
		for i in range(0, num_children):
			child, ptr = cls._parse(data, ptr)
			result.children.append(child)

		for i in range(0, num_metadata):
			result.metadata.append(data[ptr]); ptr += 1

		return result, ptr
	
	def __init__(self):
		self.children = []
		self.metadata = []
	
	def metadata_sum(self):
		result = sum(self.metadata)
		for c in self.children:
			result += c.metadata_sum()
		return result
	
	def value(self):
		if not self.children:
			return sum(self.metadata)
		result = 0
		for md in self.metadata:
			index = md - 1
			if index >= 0 and index < len(self.children):
				result += self.children[index].value()
		return result

class Day8(object):
	def __init__(self, input_file):
		with open(input_file, "r") as f:
			data = f.read().split(" ")
		self.data = map(int, data)
		self.root = Node.parse(self.data)
	
	def part1(self):
		return self.root.metadata_sum()
	
	def part2(self):
		return self.root.value()

if __name__ == "__main__":
	day = Day8("day8.txt")
	print(day.part1())
	print(day.part2())