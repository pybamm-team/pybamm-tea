import pybamm
import pybamm_tea

# create an input dictionary
input["Electrolyte density [kg.m-3]"] = 1276

# create a base parameter set
base = pybamm.ParameterValues("Chen2020")

# create a TEA class
tea_class = pybamm_tea.TEA(base, input)

# print the stack energy
print(tea_class.stack_energy_dataframe)

# print the capacities and potentials
print(tea_class.capacities_and_potentials_dataframe)

# print the mass and volume loadings as a dataframe
print(tea_class.masses_and_volumes_dataframe)

# plot the mass and volume loadings
tea_class.plot_masses_and_volumes()
