
![PyBaMM-TEA-logo](https://github.com/pybamm-team/pybamm-tea/blob/main/docs/_static/pybamm_tea_logo.PNG)

#

<div align="center">

[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/pybamm-team/PyBaMM/blob/main/)


</div>


# PyBaMM-TEA

This repository contains the work of the "Google Summer of Code" project on a techno-economic analysis library for battery cells, which _can_ be combined with PyBaMM's functionality - as for creating a Ragone plot. The library can be used to estimate how mass- and volume loadings, voltage cut-off's and more influence cell metrics such as the volumetric energy at the stack level. The project further aims to provide functionality for modelling of form factors and cell costs.

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

Create a script to plot the mass- and volume loadings of an electrode stack.

```python3
import pybamm_tea
import pybamm

# Load a base parameter set from PyBaMM
base = pybamm.ParameterValues("Ecker2015")

# Provide additional input data for the TEA model
input = {
    "Electrolyte density [kg.m-3]": 1276,  # EC:EMC
    "Negative electrode active material density [kg.m-3]": 2266,  # Graphite
    "Positive electrode active material density [kg.m-3]": 4750,  # NCO
}

# Create a TEA object, passing in the parameter set and input data
tea_class = pybamm_tea.TEA(base, input)

# Plot the mass- and volume loadings of an electrode stack
tea_class.plot_masses_and_volumes()

# Print a dataframe with values of the mass- and volume loadings plot
print(tea_class.masses_and_volumes_dataframe)
```

## Documentation
API documentation for the `pybamm_tea` package can be built locally using [Sphinx](https://www.sphinx-doc.org/en/master/). To build the documentation first [clone the repository](https://github.com/git-guides/git-clone), then run the following command:
```bash
sphinx-build docs docs/_build/html  
```
This will generate a number of html files in the `docs/_build/html` directory. To view the documentation, open the file `docs/_build/html/index.html` in a web browser, e.g. by running
```bash
open docs/_build/html/index.html
```
