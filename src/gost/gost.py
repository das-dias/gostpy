import argparse
import os
import sys


from gost import __version__, __author__, __email__, __description__
from loguru import logger as log

from pyfiglet import Figlet

from gost.cell_sizing import (
    gmoverid_cell_sizing_toml_parsing,
    gmoverid_cell_sizing_console_parsing,
)
from gost.varactor_sizing import (
    varactor_sizing_toml_parsing,
    varactor_sizing_console_parsing,
)
from gost.switch_sizing import switch_sizing_toml_parsing, switch_sizing_console_parsing
from gost.utils import getParent

from functools import wraps
import traceback

__file_dir__ = os.path.realpath(getParent(__file__))
# __file_dir__ = os.path.realpath(__file__)
__io_json__ = os.path.join(__file_dir__, "io.json")
__author__ = "Diogo André Silvares Dias"
__email__ = "das.dias6@gmail.com"

# define the subparsers
__cmds = {
    # "-ll": ("-load-lut", "Load the LUT data from the csv files", load_luts),
    "-cs": (
        "cell-sizing",
        "Compute the transistor sizing",
        gmoverid_cell_sizing_toml_parsing,
    ),
    "-vs": (
        "varactor-sizing",
        "Compute the MOS Capacitor sizing",
        varactor_sizing_toml_parsing,
    ),
    "-ss": (
        "switch-sizing",
        "Compute the MOS Switch sizing",
        switch_sizing_toml_parsing,
    ),
    "-scs": (
        "single-cell-sizing",
        "Compute the transistor sizing",
        gmoverid_cell_sizing_console_parsing,
    ),
    "-svs": (
        "single-varactor-sizing",
        "Compute the MOS Capacitor sizing",
        varactor_sizing_console_parsing,
    ),
    "-sss": (
        "single-switch-sizing",
        "Compute the MOS Switch sizing",
        switch_sizing_console_parsing,
    ),
}

