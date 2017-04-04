# Copyright (C) 2017  Patrick Totzke <patricktotzke@gmail.com>
# This file is released under the GNU GPL, version 3 or a later revision.

import json
import networkx as nx


class Game(nx.DiGraph):
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

    def effect(self, e):
        """ shortcut to extract the effect of an edge """
        src, trg = e
        return self.edge[src][trg]['effect']


class ParityGame(Game):
    """ Parity game graph """
    objective = "parity"

    def to_pgsolver_format(self):
        res = "parity %d;\n" % len(self.nodes())
        for v in self.nodes():
            res = res + ' '.join(
                (str(v),
                 str(self.node[v]['priority']),
                 str(self.node[v]['owner']),
                 ','.join(str(v) for v in self.successors(v)),
                 '\"{}\";\n'.format(self.node[v]['label'])
                 ))
        return res
