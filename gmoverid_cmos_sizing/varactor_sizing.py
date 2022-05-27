from loguru import logger as log
from utils import *
import json
import pandas as pd
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
        log.info(f"Computing {device.name} transistor sizing...")
    # retrieve the device's control parameters
    l = device.l # length
    cvar = device.cvar
    vgs = np.abs(device.vgs)
    # compute the closest transistor parameters of the lut in relation to the control parameters
    def eucl_dist(pt2:list=[], pt1:list=[], weights = []) -> float:
        if len(pt2) != len(pt1):
            raise ValueError("The two points must have the same dimension")
        ws = np.array(weights) if len(weights) == len(pt1) else np.ones(len(pt1))
        # using mahanolis distance computation for unitary correlation between the two variables pt1 and pt2
        dif = np.multiply(np.array(pt2)-np.array(pt1), ws)
        return np.dot(dif.T, dif)
    
    columns = ["l", "cvar", "vgs"] if device.type == "nch" else ["l", "cvar", "vsg"]
    control= {k:v for k,v in zip(columns, [l, cvar, vgs])}
    
    # compute the closest vsd and vsb values to the parsed values
    # and limit the look up table to those values
    vpoint = [vgs]
    vcols = [columns[-1]]
    indexes = [ k for k, row in lut[vcols].iterrows() if eucl_dist(vpoint, list(row)) == np.min([eucl_dist(vpoint, list(row2)) for _, row2 in lut[vcols].iterrows()])]
    rows = [lut.iloc[i] for i in indexes]
    filtered_lut = DataFrame(rows)
    
    control_point = list(control.values())
    row_index = [ k for k, row in filtered_lut[columns].iterrows() if eucl_dist(control_point, list(row)) == np.min([eucl_dist(control_point, list(row2)) for _, row2 in filtered_lut[columns].iterrows()])][0]
    control_row = filtered_lut.loc[row_index]
    old_width = control_row.get("w")
    # for all the entries corresponding to the control vds and vsb given,
    # compute the new table entries
    
    query = f"{columns[0]}=={control_row[columns[0]]} & {columns[1]}=={control_row[columns[1]]}"
    new_lut = lut[lut.eval(query)]
    new_lut["w"] = old_width*(cvar/control_row['cvar'])
    new_lut["id"] = [id*(w/old_width) for id,w  in zip(new_lut["id"], new_lut["w"])]
    new_lut["gds"] = [ogds*(w/old_width) for ogds, w in zip(new_lut["gds"], new_lut["w"])]
    new_lut["ron"] = [ron*(old_width/w) for ron,w  in zip(new_lut["ron"], new_lut["w"])]
    #new_lut["self_gain"] = [gm/gds for gm, gds in zip(new_lut["gm"], new_lut["gds"])]
    new_lut["cgs"] = [ocgs*(w/old_width) for ocgs, w in zip(new_lut["cgs"], new_lut["w"])]
    new_lut["cgd"] = [ocgd*(w/old_width) for ocgd, w in zip(new_lut["cgd"], new_lut["w"])]
    new_lut["csb"] = [ocsb*(w/old_width) for ocsb, w in zip(new_lut["csb"], new_lut["w"])]
    new_lut["cdb"] = [ocdb*(w/old_width) for ocdb, w in zip(new_lut["cdb"], new_lut["w"])]
    new_lut["cgg"] = [ocgg*(w/old_width) for ocgg, w in zip(new_lut["cgg"], new_lut["w"])]
    new_lut["cdep"] = [ocdep*(w/old_width) for ocdep, w in zip(new_lut["cdep"], new_lut["w"])]
    new_lut["cvar"] = [cv*(w/old_width) for cv,w in zip(new_lut["cvar", new_lut["w"]])]
    
    #new_lut["ft"] = [compute_ft(gm, cgs, cgd, csb, cdb) for gm, cgs, cgd, csb, cdb in zip(new_lut["gm"], new_lut["cgs"], new_lut["cgd"], new_lut["csb"], new_lut["cdb"])]
    # ft, gm/gds, gm/id and vearly all width independant parameters
    
    # print the graphs of the new transistor parameters for the fixed vds and vsb
    cap_cols = ["cvar", "cdep", "cgg", "cdb", "csb", "cgd", "cgs"]
    cap_scale = {k:Scale.FEMTO.value[1] for k in cap_cols}
    ycap = [np.array(list(new_lut[col]/scaling_factor)) for col,scaling_factor in cap_scale]
    yy = [ycap] + [np.array(list(new_lut[col]/scaling_factor)) for col,scaling_factor in {"id": Scale.MICRO.value[1], "ron": 1, "gds" :Scale.MILI.values[1] }.items()]
    labels = ["Parasitic Capacitances [fF]", "Id [uA]", "Ron [\u03A9]", "gds [mS]"]
    file_names = ["caps", "id", "ron", "gds"]
    vgs_col = columns[-1]
    x = list(new_lut[vgs_col])
    xlabel = "Vgs [V]" if device.type == "nch" else "Vsg [V]"
    for y, label, fname in zip(yy, labels, file_names):
        plot_function(x=x, y=y, labels=[label], xlabel=xlabel, ylabel=label, title=f"{label} vs. {xlabel}", show=False, filename=f"{device.name}-{fname}.png")
    
    output_vgs = control_row[vgs_col]
    query = f"{vgs_col}=={output_vgs}"
    output_row = new_lut[new_lut.eval(query)]
    
    # build device data
    for col in output_row.columns:
        if col in [var for var in dir(device) if not var.startswith("__")]:
            setattr(device, col, output_row[col].values[0])
    output_row = output_row[[col for col in [var for var in dir(device) if not var.startswith("__")] if col in output_row.columns]].set_index(vgs_col)
    if verbose:
        log.info("Transistor sizing completed.")
        print(f"Varactor : {device.name}")
        print(output_row)
    return device, output_row