from modelling_utils import(
    read_lut,
)
import os
import pandas as pd
from utils import getParent
import json
from loguru import logger
import traceback

__type__ = "script"
__author__ = "Diogo André"
__description__ = "Loads the data from the csv files and saves it in the lut files"
__parent_dir = os.path.realpath(getParent(__file__))
__io = os.path.join(__parent_dir,"io.json")

__pcell_lut = pd.DataFrame() # p channel mos transistor lookup table
__ncell_lut = pd.DataFrame() # n channel mos transistor lookup table
__nvaractor_lut = pd.DataFrame() # n channel varactor lookup table
__pvaractor_lut = pd.DataFrame() # p channel varactor lookup table
__nswitch_lut = pd.DataFrame() # n channel switch cmos
__pswitch_lut = pd.DataFrame() # p channel switch cmos
__pcell_rf_lut = pd.DataFrame() # p channel mos transistor rf lookup table
__ncell_rf_lut = pd.DataFrame() # n channel mos transistor rf lookup tables

__output_formats = ["csv"]

__folders = {
    "ncell": __ncell_lut,
    "pcell": __pcell_lut,
    "nvaractor": __nvaractor_lut,
    "pvaractor": __pvaractor_lut,
    "nswitch": __nswitch_lut,
    "pswitch": __pswitch_lut,
    "rf_ncell": __ncell_rf_lut,
    "rf_pcell": __pcell_rf_lut,
}

def main():
    # load input output file paths
    with open(__io, "r") as f:
        io = json.load(f)
    __input_data_path = io["__input_data_path__"]
    __luts_path = io["__luts_path__"]
    __output_data_path = io["__output_data_path__"]
    
    logger.info("Loading Look Up Tables data...")
    # read in the look up tables for the different types of devices
    if not os.path.exists(__input_data_path):
        logger.error(f"{__input_data_path} does not exist")
        raise FileNotFoundError(f"The input data path does not exist: {__input_data_path}")
    if not os.path.exists(__output_data_path):
        try:
            os.mkdir(__output_data_path)
        except Exception as ex:
            logger.error(traceback.format_exc())

    for folder in __folders.keys():
        path = os.path.join(__input_data_path, folder)
        if os.path.exists(path):
            logger.info(f"Loading {folder} data...")
            for file in os.listdir(path):
                if file.endswith(".csv"):
                    try:
                        # read in the data
                        lut = read_lut(os.path.join(path, file))
                        # adjoint the data to the existing data
                        __folders[folder] = pd.concat( [__folders[folder], lut], ignore_index=True)
                        logger.info(f"Loaded {file}")
                    except Exception as ex:
                        logger.warning(traceback.format_exc())
            print()
        else:
            logger.warning(f"{path} does not exist")
    # after importing the data, write it to the output path
    if not os.path.exists(__luts_path):
        try:
            os.mkdir(__luts_path)
        except Exception as ex:
            logger.error(f"{__luts_path} could not be created - {ex}")
            logger.error(traceback.format_exc())
            
    for fname, df in __folders.items():
        for format in __output_formats:
            try:
                if format == "csv":
                    if not df.empty:
                        logger.info(f"Saving {fname} to {__luts_path}")
                        df.to_csv(os.path.join(__luts_path, f"{fname}.csv"))
            except Exception as ex:
                logger.warning(f"Failed to write the file: {fname}.{format}")
                logger.warning(traceback.format_exc())
    logger.info("Finished loading the data.")

if __name__ == "__main__":
    main()