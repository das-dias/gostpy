import subprocess
import os
import numpy as np
from loguru import logger as log
import sys

def getParent(path, levels = 0):
    """_summary_
    Get the parent directory of a path
    according to the specified level of
    depth in the tree
    Args:
        path    (str)   : child path of the parent directory
        levels  (int)   : number of levels to go up in the tree
    """
    common = path
    for _ in range(levels+1):
        common = os.path.dirname(os.path.abspath(common))
    return common

def load_luts(directory_path):
    """
    Load the LUT data from the csv files by using 
    the subprocess module to call the python script
    to load the look up tables into known memory.
    Args:
        None
    Returns:
        None
    """
    path = os.path.join(directory_path, "load_data.py")
    subprocess.call(f"python {path}", shell=True)
    
def compute_width(old_width:float, old_id:float, id:float)->float:
    """_summary_
    Computes the new width of the transistor from
    the old W/Id ratio
    Args:
        old_width (float): the old width of the transistor
        old_id (float): the old id of the transistor
        id (float): the new id of the transistor
    Returns:
        float: the new width of the transistor
    """
    return old_width*(id/old_id)

def compute_cgs(old_cgs:float, old_width:float, width:float)->float:
    """_summary_
    Computes the new cgs of the transistor from
    the old W/Id ratio
    Args:
        old_cgs (float): the old cgs of the transistor
        width (float): the new width of the transistor
        id (float): the new id of the transistor
    Returns:
        float: the new cgs of the transistor
    """
    return old_cgs*(width/old_width)

def compute_cgd(old_cgd:float, old_width:float, width:float)->float:
    """_summary_
    Computes the new cgd of the transistor from
    the old W/Id ratio
    Args:
        old_cgd (float): the old cgd of the transistor
        width (float): the new width of the transistor
        id (float): the new id of the transistor
    Returns:
        float: the new cgd of the transistor
    """
    return old_cgd*(width/old_width)

def compute_csb(old_csb:float, old_width:float, width:float)->float:
    """_summary_
    Computes the new csb of the transistor from
    the old W/Id ratio
    Args:
        old_csb (float): the old csb of the transistor
        width (float): the new width of the transistor
        id (float): the new id of the transistor
    Returns:
        float: the new csb of the transistor
    """
    return old_csb*(width/old_width)

def compute_cdb(old_cdb:float, old_width:float, width:float)->float:
    """_summary_
    Compute the new cdb of the transistor from
    the old W/Id ratio and the vgs and vsb of the device
    Args:
        old_cdb (float): the old cdb of the transistor
        old_width (float): the old width of the transistor
        width (float): the new width of the transistor
        vsb (float): the vsb of the transistor
        vgs (float): the vgs of the transistor
    Returns:
        float: _description_
    """
    return old_cdb*(width/old_width)

def compute_cgb(old_cgb:float, old_width:float, width:float)->float:
    """_summary_

    Args:
        old_cgb (float): _description_
        old_width (float): _description_
        width (float): _description_
    Returns:
        float: _description_
    """
    return old_cgb*(width/old_width)

def compute_gm(old_gm:float, old_width:float, width:float)->float:
    """_summary_
    Computes the new gm of the transistor from
    the old W/Id ratio
    Args:
        old_gm (float): the old gm of the transistor
        old_width (float): the new width of the transistor
        width (float): the new width of the transistor
    Returns:
        float: the new gm of the transistor
    """
    return old_gm*(width/old_width)

def compute_gds(old_gds:float, old_width:float, width:float)->float:
    """_summary_
    Computes the new gds of the transistor from
    the old W/Id ratio
    Args:
        old_gds (float): the old gds of the transistor
        old_width (float): the new width of the transistor
        width (float): the new width of the transistor
    Returns:
        float: the new gds of the transistor
    """
    return old_gds*(width/old_width)

def compute_self_gain(gm:float, gds:float)->float:
    """_summary_
    Computes the self-gain of the transistor
    Args:
        gm (float): device transconductance
        gds (float): device drain transconductance
    Returns:
        float: _description_
    """
    return gm/gds

def compute_ft_angular(gm:float, cgs:float, cgd:float, csb:float, cdb:float)->float:
    """_summary_
    Computes the ft/(2*pi) of the transistor 
    Args:
        gm (float): device transconductance
        cgs (float): device gate source capacitance
        cgd (float): device gate drain capacitance
        csb (float): device source drain capacitance
        cdb (float): device drain source capacitance
    Returns:
        float: _description_
    """
    return gm/(2*np.pi*(cgs+cgd+csb+cdb))


def compute_ft(gm:float, cgs:float, cgd:float, csb:float, cdb:float)->float:
    """_summary_
    Computes the ft/(2*pi) of the transistor 
    Args:
        gm (float): device transconductance
        cgs (float): device gate source capacitance
        cgd (float): device gate drain capacitance
        csb (float): device source drain capacitance
        cdb (float): device drain source capacitance
    Returns:
        float: _description_
    """
    return gm/(cgs+cgd+csb+cdb)

def compute_ron(gm:float, gds:float)->float:
    """_summary_
    Computes the On resistance of the transistor as a switch
    Args:
        gm (float): device transconductance
        gds (float): device drain transconductance
    Returns:
        float: _description_
    """
    return 1/(gm+gds)

def compute_fosc(old_fosc:float, old_width:float, width:float)->float:
    """_summary_
    Computes the new fosc / fmax of the transistor from
    the old W/Id ratio
    Args:
        old_fosc (float): the old fosc of the transistor
        old_width (float): the old width of the transistor
        width (float): the new width of the transistor
    Returns:
        float: the new fosc of the transistor
    """
    return old_fosc/np.sqrt(width/old_width)
