from __future__ import print_function,absolute_import

import sys, os, re

def day1_part1(input_file):
	freq = 0
	with open(input_file, "r") as f:
		for line in f:
			freq += int(line)
	return freq
	
def day1_part2(input_file):
	freq = 0
	freqs_seen = set()
	with open(input_file, "r") as f:
		lines = f.readlines()
	while True:
		for line in lines:
			freq += int(line)
			if freq in freqs_seen:
				return freq
			freqs_seen.add(freq)

if __name__ == "__main__":
	print(day1_part1("day1.txt"))
	print(day1_part2("day1.txt"))