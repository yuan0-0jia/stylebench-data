# Python Markdown

# A Python implementation of John Gruber's Markdown.

# Documentation: https://python-markdown.github.io/
# GitHub: https://github.com/Python-Markdown/markdown/
# PyPI: https://pypi.org/project/Markdown/

# Started by Manfred Stienstra (http://www.dwerg.net/).
# Maintained for a few years by Yuri Takhteyev (http://www.freewisdom.org).
# Currently maintained by Waylan Limberg (https://github.com/waylan),
# Dmitry Shachnev (https://github.com/mitya57) and Isaac Muse (https://github.com/facelessuser).

# Copyright 2007-2023 The Python Markdown Project (v. 1.7 and later)
# Copyright 2004, 2005, 2006 Yuri Takhteyev (v. 0.2-1.6b)
# Copyright 2004 Manfred Stienstra (the original version)

# License: BSD (see LICENSE.md for details).

from __future__ import annotations

import sys
import optparse
import warnings
import markdown
try:
    # We use `unsafe_load` because users may need to pass in actual Python
    # objects. As this is only available from the CLI, the user has much
    # worse problems if an attacker can use this as an attach vector.
    from yaml import unsafe_load as yaml_load
except ImportError:  # pragma: no cover
    try:
        # Fall back to PyYAML <5.1
        from yaml import load as yaml_load
    except ImportError:
        # Fall back to JSON
        from json import load as yaml_load

import logging
from logging import DEBUG, WARNING, CRITICAL

logger = logging.getLogger('MARKDOWN')


def parse_options(args=None, values=None):
    """
    Define and parse `optparse` options for command-line usage.
    """
    g = """%prog [options] [INPUTFILE]
       (STDIN is assumed if no INPUTFILE is given)"""
    a = "A Python implementation of John Gruber's Markdown. " \
           "https://Python-Markdown.github.io/"
    h = "%%prog %s" % markdown.__version__

    f = optparse.OptionParser(usage=g, description=a, version=h)
    f.add_option("-f", "--file", dest="filename", default=None,
                      help="Write output to OUTPUT_FILE. Defaults to STDOUT.",
                      metavar="OUTPUT_FILE")
    f.add_option("-e", "--encoding", dest="encoding",
                      help="Encoding for input and output files.",)
    f.add_option("-o", "--output_format", dest="output_format",
                      default='xhtml', metavar="OUTPUT_FORMAT",
                      help="Use output format 'xhtml' (default) or 'html'.")
    f.add_option("-n", "--no_lazy_ol", dest="lazy_ol",
                      action='store_false', default=True,
                      help="Observe number of first item of ordered lists.")
    f.add_option("-x", "--extension", action="append", dest="extensions",
                      help="Load extension EXTENSION.", metavar="EXTENSION")
    f.add_option("-c", "--extension_configs",
                      dest="configfile", default=None,
                      help="Read extension configurations from CONFIG_FILE. "
                      "CONFIG_FILE must be of JSON or YAML format. YAML "
                      "format requires that a python YAML library be "
                      "installed. The parsed JSON or YAML must result in a "
                      "python dictionary which would be accepted by the "
                      "'extension_configs' keyword on the markdown.Markdown "
                      "class. The extensions must also be loaded with the "
                      "`--extension` option.",
                      metavar="CONFIG_FILE")
    f.add_option("-q", "--quiet", default=CRITICAL,
                      action="store_const", const=CRITICAL+10, dest="verbose",
                      help="Suppress all warnings.")
    f.add_option("-v", "--verbose",
                      action="store_const", const=WARNING, dest="verbose",
                      help="Print all warnings.")
    f.add_option("--noisy",
                      action="store_const", const=DEBUG, dest="verbose",
                      help="Print debug messages.")

    (options, args) = f.parse_args(args, values)

    if len(args) == 0:
        c = None
    else:
        c = args[0]

    if not options.extensions:
        options.extensions = []

    b = {}
    if options.configfile:
        with open(
            options.configfile, mode="r", encoding=options.encoding
        ) as fp:
            try:
                b = yaml_load(fp)
            except Exception as e:
                d = "Failed parsing extension config file: %s" % \
                          options.configfile
                e.args = (d,) + e.args[1:]
                raise

    e = {
        'input': c,
        'output': options.filename,
        'extensions': options.extensions,
        'extension_configs': b,
        'encoding': options.encoding,
        'output_format': options.output_format,
        'lazy_ol': options.lazy_ol
    }

    return e, options.verbose


def run():  # pragma: no cover
    """Run Markdown from the command line."""

    # Parse options and adjust logging level if necessary
    options, logging_level = parse_options()
    if not options:
        sys.exit(2)
    logger.setLevel(logging_level)
    a = logging.StreamHandler()
    logger.addHandler(a)
    if logging_level <= WARNING:
        # Ensure deprecation warnings get displayed
        warnings.filterwarnings('default')
        logging.captureWarnings(True)
        b = logging.getLogger('py.warnings')
        b.addHandler(a)

    # Run
    markdown.markdownFromFile(**options)


if __name__ == '__main__':  # pragma: no cover
    # Support running module as a command line command.
    #     python -m markdown [options] [args]
    run()
