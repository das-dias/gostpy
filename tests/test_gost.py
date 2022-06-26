from gost import __version__
from gost.gost import cli
from gost.utils import load_luts
from gost.varactor_sizing import varactor_sizing
from gost.cell_sizing import cell_sizing
from gost.switch_sizing import switch_sizing
import sys

import unittest
from pandas import DataFrame
import os

from modelling_utils import (
    MosCell,
    Devices,
    read_data,
)


luts_parent_dir = "./src/data/luts"
parent_dir = "./src/gost"
output_dir = "./src/data/output"


class TestGMoverIDSizing(unittest.TestCase):
    def test_version(self):
        self.assertEqual(__version__, "0.1.1")

    def test_single_cell_sizing(self):
        # create and setup an nmos device
        device = MosCell()
        device.__parse_data__("type", "nch")  # type of cmos device
        device.__parse_data__("l", "30 n")  # channel length
        device.__parse_data__("gmoverid", 5)  #
        device.__parse_data__("vds", "200 m")
        device.__parse_data__("vsb", "0.0")
        device.__parse_data__("id", "1000 u")
        # asserting
        self.assertEqual(device.type, "nch")
        self.assertEqual(device.l, 30 * pow(10, -9))
        self.assertAlmostEqual(device.gmoverid, 5.0)
        self.assertAlmostEqual(device.vds, 0.2)
        self.assertAlmostEqual(device.vsb, 0.0)
        self.assertEqual(device.id, 1000 * pow(10, -6))

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
        device.__parse_data__("type", "nch")  # type of cmos device
        device.__parse_data__("cvar", "100 f")  # varactor capacitance
        device.__parse_data__("l", "30 n")
        device.__parse_data__("vgs", 0.9)
        # asserting
        self.assertEqual(device.type, "nch")
        self.assertEqual(device.l, 30 * pow(10, -9))
        self.assertEqual(device.cvar, 100 * pow(10, -15))

        luts_path = os.path.join(luts_parent_dir, "nvaractor.csv")
        # check if path exists
        self.assertTrue(os.path.exists(luts_path))
        # import the luts into the program
        lut = read_data(luts_path)
        print(lut)
        self.assertIsNotNone(lut)
        self.assertEqual(type(lut), DataFrame)
        varactor_sizing(device, lut, output_dir, verbose=True)

    def test_single_switch_sizing(self):
        # create and setup an nmos device
        device = MosCell(name="s0")
        device.__parse_data__("type", "nch")  # type of cmos device
        device.__parse_data__("rds", 1)  # channel length
        device.__parse_data__("vgs", 0.9)
        # asserting
        self.assertEqual(device.type, "nch")
        self.assertEqual(device.l, 30 * pow(10, -9))
        self.assertEqual(device.rds, 1.0)

        luts_path = os.path.join(luts_parent_dir, "nswitch.csv")
        # check if path exists
        self.assertTrue(os.path.exists(luts_path))
        # import the luts into the program
        lut = read_data(luts_path)
        self.assertIsNotNone(lut)
        self.assertEqual(type(lut), DataFrame)
        switch_sizing(device, lut, output_dir, verbose=True)

    def test_cli(self):
        print(sys._getframe().f_code.co_name)
        with self.assertRaises(SystemExit):
            cli(["-h"])

    def test_inserting_help_subparser_cli(self):
        print(sys._getframe().f_code.co_name)
        argv = ["single-cell-sizing"]
        with self.assertRaises(SystemExit):
            cli(argv)

    def test_single_cell_sizing_cli(self):
        print(sys._getframe().f_code.co_name)
        argv = [
            "single-cell-sizing",
            "-t",
            "nch",
            "-vds",
            "200 m",
            "-vsb",
            "0.0",
            "-l",
            "60 n",
            "-gi",
            "20.0",
            "-id",
            "500 u",
        ]
        with self.assertRaises(SystemExit):
            cli(argv)

    def test_single_switch_sizing_cli(self):
        print(sys._getframe().f_code.co_name)
        argv = [
            "single-switch-sizing",
            "-t",
            "nch",
            "-vgs",
            "200 m",
            "-rds",
            "100.00",
            "-l",
            "30 n",
        ]
        with self.assertRaises(SystemExit):
            cli(argv)

    def test_single_varactor_sizing_cli(self):
        print(sys._getframe().f_code.co_name)
        argv = [
            "single-varactor-sizing",
            "-t",
            "pch",
            "-vsg",
            "400 m",
            "-l",
            "60 n",
            "-cvar",
            "200 f",
        ]
        with self.assertRaises(SystemExit):
            cli(argv)

    def test_cell_sizing_cli(self):
        print(sys._getframe().f_code.co_name)
        argv = [
            "cell-sizing",
            "-s",
            "./resources/specs.toml",
        ]
        with self.assertRaises(SystemExit):
            cli(argv)

    def test_varactor_sizing_cli(self):
        print(sys._getframe().f_code.co_name)
        argv = [
            "varactor-sizing",
            "-s",
            "./resources/vspecs.toml",
        ]
        with self.assertRaises(SystemExit):
            cli(argv)

    def test_switch_sizing_cli(self):
        print(sys._getframe().f_code.co_name)
        argv = [
            "switch-sizing",
            "-s",
            "./resources/sspecs.toml",
        ]
        with self.assertRaises(SystemExit):
            cli(argv)


if __name__ == "__main__":
    # load the tables from the input file to the lut_file
    load_luts(parent_dir)
    unittest.main()
