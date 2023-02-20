# Copyright (C) 2017  Patrick Totzke <patricktotzke@gmail.com>
# This file is released under the GNU GPL, version 3 or a later revision.

import sys
from timeit import timeit
import argparse
import logging

from .games import EnergyGame
from .generators import random_energy_game
from .solvers import ProgressMeasureSolver as Solver
from .formatters import GAME_FORMATTERS, RESULT_FORMATTERS
from .reductions import energy_to_parity
from . import __version__, __shortinfo__


def convert(args):
    """ convert game description to another format """
    logging.info("parsing input..")
    game = EnergyGame.from_game_string(args.infile.read())
    logging.debug("got game:\n%s" % game)
    if args.gametype == "parity":
        logging.debug("converting to paritygame..")
        game = energy_to_parity(game)
    if args.outfmt == "pgsolver":
        out = game.to_pgsolver_format()
    else:
        formatter = GAME_FORMATTERS[args.outfmt]
        out = formatter(game)
    logging.info("writing output..")
    args.outfile.write(out)


def generate(args):
    """ generate a random game """
    eg = random_energy_game(args.n, args.d, args.o, args.e, -args.e,
                            args.nosinks)
    formatter = GAME_FORMATTERS[args.outfmt]
    args.outfile.write(formatter(eg))


def solve(args):
    """ solve a game """
    logging.info("parsing input..")
    eg = EnergyGame.from_game_string(args.infile.read())
    logging.debug("got game:\n%s" % eg)

    logging.info("instanciating solver..")
    solver = Solver(eg)

    logging.info("solving..")
    delay = timeit(solver.solve, number=1)
    logging.info("done in %fs" % delay)

    logging.info("writing output..")
    formatter = RESULT_FORMATTERS[args.outfmt]
    args.outfile.write(formatter(eg, solver, delay))


COMMANDS = {
    'convert': convert,
    'generate': generate,
    'solve': solve,
}


def main():
    infile_help = "where to read from; defaults to \'-\' (stdin)"
    logfile_help = "where to log to; defaults to \'-\' (stdout)"
    outfile_help = "where to write to; defaults to \'-\' (stdout)"

    # define some arguments to parse
    parser = argparse.ArgumentParser(description="energy game solver")

    # global parameters
    parser.add_argument('-v', '--verbose', action='count', default=0,
                        help='increase verbosity')
    parser.add_argument('--version', action='version', version=__version__)
    parser.add_argument('-l', '--logfile', help=logfile_help,
                        type=argparse.FileType('w'), default=sys.stdout)
    subparsers = parser.add_subparsers(title="commands", dest='cmd')

    # parameters for the 'convert' subcommand
    parser_convert = subparsers.add_parser('convert', help=convert.__doc__)
    parser_convert.add_argument('infile', nargs='?', help=infile_help,
                                type=argparse.FileType('r'), default=sys.stdin)
    parser_convert.add_argument('outfile', nargs='?', help=outfile_help,
                                type=argparse.FileType('w'),
                                default=sys.stdout)
    parser_convert.add_argument('-f', '-outfmt', dest='outfmt',
                                choices=["pgsolver"] + list(GAME_FORMATTERS),
                                default='eg',
                                help='output format; defaults to \'eg\'')
    parser_convert.add_argument('-t', '-type', dest='gametype',
                                default='energy', choices={'energy', 'parity'},
                                help='the type of game to reduce to')

    # parameters for the 'generate' subcommand
    parser_generate = subparsers.add_parser('generate', help=generate.__doc__)
    parser_generate.add_argument('n', type=int, help='number of nodes')
    parser_generate.add_argument('d', type=float, help='density of edges')
    parser_generate.add_argument('o', type=float, help='density of owner')
    parser_generate.add_argument('e', type=int, help='max effect')
    parser_generate.add_argument('-s', '--nosinks', action='store_true',
                                 help='replace sinks with negative self-loops')
    parser_generate.add_argument('-f', '-outfmt', dest='outfmt',
                                 choices=list(GAME_FORMATTERS), default='eg',
                                 help='output format; defaults to \'eg\'')
    parser_generate.add_argument('outfile', nargs='?', help=outfile_help,
                                 type=argparse.FileType('w'),
                                 default=sys.stdout)

    # parameters for the 'solve' subcommand
    parser_solve = subparsers.add_parser('solve', help=solve.__doc__)
    parser_solve.add_argument('infile', nargs='?', help=infile_help,
                              type=argparse.FileType('r'), default=sys.stdin)
    parser_solve.add_argument('outfile', nargs='?', help=outfile_help,
                              type=argparse.FileType('w'), default=sys.stdout)
    parser_solve.add_argument('-f', '-outfmt', dest='outfmt', default='report',
                              choices=RESULT_FORMATTERS.keys(),
                              help='output format; defaults to \'report\'')

    # parse arguments
    args = parser.parse_args()

    # complain if arguments clash
    if args.cmd == "convert":
        if (args.gametype, args.outfmt) == ('energy','pgsolver'):
            parser.error('out format \'pgsolver\' only works for parity games')

    # set up debug logging
    levels = [logging.WARNING, logging.INFO, logging.DEBUG]
    numeric_loglevel = levels[min(2, args.verbose)]
    logformat = '%(levelname)s %(message)s'
    logging.basicConfig(level=numeric_loglevel, stream=args.logfile,
                        format=logformat)

    # welcome message
    logging.info("This is %s" % __shortinfo__)
    logging.debug("got parameters: %s" % args)

    # call subcommand function
    try:
        COMMANDS[args.cmd](args)
        sys.exit(0)
    except Exception as e:
        logging.error(e)
        sys.exit(1)
