# Copyright (C) 2017  Patrick Totzke <patricktotzke@gmail.com>
# This file is released under the GNU GPL, version 3 or a later revision.

import logging
import networkx as nx
import numpy as np
from .formatters import game_format_eg


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
        # some shorthands
        eg = self.game
        n = nx.number_of_nodes(eg)
        owner = nx.get_node_attributes(eg, 'owner')

        # get adjacency matrix and a weight matrix with non-edges masked
        adj = nx.to_numpy_matrix(eg, nonedge=0, weight=None).astype(np.bool)
        weightmatrix = nx.to_numpy_matrix(eg, weight="effect").astype(np.int)
        weightmatrix = np.ma.array(weightmatrix, mask=np.invert(adj))
        # TODO: don't use masked arrays, apparently they are slow

        # compute top element above wich we cut off
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
        def set_str(bm):
            return "{%s}" % ",".join({str(v) for v in eg.nodes() if bm[0, v]})
        logging.debug("dirty: %s" % set_str(dirty))

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
            logging.debug("dirty states: %s" % set_str(dirty))

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
                preds = adj.T[v]
                if preds.any():
                    logging.debug("enqueue predecessors: %s" % set_str(preds))
                    np.bitwise_or(dirty, preds, out=dirty)
                    # TODO: don't enqueue sinks / stuff with value top

        logging.debug("measure: %s" % pm)
        # remember and return the progress measure = winning region

        def top_as_minus_one(i):
            return -1 if i == top else int(i)
        self.win = {v: top_as_minus_one(pm[v]) for v in eg.nodes()}
        return self.win


class Z3Solver(Solver):
    """
    Solver that uses Microsoft's Z3 SMT solver (https://github.com/Z3Prover/z3)
    to guess and verify a game progress measure.

    The progress measure condition directly translated
    into constraints over an uninterpreted function En: N --> N;
    Losing states are identified as those with negative Mean-Payoff.
    Mean-Payoff values are expressed using Gain/Bias functions,
    (see e.g. :doi:`10.4230/LIPIcs.FSTTCS.2016.44`).
    """

    def __init__(self, eg, initial_credit=1):
        super(Z3Solver, self).__init__(eg)
        #import z3

    def solve(self):
        import z3
        # some shorthands
        eg = self.game
        n = nx.number_of_nodes(eg)
        owner = nx.get_node_attributes(eg, 'owner')
        effect = self.game.effect

        s = z3.Solver()
        s = z3.Optimize()
        # define energy measure, Gain and Bias as uninterpreted functions
        EN = z3.Function('Energy', z3.IntSort(), z3.IntSort())
        Gain = z3.Function('Gain', z3.IntSort(), z3.RealSort())
        Bias = z3.Function('Bias', z3.IntSort(), z3.RealSort())

        def minmax_among(player, x, Y):
            """
            builds z3 constraint encoding that x is maximum/minimum of Y,
            depending on the parity of the first parameter
            to all values in Y.
            """
            if player == 1:
                return z3.And([x <= y for y in Y]+
                              [z3.Or([x == y for y in Y])])
            else:
                return z3.And([x >= y for y in Y]+
                              [z3.Or([x == y for y in Y])])

        for v in eg.nodes():
            succs = eg.successors(v)
            logging.debug(succs)

            # Gain constraint
            # Gain(v) is min/max Gain(w) over all successors w
            clause = minmax_among(owner[v], Gain(v), [Gain(w) for w in succs])
            logging.debug("Gain constraint for state %d:\n %s" % (v,clause))
            s.add(clause)

            # Bias constraint
            # Bias(v) is min/max {edgecost - Gain(v) + Bias(w) } over successors
            # w with equal Gain
            if owner[v] == 0: # max
                forall = z3.And(
                    [
                     z3.Or(Gain(v) != Gain(w),
                           Bias(v) >= effect((v, w)) - Gain(v) + Bias(w))
                     for w in succs
                    ]
                )
                exists = z3.Or(
                    [
                     z3.And(Gain(v) == Gain(w),
                            Bias(v) == effect((v, w)) - Gain(v) + Bias(w))
                     for w in succs
                    ]
                )
                clause = z3.And(forall,exists)
            else:
                forall = z3.And(
                    [
                     z3.Or(Gain(v) != Gain(w),
                           Bias(v) <= effect((v, w)) - Gain(v) + Bias(w))
                     for w in succs
                    ]
                )
                exists = z3.Or(
                    [
                     z3.And(Gain(v) == Gain(w),
                            Bias(v) == effect((v, w)) - Gain(v) + Bias(w))
                     for w in succs
                    ]
                )
                clause = z3.And(forall,exists)

            logging.debug("Bias constraint for state %d:\n %s" % (v,clause))
            s.add(clause)

            # Energy progress measure constraints
            sc = [EN(v) >= EN(w) - effect((v,w)) for w in succs]
            if owner[v] == 1:  # pick maximum among successors
                not_top = z3.And(sc)
            else:  # pick minimum (as we later minimize the sum of EN
                not_top = z3.Or(sc)
            # the energy-proress constraint should hold for states with
            # non-negative mean-payoff.
            clause = z3.Implies(Gain(v) >=0, not_top)
            logging.debug("ePM constraint for state %d:\n %s" % (v,clause))
            s.add(clause)
            s.add(EN(v) >= 0)

        # make sure we get the minimal sulution
        s.minimize(sum(EN(v) for v in range(n)))

        # call SMT solver and prepare result
        res = s.check()
        logging.info("res: %s" % res)
        if res == z3.sat:
            model = s.model()
            logging.info("MODEL: %s\n\n" % model)
            for v in range(n):
                logging.debug("TOP: %d: %s" % (v, model.eval(Gain(v) < 0)))

            def top_as_minus_one(v):
                if z3.is_true(model.eval(Gain(v) < 0)):
                    return -1
                else:
                    return model.eval(EN(v)).as_long()

            self.win = {v: top_as_minus_one(v) for v in eg.nodes()}
        return self.win


SOLVERS = {
    'pm': ProgressMeasureSolver,
    'z3': Z3Solver,
}