# define the arguments of each subparser
__cmd_args = {
    "-cs": {
        "-s": (
            "--specs-file",
            "The path to the specifications file",
            "FILEPATH",
            str,
            "",
        ),
        "-o": (
            "--output-dir",
            "The path to the output folder",
            "DIRECTORY",
            str,
            "opt",
        ),
    },
    "-vs": {
        "-s": (
            "--specs-file",
            "The path to the specifications file",
            "FILEPATH",
            str,
            "",
        ),
        "-o": (
            "--output-dir",
            "The path to the output folder",
            "DIRECTORY",
            str,
            "opt",
        ),
    },
    "-ss": {
        "-s": (
            "--specs-file",
            "The path to the specifications file",
            "FILEPATH",
            str,
            "",
        ),
        "-o": (
            "--output-dir",
            "The path to the output folder",
            "DIRECTORY",
            str,
            "opt",
        ),
    },
    "-scs": {
        "-t": (
            "--type",
            "The device channel type [nch - nmos, pch - pmos]",
            "<pch or nch>",
            str,
            "",
        ),
        "-vds": (
            "--v-drain-source",
            "The drain to source voltage",
            "VOLTAGE",
            str,
            "opt",
        ),
        "-vsd": (
            "--v-source-drain",
            "The source to drain voltage",
            "VOLTAGE",
            str,
            "opt",
        ),
        "-vsb": (
            "--v-source-bulk",
            "The source to bulk voltage",
            "VOLTAGE",
            str,
            "opt",
        ),
        "-vbs": (
            "--v-bulk-source",
            "The bulk to source voltage",
            "VOLTAGE",
            str,
            "opt",
        ),
        "-l": ("--length", "The length of the transistor's channel", "LENGTH", str, ""),
        "-gi": (
            "--gm-over-id",
            "The device's transconductance efficiency",
            "<gm/id value>",
            str,
            "",
        ),
        "-id": (
            "--drive-current",
            "The driving current of the transistor",
            "<current>",
            str,
            "",
        ),
        "-o": (
            "--output-dir",
            "The path to the output folder",
            "DIRECTORY",
            str,
            "opt",
        ),
    },
    "-svs": {
        "-t": (
            "--type",
            "The device channel type [nch - nmos, pch - pmos]",
            "<pch or nch>",
            str,
            "",
        ),
        "-vgs": (
            "--v-gate-source",
            "The voltage applied to the terminals of the N channel varactor",
            "VOLTAGE",
            str,
            "opt",
        ),
        "-vsg": (
            "--v-source-gate",
            "The voltage applied to the terminals of the P channel varactor",
            "VOLTAGE",
            str,
            "opt",
        ),
        "-l": ("--length", "The length of the transistor's channel", "LENGTH", str, ""),
        "-cvar": (
            "--cap-varactor",
            "The device's total gate to bulk capacitance",
            "<capacitance>",
            str,
            "",
        ),
        "-o": (
            "--output-dir",
            "The path to the output folder",
            "DIRECTORY",
            str,
            "opt",
        ),
    },
    "-sss": {
        "-t": (
            "--type",
            "The device channel type [nch - nmos, pch - pmos]",
            "<pch or nch>",
            str,
            "",
        ),
        "-vgs": (
            "--v-gate-source",
            "The voltage applied to the terminals of the N channel varactor",
            "VOLTAGE",
            str,
            "opt",
        ),
        "-vsg": (
            "--v-source-gate",
            "The voltage applied to the terminals of the P channel varactor",
            "VOLTAGE",
            str,
            "opt",
        ),
        "-rds": (
            "--on-resistance",
            "The device's ON resistance",
            "RESISTANCE",
            str,
            "",
        ),
        "-l": ("--length", "The length of the transistor's channel", "LENGTH", str, ""),
        "-o": (
            "--output-dir",
            "The path to the output folder",
            "DIRECTORY",
            str,
            "opt",
        ),
    },
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


def setupParser(
    cmds: dict,
    args: dict,
    author: str = "",
    email: str = "",
    prog_name: str = "",
    prog_vers: str = "",
    desc: str = "",
    **kwargs,
) -> argparse.ArgumentParser:
    from colorama import init, Fore, Back, Style
    import re

    """_summary_
    Sets up the command line parser.
    Args:
        cmds (dict): dictionary of commands defining the callbacks to each subparser
        args (dict): dictionary of arguments for each command/subparser callback function
        entrymsg (str): entry message for the parser
        progname (str): program name
        progvers (str): program version
        desc (str): program description
    Returns:
        argparse.ArgumentParser: console argument parser object
    """
    if os.environ.get("OS", "") == "Windows_NT":
        init()  # init colorama
    gray, cyan, green, blue = Fore.WHITE, Fore.CYAN, Fore.GREEN, Fore.BLUE

    # setup the messages formatter class for the console
    col_base = gray if "col_base" not in kwargs else kwargs["col_base"]
    col_usage = cyan if "col_usage" not in kwargs else kwargs["col_usage"]
    col_option = cyan if "col_option" not in kwargs else kwargs["col_option"]
    col_caps = green if "col_caps" not in kwargs else kwargs["col_caps"]
    col_prog = green if "col_prog" not in kwargs else kwargs["col_prog"]

    def msg_formatter(msg, color=gray):
        return f"{color}{msg}{Style.RESET_ALL}"

    def entryMsg(prog_name: str = "", author: str = "", email: str = "") -> str:
        from pyfiglet import figlet_format

        """_summary_
        Returns the application entry message as a string.
        Returns:
            str: entry message
        """
        figlet_color = green
        figlet_art = (
            figlet_format(f"{prog_name.upper()}", font="alligator", justify="center")
            if bool(prog_name)
            else ""
        )
        msgs = [
            f"{msg_formatter(figlet_art, color=figlet_color)}",
            "by " + author + " (" + email + ")"
            if (bool(author) and bool(email))
            else "",
        ]
        max_ch = max([len(submsg) for submsg in [msgs[0][-1]] + msgs[1:]]) + 2
        sep_color = green
        sep = "#"
        # sep_msg = msg_formatter(sep * max_ch, color=sep_color)
        # ret = f"{sep_msg}" + "\n"
        ret = ""
        ret += msgs[0]
        for msg in msgs[1:]:
            ret += msg + " " * (max_ch - len(msg)) + "\n"
        # ret += f"{sep_msg}" + "\n"
        return ret

    def make_wide(formatter, w: int = 120, h: int = 36, max_help_position: int = 30):
        import warnings

        """Return a wider HelpFormatter, if possible."""
        try:
            # https://stackoverflow.com/a/5464440
            # beware: "Only the name of this class is considered a public API."
            kwargs = {
                "width": w,
                "max_help_position": h,
                "max_help_position": max_help_position,
            }
            formatter(None, **kwargs)
            return lambda prog: formatter(prog, **kwargs)
        except TypeError:
            warnings.warn("Argparse help formatter failed, falling back.")
            return formatter

    class FormattedConsoleParser(argparse.ArgumentParser):
        def _print_message(self, message, file=None):
            if message:
                if message.startswith("usage"):
                    print(entryMsg(prog_name, author, email))

                    message = f"{msg_formatter(prog_name, color=col_prog)} {prog_vers}\n\n{message}"
                    message = re.sub(
                        r"(-[a-z]+\s*|\[)([A-Z]+)(?=]|,|\s\s|\s\.)",
                        r"\1{}\2{}".format(col_caps, Style.RESET_ALL),
                        message,
                    )
                    message = re.sub(
                        r"((-|--)[a-z]+)",
                        r"{}\1{}".format(col_option, Style.RESET_ALL),
                        message,
                    )

                    usage = msg_formatter("USAGE", color=col_usage)
                    message = message.replace("usage", f"{usage}")

                    flags = msg_formatter("FLAGS", color=col_usage)
                    message = message.replace("options", f"{flags}")

                    progg = msg_formatter(self.prog, color=col_prog)
                    message = message.replace(self.prog, f"{progg}")
                message = f"{msg_formatter(message.strip(), color=col_base)}"
                print(message)

    parser = FormattedConsoleParser(
        prog=prog_name,
        description=desc,
        formatter_class=make_wide(argparse.HelpFormatter, max_help_position=45),
    )
    parser.add_argument(
        "-v",
        "--version",
        action="version",
        version=f"{msg_formatter(prog_name, color=col_prog)} v{msg_formatter(prog_vers, color=col_base)}",
    )
    # mutually exclusive arguments
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--quiet", action="store_true", help="quiet run")
    group.add_argument("--verbose", action="store_true", help="verbose run")
    subparsers = parser.add_subparsers()
    for cmd, (cmd_name, cmd_desc, cmd_callback) in cmds.items():
        subparser = subparsers.add_parser(
            cmd_name,
            help=cmd_desc,
            formatter_class=make_wide(argparse.HelpFormatter, max_help_position=45),
            fromfile_prefix_chars="@",  # to run the script from a text file
        )
        subparser.set_defaults(func=mapSubparserToFun(cmd_callback, subparser))
        optional = subparser._action_groups.pop()
        required = subparser.add_argument_group("required arguments")
        if bool(args.get("all")):
            for arg, (arg_literal, arg_desc, arg_metavar, arg_type, arg_opt,) in args[
                "all"
            ].items():
                if arg_type in [bool, None]:
                    subparser.add_argument(
                        arg,
                        arg_literal,
                        action="store_true",
                        required=False if arg_opt == "opt" else True,
                        help=arg_desc,
                    )
                else:
                    if arg_opt in ["opt", "optional"]:
                        optional.add_argument(
                            arg,
                            arg_literal,
                            nargs=1,
                            type=arg_type,
                            help=arg_desc,
                            metavar=arg_metavar,
                        )
                    else:
                        required.add_argument(
                            arg,
                            arg_literal,
                            nargs=1,
                            type=arg_type,
                            help=arg_desc,
                            required=True,
                            metavar=arg_metavar,
                        )
        for arg, (arg_literal, arg_desc, arg_metavar, arg_type, arg_opt) in args[
            cmd
        ].items():
            if arg_opt in ["opt", "optional"]:
                optional.add_argument(
                    arg,
                    arg_literal,
                    nargs=1,
                    type=arg_type,
                    help=arg_desc,
                    metavar=arg_metavar,
                )
            else:
                required.add_argument(
                    arg,
                    arg_literal,
                    nargs=1,
                    type=arg_type,
                    help=arg_desc,
                    required=True,
                    metavar=arg_metavar,
                )
        subparser._action_groups.append(optional)
    return parser


def cli(argv=None) -> None:
    """_summary_
    Command Line Interface entry point for user interaction.
    Args:
        argv (list, optional): Commands parsed as method input for CLI testing purposes. Defaults to None.
    """
    if argv is None:
        argv = sys.argv[1:]
    parser = setupParser(
        __cmds,
        __cmd_args,
        author=__author__,
        email=__email__,
        prog_vers=__version__,
        prog_name="gost",
        desc=__description__,
    )
    subparsers = [tok for tok in __cmds.keys()] + [tok[0] for tok in __cmds.values()]
    if len(argv) == 0:  # append "help" if no arguments are given
        argv.append("-h")
    elif argv[0] in subparsers:
        if len(argv) == 1:
            argv.append("-h")  # append help when only
            # one positional argument is given
    try:
        args = parser.parse_args(argv)
        try:
            args.func(argv, data_dir=__file_dir__, io_json=__io_json__)
        except Exception as e:
            log.error(traceback.format_exc())
    except argparse.ArgumentError as e:  # catching unknown arguments
        log.warning(e)
    except Exception as e:
        log.error(traceback.format_exc())
    sys.exit(1)  # traceback successful command run
