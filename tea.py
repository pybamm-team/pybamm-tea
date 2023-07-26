#
# TEA class
# 

import pybamm
import matplotlib.pyplot as plt
#import numpy as np
import matplotlib.patches as patches
import pandas as pd


class TEA:
    """
    A Techno-Economic Analysis class for estimation of cell metrics:

    Parameters
    ----------
    parameter_values : dict
        A dictionary of parameters and their corresponding numerical values.
        Default is NoneParameters
    """

    def __init__(self, parameter_values):
        self.parameter_values = parameter_values

    def print_stack_breakdown(self, print_dict=False):
        if not hasattr(self, "stack_bd"):
                self.calculate_stack_breakdown()
        if print_dict == True:
            print(dict)
        # convert the stackbreakdown dict to a dataframe with three columns,
        # in the first column the keys, in the second column the values for volume loadings
        # and in the third column the values for mass loadings

        # Create a dataframe with a column for the components, a column for the volume loadings, and a column for the mass loadings
        components = pd.DataFrame(["Negative current collector",
                                   "Negative electrode active material",
                                   "Negative electrode inactive material",
                                   "Negative electrode electrolyte",
                                   "Separator",
                                   "Separator electrolyte",
                                   "Positive electrode active material",
                                   "Positive electrode inactive material",
                                   "Positive electrode electrolyte",
                                   "Positive current collector",
                                   "Dry negative electrode",
                                   "Dry positive electrode"], columns=["Components"])
        volumes = pd.DataFrame([self.stack_bd.get("Negative current collector volume loading [uL.cm-2]"),
                                self.stack_bd.get("Negative electrode active material volume loading [uL.cm-2]"),
                                self.stack_bd.get("Negative electrode inactive material volume loading [uL.cm-2]"),
                                self.stack_bd.get("Negative electrode electrolyte volume loading [uL.cm-2]"),
                                self.stack_bd.get("Separator volume loading [uL.cm-2]"),
                                self.stack_bd.get("Separator electrolyte volume loading [uL.cm-2]"),
                                self.stack_bd.get("Positive electrode active material volume loading [uL.cm-2]"),
                                self.stack_bd.get("Positive electrode inactive material volume loading [uL.cm-2]"),
                                self.stack_bd.get("Positive electrode electrolyte volume loading [uL.cm-2]"),
                                self.stack_bd.get("Positive current collector volume loading [uL.cm-2]"),
                                self.stack_bd.get("Negative electrode active material volume loading [uL.cm-2]") + self.stack_bd.get("Negative electrode inactive material volume loading [uL.cm-2]") + self.stack_bd.get("Negative electrode electrolyte volume loading [uL.cm-2]"),
                                self.stack_bd.get("Positive electrode active material volume loading [uL.cm-2]") + self.stack_bd.get("Positive electrode inactive material volume loading [uL.cm-2]") + self.stack_bd.get("Positive electrode electrolyte volume loading [uL.cm-2]")], columns=["Volume loading [uL.cm-2]"])
        masses = pd.DataFrame([self.stack_bd.get("Negative current collector mass loading [mg.cm-2]"),
                                self.stack_bd.get("Negative electrode active material mass loading [mg.cm-2]"),
                                self.stack_bd.get("Negative electrode inactive material mass loading [mg.cm-2]"),
                                self.stack_bd.get("Negative electrode electrolyte mass loading [mg.cm-2]"),
                                self.stack_bd.get("Separator mass loading [mg.cm-2]"),
                                self.stack_bd.get("Separator electrolyte mass loading [mg.cm-2]"),
                                self.stack_bd.get("Positive electrode active material mass loading [mg.cm-2]"),
                                self.stack_bd.get("Positive electrode inactive material mass loading [mg.cm-2]"),
                                self.stack_bd.get("Positive electrode electrolyte mass loading [mg.cm-2]"),
                                self.stack_bd.get("Positive current collector mass loading [mg.cm-2]"),
                                self.stack_bd.get("Negative electrode active material mass loading [mg.cm-2]") + self.stack_bd.get("Negative electrode inactive material mass loading [mg.cm-2]"),
                                self.stack_bd.get("Positive electrode active material mass loading [mg.cm-2]") + self.stack_bd.get("Positive electrode inactive material mass loading [mg.cm-2]")], columns=["Mass loading [mg.cm-2]"])
        densities = pd.DataFrame([self.stack_bd.get("Negative current collector mass loading [mg.cm-2]")/self.stack_bd.get("Negative current collector volume loading [uL.cm-2]") if self.stack_bd.get("Negative current collector volume loading [uL.cm-2]") != 0 else 0,
                          self.stack_bd.get("Negative electrode active material mass loading [mg.cm-2]")/self.stack_bd.get("Negative electrode active material volume loading [uL.cm-2]") if self.stack_bd.get("Negative electrode active material volume loading [uL.cm-2]") != 0 else 0,
                          self.stack_bd.get("Negative electrode inactive material mass loading [mg.cm-2]")/self.stack_bd.get("Negative electrode inactive material volume loading [uL.cm-2]") if self.stack_bd.get("Negative electrode inactive material volume loading [uL.cm-2]") != 0 else 0,
                          self.stack_bd.get("Negative electrode electrolyte mass loading [mg.cm-2]")/self.stack_bd.get("Negative electrode electrolyte volume loading [uL.cm-2]") if self.stack_bd.get("Negative electrode electrolyte volume loading [uL.cm-2]") != 0 else 0,
                          self.stack_bd.get("Separator mass loading [mg.cm-2]")/self.stack_bd.get("Separator volume loading [uL.cm-2]") if self.stack_bd.get("Separator volume loading [uL.cm-2]") != 0 else 0,
                          self.stack_bd.get("Separator electrolyte mass loading [mg.cm-2]")/self.stack_bd.get("Separator electrolyte volume loading [uL.cm-2]") if self.stack_bd.get("Separator electrolyte volume loading [uL.cm-2]") != 0 else 0,
                          self.stack_bd.get("Positive electrode active material mass loading [mg.cm-2]")/self.stack_bd.get("Positive electrode active material volume loading [uL.cm-2]") if self.stack_bd.get("Positive electrode active material volume loading [uL.cm-2]") != 0 else 0,
                          self.stack_bd.get("Positive electrode inactive material mass loading [mg.cm-2]")/self.stack_bd.get("Positive electrode inactive material volume loading [uL.cm-2]") if self.stack_bd.get("Positive electrode inactive material volume loading [uL.cm-2]") != 0 else 0,
                          self.stack_bd.get("Positive electrode electrolyte mass loading [mg.cm-2]")/self.stack_bd.get("Positive electrode electrolyte volume loading [uL.cm-2]") if self.stack_bd.get("Positive electrode electrolyte volume loading [uL.cm-2]") != 0 else 0,
                          self.stack_bd.get("Positive current collector mass loading [mg.cm-2]")/self.stack_bd.get("Positive current collector volume loading [uL.cm-2]") if self.stack_bd.get("Positive current collector volume loading [uL.cm-2]") != 0 else 0,
                          (self.stack_bd.get("Negative electrode active material mass loading [mg.cm-2]") + self.stack_bd.get("Negative electrode inactive material mass loading [mg.cm-2]")) / (self.stack_bd.get("Negative electrode active material volume loading [uL.cm-2]") + self.stack_bd.get("Negative electrode inactive material volume loading [uL.cm-2]") + self.stack_bd.get("Negative electrode electrolyte volume loading [uL.cm-2]")) if (self.stack_bd.get("Negative electrode active material volume loading [uL.cm-2]") + self.stack_bd.get("Negative electrode inactive material volume loading [uL.cm-2]") + self.stack_bd.get("Negative electrode electrolyte volume loading [uL.cm-2]")) != 0 else 0,
                          (self.stack_bd.get("Positive electrode active material mass loading [mg.cm-2]") + self.stack_bd.get("Positive electrode inactive material mass loading [mg.cm-2]")) / (self.stack_bd.get("Positive electrode active material volume loading [uL.cm-2]") + self.stack_bd.get("Positive electrode inactive material volume loading [uL.cm-2]") + self.stack_bd.get("Positive electrode electrolyte volume loading [uL.cm-2]")) if (self.stack_bd.get("Positive electrode active material volume loading [uL.cm-2]") + self.stack_bd.get("Positive electrode inactive material volume loading [uL.cm-2]") + self.stack_bd.get("Positive electrode electrolyte volume loading [uL.cm-2]")) != 0 else 0], columns=["Density [mg.uL-1]"])

        # Concatenate the dataframes side by side
        df = pd.concat([components, volumes, masses, densities], axis=1)
        df.set_index('Components', inplace=True)
        df.index.name = None
        print(df)
        return df
    
    def print_stack_energy_densities(self, print_dict=False):
        if not hasattr(self, "stack_edd"):
                self.calculate_stack_energy_densities()
        if print_dict == True:
            print(dict)
            
    def calculate_stack_energy_densities(self):
        # defaults for current collector thicknesses and density, as well as for electrolyte density are provided
        self.stack_edd = {} # stack energy densities dict

        # ocv's
        ### add optional user defined cut-off voltages (supplied with inputs)?
        ne_ocv = self.parameter_values["Negative electrode OCP [V]"]
        pe_ocv = self.parameter_values["Positive electrode OCP [V]"]
        x0, x100, y100, y0 = pybamm.lithium_ion.get_min_max_stoichiometries(
            self.parameter_values
        )
        soc = pybamm.linspace(0, 1)
        x = x0 + soc * (x100 - x0)
        y = y0 - soc * (y0 - y100)

        self.stack_edd["Negative electrode average OCP [V]"] = self.parameter_values.get("Negative electrode average OCP [V]") or ne_ocv(x).entries.mean()
        self.stack_edd["Positive electrode average OCP [V]"] = self.parameter_values.get("Positive electrode average OCP [V]") or pe_ocv(y).entries.mean()
        self.stack_edd["Stack average OCP [V]"] = self.stack_edd.get("Stack average OCP [V]") or self.stack_edd.get("Positive electrode average OCP [V]") - self.stack_edd.get("Negative electrode average OCP [V]")

        # areal capacity
        ### add optional user defined 1st cycle capacity loss in case capacity is supplied explicitly or on top of "Formation capacity loss [mA.h.cm-2]"?
        ### calculate capacity based on user defined cut-off voltages?
        param = pybamm.LithiumIonParameters()
        esoh_solver = pybamm.lithium_ion.ElectrodeSOHSolver(
            self.parameter_values, param
        )
        Q_n = self.parameter_values.evaluate(param.n.Q_init)
        Q_p = self.parameter_values.evaluate(param.p.Q_init)
        Q_Li = self.parameter_values.evaluate(param.Q_Li_particles_init)
        inputs_ = {"Q_Li": Q_Li, "Q_n": Q_n, "Q_p": Q_p}
        sol = esoh_solver.solve(inputs_)
        areal_capacity = sol[
            "Capacity [mA.h.cm-2]" # or better min("sol[Q_n * (x_100 - x_0)]"", "sol[Q_p * (y_0 - y_100)]")?
        ]
        self.stack_edd["Capacity [mA.h.cm-2]"] = self.stack_edd.get("Capacity [mA.h.cm-2]") or areal_capacity

        # thicknesses
        if self.parameter_values.get("Negative current collector thickness [m]") is None:
            self.stack_edd["Negative current collector thickness [m]"] = 0.000012 # [m]
            print(
                "Warning: Missing 'Negative current collector thickness [m]', 12 [um] has been used."
            )
        else:
            self.stack_edd["Negative current collector thickness [m]"] = self.parameter_values.get("Negative current collector thickness [m]")
        if self.parameter_values.get("Positive current collector thickness [m]") is None:
            self.stack_edd["Positive current collector thickness [m]"] = 0.000016 # [m]
            print(
                "Warning: Missing 'Positive current collector thickness [m]', 16 [um] has been used."
            )
        else:
            self.stack_edd["Positive current collector thickness [m]"] = self.parameter_values.get("Positive current collector thickness [m]")
        self.stack_edd["Negative electrode thickness [m]"] = self.parameter_values.get("Negative electrode thickness [m]")
        self.stack_edd["Positive electrode thickness [m]"] = self.parameter_values.get("Positive electrode thickness [m]")
        self.stack_edd["Separator thickness [m]"] = self.parameter_values.get("Separator thickness [m]")
        self.stack_edd["Stack thickness [m]"] = self.stack_edd.get("Negative current collector thickness [m]") / 2 + self.stack_edd.get("Negative electrode thickness [m]") + self.stack_edd.get("Separator thickness [m]") + self.stack_edd.get("Positive electrode thickness [m]") + self.stack_edd.get("Positive current collector thickness [m]") / 2
        
        # volumetric stack energy density
        self.stack_edd["Volumetric stack energy density [Wh.L-1]"] = self.stack_edd.get("Stack average OCP [V]") * self.stack_edd.get("Capacity [mA.h.cm-2]") / self.stack_edd.get("Stack thickness [m]") / 100
        
        # dry layer and electrolyte bulk densities
        if self.parameter_values.get("Negative current collector density [kg.m-3]") is None:
            self.stack_edd["Negative current collector density [kg.m-3]"] = 8960 # [kg.m-3]
            print(
                "Warning: Missing 'Negative current collector density [kg.m-3]', 8960 [kg.m-3] has been used."
            )
        else:
            self.stack_edd["Negative current collector density [kg.m-3]"] = self.parameter_values.get("Negative current collector density [kg.m-3]")
        if self.parameter_values.get("Positive current collector density [kg.m-3]") is None:
            self.stack_edd["Positive current collector density [kg.m-3]"] = 2700 # [kg.m-3]
            print(
                "Warning: Missing 'Positive current collector density [kg.m-3]', 2700 [kg.m-3] has been used."
            )
        else:
            self.stack_edd["Positive current collector density [kg.m-3]"] = self.parameter_values.get("Positive current collector density [kg.m-3]")
        if self.parameter_values.get("Electrolyte density [kg.m-3]") is None:
            self.stack_edd["Electrolyte density [kg.m-3]"] = 1276 # [kg.m-3]
            print(
                "Warning: Missing 'Electrolyte density [kg.m-3]', 1276 [kg.m-3] has been used."
            )
        else:
            self.stack_edd["Electrolyte density [kg.m-3]"] = self.parameter_values.get("Electrolyte density [kg.m-3]")
        self.stack_edd["Negative electrode density [kg.m-3]"] = self.parameter_values.get("Negative electrode density [kg.m-3]")
        self.stack_edd["Positive electrode density [kg.m-3]"] = self.parameter_values.get("Positive electrode density [kg.m-3]")
        self.stack_edd["Separator density [kg.m-3]"] = self.parameter_values.get("Separator density [kg.m-3]")
        
        # porosities
        self.stack_edd["Negative electrode porosity"] = self.parameter_values.get("Negative electrode porosity")
        self.stack_edd["Positive electrode porosity"] = self.parameter_values.get("Positive electrode porosity")
        self.stack_edd["Separator porosity"] = self.parameter_values.get("Separator porosity")
        
        # dry layer true density
        self.stack_edd["Negative electrode composite true density [kg.m-3]"] = self.stack_edd.get("Negative electrode density [kg.m-3]") / (1 - self.stack_edd.get("Negative electrode porosity"))
        self.stack_edd["Positive electrode composite true density [kg.m-3]"] = self.stack_edd.get("Positive electrode density [kg.m-3]") / (1 - self.stack_edd.get("Positive electrode porosity"))
        if self.stack_edd.get("Separator porosity") == 1: # e.g. in "Marquis2019" or for solid electrolytes
            self.stack_edd["Separator true density [kg.m-3]"] = 0
        else:
            self.stack_edd["Separator true density [kg.m-3]"] = self.stack_edd.get("Separator density [kg.m-3]") / (1 - self.stack_edd.get("Separator porosity"))

        # weight fractions
        self.stack_edd["Negative electrode composite weight fraction"] = (1 - self.stack_edd.get("Negative electrode porosity")) * self.stack_edd.get("Negative electrode composite true density [kg.m-3]") / ((1 - self.stack_edd.get("Negative electrode porosity")) * self.stack_edd.get("Negative electrode composite true density [kg.m-3]") + self.stack_edd.get("Negative electrode porosity") * self.stack_edd.get("Electrolyte density [kg.m-3]"))
        self.stack_edd["Positive electrode composite weight fraction"] = (1 - self.stack_edd.get("Positive electrode porosity")) * self.stack_edd.get("Positive electrode composite true density [kg.m-3]") / ((1 - self.stack_edd.get("Positive electrode porosity")) * self.stack_edd.get("Positive electrode composite true density [kg.m-3]") + self.stack_edd.get("Positive electrode porosity") * self.stack_edd.get("Electrolyte density [kg.m-3]"))
        self.stack_edd["Separator weight fraction"] = (1 - self.stack_edd.get("Separator porosity")) * self.stack_edd.get("Separator true density [kg.m-3]") / ((1 - self.stack_edd.get("Separator porosity")) * self.stack_edd.get("Separator true density [kg.m-3]") + self.stack_edd.get("Separator porosity") * self.stack_edd.get("Electrolyte density [kg.m-3]"))

        # electrode and separator with electrolyte densities
        self.stack_edd["Negative electrode with electrolyte density [kg.m-3]"] = self.stack_edd.get("Negative electrode composite weight fraction") * self.stack_edd.get("Negative electrode composite true density [kg.m-3]") + self.stack_edd.get("Electrolyte density [kg.m-3]") * (1 - self.stack_edd.get("Negative electrode composite weight fraction"))
        self.stack_edd["Positive electrode with electrolyte density [kg.m-3]"] = self.stack_edd.get("Positive electrode composite weight fraction") * self.stack_edd.get("Positive electrode composite true density [kg.m-3]") + self.stack_edd.get("Electrolyte density [kg.m-3]") * (1 - self.stack_edd.get("Positive electrode composite weight fraction"))
        self.stack_edd["Separator with electrolyte density [kg.m-3]"] = self.stack_edd.get("Separator weight fraction") * self.stack_edd.get("Separator true density [kg.m-3]") + self.stack_edd.get("Electrolyte density [kg.m-3]") * (1 - self.stack_edd.get("Separator weight fraction"))

        # stack density
        self.stack_edd["Stack density [kg.m-3]"] = (self.stack_edd.get("Negative current collector thickness [m]") / 2 * self.stack_edd.get("Negative current collector density [kg.m-3]") + self.stack_edd.get("Negative electrode thickness [m]") * self.stack_edd.get("Negative electrode with electrolyte density [kg.m-3]") + self.stack_edd.get("Separator thickness [m]") * self.stack_edd.get("Separator with electrolyte density [kg.m-3]") + self.stack_edd.get("Positive electrode thickness [m]") * self.stack_edd.get("Positive electrode with electrolyte density [kg.m-3]") + self.stack_edd.get("Positive current collector thickness [m]") / 2 * self.stack_edd.get("Positive current collector density [kg.m-3]")) / self.stack_edd.get("Stack thickness [m]")
        
        # gravimetric stack energy density Wh.kg-1 better "specific energy"?
        self.stack_edd["Gravimetric stack energy density [Wh.kg-1]"] = self.stack_edd.get("Volumetric stack energy density [Wh.L-1]") / self.stack_edd.get("Stack density [kg.m-3]") * 1000
        
        return self.stack_edd

    def calculate_stack_breakdown(self):

        if not hasattr(self, "stack_edd"):
                self.calculate_stack_energy_densities()
        
        self.stack_bd = {} # stack breakdown dict
        
        # volume loadings
        self.stack_bd["Negative current collector volume loading [uL.cm-2]"] = self.stack_edd.get("Negative current collector thickness [m]") / 2 * 100000
        self.stack_bd["Negative electrode active material volume loading [uL.cm-2]"] = self.stack_edd.get("Negative electrode thickness [m]") * self.parameter_values.get("Negative electrode active material volume fraction") * 100000
        self.stack_bd["Negative electrode inactive material volume loading [uL.cm-2]"] = self.stack_edd.get("Negative electrode thickness [m]") * (1 - self.parameter_values.get("Negative electrode active material volume fraction") - self.parameter_values.get("Negative electrode porosity")) * 100000
        self.stack_bd["Negative electrode electrolyte volume loading [uL.cm-2]"] = self.stack_edd.get("Negative electrode thickness [m]") * self.parameter_values.get("Negative electrode porosity") * 100000
        self.stack_bd["Separator volume loading [uL.cm-2]"] = self.stack_edd.get("Separator thickness [m]") * (1 - self.parameter_values.get("Separator porosity")) * 100000
        self.stack_bd["Separator electrolyte volume loading [uL.cm-2]"] = self.stack_edd.get("Separator thickness [m]") * self.stack_edd.get("Separator porosity") * 100000
        self.stack_bd["Positive electrode active material volume loading [uL.cm-2]"] = self.stack_edd.get("Positive electrode thickness [m]") * self.parameter_values.get("Positive electrode active material volume fraction") * 100000
        self.stack_bd["Positive electrode inactive material volume loading [uL.cm-2]"] = self.stack_edd.get("Positive electrode thickness [m]") * (1 - self.parameter_values.get("Positive electrode active material volume fraction") - self.parameter_values.get("Positive electrode porosity")) * 100000
        self.stack_bd["Positive electrode electrolyte volume loading [uL.cm-2]"] = self.stack_edd.get("Positive electrode thickness [m]") * self.parameter_values.get("Positive electrode porosity") * 100000
        self.stack_bd["Positive current collector volume loading [uL.cm-2]"] = self.stack_edd.get("Positive current collector thickness [m]") / 2 * 100000

        # mass loadings
        self.stack_bd["Negative current collector mass loading [mg.cm-2]"] = self.stack_bd.get("Negative current collector volume loading [uL.cm-2]") * self.stack_edd.get("Negative current collector density [kg.m-3]") / 1000
        if self.parameter_values.get("Negative electrode active material volume fraction") + self.parameter_values.get("Negative electrode porosity") == 1:
            self.stack_bd["Negative electrode active material mass loading [mg.cm-2]"] = self.stack_bd.get("Negative electrode active material volume loading [uL.cm-2]") * self.stack_edd.get("Negative electrode composite true density [kg.m-3]") / 1000
        elif self.parameter_values.get("Negative electrode active material true density [kg.m-3]") == None:
            self.stack_bd["Negative electrode active material mass loading [mg.cm-2]"] = 0
            print("Error: Missing 'Negative electrode active material true density [kg.m-3]'")
        else:
            self.stack_bd["Negative electrode active material mass loading [mg.cm-2]"] = self.stack_bd.get("Negative electrode active material volume loading [uL.cm-2]") * self.parameter_values.get("Negative electrode active material true density [kg.m-3]") / 1000
        self.stack_bd["Negative electrode electrolyte mass loading [mg.cm-2]"] = self.stack_bd.get("Negative electrode electrolyte volume loading [uL.cm-2]") * self.stack_edd.get("Electrolyte density [kg.m-3]") / 1000
        self.stack_bd["Negative electrode inactive material mass loading [mg.cm-2]"] = self.stack_edd.get("Negative electrode density [kg.m-3]") * self.stack_edd.get("Negative electrode thickness [m]") * 100 - self.stack_bd.get("Negative electrode active material mass loading [mg.cm-2]")
        self.stack_bd["Separator mass loading [mg.cm-2]"] = self.stack_bd.get("Separator volume loading [uL.cm-2]") * self.stack_edd.get("Separator density [kg.m-3]") / 1000
        self.stack_bd["Separator electrolyte mass loading [mg.cm-2]"] = self.stack_bd.get("Separator electrolyte volume loading [uL.cm-2]") * self.stack_edd.get("Electrolyte density [kg.m-3]") / 1000
        if self.parameter_values.get("Positive electrode active material volume fraction") + self.parameter_values.get("Positive electrode porosity") == 1:
                self.stack_bd["Positive electrode active material mass loading [mg.cm-2]"] = self.stack_bd.get("Positive electrode active material volume loading [uL.cm-2]") * self.stack_edd.get("Positive electrode composite true density [kg.m-3]") / 1000
        elif self.parameter_values.get("Positive electrode active material true density [kg.m-3]") == None:
                self.stack_bd["Positive electrode active material mass loading [mg.cm-2]"] = 0
                print("Error: Missing 'Positive electrode active material true density [kg.m-3]'")
        else:
                self.stack_bd["Positive electrode active material mass loading [mg.cm-2]"] = self.stack_bd.get("Positive electrode active material volume loading [uL.cm-2]") * self.parameter_values.get("Positive electrode active material true density [kg.m-3]") / 1000
        self.stack_bd["Positive electrode electrolyte mass loading [mg.cm-2]"] = self.stack_bd.get("Positive electrode electrolyte volume loading [uL.cm-2]") * self.stack_edd.get("Electrolyte density [kg.m-3]") / 1000
        self.stack_bd["Positive electrode inactive material mass loading [mg.cm-2]"] = self.stack_edd.get("Positive electrode density [kg.m-3]") * self.stack_edd.get("Positive electrode thickness [m]") * 100 - self.stack_bd.get("Positive electrode active material mass loading [mg.cm-2]")
        self.stack_bd["Positive current collector mass loading [mg.cm-2]"] = self.stack_bd.get("Positive current collector volume loading [uL.cm-2]") * self.stack_edd.get("Positive current collector density [kg.m-3]") / 1000

        return self.stack_bd

    def plot_stack_breakdown(self):

        if not hasattr(self, "stack_bd"):
                self.calculate_stack_breakdown()

        heights = [
        self.stack_bd["Negative current collector mass loading [mg.cm-2]"]/2,
        self.stack_bd["Negative current collector mass loading [mg.cm-2]"]/2,
        self.stack_bd["Negative electrode active material mass loading [mg.cm-2]"],
        self.stack_bd["Negative electrode inactive material mass loading [mg.cm-2]"],
        self.stack_bd["Negative electrode electrolyte mass loading [mg.cm-2]"],
        self.stack_bd["Separator mass loading [mg.cm-2]"],
        self.stack_bd["Separator electrolyte mass loading [mg.cm-2]"],
        self.stack_bd["Positive electrode active material mass loading [mg.cm-2]"],
        self.stack_bd["Positive electrode inactive material mass loading [mg.cm-2]"],
        self.stack_bd["Positive electrode electrolyte mass loading [mg.cm-2]"],
        self.stack_bd["Positive current collector mass loading [mg.cm-2]"]/2,
        self.stack_bd["Positive current collector mass loading [mg.cm-2]"]/2
        ]
        widths = [
        self.stack_bd["Negative current collector volume loading [uL.cm-2]"]/2,
        self.stack_bd["Negative current collector volume loading [uL.cm-2]"]/2,
        self.stack_bd["Negative electrode active material volume loading [uL.cm-2]"],
        self.stack_bd["Negative electrode inactive material volume loading [uL.cm-2]"],
        self.stack_bd["Negative electrode electrolyte volume loading [uL.cm-2]"],
        self.stack_bd["Separator volume loading [uL.cm-2]"],
        self.stack_bd["Separator electrolyte volume loading [uL.cm-2]"],
        self.stack_bd["Positive electrode active material volume loading [uL.cm-2]"],
        self.stack_bd["Positive electrode inactive material volume loading [uL.cm-2]"],
        self.stack_bd["Positive electrode electrolyte volume loading [uL.cm-2]"],
        self.stack_bd["Positive current collector volume loading [uL.cm-2]"]/2,
        self.stack_bd["Positive current collector volume loading [uL.cm-2]"]/2
        ]
        labels = [
        None, # no label for the negative cc-half out of stack
        'Negative current collector',
        'Negative electrode active material',
        'Negative electrode inactive material',
        'Negative electrode electrolyte',
        'Separator',
        'Separator electrolyte',
        'Positive electrode active material',
        'Positive electrode inactive material',
        'Positive electrode electrolyte',
        'Positive current collector',
        None # no label for the positive cc-half out of stack	
        ]

        #RGB + transparency
        colors = [
        (0, 0, 0, 0.5),
        (0, 0, 0, 1),
        (0, 0, 0, 0.75),
        (0, 1, 0, 0.75),
        (0, 0, 1, 0.75),
        (0, 1, 0, 0.5),
        (0, 0, 1, 0.5),
        (1, 0, 0, 0.75),
        (0, 1, 0, 0.25),
        (0, 0, 1, 0.25),
        (1, 0, 0, 1),
        (1, 0, 0, 0.5)
        ]

        rectangle_sizes = {
        'heights': heights,
        'widths': widths,
        'labels': labels,
        'colors': colors
        }

        # Data for the rectangle heights, widths, labels, and colors
        rectangle_heights = heights
        rectangle_widths = widths
        rectangle_colors = colors
     
        # Set up the figure and axis objects
        fig = plt.figure(figsize=(8, 4), facecolor = 'white')
        ax = fig.add_axes([0.1, 0.25, 0.8, 0.6])

        # Create a collection of rectangles
        rectangles = []
        x_pos = - widths[0]

        for i, (h, w, color) in enumerate(zip(heights, widths, colors)):
            rect = patches.Rectangle((x_pos, 0), w, h, linewidth=1, edgecolor='black', facecolor=color)
            rectangles.append(rect)
            ax.add_patch(rect)
            x_pos += w

        # Add transparent rectangles with dashed lines for the specified sets of rectangles
        transparent_rect_0 = patches.Rectangle((rectangles[0].get_x(), rectangles[0].get_y()), sum(widths[0:2]), sum(heights[0:2]),
                                               linewidth=1, linestyle='dashed', edgecolor='black', facecolor='none')
        ax.add_patch(transparent_rect_0)
    
        transparent_rect_1 = patches.Rectangle((rectangles[2].get_x(), rectangles[2].get_y()), rectangles[4].get_x() + rectangles[4].get_width() - rectangles[2].get_x(), sum(heights[2:5]),
                                           linewidth=1, linestyle='dashed', edgecolor='black', facecolor='none')
        ax.add_patch(transparent_rect_1)

        transparent_rect_2 = patches.Rectangle((rectangles[5].get_x(), rectangles[5].get_y()), rectangles[6].get_x() + rectangles[6].get_width() - rectangles[5].get_x(), sum(heights[5:7]),
                                           linewidth=1, linestyle='dashed', edgecolor='black', facecolor='none')
        ax.add_patch(transparent_rect_2)

        transparent_rect_3 = patches.Rectangle((rectangles[7].get_x(), rectangles[7].get_y()), sum(widths[7:10]), sum(heights[7:10]),
                                               linewidth=1, linestyle='dashed', edgecolor='black', facecolor='none')
        ax.add_patch(transparent_rect_3)

        transparent_rect_4 = patches.Rectangle((rectangles[10].get_x(), rectangles[10].get_y()), rectangles[11].get_x() + rectangles[11].get_width() - rectangles[10].get_x(), sum(heights[10:12]),
                                               linewidth=1, linestyle='dashed', edgecolor='black', facecolor='none')
        ax.add_patch(transparent_rect_4)

        # add vertical line
        ax.axvline(sum(widths[1:11]), color='black', linestyle='-')
        ax.axvline(0, color='black', linestyle='-')
    
        # Set the x-axis limits based on the maximum x position
        ax.set_xlim( - widths[0], x_pos)
        ax.set_ylim(0, max(sum(heights[0:2]), sum(heights[2:5]), sum(heights[5:7]), sum(heights[7:10]), sum(heights[10:12]))*1.05) # 

        ax2 = ax.twiny()
        ax2.set_xlim( - widths[0]*10, x_pos*10)
        ax2.set_xlabel('Thickness [um]')

        # Add labels and title to the chart
        ax.set_xlabel('Volume loading [uL cm-2]')
        ax.set_ylabel('Mass loading [mg cm-2]')

        # Create a legend for the chart
        label_indexes = [i for i in range(1, len(labels)-1) if heights[i] != 0 and widths[i] != 0]
        legend_labels = [labels[i] for i in label_indexes]
        legend_handles = [patches.Patch(color=color, label=label) for color, label in zip(colors[1:-1], legend_labels)]
        ax.legend(handles=legend_handles, loc='upper left', bbox_to_anchor=(1.05, 1))

        # Display the chart
        plt.show()

