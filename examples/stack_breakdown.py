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
