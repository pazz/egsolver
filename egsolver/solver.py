# Copyright (C) 2017  Patrick Totzke <patricktotzke@gmail.com>
# This file is released under the GNU GPL, version 3 or a later revision.

import logging
import networkx as nx
import numpy as np


class Solver(object):
    """ Solver base class """

    def __init__(self, eg):
        self.game = eg
        self.win = {}

    def solve(self):
        return self.win

    def optimal_strategy(self):
        eg = self.game
        win = self.win
        effect = self.game.effect
        playernodes = eg.playernodes(0)

        if win:
            def opt_succ(v):
                # get all winning successor nodes
                winsuccs = [t for t in eg.successors(v) if win[t] >= 0]

                # pick the one where its value after getting there is minimal
                def needs_energy(t):
                    return win[t] - effect((v, t))
                return min(winsuccs, key=needs_energy)
            opt = {v: opt_succ(v) for v in playernodes if win[v] >= 0}
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
        weightmatrix = nx.to_numpy_matrix(eg, weight="effect").astype(np.int)
        weightmatrix = np.ma.array(weightmatrix, mask=np.invert(adj))
        # TODO: don't use masked arrays, apparently they are slow

        # compute top element above with we cut off
        em = nx.to_numpy_matrix(eg, weight="effect")
        maxinc = np.max(em)

        def maxdrop_from(src):
            return -np.min(em[src])

        cutoff = sum(maxdrop_from(v) for v in eg) + 1
        logging.debug("CUTOFF = %d" % cutoff)
        top = cutoff + maxinc
        logging.debug("TOP = %d" % top)

        # bitvector to remember set of states to reconsider
        dirty = np.matrix([True] * n)

        # initialize progress measure
        # we'll use an integer vector with (initially empty) bitmask
        pm = np.zeros(n, dtype=np.int).view(np.ma.MaskedArray)
        for v in eg.nodes():  # sinks should be losing.
            if not adj[v].any():
                pm[v] = top   # mark them so
                dirty[0, v] = False   # mark them as done

        # define formatter used in logging
        def as_set(bm):
            return {v for v in eg.nodes() if bm[0, v]}
        logging.debug("dirty: %s" % as_set(dirty))

        # compute the new measure for state v
        bestfor = {0: np.min, 1: np.max}  # player 0 is the minimizer

        def lift(v):
            # TODO: only do this for successors of v
            lifts = (pm - weightmatrix[v])
            logging.debug("lifts: %s" % lifts)
            return bestfor[owner[v]](lifts)

        # main loop
        while dirty.any():
            logging.debug("measure: %s" % pm)
            logging.debug("dirty states: %s" % as_set(dirty))

            v = dirty.argmax()   # pick some dirty state
            dirty[0, v] = False   # mark it not dirty
            logging.debug("considering state %d" % v)

            # compute new measure and remember previous one for comparison
            nextval = lift(v)
            if (nextval >= cutoff) or (nextval is np.ma.masked):
                nextval = top
            logging.debug("the new value for state %d is %s" % (v, nextval))

            # really update only on strict increases
            if (nextval > pm[v]):
                pm[v] = nextval

                # mark predecessors dirty if there are any
                if adj.T[v].any():
                    logging.debug("enqueue predecessors: %s" % as_set(adj.T[v]))
                    np.bitwise_or(dirty, adj.T[v], out=dirty)
                    # TODO: don't enqueue sinks / stuff with value top

        logging.debug("measure: %s" % pm)
        # remember and return the progress measure = winning region

        def top_as_minus_one(i):
            return -1 if i == top else int(i)
        self.win = {v: top_as_minus_one(pm[v]) for v in eg.nodes()}
        return self.win
