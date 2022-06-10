from gmoverid_cmos_sizing import(
    __version__,
    load_luts,
    cell_sizing,
    switch_sizing,
    varactor_sizing
)
import unittest
from pandas import DataFrame
import os

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

luts_parent_dir = "/Users/dasdias/Documents/PhD-NOVA/Circuits/ResidueAmplifier_Gain8_28nmTSMC/gmoverid_cmos_sizing/gmoverid_cmos_sizing/data/luts"
parent_dir = "/Users/dasdias/Documents/PhD-NOVA/Circuits/ResidueAmplifier_Gain8_28nmTSMC/gmoverid_cmos_sizing/gmoverid_cmos_sizing"
output_dir = "/Users/dasdias/Documents/PhD-NOVA/Circuits/ResidueAmplifier_Gain8_28nmTSMC/gmoverid_cmos_sizing/gmoverid_cmos_sizing/data/output"
class TestGMoverIDSizing(unittest.TestCase):
    def test_version(self):
        self.assertEqual(__version__, "0.1.0")
    
    def test_single_cell_sizing(self):
        # create and setup an nmos device
        device = MosCell()
        device.__parse_data__("type", "nch") # type of cmos device
        device.__parse_data__("l", "30 n") # channel length
        device.__parse_data__("gmoverid", 5) # 
        device.__parse_data__("vds", "200 m")
        device.__parse_data__("vsb", "0.0")
        device.__parse_data__("id", "1000 u")
        # asserting
        self.assertEqual(device.type, "nch")
        self.assertEqual(device.l, 30*pow(10, -9))
        self.assertAlmostEqual(device.gmoverid, 5.0)
        self.assertAlmostEqual(device.vds, 0.2)
        self.assertAlmostEqual(device.vsb, 0.0)
        self.assertEqual(device.id, 1000*pow(10,-6))
        
        luts_path = os.path.join(luts_parent_dir, "ncell.csv")
        # check if path exists
        self.assertTrue(os.path.exists(luts_path))
        # import the luts into the program
        lut = read_data(luts_path)
        self.assertIsNotNone(lut)
        self.assertEqual(type(lut), DataFrame)
        cell_sizing(device, lut, output_dir, verbose=True)
        
    
    def test_single_varactor_sizing(self):
        # create and setup an nmos device
        device = MosCell(name="v0")
        device.__parse_data__("type", "nch") # type of cmos device
        device.__parse_data__("cvar", "100 f") # varactor capacitance
        device.__parse_data__("l", "30 n")
        device.__parse_data__("vgs", 0.9)
        # asserting
        self.assertEqual(device.type, "nch")
        self.assertEqual(device.l, 30*pow(10, -9))
        self.assertEqual(device.cvar, 100*pow(10,-15))
        
        luts_path = os.path.join(luts_parent_dir, "nvaractor.csv")
        # check if path exists
        self.assertTrue(os.path.exists(luts_path))
        # import the luts into the program
        lut = read_data(luts_path)
        self.assertIsNotNone(lut)
        self.assertEqual(type(lut), DataFrame)
        varactor_sizing(device, lut, output_dir, verbose=True)
    
    def test_single_switch_sizing(self):
        # create and setup an nmos device
        device = MosCell(name="s0")
        device.__parse_data__("type", "nch") # type of cmos device
        device.__parse_data__("rds", 1) # channel length
        device.__parse_data__("vgs", 0.9)
        # asserting
        self.assertEqual(device.type, "nch")
        self.assertEqual(device.l, 30*pow(10, -9))
        self.assertEqual(device.rds, 1.0)
        
        luts_path = os.path.join(luts_parent_dir, "nswitch.csv")
        # check if path exists
        self.assertTrue(os.path.exists(luts_path))
        # import the luts into the program
        lut = read_data(luts_path)
        self.assertIsNotNone(lut)
        self.assertEqual(type(lut), DataFrame)
        switch_sizing(device, lut, output_dir, verbose=True)
        
        
        

if __name__ == "__main__":
    # load the tables from the input file to the lut_file
    load_luts(parent_dir)
    unittest.main()