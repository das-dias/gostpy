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