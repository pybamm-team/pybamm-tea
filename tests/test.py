import pybamm
import pybamm_tea as TEA
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import pandas as pd

# load example model
nco_input_data = {
    "Electrolyte density [kg.m-3]": 1276,
    "Negative electrode active material density [kg.m-3]": 2266,  # Graphite
    "Positive electrode active material density [kg.m-3]": 4750,  # NCO
}
param_nco = pybamm.ParameterValues("Ecker2015")
param_nco.update(nco_input_data, check_already_exists=False)
tea_nco = TEA(param_nco)

# test stack energy densities dict
assert isinstance(tea_nco.stack_energy_densities, dict), "stack_energy_densities is not a dict"
assert len(list(tea_nco.stack_energy_densities.keys())) == 15, "Number of stack_energy_densities keys is not 15"
assert tea_nco.stack_energy_densities.get("Gravimetric stack energy density [Wh.kg-1]").round() == 200.0, "Gravimetric stack energy density is not calculated correctly"

# test stack breakdown dict
assert isinstance(tea_nco.stack_breakdown, dict), "stack_breakdown is not a dict"
assert len(list(tea_nco.stack_breakdown.keys())) == 46, "Number of stack_breakdown keys is not 46"

# test stack breakdown dataframe
assert isinstance(tea_nco.stack_breakdown_dataframe, pd.DataFrame), "stack_breakdown_dataframe is not a DataFrame"
assert list(tea_nco.stack_breakdown_dataframe.columns) == ['Volume loading [uL.cm-2]', 'Mass loading [mg.cm-2]', 'Density [mg.uL-1]'], "stack_breakdown_dataframe columns are correct"

# test stack breakdown plot
assert isinstance(tea_nco.plot_stack_breakdown(), plt.Figure), "plot_stack_breakdown is not a matplotlib Figure"
