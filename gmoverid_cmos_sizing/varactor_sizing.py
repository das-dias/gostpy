from loguru import logger as log
from gmoverid_cmos_sizing.utils import *
import json
import pandas as pd
from numpy.linalg import norm
from pandas import DataFrame
import traceback
import warnings
warnings.filterwarnings("ignore")
from modelling_utils import(
    MosCell,
    Devices,
    Scale,
    TomlControlType,
    timer,
    read_specs,
    read_data,
    plot_function,
    plot_hist,
    stof,
)
import argparse

def varactor_sizing_console_parsing(subparser, *args, **kwargs):
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
    device.__parse_data__("l", argv.length[0])
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
    lut_name = "pvaractor.csv" if device.type == "pch" else "nvaractor.csv"
    
    # load lut data
    load_luts(data_path)
    # read lut data from memory
    lut = read_data(os.path.join(luts_path, lut_name))
    # perform sizing
    varactor_sizing(device,lut, output_data_path, verbose=True)

def varactor_sizing_toml_parsing(subparser, *args, **kwargs):
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
    plut_name = "pvaractor.csv" 
    nlut_name = "nvaractor.csv"
    # load lut data
    load_luts(data_path)
    # read lut data from memory
    plut = read_data(os.path.join(luts_path, plut_name))
    nlut = read_data(os.path.join(luts_path, nlut_name))
    varactors_sizing(devices, plut, nlut, output_data_path, verbose=True)
    

def varactors_sizing(devices:Devices, plut:DataFrame, nlut:DataFrame, output_dir:str = "./", verbose:bool = False):
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
    for dev_name, device in devices.varactors.items():
        if device.type == "pch":
            varactor_sizing(device, plut, output_dir, verbose = False)
        else:
            varactor_sizing(device, nlut, output_dir, verbose = False)
    # for each device, compute the sizing
    if verbose:
        print(devices)
    # output the sizing results to a yaml file
    devices.__data_frame__().to_json(os.path.join(output_dir, "varactors.json"))
    devices.__data_frame__().to_json(os.path.join(output_dir, "varactors.csv"))
    devices.__data_frame__().to_markdown(os.path.join(output_dir, "varactors.md"))
    devices.__data_frame__().to_latex(os.path.join(output_dir, "varactors.tex"))

@timer
def varactor_sizing(device:MosCell, lut:DataFrame, output_dir:str = "./", verbose:bool = False):
    """_summary_
    Function to compute the transistor sizing for a given device
    Args:
        device (MosCell): _description_
        lut (DataFrame): _description_
    """
    if verbose:
        log.info(f"Computing {device.name} varactor sizing...")
    # retrieve the device's control parameters
    l = device.l # length
    cvar = device.cvar
    # cvar = cgg + cgs + cgd
    vgs = np.abs(device.vgs)
    # compute the closest transistor parameters of the lut in relation to the control parameters
    def weighted_norm(row, pt1, cols=[], weights=[], p=1) -> float:
        pt2 = [row[col] for col in cols]
        if len(pt2) != len(pt1):
            raise ValueError("The two points must have the same dimension")
        ws = np.array(weights) if len(weights) == len(pt1) else np.ones(len(pt1))
        vec = np.multiply(np.array(pt2)-np.array(pt1), ws)
        return norm(vec, p)
    new_lut = lut.copy()
    new_lut["cvar"] = new_lut["cgg"]+new_lut["cgs"]+new_lut["cgd"]
    columns = ["l", "cvar", "vgs"] if device.type == "nch" else ["l", "cvar", "vsg"]
    control= {k:v for k,v in zip(columns, [l, cvar, vgs])}
    norm_weights = [1/new_lut[col].max() for col in control.keys()]
    # compute the closest vsd and vsb values to the parsed values
    # and limit the look up table to those values
    control_dists = new_lut.apply(weighted_norm, axis=1, args=( list(control.values()), ), cols=list(control.keys()), weights=norm_weights )
    control_row = new_lut[ new_lut.apply(weighted_norm, axis=1, args=( list(control.values()), ), cols=list(control.keys()), weights=norm_weights ) == np.min(control_dists) ].copy()
    old_width = control_row["w"].values[0]
    # for all the entries corresponding to the control vds and vsb given,
    # compute the new table entries
    
    # create cvar column
    query = f"{columns[0]}=={control_row[columns[0]].values[0]} & {columns[2]}=={control_row[columns[2]].values[0]}"
    # changed: added channel length - l - as a query control variable!
    new_lut = new_lut[new_lut.eval(query)].copy()
    
    new_lut["w"] = old_width*(cvar/control_row['cvar'].values[0])
    new_lut["gds"] = new_lut["gds"]*(new_lut["w"]/old_width)
    new_lut["rds"] = 1/new_lut["gds"]
    #new_lut["self_gain"] = [gm/gds for gm, gds in zip(new_lut["gm"], new_lut["gds"])]
    new_lut["cgs"] = new_lut["cgs"]*(new_lut["w"]/old_width)
    new_lut["cgd"] = new_lut["cgd"]*(new_lut["w"]/old_width)
    new_lut["csb"] = new_lut["csb"]*(new_lut["w"]/old_width)
    new_lut["cdb"] = new_lut["cdb"]*(new_lut["w"]/old_width)
    new_lut["cgg"] = new_lut["cgg"]*(new_lut["w"]/old_width)
    new_lut["cvar"] = new_lut["cgg"] + new_lut["cgs"] + new_lut["cgd"]
    #new_lut["ft"] = [compute_ft(gm, cgs, cgd, csb, cdb) for gm, cgs, cgd, csb, cdb in zip(new_lut["gm"], new_lut["cgs"], new_lut["cgd"], new_lut["csb"], new_lut["cdb"])]
    # ft, gm/gds, gm/id and vearly all width independant parameters
    """
    # print the graphs of the new transistor parameters for the fixed vds and vsb
    cap_cols = ["cdb", "csb", "cgd", "cgs", "cgg"]
    cap_scale = {k:Scale.FEMTO.value[1] for k in cap_cols}
    ycap = [np.array(list(new_lut[col]/scaling_factor)) for col,scaling_factor in cap_scale.items()]
    yy = [ycap] + [np.array(list(new_lut[col]/scaling_factor)) for col,scaling_factor in {"rds": 1 }.items()]
    pcap_labels = ["Drain-Bulk Parasitic Capacitance [fF]", "Source-Bulk Parasitic Capacitance [fF]", "Gate-Drain Parasitic Capacitance [fF]", "Gate-Source Parasitic Capacitance [fF]", "Total Gate Capacitance [fF]"]
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
        log.info("Varactor sizing completed.")
        print(f"Varactor : {device.name}")
        print(output_row.transpose())
    return device, output_row