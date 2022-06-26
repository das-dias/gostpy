from loguru import logger as log
from gost.utils import *
import json
import pandas as pd
from pandas import DataFrame
import traceback
import warnings
from numpy.linalg import norm

warnings.filterwarnings("ignore")
from modelling_utils import (
    MosCell,
    Devices,
    Scale,
    timer,
    read_specs,
    read_data,
    plot_function,
    plot_hist,
    stof,
)
import argparse


def gmoverid_cell_sizing_console_parsing(subparser, *args, **kwargs):
    """
    Function to call the script that will computes
    transistor sizing from the parsed specification data.
    Args:
        specifications_file_path (str): The path to the .toml 
            file containing the specifications for each device
    Returns:
        None: all the output of the script will be 
            written to console, output files and image files
    """
    argv = None
    # read data
    sysargs = args[0]
    data_path = kwargs.get("data_dir")
    io_json = kwargs.get("io_json")
    try:
        argv = subparser.parse_args(sysargs[1:])
    except Exception as e:
        log.error(traceback.format_exc())
    # handle optional mutually exclusive arguments
    if not (
        bool(argv.v_source_drain)
        or bool(argv.v_source_bulk)
        or bool(argv.v_drain_source)
        or bool(argv.v_bulk_source)
    ):
        raise ValueError(
            "At least two of the following DOF -vsd, -vsb, -vds, -vbs are required"
        )

    if bool(argv.v_source_drain) and bool(argv.v_drain_source):
        raise ValueError("-vsd and -vds are mutually exclusive")
    if bool(argv.v_bulk_source) and bool(argv.v_source_bulk):
        raise ValueError("-vbs and -vsb are mutually exclusive")

    if (bool(argv.v_source_bulk) and not (bool(argv.v_drain_source))) or (
        bool(argv.v_drain_source) and not (bool(argv.v_source_bulk))
    ):
        raise ValueError("-vds and -vsb are required at the same time")

    if (bool(argv.v_bulk_source) and not (bool(argv.v_source_drain))) or (
        bool(argv.v_source_drain) and not (bool(argv.v_bulk_source))
    ):
        raise ValueError("-vsd and -vbs are required at the same time")

    # extract device parameters
    device = MosCell()
    device.__parse_data__("type", argv.type[0])
    device.__parse_data__("l", argv.length[0])
    device.__parse_data__("gmoverid", argv.gm_over_id[0])
    if device.type == "nch":
        device.__parse_data__("vds", argv.v_drain_source[0])
        device.__parse_data__("vsb", argv.v_source_bulk[0])
    else:
        device.__parse_data__("vsd", argv.v_source_drain[0])
        device.__parse_data__("vbs", argv.v_bulk_source[0])
    device.__parse_data__("id", argv.drive_current[0])
    # extract necessary data
    io = {}
    with open(io_json, "r") as f:
        io = json.load(f)
    luts_path = io.get("__luts_path__")
    output_data_path = (
        argv.output_dir[0] if bool(argv.output_dir) else io.get("__output_data_path__")
    )
    lut_name = "pcell.csv" if device.type == "pch" else "ncell.csv"

    # load lut data
    load_luts(data_path)
    # read lut data from memory
    lut = read_data(os.path.join(luts_path, lut_name))
    # perform sizing
    cell_sizing(device, lut, output_data_path, verbose=True)


def gmoverid_cell_sizing_toml_parsing(subparser, *args, **kwargs):
    """
    Function to call the script that will computes
    transistor sizing from the parsed specification data.
    Args:
        specifications_file_path (str): The path to the .toml 
            file containing the specifications for each device
    Returns:
        None: all the output of the script will be 
            written to console, output files and image files
    """
    argv = None
    sysargs = args[0]
    data_path = kwargs.get("data_dir")
    io_json = kwargs.get("io_json")
    try:
        argv = subparser.parse_args(sysargs[1:])
    except Exception as e:
        log.error(traceback.format_exc())
    # proceed with the extraction of arguments
    # handle mutually exclusive arguments
    specs_file = argv.specs_file[0] if bool(argv.specs_file) else ""
    devices = None
    try:
        devices = read_specs(specs_file)
    except Exception as e:
        log.error(traceback.format_exc())

    io = {}
    with open(io_json, "r") as f:
        io = json.load(f)
    luts_path = io.get("__luts_path__")
    output_data_path = (
        argv.output_dir[0] if bool(argv.output_dir) else io.get("__output_data_path__")
    )
    # from the arguments, extract the necessary info to proceed with the computation
    plut_name = "pcell.csv"
    nlut_name = "ncell.csv"
    # load lut data
    load_luts(data_path)
    # read lut data from memory
    plut = read_data(os.path.join(luts_path, plut_name))
    nlut = read_data(os.path.join(luts_path, nlut_name))
    devices_sizing(devices, plut, nlut, output_data_path, verbose=True)


def devices_sizing(
    devices: Devices,
    plut: DataFrame,
    nlut: DataFrame,
    output_dir: str = "./",
    verbose: bool = False,
):
    """_summary_
    Function to compute the transistor sizing for all
    extracted devices
    Args:
        devices (Devices): The Devices object containing
        plut (DataFrame): The dataframe containing the
        nlut (DataFrame): The dataframe containing the
        output_dir (str): The directory where the output
        verbose (bool): Verbose or not the output
    """
    # load devices from specification file
    out_row = None
    for dev_name, device in devices.devices.items():
        if device.type == "pch":
            cell_sizing(device, plut, output_dir, verbose=False)
        else:
            cell_sizing(device, nlut, output_dir, verbose=False)
    # for each device, compute the sizing
    if verbose:
        print(devices)
    # output the sizing results to a yaml file
    devices.__data_frame__().to_json(os.path.join(output_dir, "devices.json"))
    devices.__data_frame__().to_csv(os.path.join(output_dir, "devices.csv"))
    devices.__data_frame__().to_markdown(os.path.join(output_dir, "devices.md"))
    devices.__data_frame__().to_latex(os.path.join(output_dir, "devices.tex"))


