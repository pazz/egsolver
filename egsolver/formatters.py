# Copyright (C) 2017  Patrick Totzke <patricktotzke@gmail.com>
# This file is released under the GNU GPL, version 3 or a later revision.

import json
import networkx as nx


def format_report(game, solver):
    output = "winning region: %s\n" % solver.win
    output += "an optimal strategy: %s" % solver.optimal_strategy()
    return output


def format_json(game, solver):
    opt = solver.optimal_strategy()
    return json.dumps({'win': solver.win, 'opt': opt})


def format_dot(game, solver):
    opt = solver.optimal_strategy()
    win = solver.win
    nx.set_node_attributes(game, "win", win)
    color = {}
    for v in game.nodes():
        color[v] = "green" if win[v] >= 0 else "red"
    nx.set_node_attributes(game, "color", color)
    return game.format('dot')


FORMATTERS = {
    'report': format_report,
    'json': format_json,
    'dot': format_dot,
}

