# Copyright (C) 2017  Patrick Totzke <patricktotzke@gmail.com>
# This file is released under the GNU GPL, version 3 or a later revision.

import random
import networkx as nx
from .energygame import EnergyGame


def random_energy_game(n, d, o, maxweight, minweight=None):
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
    """
    eg = EnergyGame(nx.fast_gnp_random_graph(n, d, directed=True))

    owner = {v: 1*(random.random() > o) for v in eg.nodes()}
    nx.set_node_attributes(eg, 'owner', owner)

    minweight = minweight or -maxweight
    weight = {e: random.randint(minweight, maxweight) for e in eg.edges()}
    nx.set_edge_attributes(eg, 'weight', weight)
    return eg
