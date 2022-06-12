from re import I
from loguru import logger as log
from gover.utils import *
import json
import pandas as pd
from pandas import DataFrame
import traceback
import warnings
from numpy.linalg import norm
warnings.filterwarnings("ignore")
from modelling_utils import(
    MosCell,
    Devices,
    timer,
    read_specs,
    read_data,
)
import argparse

def switch_sizing_console_parsing(subparser, *args, **kwargs):
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
    if not(bool(argv.v_source_gate) or bool(argv.v_gate_source) ):
        raise ValueError("At least two of the following DOF -vgs or -vsg are required")
    
    if bool(argv.v_source_gate) and bool(argv.v_gate_source):
        raise ValueError("-vsg and -vgs are mutually exclusive")
    
    # extract device parameters
    device = MosCell()
    device.__parse_data__("type", argv.type[0])
    device.__parse_data__("rds", argv.on_resistance[0])
    device.__parse_data__("l", "30 n") # parse minimum length
    if device.type == "nch":
        device.__parse_data__("vgs", argv.v_gate_source[0])
    else:
        device.__parse_data__("vsg", argv.v_source_gate[0])
    # extract necessary data
    io = {}
    with open(io_json, "r") as f:
        io = json.load(f)
    luts_path = io.get("__luts_path__")
    output_data_path = io.get("__output_data_path__")
    lut_name = "pswitch.csv" if device.type == "pch" else "nswitch.csv"
    
    # load lut data
    load_luts(data_path)
    # read lut data from memory
    lut = read_data(os.path.join(luts_path, lut_name))
    # perform sizing
    switch_sizing(device,lut, output_data_path, verbose=True)

def switch_sizing_toml_parsing(subparser, *args, **kwargs):
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
    data_path=kwargs.get("data_dir")
    io_json=kwargs.get("io_json")
    try:
        argv = subparser.parse_args(sysargs[1:])
    except Exception as e:
        log.error(traceback.format_exc())
    # proceed with the extraction of arguments
    # handle mutually exclusive arguments
    specs_file=argv.specs_file[0] if bool(argv.specs_file) else ""
    devices = None
    try:
        devices = read_specs(specs_file)
    except Exception as e:
        log.error(traceback.format_exc())

    io = {}
    with open(io_json, "r") as f:
        io = json.load(f)
    luts_path = io.get("__luts_path__")
    output_data_path = io.get("__output_data_path__")
    # from the arguments, extract the necessary info to proceed with the computation
    plut_name = "pswitch.csv" 
    nlut_name = "nswitch.csv"
    # load lut data
    load_luts(data_path)
    # read lut data from memory
    plut = read_data(os.path.join(luts_path, plut_name))
    nlut = read_data(os.path.join(luts_path, nlut_name))
    switches_sizing(devices, plut, nlut, output_data_path, verbose=True)
    

def switches_sizing(devices:Devices, plut:DataFrame, nlut:DataFrame, output_dir:str = "./", verbose:bool = False):
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
    for dev_name, device in devices.switches.items():
        if device.type == "pch":
            switch_sizing(device, plut, output_dir, verbose = False)
        else:
            switch_sizing(device, nlut, output_dir, verbose = False)
    # for each device, compute the sizing
    if verbose:
        print(devices)
    # output the sizing results to a yaml file
    devices.__data_frame__(dev_type = "switch").to_json(os.path.join(output_dir, "switches.json"))
    devices.__data_frame__(dev_type = "switch").to_json(os.path.join(output_dir, "switches.csv"))
    devices.__data_frame__(dev_type = "switch").to_markdown(os.path.join(output_dir, "switches.md"))
    devices.__data_frame__(dev_type = "switch").to_latex(os.path.join(output_dir, "switches.tex"))

