import argparse
import os
import sys

from pkg_resources import require
from loguru import logger as log

from pyfiglet import Figlet

from gover.cell_sizing import gmoverid_cell_sizing_toml_parsing, gmoverid_cell_sizing_console_parsing
from gover.varactor_sizing import varactor_sizing_toml_parsing, varactor_sizing_console_parsing
from gover.switch_sizing import switch_sizing_toml_parsing, switch_sizing_console_parsing
from gover.utils import getParent

from functools import wraps
import traceback

__file_dir__ = os.path.realpath(getParent(__file__))
__io_json__ = os.path.join(__file_dir__, "io.json")
__author__ = "Diogo André Silvares Dias"
__email__ = "das.dias6@gmail.com"



__cmds = {
    #"-ll": ("-load-lut", "Load the LUT data from the csv files", load_luts),
    "-cs": ("cell-sizing", "Compute the transistor sizing", gmoverid_cell_sizing_toml_parsing),
    "-vs": ("varactor-sizing", "Compute the MOS Capacitor sizing", varactor_sizing_toml_parsing),
    "-ss": ("switch-sizing", "Compute the MOS Switch sizing", switch_sizing_toml_parsing),
    "-scs": ("single-cell-sizing", "Compute the transistor sizing", gmoverid_cell_sizing_console_parsing),
    "-svs": ("single-varactor-sizing", "Compute the MOS Capacitor sizing", varactor_sizing_console_parsing),
    "-sss": ("single-switch-sizing", "Compute the MOS Switch sizing", switch_sizing_console_parsing),
}

__cmd_args = {
    "-cs": {
        "-s": ("--specs-file", "The path to the specifications file", "<file path>", str, "opt"), 
        "-o": ("--output-dir", "The path to the output folder", "<directory path>", str, "opt"),
        "-p": ("--print-curves", "Print the curves regarding the found DC Operating Point", "<>", bool, "opt")
    },
    "-vs": {
        "-s": ("--specs-file", "The path to the specifications file", "<file path>", str, "opt"), 
        "-o": ("--output-dir", "The path to the output folder", "<directory path>", str, "opt"),
        "-p": ("--print-curves", "Print the curves regarding the found DC Operating Point", "<>", bool, "opt")
    },
    "-ss": {
        "-s": ("--specs-file", "The path to the specifications file", "<file path>", str, "opt"), 
        "-o": ("--output-dir", "The path to the output folder", "<directory path>", str, "opt"),
        "-p": ("--print-curves", "Print the curves regarding the found DC Operating Point", "<>", bool, "opt")
    },
    "-scs": {
        "-t": ("--type", "The device channel type [nch - nmos, pch - pmos]", "<pch or nch>", str, ""), 
        "-vds": ("--v-drain-source", "The drain to source voltage", "<voltage>", str, "opt"),
        "-vsd": ("--v-source-drain", "The source to drain voltage", "<voltage>", str, "opt"),
        "-vsb": ("--v-source-bulk", "The source to bulk voltage", "<voltage>", str, "opt"),
        "-vbs": ("--v-bulk-source", "The bulk to source voltage", "<voltage>", str, "opt"),
        "-l": ("--length", "The length of the transistor's channel", "<length>", str, ""),
        "-gi": ("--gm-over-id", "The device\'s transconductance efficiency", "<gm/id value>", str, ""),
        "-id": ("--drive-current", "The driving current of the transistor", "<current>", str, "")
    },
    "-svs": {
        "-t": ("--type", "The device channel type [nch - nmos, pch - pmos]", "<pch or nch>", str, ""),
        "-vgs": ("--v-gate-source", "The voltage applied to the terminals of the N channel varactor", "<voltage>", str, "opt"),
        "-vsg": ("--v-source-gate", "The voltage applied to the terminals of the P channel varactor", "<voltage>", str, "opt"),
        "-l": ("--length", "The length of the transistor's channel", "<length>", str, ""),
        "-cvar": ("--cap-varactor", "The device\'s total gate to bulk capacitance", "<capacitance>", str, "")
    },
    "-sss": {
        "-t": ("--type", "The device channel type [nch - nmos, pch - pmos]", "<pch or nch>", str, ""),
        "-vgs": ("--v-gate-source", "The voltage applied to the terminals of the N channel varactor", "<voltage>", str, "opt"),
        "-vsg": ("--v-source-gate", "The voltage applied to the terminals of the P channel varactor", "<voltage>", str, "opt"),
        "-rds": ("--on-resistance", "The device\'s ON resistance", "<resistance>", str, "")
    }
}


