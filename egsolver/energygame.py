# Copyright (C) 2017  Patrick Totzke <patricktotzke@gmail.com>
# This file is released under the GNU GPL, version 3 or a later revision.

from networkx import DiGraph
import json


class Game(DiGraph):
    """ base class for game graphs"""

    @classmethod
    def from_game_string(cls, game_as_string):
        """
        read game graph from a string
        """
        gameinfo = json.loads(game_as_string)
        game = cls()
        for v, attrs in gameinfo['nodes']:
            game.add_node(v, attrs)
        for src, trg, attrs in gameinfo['edges']:
            game.add_edge(src, trg, attrs)
        return game


class EnergyGame(Game):
    """ Energy game graph """
    objective = "energy"

    def playernodes(self, player):
        return [v for v in self.nodes() if self.node[v]['owner'] == player]

    def weight(self, e):
        """ shortcut to extract the effect of an edge """
        src, trg = e
        return self.edge[src][trg]['effect']

    def maxdrop(self, node=None):
        def min_successor_effect(v):
            return min([0] + [self[v][nbr]['effect'] for nbr in self[v]])
        if node is None:
            return max(-min(0, min_successor_effect(v)) for v in self.nodes())
        else:
            return -min(0, min_successor_effect(node))
