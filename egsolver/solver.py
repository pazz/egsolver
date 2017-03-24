# Copyright (C) 2017  Patrick Totzke <patricktotzke@gmail.com>
# This file is released under the GNU GPL, version 3 or a later revision.

import networkx as nx
import numpy as np
from numpy.ma import masked
import logging


class Solver(object):
    """
    Solver base class
    """

    def __init__(self, eg):
        self.game = eg
        self.win = {}

    def solve(self):
        return self.win

    def optimal_strategy(self):
        eg = self.game
        win = self.win
        weight = self.game.weight
        nodes = self.game.nodes()
        #nodes = [v in self.game.nodes() if self.game.node[v]['owner']==1]
        playernodes = eg.playernodes(0)

        if win:
            def opt_succ(v):
                # get all winning successor nodes
                winsuccs = [t for t in self.game.successors(v) if win[t] >= 0]

                # pick the one where its value after getting there is minimal
                def needs_energy(t):
                    return win[t] - weight((v, t))
                return min(winsuccs, key=needs_energy)
            opt = {v:opt_succ(v) for v in playernodes if win[v] >= 0}
        else:
            opt = {}
        return opt


class ProgressMeasureSolver(Solver):
    """
    Solver that implements the small progress measures algorithm.

    The procedure is described in detail in
        Faster algorithms for mean-payoff games
        Brim, Chaloupka, Doyen, Gentilini, Raskin
        Form Methods Syst Des (2011) 38: 97.
        :doi:`10.1007/s10703-010-0105-x`

    Progress measures, state sets, and weight/adjacency matrices
    are represented directly in numpy.
    """

    def solve(self):
        # shortcuts for quick lookups
        eg = self.game
        n = nx.number_of_nodes(eg)
        owner = nx.get_node_attributes(eg, 'owner')

        # get adjacency matrix and a weight matrix with non-edges masked
        adj = nx.to_numpy_matrix(eg, nonedge=0, weight=None).astype(np.bool)
        weightmatrix = nx.to_numpy_matrix(eg).astype(np.int)
        weightmatrix = np.ma.array(weightmatrix, mask=np.invert(adj))

        # compute top element above with we cut off
        cutoff = sum(eg.maxdrop(v) for v in eg)
        top = cutoff + eg.maxdrop()
        logging.debug("TOP = %d" % top)

        # initialize progress measure
        # we'll use an intvector with (initially empty) bitmask
        # sinks are already top, i.e. losing.
        pm = np.zeros(n, dtype=np.int).view(np.ma.MaskedArray)
        for v in eg.nodes():
            if not adj[v].any():
                pm[v] = top

        # bitvector to remember set of dirty states
        dirty = np.matrix([True] * n)

        # define formatter used in logging etc
        def as_set(bm):
            return {v for v in eg.nodes() if bm[0,v]}
        logging.debug("dirty: %s" % as_set(dirty))

        # compute the new measure for state v
        bestfor = {0: np.min, 1: np.max}  # player 0 is the minimizer

        def lift(v):
            lifts = (pm - weightmatrix[v])
            logging.debug("lifts: %s" % lifts)
            # mask everything above equal to top
            #lifts = np.ma.masked_where(lifts >= top, lifts)
            #logging.debug("lifts masked: %s" % lifts)
            return bestfor[owner[v]](lifts)

        # main loop
        while dirty.any():
            logging.debug("measure: %s" % pm)
            logging.debug("dirty states: %s" % as_set(dirty))

            v = dirty.argmax()   # pick some dirty state
            dirty[0,v] = False   # mark it not dirty
            logging.debug("considering state %d" % v)

            # compute new measure and remember previous one for comparison
            nextval = lift(v)
            logging.debug("the new value for state %d is %s" % (v, nextval))
            if nextval >= cutoff:
                nextval = top

            # really update?
            # the complication is due to our use of numpy.ma.masked for top:
            # equality tests on them via == always return masked ~ False.
            #if (nextval is masked and pm is not masked):
            #    pm[v] = top
            if (nextval > pm[v]):
                pm[v] = nextval

                # mark predecessors dirty if there are any
                if adj.T[v].any():
                    logging.debug("enqueue predecessors: %s" % as_set(adj.T[v]))
                    np.bitwise_or(dirty,adj.T[v], out=dirty)

        # remember and return the progress measure = winning region
        def top_as_minus_one(i):
            return -1 if i == top else int(i)
        self.win = {v:top_as_minus_one(pm[v]) for v in eg.nodes()}
        return self.win
