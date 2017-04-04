# Copyright (C) 2017  Patrick Totzke <patricktotzke@gmail.com>
# This file is released under the GNU GPL, version 3 or a later revision.

import logging
import numpy as np
import networkx as nx
from .games import ParityGame


def energy_to_parity(eg, initial_credit=0):
    """ reduce an energy game to a parity game """
    priority = {}
    initial_credit = initial_credit

    p = ParityGame()
    number_of_states = len(eg.nodes())

    em = nx.to_numpy_matrix(eg, weight="effect")
    maxeffect =  int(np.max(np.abs(em)))

    top = maxeffect * number_of_states +1
    bottom = -(initial_credit or top)

    nid = 0
    egnode_of = {}
    pgnode_of = {}
    for n in range(bottom,top+1):
        for s in eg.nodes():

            egnode_of[nid] = (s,n)
            pgnode_of[(s,n)] = nid
            label = "{}({})".format(s,n)

            if n == bottom:
                owner = eg.node[s]['owner']
                priority = 0
                p.add_node(nid, owner=0, priority=0, label=label)
                p.add_edge(nid, nid)
            elif n == top:
                p.add_node(nid, owner=0, priority=1, label=label)
                p.add_edge(nid, nid)
            else:
                o = eg.node[s]['owner']
                p.add_node(nid, owner=o, priority=1, label=label)

            nid += 1

    for n in range(bottom+1,top):
        for (s,t) in eg.edges():
            m = max(min(n+eg.effect((s,t)), top), bottom)
            p.add_edge(pgnode_of[(s,n)], pgnode_of[(t,m)])
    logging.debug("Parity Game:\n %s" % p.to_pgsolver_format())
    return p
