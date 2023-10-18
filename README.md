#

![PyBaMM-TEA-logo](https://github.com/pybamm-team/pybamm-tea/blob/main/docs/_static/pybamm_tea_logo.PNG)


# PyBaMM-TEA

This repository contains the work of the "Google Summer of Code" project on a techno-economic analysis library for battery cells, which can be combined with PyBaMM's functionality.
So far, there is a method to visualize mass- and volume loadings of an electrode stack and to estimate energy densities without simulation. The project further aims to estimate cell metrics with simulations (e.g. a Ragone plot) and manufacturing metrics with a Process-based Cost Model.


## Installation
We recommend installing within a [virtual environment](https://docs.python.org/3/tutorial/venv.html) in order to not alter any python distribution files on your machine.

PyBaMM is available on GNU/Linux, MacOS and Windows. For more detailed instructions on how to install PyBaMM, see [the PyBaMM documentation](https://pybamm.readthedocs.io/en/latest/install/GNU-linux.html#user-install).

**Linux/Mac OS**
1. Clone the repository using git
```bash
git clone https://github.com/pybamm-team/PyBaMM-TEA.git
```
or download (and extract) the ZIP file by clicking the green button on the top right of the page or use GitHub Desktop.
2. Change into the `pybamm-tea` directory
```bash
cd pybamm-tea
```
3. Create a virtual environment
```bash
virtualenv env
```
4. Activate the virtual environment
```bash
source env/bin/activate
```
5. Install the package
```
pip install .
```
To install the project in editable mode use `pip install -e .`

**Windows**
To install the package from the local project path on Windows use the following commands:

1. Clone the repository using git
```bash
git clone https://github.com/pybamm-team/PyBaMM-TEA.git
```
or download (and extract) the ZIP file by clicking the green button on the top right of the page or use GitHub Desktop.
2. Change into the pybamm-tea directory
```bash
cd pybamm-tea
```
3. Create a virtual environment
```bash
virtualenv env
```
4. Activate the virtual environment
```
\path\to\env\Scripts\activate
```
where `\path\to\env` is the path to the environment created in step 3 (e.g. `C:\Users\'Username'\env\Scripts\activate.bat`).
5. Install the package
```bash
pip install .
```
To install the project in editable mode use `pip install -e .`

As an alternative, you can set up [Windows Subsystem for Linux](https://docs.microsoft.com/en-us/windows/wsl/about). This allows you to run a full Linux distribution within Windows.

## Example usage

Create a script - e.g. to plot a mass- and volume-breakdown of an electrode stack - as below or as in the example notebook.

```python3
from pybamm_tea import TEA
import pybamm

# Load a base parameter set from PyBaMM
param_nco = pybamm.ParameterValues("Ecker2015")

# Provide additional input data for the TEA model
nco_input_data = {
    "Electrolyte density [kg.m-3]": 1276,  # EC:EMC
    "Negative electrode active material density [kg.m-3]": 2266,  # Graphite
    "Positive electrode active material density [kg.m-3]": 4750,  # NCO
}

# Create a TEA object, passing in the parameter set and input data
tea_nco = TEA(param_nco, nco_input_data)

# Plot a mass- and volume-loading breakdown for an electrode stack
tea_nco.plot_stack_breakdown()

# Print a dataframe with values of the mass- and volume-loading breakdown for an
# electrode stack
print(tea_nco.stack_breakdown_dataframe)
```