@timer
def cell_sizing(
    device: MosCell, lut: DataFrame, output_dir: str = "./", verbose: bool = False
):
    """_summary_
    Function to compute the transistor sizing for a given device
    Args:
        device (MosCell): _description_
        lut (DataFrame): _description_
    """
    if verbose:
        log.info(f"Computing {device.name} transistor sizing...")
    # retrieve the device's control parameters
    l = device.l  # length
    gm_id = device.gmoverid  # gm over id
    vds = np.abs(device.vds)  # drain to source voltage in absolute value
    vsb = np.abs(device.vsb)  # source to bulk voltage in absolute value
    id = device.id  # drain current
    # compute the closest transistor parameters of the lut in relation to the control parameters
    def weighted_norm(row, pt1, cols=[], weights=[], p=1) -> float:
        pt2 = [row[col] for col in cols]
        if len(pt2) != len(pt1):
            raise ValueError("The two points must have the same dimension")
        ws = np.array(weights) if len(weights) == len(pt1) else np.ones(len(pt1))
        vec = np.multiply(np.array(pt2) - np.array(pt1), ws)
        return norm(vec, p)

    columns = (
        ["l", "gmoverid", "vds", "vsb"]
        if device.type == "nch"
        else ["l", "gmoverid", "vsd", "vbs"]
    )
    control = {k: v for k, v in zip(columns, [l, gm_id, vds, vsb])}
    norm_weights = [1 / lut[col].max() for col in control.keys()]
    # compute the closest vsd and vsb values to the parsed values
    # and limit the look up table to those values
    control_dists = lut.apply(
        weighted_norm,
        axis=1,
        args=(list(control.values()),),
        cols=list(control.keys()),
        weights=norm_weights,
    )
    control_row = lut[
        lut.apply(
            weighted_norm,
            axis=1,
            args=(list(control.values()),),
            cols=list(control.keys()),
            weights=norm_weights,
        )
        == np.min(control_dists)
    ].copy()
    old_width = control_row["w"].values[0]
    # for all the entries corresponding to the control vds and vsb given,
    # compute the new table entries
    query = f"{columns[-2]}=={control_row[columns[-2]].values[0]} & {columns[-1]}=={control_row[columns[-1]].values[0]} & {columns[0]}=={control_row[columns[0]].values[0]}"
    # changed: added channel length - l - as a query control variable!
    new_lut = lut[lut.eval(query)].copy()
    new_lut["w"] = old_width * (id / control_row["id"].values[0])
    new_lut["gm"] = new_lut["gm"] * (new_lut["w"] / old_width)
    new_lut["id"] = new_lut["gm"] / new_lut["gmoverid"]
    new_lut["gds"] = new_lut["gds"] * (new_lut["w"] / old_width)
    new_lut["cgs"] = new_lut["cgs"] * (new_lut["w"] / old_width)
    new_lut["cgd"] = new_lut["cgd"] * (new_lut["w"] / old_width)
    new_lut["csb"] = new_lut["csb"] * (new_lut["w"] / old_width)
    new_lut["cdb"] = new_lut["cdb"] * (new_lut["w"] / old_width)
    new_lut["self_gain"] = new_lut["gm"] / new_lut["gds"]
    new_lut["ft"] = (
        (1 / (2 * np.pi)) * new_lut["gm"] / (new_lut["cgs"] + new_lut["cgd"])
    )
    # print the graphs of the new transistor parameters for the fixed vds and vsb
    yy = [
        np.array(list(new_lut[col] / scaling_factor))
        for col, scaling_factor in {
            "id": Scale.MILI.value[1],
            "gmoverid": 1,
            "self_gain": 1,
            "ft": Scale.GIGA.value[1],
        }.items()
    ]
    labels = [
        "Drive Current [mA]",
        r"Gm/Id [$V^{-1}$]",
        r"Self-Gain [$VV^{-1}$]",
        "Ft [GHz]",
    ]
    file_names = ["drive_current", "gm_over_id", "self_gain", "ft"]
    vgs_col = "vgs" if device.type == "nch" else "vsg"
    x = list(new_lut[vgs_col])
    xlabel = "Vgs [V]" if device.type == "nch" else "Vsg [V]"
    for y, label, fname in zip(yy, labels, file_names):
        plot_function(
            x=x,
            y=y,
            labels=[label],
            xlabel=xlabel,
            ylabel=label,
            title=f"{label} vs. {xlabel}",
            show=False,
            filename=f"{device.name}-{fname}.png",
        )

    output_vgs = control_row[vgs_col].values[0]
    query = f"{vgs_col}=={output_vgs}"
    output_row = new_lut[new_lut.eval(query)]

    # build device data
    for col in output_row.columns:
        if col in [var for var in dir(device) if not var.startswith("__")]:
            setattr(device, col, output_row[col].values[0])
    output_row = output_row[
        [
            col
            for col in [var for var in dir(device) if not var.startswith("__")]
            if col in output_row.columns
        ]
    ].set_index(vgs_col)
    if verbose:
        log.info("Transistor sizing completed.")
        print(f"Device : {device.name}")
        print(output_row.transpose())
    return device, output_row
