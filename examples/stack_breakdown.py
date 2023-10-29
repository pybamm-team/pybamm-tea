import pybamm
from pybamm_tea import tea

# input parameter-set
input = {
    "Electrolyte density [kg.m-3]": 1276, # LiPF6 in EC:EMC 3:7 + 2% VC
}

# base parameter-sets
base = pybamm.ParameterValues("Chen2020")

# create a TEA class
tea_class = tea.TEA(base, input)


# get the stack energy
print(tea_class.stack_energy_dataframe)

# get the capacities and potentials
print(tea_class.capacities_and_potentials_dataframe)

# plot the mass and volume loadings
tea_class.plot_masses_and_volumes()

# get the mass and volume loadings as a dataframe
tea_class.masses_and_volumes_dataframe
