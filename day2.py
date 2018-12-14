from __future__ import print_function,absolute_import
import sys, os, re

from pprint import pprint
from collections import defaultdict

def day2_part1(input_file):
	with open(input_file, "r") as f:
		lines = f.readlines()
	two_count = 0
	three_count = 0
	for line in lines:
		counters = defaultdict(int)
		for char in line.strip():
			counters[char] += 1
		if 2 in counters.values():
			two_count += 1
		if 3 in counters.values():
			three_count += 1
	return two_count * three_count

def day2_part2(input_file):
	with open(input_file, "r") as f:
		lines = map(lambda line: line.strip(), f.readlines())
	maxlen = max(len(L) for L in lines)

	# iterating over N, split each line at position N and see if any duplicates happen
	for i in range(0, maxlen+1):
		unique_splits = {} # split result -> line
		for line in lines:
			split = line[:i], line[i+1:]
			if split in unique_splits:
				return "".join(split)
			unique_splits[split] = line

if __name__ == "__main__":
	print(day2_part1("day2.txt"))
	print(day2_part2("day2.txt"))