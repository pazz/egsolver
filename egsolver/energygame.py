# Copyright (C) 2017  Patrick Totzke <patricktotzke@gmail.com>
# This file is released under the GNU GPL, version 3 or a later revision.

import logging
from networkx import DiGraph
import networkx as nx
import json

from io import StringIO


class Game(DiGraph):
    """ base class for game graphs"""

    @classmethod
    def from_game_string(cls, game_as_string):
        """
        read game graph from a string
        """
        gameinfo = json.loads(game_as_string)

        game = cls(gameinfo['edges'])
        for v, attrs in gameinfo['nodes']:
            game.node[v] = attrs
        return game

    def to_game_string(self, indent=2):
        """
        format this game as (pretty printed) json string
        """
        GAME_FILE_FORMAT="{{\n\"objective\": \"{objective}\",\n"\
                         +"\"nodes\":{nodes},\n" \
                         +"\"edges\":{edges}\n}}"

        def nodeline(v):
            return indent * " " + json.dumps((v, self.node[v]))

        def edgeline(e):
            return indent * " " + json.dumps(e)

        elist = nx.to_edgelist(self)
        elist_json = "[\n" + ",\n".join([edgeline(e) for e in elist]) + "\n]"

        nlist = self.nodes()
        nlist_json = "[\n" + ",\n".join([nodeline(v) for v in nlist]) + "\n]"
        return GAME_FILE_FORMAT.format(objective=self.objective,
                                       nodes=nlist_json,
                                       edges=elist_json,
                                       )

    def format(self, fmt='eg', out=None, solver=None):
        # we'll write to a file object, since networkx's formatter are weird..
        out = out or StringIO()

        if fmt == 'eg':
            out.write(self.to_game_string())

        elif fmt == 'dot':
            def propfmt(prop):
                return "{}=\"{}\"".format(*prop)

            def propsfmt(props):
                return ", ".join([propfmt(it) for it in props.items()])

            def dotnode(v):
                return "%d [%s];" % (v, propsfmt(self.node[v]))

                return "%d [%s];" % (v, propsfmt(self.node[v]))

            def dotedge(e):
                s, t = e
                return "%d -> %d [%s];" % (s, t, propsfmt(self.edge[s][t]))

            out.write("digraph G {{\n{}\n{}\n}}\n".format(
                '\n'.join([dotnode(v) for v in self.nodes()]),
                '\n'.join([dotedge(e) for e in self.edges()])
            ))
        else:
            logging.error("unknown format %s" % fmt)
        return out.getvalue()


class EnergyGame(Game):
    objective = "energy"

    def playernodes(self, player):
        return [v for v in self.nodes() if self.node[v]['owner'] == player]

    def weight(self, e):
        """ shortcut to extract the weight of an edge """
        src, trg = e
        return self.edge[src][trg]['weight']

    def __str__(self):
        return self.format('eg')

    def maxdrop(self, node=None):
        def min_successor_weight(v):
            return min([0] + [self[v][nbr]['weight'] for nbr in self[v]])
        if node is None:
            return max(-min(0, min_successor_weight(v)) for v in self.nodes())
        else:
            return -min(0, min_successor_weight(node))
