# Copyright (C) 2017  Patrick Totzke <patricktotzke@gmail.com>
# This file is released under the GNU GPL, version 3 or a later revision.

import logging
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

    # shape nodes according to owner
    shape = {}
    for v in game.nodes():
        shape[v] = "box" if game.node[v]['owner'] else "diamond"
    nx.set_node_attributes(game, "shape", shape)

    return "digraph G {{\n{}\n{}\n}}\n".format(
        '\n'.join([dotnode(v) for v in game.nodes()]),
        '\n'.join([dotedge(e) for e in game.edges()])
    )

GAME_FORMATTERS = {
    'eg': game_format_eg,
    'dot': game_format_dot,
}


def result_format_report(game, solver, time):
    res = "This game has %d nodes and %d edges.\n" % (len(game.nodes()),
                                                      len(game.edges()))
    res += "The winning region is: %s\n" % solver.win
    opt = solver.optimal_strategy()
    if opt:
        opt = ", ".join([ "%d-->%d" % (s,t) for (s,t) in opt.items()])
        res += "An optimal strategy is: %s\n" % opt
    res += "It took me %fs to solve this game.\n" % time
    res += "Goodbye."
    return res


def result_format_json(game, solver, time):
    opt = solver.optimal_strategy()
    return json.dumps({
        'win': solver.win,
        'opt': opt,
        'time': time
    })


def result_format_dot(game, solver, time):
    win = solver.win
    opt = solver.optimal_strategy()
    nx.set_node_attributes(game, "win", win)

    # color nodes according to who wins
    logging.debug(opt)
    logging.debug(win)
    color = {}
    label = {}
    for v in game.nodes():
        color[v] = "green" if win[v] >= 0 else "red"
        label[v] = "%d (%d)" % (v, win[v]) if win[v]>=0 else str(v)

    nx.set_node_attributes(game, "label", label)
    nx.set_node_attributes(game, "color", color)

    # color edges to indicate optimal moves
    color = {}
    for src, trg in game.edges():
        if src in opt and opt[src] == trg:
            color[(src,trg)] = "green"
    logging.debug(color)
    nx.set_edge_attributes(game, "color", color)

    return game_format_dot(game)


RESULT_FORMATTERS = {
    'report': result_format_report,
    'json': result_format_json,
    'dot': result_format_dot,
}
