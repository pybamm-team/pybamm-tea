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

# print the electrolyte metrics
print(tea_class.electrolyte_dataframe)

# plot the mass and volume loadings
tea_class.plot_masses_and_volumes(show_plot=True)

# plot the lithiation plot
tea_class.plot_lithiation(show_plot=True)

# plot the differential lithiation plot
tea_class.differential_lithiation_plot(show_plot=True)

# plot a Ragone plot
pybamm_tea.plot_ragone([tea_class], C_rates = [0.1,1,2,3,5], plot_capacities_and_potentials=True, show_plot=True)