@timer
def switch_sizing(device:MosCell, lut:DataFrame, output_dir:str = "./", verbose:bool = False):
    """_summary_
    Function to compute the transistor sizing for a given device
    Args:
        device (MosCell): _description_
        lut (DataFrame): _description_
    """
    if verbose:
        log.info(f"Computing {device.name} switch sizing...")
    # retrieve the device's control parameters
    # NOTE: when designing switches, the channel length is assumed to always be equal to the 
    # minimum channel length
    device.l = np.min(lut["l"])
    l = device.l
    gds = device.gds
    rds = 1/gds
    vgs = np.abs(device.vgs)
    # compute the closest transistor parameters of the lut in relation to the control parameters
    def weighted_norm(row, pt1, cols=[], weights=[], p=1) -> float:
        pt2 = [row[col] for col in cols]
        if len(pt2) != len(pt1):
            raise ValueError("The two points must have the same dimension")
        ws = np.array(weights) if len(weights) == len(pt1) else np.ones(len(pt1))
        vec = np.multiply(np.array(pt2)-np.array(pt1), ws)
        return norm(vec, p)
    
    columns = ["l", "vgs"] if device.type == "nch" else ["l", "vsg"]
    control= {k:v for k,v in zip(columns, [l, vgs])}
    norm_weights = [1/lut[col].max() for col in control.keys()]
    # compute the closest vsd and vsb values to the parsed values
    # and limit the look up table to those values
    control_dists = lut.apply(weighted_norm, axis=1, args=( list(control.values()), ), cols=list(control.keys()), weights=norm_weights )
    control_row = lut[ lut.apply(weighted_norm, axis=1, args=( list(control.values()), ), cols=list(control.keys()), weights=norm_weights ) == np.min(control_dists) ].copy()
    old_width = control_row["w"].values[0]
    control_row["rds"] = 1/control_row["gds"]
    # for all the entries corresponding to the control vds and vsb given,
    # compute the new table entries
    
    #query = f"{columns[0]}=={control_row[columns[0]].values[0]} & {columns[1]}=={control_row[columns[1]].values[0]}"
    new_lut = lut.copy()
    new_lut["w"] = old_width*(control_row['rds'].values[0]/rds)
    new_lut["gds"] = new_lut["gds"]*(new_lut["w"]/old_width)
    new_lut["rds"] = 1/new_lut["gds"]
    #new_lut["self_gain"] = [gm/gds for gm, gds in zip(new_lut["gm"], new_lut["gds"])]
    new_lut["cgs"] = new_lut["cgs"]*(new_lut["w"]/old_width)
    new_lut["cgd"] = new_lut["cgd"]*(new_lut["w"]/old_width)
    new_lut["csb"] = new_lut["csb"]*(new_lut["w"]/old_width)
    new_lut["cdb"] = new_lut["cdb"]*(new_lut["w"]/old_width)
    # print the graphs of the new transistor parameters for the fixed vds and vsb
    vgs_col = columns[-1]
    """
    cap_cols = ["cdb", "csb", "cgd", "cgs"]
    cap_scale = {k:Scale.FEMTO.value[1] for k in cap_cols}
    ycap = [np.array(list(new_lut[col]/scaling_factor)) for col,scaling_factor in cap_scale.items()]
    yy = [ycap] + [np.array(list(new_lut[col]/scaling_factor)) for col,scaling_factor in {"rds": 1 }.items()]
    pcap_labels = ["Drain-Bulk Parasitic Capacitance [fF]", "Source-Bulk Parasitic Capacitance [fF]", "Gate-Drain Parasitic Capacitance [fF]", "Gate-Source Parasitic Capacitance [fF]"]
    labels = [ pcap_labels, r"$R_{DS}$ [$\Omega$]", r"$g_{DS}$ [mS]"]
    file_names = ["caps", "rds"]
    vgs_col = columns[-1]
    x = list(new_lut[vgs_col])
    xlabel = "Vgs [V]" if device.type == "nch" else "Vsg [V]"
    for y, label, fname in zip(yy, labels, file_names):
        if type(label) != list:
            plot_function(x=x, y=y, labels=[label], xlabel=xlabel, ylabel=label, title=f"{label} vs. {xlabel}", show=False, filename=f"{device.name}-{fname}.png")
        else:
            plot_function(x=new_lut[vgs_col].values, y=y, labels=label, xlabel=xlabel, ylabel="Capacitance [fF]", title=f"Parasitic Capacitance vs. {xlabel}", show=False, filename=f"{device.name}-{fname}.png")
    """
    output_vgs = control_row[vgs_col].values[0]
    query = f"{vgs_col}=={output_vgs}"
    output_row = new_lut[new_lut.eval(query)]
    
    # build device data
    for col in output_row.columns:
        if col in [var for var in dir(device) if not var.startswith("__")]:
            setattr(device, col, output_row[col].values[0])
    output_row = output_row[[col for col in [var for var in dir(device) if not var.startswith("__")] if col in output_row.columns]].set_index(vgs_col)
    if verbose:
        log.info("Switch sizing completed.")
        print(f"Switch : {device.name}")
        print(output_row.transpose())
    return device, output_row