def mapSubparserToFun(func, subparser):
    """_summary_
    Maps subparser to callback function
    Args:
        func (Function): callback function
        subparser (_type_): subparser object
    Returns:
        result (_type_): result of the callback function
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        return func(subparser, *args, **kwargs)
    return wrapper

def setup_parser(cmds, args) -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=f"Gm / Id Device Sizing Tool by {__author__} ({__email__})")
    # mutually exclusive arguments
    group = parser.add_mutually_exclusive_group()
    group.add_argument(
        "-q", "--quiet", 
        action="store_true", 
        help="quiet verbose"
    )
    group.add_argument(
        "-v", 
        "--verbose", 
        action="store_true", 
        help="print verbose"
    )
    # setup the subparsers
    subparsers = parser.add_subparsers()
    for cmd, (cmd_name, cmd_desc, cmd_func) in cmds.items():
        # setup the subparser
        subparser = subparsers.add_parser(cmd_name, help=cmd_desc)
        subparser.set_defaults(
            func = mapSubparserToFun(cmd_func, subparser)
        )
        for arg, (arg_name, arg_desc, arg_metavar, arg_type, opt) in args[cmd].items():
            
            if arg_type == str:
                subparser.add_argument(
                    arg, 
                    arg_name,
                    nargs=1,
                    type=arg_type,
                    help=arg_desc,
                    required=False if opt == "opt" else True,
                    metavar = arg_metavar if arg_metavar != "<>" else ""
                )
            elif arg_type in [bool, None]:
                subparser.add_argument(
                    arg, 
                    arg_name, 
                    action="store_true",
                    required=False if opt == "opt" else True,
                    help=arg_desc
                )
    return parser

def entry_msg() -> str:
    msgs = [
        Figlet(font="slant").renderText("GOVER"),
        "Gm / Id Device Sizing Tool",
        "by " + __author__ + " (" + __email__ + ")"
    ]
    max_ch = max([len(msg) for msg in msgs[1:]])+2
    sep = "#"
    ret = sep * (max_ch) + "\n"
    ret += msgs[0]
    for msg in msgs[1:]:
        ret += " " + msg + " "*(max_ch-len(msg)) + "\n"
    ret += sep * (max_ch) + "\n"
    return ret
    
def cli(argv = None) -> None:
    if argv is None:
        print(entry_msg())
        argv = list(sys.argv)
    # load lut data
    #load_luts(__file_dir__)
    # setup the parser and parse the arguments
    parser = setup_parser(__cmds, __cmd_args)
    subparsers = [tok for tok in __cmds.keys()] + [tok[0] for tok in __cmds.values()]
    if len(argv) <= 1: # append "help" if no arguments are given
        argv.append("-h")
    elif argv[1] in subparsers:
        if len(argv) == 2:
            argv.append("-h")   # append help when only 
                                    # one positional argument is given
    try:
        args = parser.parse_args(argv[1:])
        try:
            args.func(argv[1:], data_dir=__file_dir__, io_json = __io_json__)
        except Exception as e:
            log.error(traceback.format_exc())
    except argparse.ArgumentError as e: # catching unknown arguments
        log.warning(e)
    except Exception as e:
        log.error(traceback.format_exc())