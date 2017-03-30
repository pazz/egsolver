Egsolver solves finite, two-player energy games [[0],[1],[2]].
It is written in python and loosely motivated by the [pgsolver][pgsolver] suite for parity games.

Installation
------------

Get the latest version:

```
git clone git@github.com:pazz/egsolver.git
```

In case you have [pip][pip] installed, the following will do.

```
pip install ./egsolver
```

Otherwise, manually install the dependencies:

1. [numpy][np]
2. [networkx][nx]

On debian/ubuntu:
```
sudo aptitude install python-networkx python-numpy
```

Now install egsolver using the setup script:

```
./setup.py install --user
```

This should install the executable as `$HOME.local/bin/egsolver`.


Usage
------

There are currently three subcommands: `convert`, `generate`, and `solve`.

```
$egsolver -h

usage: egsolver [-h] [-v] [--version] [-l LOGFILE] {convert,generate,solve} ...

energy game solver

optional arguments:
  -h, --help            show this help message and exit
  -v, --verbose         increase verbosity
  --version             show program's version number and exit
  -l LOGFILE, --logfile LOGFILE
                        where to log to; defaults to '-' (stdout)

commands:
  {convert,generate,solve}
    convert             convert game description to another format
    generate            generate a random game
    solve               solve a game
```

Also check out `egsolver solve -h` etc.

To generate and solve a random game:

```
egsolver generate 5 0.5 0.5 10 | egsolver solve
```

To format the result in [dot][dot]-format and display with `xdot`:

```
egsolver generate 5 0.5 0.5 10 | egsolver solve -f dot | xdot -
```


Input Format
------------
egsolver uses a custom [JSON][json] format.
To see an example, just generate a random game graph:

```
egsolver generate 5 0.5 0.5 10
```


[np]: http://www.numpy.org
[nx]: http://networkx.github.io
[json]: https://en.wikipedia.org/wiki/JSON
[dot]: https://en.wikipedia.org/wiki/DOT_(graph_description_language)
[pip]: https://pip.pypa.io
[pgsolver]: https://github.com/tcsprojects/pgsolver

[0]: http://dx.doi.org/10.1007/978-3-540-85778-5_4
[1]: http://dx.doi.org/10.1007/978-3-540-45212-6_9
[2]: http://dx.doi.org/10.1007/s10703-010-0105-x