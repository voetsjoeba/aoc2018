#!/usr/bin/env python
from __future__ import print_function, absolute_import
import sys, os, re
from collections import namedtuple, defaultdict
from pprint import pprint

class Game(object):
	def __init__(self, num_players):
		self.num_players = num_players
		#self.num_marbles = num_marbles
		
		self.turns_played = 0
		self.current_index = 0
		self.state = [0]
		self.scores = [0]*self.num_players
	
	def play_turn(self):
		marble_value = self.turns_played + 1
		player_index = self.turns_played % self.num_players
		
		if marble_value % 23 == 0:
			remove_index = (self.current_index-7) % len(self.state)
			self.scores[player_index] += marble_value + self.state.pop(remove_index)
			self.current_index = remove_index
		else:
			insert_after = (self.current_index + 1) % len(self.state)
			self.state.insert(insert_after+1, marble_value)
			self.current_index = insert_after + 1
		
		self.turns_played += 1
	
	def winner(self):
		winner = max(enumerate(self.scores), key=lambda pair: pair[1])
		return winner
	
	def visualize(self):
		result = ""
		for i,n in enumerate(self.state):
			entry = " %d " % (n,)
			if i == self.current_index:
				entry = "(" + entry[1:-1] + ")"
			result += entry
		return result

class Day9(object):
	def winning_score(self, num_players, num_turns):
		game = Game(num_players)
		#print("[-] %s" % game.visualize())
		while game.turns_played < num_turns:
			game.play_turn()
			if game.turns_played % (num_turns//100) == 0:
				sys.stdout.write(".")
			#print("[%d] %s" % ((i%num_players)+1, game.visualize()))
		
		winner = game.winner()
		return winner[1]
		
	def part1(self):
		return self.winning_score(452, 71250)
	
	def part2(self):
		return self.winning_score(452, 71250*100)

if __name__ == "__main__":
	day = Day9()
	print(day.part1())
	print(day.part2())