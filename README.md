![algarvia_1.png](docs/algarvia_1.png)
# Gover

```Gover``` is a tool dedicated to aiding analog integrated circuit designers sizing the devices integrating the circuits being designed through the use of the Gm (transconductance) over Id (Drain-Source) (Gm/Id) design methodology.

## Summary

The tool allows for the sizing of three possible CMOS devices:

- CMOS Transistors
- CMOS Switches
- CMOS Varactors (MOSCap)

The tool works in a very simple manner. The engineer himself needs to obtain the look up tables (LUTs) through simulation. The obtained LUTs must be in comma separated values (.CSV) format, and must have the exact topology as the LUTs already present in the ```src/data``` directory. These LUTs obtained in simulation must be inserted into the ```src/data/input``` directory, in which each set of LUTs for the correspondent device type must be inserted into its correspondent directory:

- Transistor related LUTs into ```src/data/input/ncell``` and ```src/data/input/pcell``` for NMOS and PMOS devices, respectively
- Switch related LUTs into ```src/data/input/nswitch``` and ```src/data/input/pswitch``` for NMOS and PMOS devices, respectively
- Varactor related LUTs into ```src/data/input/nvaractor``` and ```src/data/input/pvaractor``` for NMOS and PMOS devices, respectively

After providing the necessary simulation data to the input directory, the tool will perform conditional searches in the database and afterwards apply the Gm/Id method in order to provide the necessary Channel Width (Wch) and Gate-to-Source (Vgs) voltage that allow to obtain a device that meets the design requirements laid out by the designer.

## Dependencies