lco_input_data = {
    "Negative electrode active material true density [kg.m-3]": 2266,  # Graphite
    "Positive electrode active material true density [kg.m-3]": 5050,  # LCO
}
print("Ramadass2004 LCO cell stack breakdown:")
param_lco_ = pybamm.ParameterValues("Ramadass2004")
param_lco_.update(lco_input_data, check_already_exists=False)
tea_lco_ = TEA(param_lco_)
tea_lco_.plot_stack_breakdown()
tea_lco_.print_stack_breakdown()

print("Marquis2019 LCO cell stack breakdown:")
param_lco = pybamm.ParameterValues("Marquis2019")
param_lco.update(lco_input_data, check_already_exists=False)
tea_lco = TEA(param_lco)
tea_lco.plot_stack_breakdown()
tea_lco.print_stack_breakdown()

nca_input_data = {
    "Negative electrode active material true density [kg.m-3]": 2266,  # Graphite
    "Positive electrode active material true density [kg.m-3]": 4450,  # NCA
}
print("NCA_Kim2011 LCO cell stack breakdown:")
param_nca = pybamm.ParameterValues("NCA_Kim2011")
param_nca.update(nca_input_data, check_already_exists=False)
tea_nca = TEA(param_nca)
tea_nca.plot_stack_breakdown()
tea_nca.print_stack_breakdown()

lfp_input_data = {
    "Negative electrode active material true density [kg.m-3]": 2266,  # Graphite
    "Positive electrode active material true density [kg.m-3]": 3600,  # LFP
    "Negative electrode density [kg.m-3]": 1675,  # Graphite
    "Positive electrode density [kg.m-3]": 2400,  # LFP
    "Separator density [kg.m-3]": 1000,
}

print("Prada 2013 LCO cell stack breakdown:")
param_lfp = pybamm.ParameterValues("Prada2013")
param_lfp.update(lfp_input_data, check_already_exists=False)
tea_lfp = TEA(param_lfp)
tea_lfp.plot_stack_breakdown()
tea_lfp.print_stack_breakdown()

print("Chen2020")
param_nmc = pybamm.ParameterValues("Chen2020")
tea_nmc = TEA(param_nmc)
tea_nmc.plot_stack_breakdown()
tea_nmc.print_stack_breakdown()