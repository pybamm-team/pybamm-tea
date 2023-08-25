#

![logo](https://raw.githubusercontent.com/pybamm-team/pybamm-tea/main/docs/pybamm_tea_logo.png)


# PyBaMM-TEA

This repository contains the work of the "Google Summer of Code" project on a techno-economic analysis library for battery cells, which can be combined with PyBaMM's functionality.
So far, there is a method to visualize mass- and volume loadings of an electrode stack and to estimate energy densities without simulation. The project further aims to estimate cell metrics with simulations (e.g. a Ragone plot) and manufacturing metrics with a Process-based Cost Model.


## Installation

Clone the repository using git, or download (and extract) the ZIP file by clicking the green button

```bash
git clone https://github.com/pybamm-team/PyBaMM-TEA.git
```

Navigate to the repository directory

```bash
cd /Users/yourusername/Downloads/PyBaMM-TEA
```

Create a new virtual environment, or activate an existing one (this example uses the python `venv` module, but you could use Anaconda and a `conda` environment)

```bash
python3 -m venv env
source env/bin/activate
```

Install the required packages
```bash
pip install -r requirements.txt
```

Install the `pybamm_tea` module using pip

```bash
pip install .
```

## Example usage

Create a python script similar to that below

```python
from pybamm_tea import TEA
import pybamm
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import pandas as pd

nco_input_data = {
    "Electrolyte density [kg.m-3]": 1276, # EC:EMC
    "Negative electrode active material density [kg.m-3]": 2266,  # Graphite
    "Positive electrode active material density [kg.m-3]": 4750,  # NCO
}
param_nco = pybamm.ParameterValues("Ecker2015")
param_nco.update(nco_input_data, check_already_exists=False)

tea_nco = TEA(param_nco)
tea_nco.plot_stack_breakdown()
tea_nco.stack_breakdown_dataframe()
```