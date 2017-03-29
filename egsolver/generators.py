# Copyright (C) 2017  Patrick Totzke <patricktotzke@gmail.com>
# This file is released under the GNU GPL, version 3 or a later revision.

import random
import networkx as nx
from .energygame import EnergyGame


def random_energy_game(n, d, o, maxweight, minweight=None, nosinks=False):
    """
    generates a random energy game graph.

    :param n: number of nodes
    :type n: int
    :param d: probability of there being an edge between two nodes
    :type d: float
    :param o: probability of a node being owned by player 0
    :type o: float
    :param maxweight: maximal positive edge weight
    :type maxweight: int
    :param minweight: maximal negative edge weight (defaults to -maxweight)
    :type minweight: int
    :param nosinks: add negative-weight self-loops to sink nodes
    :type nosinks: bool
    """
    eg = EnergyGame(nx.fast_gnp_random_graph(n, d, directed=True))

    # add random weights to all edges
    minweight = minweight or -maxweight
    weight = {e: random.randint(minweight, maxweight) for e in eg.edges()}
    nx.set_edge_attributes(eg, 'weight', weight)

    # randomly assign owner to each node
    owner = {v: 1*(random.random() > o) for v in eg.nodes()}
    nx.set_node_attributes(eg, 'owner', owner)

    # the generator nx.fast_gnp_random_graph used above specifically avoids
    # self-loops, so we'll add them ourselves
    for v in eg.nodes():
        if random.random() <= d:
            # add a random self-loop according to edge probability
            eg.add_edge(v, v, weight=random.randint(minweight, maxweight))
        elif nosinks:
            # if no self-loop was generated but sinks are forbidden, add a
            # decreasing self-loop (makes the state losing)
            eg.add_edge(v, v, weight=-1)
    return eg
