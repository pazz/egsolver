# Copyright (C) 2017  Patrick Totzke <patricktotzke@gmail.com>
# This file is released under the GNU GPL, version 3 or a later revision.

import json
import networkx as nx


def game_format_eg(game, indent=2):
    """
    format a game as (pretty printed) json string
    """
    GAME_FILE_FORMAT = "{{\n\"objective\": \"{objective}\",\n"\
        + "\"nodes\":{nodes},\n" \
        + "\"edges\":{edges}\n}}"

    def nodeline(v):
        return indent * " " + json.dumps((v, game.node[v]))

    def edgeline(e):
        return indent * " " + json.dumps(e)

    elist = nx.to_edgelist(game)
    elist_json = "[\n" + ",\n".join([edgeline(e) for e in elist]) + "\n]"

    nlist = game.nodes()
    nlist_json = "[\n" + ",\n".join([nodeline(v) for v in nlist]) + "\n]"
    return GAME_FILE_FORMAT.format(objective=game.objective,
                                   nodes=nlist_json,
                                   edges=elist_json,)


def game_format_dot(game):
    def propfmt(k, v):
        fmt = "{}={}"
        if isinstance(v, str):
            fmt = "{}=\"{}\""
        return fmt.format(k, v)

    def propsfmt(props):
        return ", ".join([propfmt(k, v) for k, v in props.items()])

    def dotnode(v):
        return "%d [%s];" % (v, propsfmt(game.node[v]))

    def dotedge(e):
        s, t = e
        return "%d -> %d [%s];" % (s, t, propsfmt(game.edge[s][t]))

    return "digraph G {{\n{}\n{}\n}}\n".format(
        '\n'.join([dotnode(v) for v in game.nodes()]),
        '\n'.join([dotedge(e) for e in game.edges()])
    )

GAME_FORMATTERS = {
    'eg': game_format_eg,
    'dot': game_format_dot,
}


def result_format_report(game, solver):
    output = "winning region: %s\n" % solver.win
    output += "an optimal strategy: %s" % solver.optimal_strategy()
    return output


def result_format_json(game, solver):
    opt = solver.optimal_strategy()
    return json.dumps({'win': solver.win, 'opt': opt})


def result_format_dot(game, solver):
    win = solver.win
    nx.set_node_attributes(game, "win", win)
    color = {}
    for v in game.nodes():
        color[v] = "green" if win[v] >= 0 else "red"
    nx.set_node_attributes(game, "color", color)
    return game_format_dot(game)


RESULT_FORMATTERS = {
    'report': result_format_report,
    'json': result_format_json,
    'dot': result_format_dot,
}
