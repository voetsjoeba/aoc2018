from __future__ import print_function,absolute_import
import sys, os, re
from collections import defaultdict, namedtuple

Claim = namedtuple("Claim", "id left top width height")
class Day3(object):
	def __init__(self, input_file):
		self.claims = {} # id -> Claim
		
		with open(input_file, "r") as f:
			lines = map(lambda line: line.strip(), f.readlines())
		rex = re.compile(r"^#(\d+) @ (\d+),(\d+): (\d+)x(\d+)$")
		for line in lines:
			match = rex.match(line)
			if not match: raise ValueError("line")
			id = int(match.group(1))
			left, top, width, height = map(lambda s: int(s), iter((match.group(2), match.group(3), match.group(4), match.group(5))))
			
			self.claims[id] = Claim(id, left, top, width, height)

	def part1(self):
		tiles = defaultdict(int) # tile (x,y) -> count
		
		for c in self.claims.values():
			for x in range(c.left, c.left+c.width):
				for y in range(c.top, c.top+c.height):
					tiles[(x,y)] += 1

		return len([v for v in tiles.values() if v > 1])

	def part2(self):
		claims_by_tile = defaultdict(set) # tile (x,y) -> set of claim IDs that occupy it
		tiles_by_claim = defaultdict(set) # claim ID -> tiles that it occupies
		
		for c in self.claims.values():
			for x in range(c.left, c.left+c.width):
				for y in range(c.top, c.top+c.height):
					claims_by_tile[(x,y)].add(c.id)
					tiles_by_claim[c.id].add((x,y))
		
		candidate_ids = [list(ids)[0] for tile,ids in claims_by_tile.items() if len(ids) == 1]
		for id in candidate_ids:
			if all(len(claims_by_tile[tile]) == 1 for tile in tiles_by_claim[id]):
				return id
		
if __name__ == "__main__":
	day = Day3("day3.txt")
	print(day.part1())
	print(day.part2())