- ```Poetry``` - Python language’s most famous and best package manager, allowing to quickly deploy any application or package written in Python ([https://python-poetry.org/docs/](https://python-poetry.org/docs/))
- SPICE simulation-generated look up tables with each device type’s direct-current (DC) operating point (OP). The data available in ```src/data/input``` was generated using ```Cadence-Virtuoso``` software, and relates to a 28 nm TSMC CMOS technology.

## Installing
After installing ```Poetry``` run the following command inside the code folder:
```
foo/bar/goverpy % poetry install
```
In this case it was considered that the application directory, ```/goverpy``` was placed inside the directory ```foo/bar/```.


## Methodology

The sizing of each type of N-channel (nch) or P-channel (pch) CMOS device is bound by its specific set of degrees of freedom (DOF):

- CMOS Transistors:
    - Degrees of Freedom (DOF):
        - Channel Length (Lch)
        - Drain-to-Source (Vds) voltage - controlling the saturation level of the channel, very dependant of the circuit topology
        - Gm/Id - controlling the transconductance efficiency of the device
        - Source-to-Bulk(Back Gate) Voltage (Vsb) - controlling the threshold voltage necessary to place the device in the saturation region, and often directly dependant on the circuit topology
- CMOS Switches:
    - Degrees of Freedom (DOF):
        - Channel Length(Lch) - not really a DOF, because in order to minimize switch On-Resistance while maximising switching speed one must use minimum Length
        - Gate-to-Source (Vgs) voltage - controlling the inversion level of the channel, and thus modulating the total resistance offered by the channel when conducting current. This is not really a DOF as well, because Vgs = VDD always minimizes the On-Resistance of the channel, while allowing for the maximum operating frequency (ft) of the device
        - Output Resistance (Rds) - the required Drain-Output resistance for the switch, bound by distortion and gain specifications
- CMOS Varactors:
    - Degrees of Freedom (DOF):
        - Channel Length (Lch)
        - Gate-to-Source (Vgs) voltage - controlling the inversion level of the channel, and thus modulating the total Gate-Capacitance of the device (maximising it for maximum Vgs). Usually Vgs is bound by circuit topology, and thus it is not really a DOF.
        - Total MOSCap capacitancein inversion (Cvar) - the total capacitance that the designer wants to observe at the gate terminal of the device (high-impedance terminal) during the phase in which the device is considered to be in the inversion region (the channel is inverted - for Vgs > Vth).

All the aforementioned DOF will enable the generation of a ```Channel Width (Wch)``` that allows for each device to accomplish its design specification (Gm/Id for transistors, Ron for switches and Cvar for MOSCaps). The operation of the tool can then be summarised in the following system diagrams:

#Insert diagrams here

## How to Use

```Gover``` is an application based on a command-line interface (CLI) that allows the user to interact with the application itself, and therefore the use of the app is based on the parsing of commands and its associated parameters in order to generate an output based on the given input of the user. Some examples are given on how to interact with the tool.

---

### Asking for Help

*Main-frame*

In order to observe the sub-processes that are embedded into the tool, one can call for help in its main-frame:

```
poetry run gover -h
```
OR
```
poetry run gover —help
```

An output like this will appear:

```
usage: gover [-h] [-q | -v] {cell-sizing,varactor-sizing,switch-sizing,single-cell-sizing,single-varactor-sizing,single-switch-sizing} ...

Gm / Id Device Sizing Tool by Diogo André Silvares Dias (das.dias6@gmail.com)

positional arguments:

{cell-sizing,varactor-sizing,switch-sizing,single-cell-sizing,single-varactor-sizing,single-switch-sizing}

cell-sizing         Compute the transistor sizing
varactor-sizing     Compute the MOS Capacitor sizing
switch-sizing       Compute the MOS Switch sizing
single-cell-sizing  Compute the transistor sizing

single-varactor-sizing

Compute the MOS Capacitor sizing

single-switch-sizing

Compute the MOS Switch sizing

optional arguments:

-h, --help            show this help message and exit
-q, --quiet           quiet verbose
-v, --verbose         print verbose

```
---
*Device Sizing Secondary-Frames:*

Each sub-frame has its own ```help``` console output, and one can call it by simply typing into console the call of the ```Gover``` application, followed by the sub-frame we want to call (depending on the kind of device we want to size) and the help command. For example, if we want some help on sizing multiple CMOS switches using a ```.TOML``` file for the input of switch specifications we can run the following command:

```
poetry run gover switch-sizing -h
```

OR

```
poetry run gover switch-sizing —help
```

As stated before, the supports the sizing of multiple devices (of the same type) at once through the use of a ```.TOML``` file to parse specifications for each device to design into the application, and also supports the sizing of a single device of any type by parsing the device’s specifications directly from console into the tool.

---

### Sizing a single device

An example regarding the sizing operation of a single transistor using console parsing is given in the following snippet.

```
poetry run gover single-cell-sizing -t nch -vds “200 m” -vsb 0.0 -l “60 n” -gi 20 -id “500 u”
```

In this snippet, an NMOS (```-t nch```) transistor device is being sized, in which its:

- expected Vds is 200 milivolt (mV)
- bound Vsb (Source-Bulk voltage) is 0 volt (V) - thus eliminating the *Body Effect*
- Channel Length is 2x the minimum channel length of the 28 nm tech. node (60 nanometers)
- The device is expected to operate with a transconductance efficiency (Gm/Id) of 20 V^{-1} (```-gi 20```)
- The polarising current of the transistor’s channel (Id) is 500 micro-ampere (uA)

The obtained console output for these sizing parameters is currently computed through the performance of a table query to obtain the scaled Channel Width of the device (through the Gm/Id sizing methodology) that allows for the accomplishment of the specified Drain current -Id. 

The console output for the previous command will be as such:

```
2022-06-13 14:03:53.510 | **INFO**     | gover.cell_sizing:cell_sizing:165 - **Computing m0 transistor sizing...**
2022-06-13 14:03:54.021 | **INFO**     | gover.cell_sizing:cell_sizing:224 - **Transistor sizing completed.**
Device : m0
vgs                 0.4
cdb        2.180952e-14
cgb        1.762000e-16
cgd        9.486216e-15
cgs        2.847118e-14
csb        2.468672e-14
ft         4.186684e+10
gds        6.651629e-04
gm         9.984962e-03
gmbs       4.176000e-05
gmoverid   1.997000e+01
id         4.999981e-04
l          6.000000e-08
region     2.000000e+00
self_gain  1.501130e+01
vds        2.000000e-01
vdsat      1.156000e-01
vsb        0.000000e+00
w          5.764411e-05
2022-06-13 14:03:54.024 | **INFO**     | modelling_utils.utils:wrapper:98 -

**Function: cell_sizing	Runtime: 513.834 ms.**
```

Graphical results will also be generated when performing transistor and switch sizing operations. In the case of the sizing of transistors, the graphs will present the curves of dependance between the transistor’s intrinsic gain, maximum operating frequency and transconductance efficiency towards the variation of the level of inversion through the variation of the Vgs voltage.

![m0-gm_over_id.png](docs/m0-gm_over_id.png)

---

### Sizing multiple devices automatically

Instead of parsing each devices specification through console parsing, it is also possible to write a Tom’s Obvious Minimal Language (TOML) file stating the specifications for each device of the same class (transistor, switch or MOSCap). This ```.toml``` file can then be parsed to the tool through dedicated commands and the devices will be automatically sized.

Given the example of the following ```.toml``` file containing the design specifications for 4 CMOS switches:

```TOML
#file-name: foo/bar/switch_specs.toml

[control] # control parameters for each device of the circuit
switches=["s0","s1","s2","s3"]
s0={type="nch", vgs="150 m", rds="100", l="30 n"}
s1={type="nch", vgs="150 m", rds="60", l="30 n"}
s2={type="pch", vsg="150 m", rds="70", l="30 n"}
s3={type="pch", vsg="150 m", rds="85", l="30 n"}

[spit] # output control variables
vars={s0=["all"], s1=["vgs","cgs"], s2=["ft"], s3=["all"]}
```

By running the following command:

```
poetry run gover switch-sizing -s foo/bar/switch_specs.toml
```

The switches ```s0``` to ```s3``` will be automatically sized, and the following output will be generated to console (along with the generated graphs):

```
2022-06-13 14:03:58.748 | **INFO**     | modelling_utils.utils:wrapper:98 -
**Function: switch_sizing	Runtime: 7.283 ms.**
2022-06-13 14:03:58.753 | **INFO**     | modelling_utils.utils:wrapper:98 -
**Function: switch_sizing	Runtime: 5.055 ms.**
2022-06-13 14:03:58.758 | **INFO**     | modelling_utils.utils:wrapper:98 -
**Function: switch_sizing	Runtime: 4.631 ms.**
2022-06-13 14:03:58.762 | **INFO**     | modelling_utils.utils:wrapper:98 -
**Function: switch_sizing	Runtime: 4.459 ms.**

Devices:
- -None--

Varactors:
- -None--

Switches:
name[] type[]  vgs[V]          l[m]      w[m]  rds[Ω]        cdb[F] cdep[F] cgb[F]        cgd[F]  ... gmoverid[V^-1]  id[A]  region[] self_gain[VV^-01] vbs[V] vds[V]  vdsat[V] vsb[V] vsd[V]  vsg[V]

s0     s0    nch    0.15  3.000000e-08  0.011252   100.0  4.612035e-12    None   None  1.822896e-12  ...            1.0    0.0      None              None   -0.0    0.0      None    0.0   -0.0   -0.15

s1     s1    nch    0.15  3.000000e-08  0.018754    60.0  7.686725e-12    None   None  3.038160e-12  ...            1.0    0.0      None              None   -0.0    0.0      None    0.0   -0.0   -0.15

s2     s2    pch   -0.15  3.000000e-08  0.061050    70.0  2.464564e-11    None   None  1.129692e-11  ...            1.0    0.0      None              None    0.0    0.0      None    0.0    0.0    0.15

s3     s3    pch   -0.15  3.000000e-08  0.050277    85.0  2.029641e-11    None   None  9.303342e-12  ...            1.0    0.0      None              None    0.0    0.0      None    0.0    0.0    0.15

[4 rows x 29 columns]
```

## Future Work
 
Right now the tool is solemnly based on conditional queries to a previously acquired databased by the engineer/designer himself, but efforts are being made to build a multivariate regression model based on machine learning algorithms to model the data of these same databases and rely on these models to obtain the corerspondant DC OP that best accomodates our design specifications. This way, the engineer will have no problem in sizing a device with a channel length of 1.1, or 1.4 or even 1.6 times the minimum channel length of the technology - liberating themselves from the natural integers used during the simulations that resulted in the obtained look up tables.