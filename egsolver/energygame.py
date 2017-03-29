# Copyright (C) 2017  Patrick Totzke <patricktotzke@gmail.com>
# This file is released under the GNU GPL, version 3 or a later revision.

import re
import logging
from networkx import DiGraph

from io import StringIO


class ParseError(Exception):
    pass


class EnergyGame(DiGraph):

    @classmethod
    def from_string(cls, game_as_string):
        # some regexps to extract node/edge info
        NRE = r'^\s*[Nn]ode\s+(?P<id>\d+)'\
              r'\s+(?P<owner>\d+)\s*("(?P<label>\S*)")?'
        ERE = r'^\s*[Ee]dge\s+(?P<src>\d+)\s+(?P<trg>\d+)'\
              r'\s*(?P<weight>(-|\+)?\d*)'

        game = cls()
        for line in game_as_string.splitlines():
            line = re.sub(r'\s*\#.*$', '', line)
            line = line.strip()
            if line:
                match = re.match(NRE, line)
                if match:
                    nodeprops = match.groupdict()
                    id = int(nodeprops.pop('id'))
                    owner = int(nodeprops.pop('owner'))
                    game.add_node(id, owner=owner, **nodeprops)
                    continue

                match = re.match(ERE, line)
                if match:
                    edgeprops = match.groupdict()
                    src = int(edgeprops.pop('src'))
                    trg = int(edgeprops.pop('trg'))
                    w = int(edgeprops.pop('weight'))
                    game.add_edge(src, trg, weight=w)
                    continue

                raise ParseError(line)
        return game

    def format(self, fmt='eg', out=None, solver=None):
        # we'll write to a file object, since networkx's formatter are weird..
        out = out or StringIO()

        # get winning set and optimal strategy from solver
        if solver:
            win = solver.win
            opt = solver.optimal_strategy()  # this is a list of edges
        else:
            win = opt = {}

        if fmt == 'eg':
            def nodestr(v):
                return "node %d %d \"%s\"" % (v,
                                              self.node[v]['owner'],
                                              self.node[v].get('label', ''))

            def edgestr(e):
                s, t = e
                return "edge %d %d %d" % (s, t, self[s][t]['weight'])

            out.write("\n".join(
                [nodestr(v) for v in self.nodes()] +
                [edgestr(e) for e in self.edges()]
            ))

        elif fmt == 'dot':
            def dotnode(v):
                info = {
                    'id': v,
                    'shape': "box" if self.node[v]['owner'] else "diamond",
                    'label': self.node[v].get('label', '') or str(v)
                }
                if win:
                    fmt = "{id} [shape=\"{shape}\"," \
                        "label=\"{label}\", color=\"{color}\"];"
                    info['color'] = "red"
                    if win[v] >= 0:
                        info['color'] = "green"
                        info['label'] += (": %s" % win[v])
                else:
                    fmt = "{id} [shape=\"{shape}\", label=\"{label}\"];"
                return fmt.format(**info)

            def dotedge(e):
                src, trg = e
                info = {
                    'src': src,
                    'trg': trg,
                    'lbl': self[src][trg]['weight']
                }
                if win and (src in opt) and src in self.playernodes(0)\
                   and (trg == opt[src]):
                    fmt = "{src} -> {trg} [label=\"{lbl}\", color=\"{col}\"];"
                    info['col'] = "green"
                else:
                    fmt = "{src} -> {trg} [label=\"{lbl}\"];"
                return fmt.format(**info)

            out.write("digraph G {{\n{}\n{}\n}}\n".format(
                '\n'.join([dotnode(v) for v in self.nodes()]),
                '\n'.join([dotedge(e) for e in self.edges()])
            ))
        else:
            logging.error("unknown format %s" % fmt)
        return out.getvalue()

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
