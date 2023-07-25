import pybamm
import matplotlib.pyplot as plt
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as patches


class TEA():
    """Techno-Economic Analysis class with functions for the estimation of cell and cell-production metrics:

    Cell metrics:
     stack_energy_densities - Calculation of gravimetric and volumetric energy densities on stack level (WIP)
     stack_breakdown - Calculation of areal mass and volume loadings (WIP)
     plot_stack_breakdown - Plot of areal mass and volume loadings (WIP)
     stack_power_densities - Calculation of gravimetric and volumetric power densities on stack level (to be implemented)
     cell_energy_densities - Calculation of gravimetric and volumetric energy densities on cell level (to be implemented)
     cell_power_densities - Calculation of gravimetric and volumetric power densities on cell level (to be implemented)
     cell_breakdown - Calculation of total masses and volumes on cell level (to be implemented)
     plot_cell_breakdown - Plot of total masses and volumes on cell level (to be implemented)

    Process metrics:
     component_cost_breakdown - Calculation of total component costs on cell level (to be implemented)
     plot_component_cost_breakdown - Plot of total component costs on cell level (to be implemented)
     End of next month:
     (bottom-up model for production costs (+emissions,waste) with respect to the cell design)
     (from precursor_production to electrode_production, cell_assembly, formation up to recycling)
     """
    
    # nearly all used parameter are saved in the results dict
    # maybe example results-sets for PyBaMM parameter-sets and non Li-ion chemistries can be provided?

    # In case parameter are not available in a specific parameter_values set (as for non Li-ion chemistries),
    # the values can be predefined/supplied with results
    # In case parameter are in general not included in parameter_values, e.g. active material density or price
    # they are supplied with inputs to the functions
    # In case parameter are not available in parameter_values or results, defaults are used for:
    # current collector thicknesses and densities and for electrolyte density
    # if values are in results and in inputs or parameter_values, the values from results are not used

    def __init__(self, parameter_values=None, results=None):
        self.parameter_values = parameter_values
        if results is not None:
            self.results = results
        else:
            self.results = {}

        if parameter_values is None and results is None:
            print(
                "Error: Missing parameter_values and results, please supply parameters to TEA()"
            )
        if parameter_values is None and results is not None:
            print(
                "Warning: Missing parameter_values, values from results are used."
            )
        
        super().__init__()

    def stack_energy_densities(self, inputs=None, print_values=False):
        # Inputs: "Electrolyte density [kg.m-3]"
        if inputs is None:
            # print("Warning: Missing input parameters")
            inputs = {}
        else:
            inputs = inputs

        # ocv's
        # add optional user defined cut-off voltages (supplied with inputs)?
        ne_ocv = self.parameter_values["Negative electrode OCP [V]"]
        pe_ocv = self.parameter_values["Positive electrode OCP [V]"]
        x0, x100, y100, y0 = pybamm.lithium_ion.get_min_max_stoichiometries(
            self.parameter_values
        )
        soc = pybamm.linspace(0, 1)
        x = x0 + soc * (x100 - x0)
        y = y0 - soc * (y0 - y100)

        self.results["Negative electrode average OCP [V]"] = self.results.get("Negative electrode average OCP [V]") or ne_ocv(x).entries.mean()
        self.results["Positive electrode average OCP [V]"] = self.results.get("Positive electrode average OCP [V]") or pe_ocv(y).entries.mean()
        self.results["Stack average OCP [V]"] = self.results.get("Stack average OCP [V]") or self.results.get("Positive electrode average OCP [V]") - self.results.get("Negative electrode average OCP [V]")

        # areal capacity
        # add optional user defined 1st cycle capacity loss in case capacity is supplied explicitly (with results) or on top of "Formation capacity loss [mA.h.cm-2]"?
        # update capacity, in case of optional user defined cut-off voltages (supplied with inputs)?
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
        self.results["Capacity [mA.h.cm-2]"] = self.results.get("Capacity [mA.h.cm-2]") or areal_capacity

        # thicknesses
        if self.results.get("Negative current collector thickness [m]") is None and self.parameter_values.get("Negative current collector thickness [m]") is None:
            self.results["Negative current collector thickness [m]"] = 0.000012 # [m]
            print(
                "Warning: Missing 'Negative current collector thickness [m]', 12 [um] has been used."
            )
        else:
            self.results["Negative current collector thickness [m]"] = self.parameter_values.get("Negative current collector thickness [m]") or self.results.get("Negative current collector thickness [m]")
        if self.results.get("Positive current collector thickness [m]") is None and self.parameter_values.get("Positive current collector thickness [m]") is None:
            self.results["Positive current collector thickness [m]"] = 0.000016 # [m]
            print(
                "Warning: Missing 'Positive current collector thickness [m]', 16 [um] has been used."
            )
        else:
            self.results["Positive current collector thickness [m]"] = self.parameter_values.get("Positive current collector thickness [m]") or self.results.get("Positive current collector thickness [m]")
        self.results["Negative electrode thickness [m]"] = self.parameter_values.get("Negative electrode thickness [m]") or self.results.get("Negative electrode thickness [m]")
        self.results["Positive electrode thickness [m]"] = self.parameter_values.get("Positive electrode thickness [m]") or self.results.get("Positive electrode thickness [m]")
        self.results["Separator thickness [m]"] = self.parameter_values.get("Separator thickness [m]") or self.results.get("Separator thickness [m]")
        self.results["Stack thickness [m]"] = self.results.get("Stack thickness [m]") or self.results.get("Negative current collector thickness [m]") / 2 + self.results.get("Negative electrode thickness [m]") + self.results.get("Separator thickness [m]") + self.results.get("Positive electrode thickness [m]") + self.results.get("Positive current collector thickness [m]") / 2
        
        # volumetric stack energy density
        self.results["Volumetric stack energy density [Wh.L-1]"] = self.results.get("Volumetric stack energy density [Wh.L-1]") or self.results.get("Stack average OCP [V]") * self.results.get("Capacity [mA.h.cm-2]") / self.results.get("Stack thickness [m]") / 100
        
        # dry layer and electrolyte bulk densities better sth else than "bulk"?
        if self.results.get("Negative current collector density [kg.m-3]") is None and self.parameter_values.get("Negative current collector density [kg.m-3]") is None:
            self.results["Negative current collector density [kg.m-3]"] = 8960 # [kg.m-3]
            print(
                "Warning: Missing 'Negative current collector density [kg.m-3]', 8960 [kg.m-3] has been used."
            )
        else:
            self.results["Negative current collector density [kg.m-3]"] = self.parameter_values.get("Negative current collector density [kg.m-3]") or self.results.get("Negative current collector density [kg.m-3]")
        if self.results.get("Positive current collector density [kg.m-3]") is None and self.parameter_values.get("Positive current collector density [kg.m-3]") is None:
            self.results["Positive current collector density [kg.m-3]"] = 2700 # [kg.m-3]
            print(
                "Warning: Missing 'Positive current collector density [kg.m-3]', 2700 [kg.m-3] has been used."
            )
        else:
            self.results["Positive current collector density [kg.m-3]"] = self.parameter_values.get("Positive current collector density [kg.m-3]") or self.results.get("Positive current collector density [kg.m-3]")
        if self.results.get("Electrolyte density [kg.m-3]") is None and inputs.get("Electrolyte density [kg.m-3]") is None:
            self.results["Electrolyte density [kg.m-3]"] = 1276 # [kg.m-3] google: (EC:EMC 1:1 1M LiPF6 2% FEC) better just use 1300?
            print(
                "Warning: Missing 'Electrolyte density [kg.m-3]', 1276 [kg.m-3] has been used."
            )
        else:
            self.results["Electrolyte density [kg.m-3]"] = inputs.get("Electrolyte density [kg.m-3]") or self.results.get("Electrolyte density [kg.m-3]")
        self.results["Negative electrode density [kg.m-3]"] = self.parameter_values.get("Negative electrode density [kg.m-3]") or self.results.get("Negative electrode density [kg.m-3]")
        self.results["Positive electrode density [kg.m-3]"] = self.parameter_values.get("Positive electrode density [kg.m-3]") or self.results.get("Positive electrode density [kg.m-3]")
        self.results["Separator density [kg.m-3]"] = self.parameter_values.get("Separator density [kg.m-3]") or self.results.get("Separator density [kg.m-3]")
        
        # porosities
        self.results["Negative electrode porosity"] = self.parameter_values.get("Negative electrode porosity") or self.results.get("Negative electrode porosity")
        self.results["Positive electrode porosity"] = self.parameter_values.get("Positive electrode porosity") or self.results.get("Positive electrode porosity")
        self.results["Separator porosity"] = self.parameter_values.get("Separator porosity") or self.results.get("Separator porosity")
        
        # dry layer true density better sth else than "true"?
        self.results["Negative electrode composite true density [kg.m-3]"] = self.results.get("Negative electrode composite true density [kg.m-3]") or self.results.get("Negative electrode density [kg.m-3]") / (1 - self.results.get("Negative electrode porosity"))
        self.results["Positive electrode composite true density [kg.m-3]"] = self.results.get("Positive electrode composite true density [kg.m-3]") or self.results.get("Positive electrode density [kg.m-3]") / (1 - self.results.get("Positive electrode porosity"))
        if self.results.get("Separator porosity") == 1:
            self.results["Separator true density [kg.m-3]"] = 0
        else:
            self.results["Separator true density [kg.m-3]"] = self.results.get("Separator true density [kg.m-3]") or self.results.get("Separator density [kg.m-3]") / (1 - self.results.get("Separator porosity"))

        # weight fractions
        self.results["Negative electrode composite weight fraction"] = self.results.get("Negative electrode composite weight fraction") or (1 - self.results.get("Negative electrode porosity")) * self.results.get("Negative electrode composite true density [kg.m-3]") / ((1 - self.results.get("Negative electrode porosity")) * self.results.get("Negative electrode composite true density [kg.m-3]") + self.results.get("Negative electrode porosity") * self.results.get("Electrolyte density [kg.m-3]"))
        self.results["Positive electrode composite weight fraction"] = self.results.get("Positive electrode composite weight fraction") or (1 - self.results.get("Positive electrode porosity")) * self.results.get("Positive electrode composite true density [kg.m-3]") / ((1 - self.results.get("Positive electrode porosity")) * self.results.get("Positive electrode composite true density [kg.m-3]") + self.results.get("Positive electrode porosity") * self.results.get("Electrolyte density [kg.m-3]"))
        self.results["Separator weight fraction"] = self.results.get("Separator weight fraction") or (1 - self.results.get("Separator porosity")) * self.results.get("Separator true density [kg.m-3]") / ((1 - self.results.get("Separator porosity")) * self.results.get("Separator true density [kg.m-3]") + self.results.get("Separator porosity") * self.results.get("Electrolyte density [kg.m-3]"))

        # electrode and separator with electrolyte densities
        self.results["Negative electrode with electrolyte density [kg.m-3]"] = self.results.get("Negative electrode with electrolyte density [kg.m-3]") or self.results.get("Negative electrode composite weight fraction") * self.results.get("Negative electrode composite true density [kg.m-3]") + self.results.get("Electrolyte density [kg.m-3]") * (1 - self.results.get("Negative electrode composite weight fraction"))
        self.results["Positive electrode with electrolyte density [kg.m-3]"] = self.results.get("Positive electrode with electrolyte density [kg.m-3]") or self.results.get("Positive electrode composite weight fraction") * self.results.get("Positive electrode composite true density [kg.m-3]") + self.results.get("Electrolyte density [kg.m-3]") * (1 - self.results.get("Positive electrode composite weight fraction"))
        self.results["Separator with electrolyte density [kg.m-3]"] = self.results.get("Separator with electrolyte density [kg.m-3]") or self.results.get("Separator weight fraction") * self.results.get("Separator true density [kg.m-3]") + self.results.get("Electrolyte density [kg.m-3]") * (1 - self.results.get("Separator weight fraction"))

        # stack density
        self.results["Stack density [kg.m-3]"] = self.results.get("Stack density [kg.m-3]") or (self.results.get("Negative current collector thickness [m]") / 2 * self.results.get("Negative current collector density [kg.m-3]") + self.results.get("Negative electrode thickness [m]") * self.results.get("Negative electrode with electrolyte density [kg.m-3]") + self.results.get("Separator thickness [m]") * self.results.get("Separator with electrolyte density [kg.m-3]") + self.results.get("Positive electrode thickness [m]") * self.results.get("Positive electrode with electrolyte density [kg.m-3]") + self.results.get("Positive current collector thickness [m]") / 2 * self.results.get("Positive current collector density [kg.m-3]")) / self.results.get("Stack thickness [m]")
        
        # gravimetric stack energy density Wh.kg-1 better "specific energy"?
        self.results["Gravimetric stack energy density [Wh.kg-1]"] = self.results.get("Gravimetric stack energy density [Wh.kg-1]") or self.results.get("Volumetric stack energy density [Wh.L-1]") / self.results.get("Stack density [kg.m-3]") * 1000
        
        if print_values == True:
            print(self.results)

        return self.results.get("Volumetric stack energy density [Wh.L-1]"), self.results.get("Gravimetric stack energy density [Wh.kg-1]")

    def stack_breakdown(self, inputs=None, print_values=False):
        # Inputs: "Electrolyte density [kg.m-3]", "Negative electrode active material true density [kg.m-3]", "Positive electrode active material true density [kg.m-3]"
        if inputs is None:
            inputs = {}
        else:
            inputs = inputs

        # call stack_energy_densities
        self.stack_energy_densities(inputs=inputs)

        # volume loadings
        self.results["Negative current collector volume loading [uL.cm-2]"] = self.results.get("Negative current collector volume loading [uL.cm-2]") or self.results.get("Negative current collector thickness [m]") / 2 * 100000
        self.results["Negative electrode active material volume loading [uL.cm-2]"] = self.results.get("Negative electrode active material volume loading [uL.cm-2]") or self.results.get("Negative electrode thickness [m]") * self.parameter_values.get("Negative electrode active material volume fraction") * 100000
        self.results["Negative electrode inactive material volume loading [uL.cm-2]"] = self.results.get("Negative electrode inactive material volume loading [uL.cm-2]") or self.results.get("Negative electrode thickness [m]") * (1 - self.parameter_values.get("Negative electrode active material volume fraction") - self.parameter_values.get("Negative electrode porosity")) * 100000
        self.results["Negative electrode electrolyte volume loading [uL.cm-2]"] = self.results.get("Negative electrode electrolyte volume loading [uL.cm-2]") or self.results.get("Negative electrode thickness [m]") * self.parameter_values.get("Negative electrode porosity") * 100000
        self.results["Separator volume loading [uL.cm-2]"] = self.results.get("Separator volume loading [uL.cm-2]") or self.results.get("Separator thickness [m]") * (1 - self.parameter_values.get("Separator porosity")) * 100000
        self.results["Separator electrolyte volume loading [uL.cm-2]"] = self.results.get("Separator electrolyte volume loading [uL.cm-2]") or self.results.get("Separator thickness [m]") * self.results.get("Separator porosity") * 100000
        self.results["Positive electrode active material volume loading [uL.cm-2]"] = self.results.get("Positive electrode active material volume loading [uL.cm-2]") or self.results.get("Positive electrode thickness [m]") * self.parameter_values.get("Positive electrode active material volume fraction") * 100000
        self.results["Positive electrode inactive material volume loading [uL.cm-2]"] = self.results.get("Positive electrode inactive material volume loading [uL.cm-2]") or self.results.get("Positive electrode thickness [m]") * (1 - self.parameter_values.get("Positive electrode active material volume fraction") - self.parameter_values.get("Positive electrode porosity")) * 100000
        self.results["Positive electrode electrolyte volume loading [uL.cm-2]"] = self.results.get("Positive electrode electrolyte volume loading [uL.cm-2]") or self.results.get("Positive electrode thickness [m]") * self.parameter_values.get("Positive electrode porosity") * 100000
        self.results["Positive current collector volume loading [uL.cm-2]"] = self.results.get("Positive current collector volume loading [uL.cm-2]") or self.results.get("Positive current collector thickness [m]") / 2 * 100000

        # mass loadings
        self.results["Negative current collector mass loading [mg.cm-2]"] = self.results.get("Negative current collector mass loading [mg.cm-2]") or self.results.get("Negative current collector volume loading [uL.cm-2]") * self.results.get("Negative current collector density [kg.m-3]") / 1000
        #print(self.results.get("Negative electrode active material true density [kg.m-3]"))
        #print(inputs.get("Negative electrode active material true density [kg.m-3]"))
        if self.parameter_values.get("Negative electrode active material volume fraction") + self.parameter_values.get("Negative electrode porosity") == 1:
                self.results["Negative electrode active material mass loading [mg.cm-2]"] = self.results.get("Negative electrode active material mass loading [mg.cm-2]") or self.results.get("Negative electrode active material volume loading [uL.cm-2]") * self.results.get("Negative electrode composite true density [kg.m-3]") / 1000
        elif (inputs.get("Negative electrode active material true density [kg.m-3]") == None) and (self.results.get("Negative electrode active material true density [kg.m-3]") == None):
                self.results["Negative electrode active material mass loading [mg.cm-2]"] = self.results["Negative electrode active material mass loading [mg.cm-2]"] or 0
                print("Warning: Missing 'Negative electrode active material true density [kg.m-3]'")
        else:
                self.results["Negative electrode active material mass loading [mg.cm-2]"] = self.results.get("Negative electrode active material mass loading [mg.cm-2]") or self.results.get("Negative electrode active material volume loading [uL.cm-2]") * (inputs.get("Negative electrode active material true density [kg.m-3]") or self.results.get("Negative electrode active material true density [kg.m-3]")) / 1000
        self.results["Negative electrode electrolyte mass loading [mg.cm-2]"] = self.results.get("Negative electrode electrolyte mass loading [mg.cm-2]") or self.results.get("Negative electrode electrolyte volume loading [uL.cm-2]") * self.results.get("Electrolyte density [kg.m-3]") / 1000
        self.results["Negative electrode inactive material mass loading [mg.cm-2]"] = self.results.get("Negative electrode inactive material mass loading [mg.cm-2]") or self.results.get("Negative electrode density [kg.m-3]") * self.results.get("Negative electrode thickness [m]") * 100 - self.results.get("Negative electrode active material mass loading [mg.cm-2]")
        self.results["Separator mass loading [mg.cm-2]"] = self.results.get("Separator mass loading [mg.cm-2]") or self.results.get("Separator volume loading [uL.cm-2]") * self.results.get("Separator density [kg.m-3]") / 1000
        self.results["Separator electrolyte mass loading [mg.cm-2]"] = self.results.get("Separator electrolyte mass loading [mg.cm-2]") or self.results.get("Separator electrolyte volume loading [uL.cm-2]") * self.results.get("Electrolyte density [kg.m-3]") / 1000
        if self.parameter_values.get("Positive electrode active material volume fraction") + self.parameter_values.get("Positive electrode porosity") == 1:
                    self.results["Positive electrode active material mass loading [mg.cm-2]"] = self.results.get("Positive electrode active material mass loading [mg.cm-2]") or self.results.get("Positive electrode active material volume loading [uL.cm-2]") * self.results.get("Positive electrode composite true density [kg.m-3]") / 1000
        elif (inputs.get("Positive electrode active material true density [kg.m-3]") == None) and (self.results.get("Positive electrode active material true density [kg.m-3]") == None):
                    self.results["Positive electrode active material mass loading [mg.cm-2]"] = self.results["Positive electrode active material mass loading [mg.cm-2]"] or 0
                    print("Warning: Missing 'Positive electrode active material true density [kg.m-3]'")
        else:
                    self.results["Positive electrode active material mass loading [mg.cm-2]"] = self.results.get("Positive electrode active material mass loading [mg.cm-2]") or self.results.get("Positive electrode active material volume loading [uL.cm-2]") * (inputs.get("Positive electrode active material true density [kg.m-3]") or self.results.get("Positive electrode active material true density [kg.m-3]")) / 1000
        self.results["Positive electrode electrolyte mass loading [mg.cm-2]"] = self.results.get("Positive electrode electrolyte mass loading [mg.cm-2]") or self.results.get("Positive electrode electrolyte volume loading [uL.cm-2]") * self.results.get("Electrolyte density [kg.m-3]") / 1000
        self.results["Positive electrode inactive material mass loading [mg.cm-2]"] = self.results.get("Positive electrode inactive material mass loading [mg.cm-2]") or self.results.get("Positive electrode density [kg.m-3]") * self.results.get("Positive electrode thickness [m]") * 100 - self.results.get("Positive electrode active material mass loading [mg.cm-2]")
        self.results["Positive current collector mass loading [mg.cm-2]"] = self.results.get("Positive current collector mass loading [mg.cm-2]") or self.results.get("Positive current collector volume loading [uL.cm-2]") * self.results.get("Positive current collector density [kg.m-3]") / 1000

        if print_values == True:
            print(self.results)

    def plot_stack_breakdown(self, inputs=None, print_values=False):

        if inputs is None:
            inputs = {}
        else:
            inputs = inputs

        if print_values == True:
            print_values = True
        else:
            print_values = False

        # call stack_breakdown
        self.stack_breakdown(inputs=inputs, print_values=print_values)

        heights = [
        self.results["Negative current collector mass loading [mg.cm-2]"]/2,
        self.results["Negative current collector mass loading [mg.cm-2]"]/2,
        self.results["Negative electrode active material mass loading [mg.cm-2]"],
        self.results["Negative electrode inactive material mass loading [mg.cm-2]"],
        self.results["Negative electrode electrolyte mass loading [mg.cm-2]"],
        self.results["Separator mass loading [mg.cm-2]"],
        self.results["Separator electrolyte mass loading [mg.cm-2]"],
        self.results["Positive electrode active material mass loading [mg.cm-2]"],
        self.results["Positive electrode inactive material mass loading [mg.cm-2]"],
        self.results["Positive electrode electrolyte mass loading [mg.cm-2]"],
        self.results["Positive current collector mass loading [mg.cm-2]"]/2,
        self.results["Positive current collector mass loading [mg.cm-2]"]/2
        ]
        widths = [
        self.results["Negative current collector volume loading [uL.cm-2]"]/2,
        self.results["Negative current collector volume loading [uL.cm-2]"]/2,
        self.results["Negative electrode active material volume loading [uL.cm-2]"],
        self.results["Negative electrode inactive material volume loading [uL.cm-2]"],
        self.results["Negative electrode electrolyte volume loading [uL.cm-2]"],
        self.results["Separator volume loading [uL.cm-2]"],
        self.results["Separator electrolyte volume loading [uL.cm-2]"],
        self.results["Positive electrode active material volume loading [uL.cm-2]"],
        self.results["Positive electrode inactive material volume loading [uL.cm-2]"],
        self.results["Positive electrode electrolyte volume loading [uL.cm-2]"],
        self.results["Positive current collector volume loading [uL.cm-2]"]/2,
        self.results["Positive current collector volume loading [uL.cm-2]"]/2
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

            if i == 2:
                second_rect = rect
            elif i == 4:
                fourth_rect = rect

        # Add transparent rectangles with dashed lines for the specified sets of rectangles
        rect_height_sum_0 = sum(heights[0:2])
        rect_width_sum_0 = sum(widths[0:2])
        transparent_rect_0 = patches.Rectangle((rectangles[0].get_x(), rectangles[0].get_y()), rect_width_sum_0, rect_height_sum_0,
                                               linewidth=1, linestyle='dashed', edgecolor='black', facecolor='none')
        ax.add_patch(transparent_rect_0)
    
        rect_height_sum_1 = sum(heights[2:5])
        transparent_rect_1 = patches.Rectangle((second_rect.get_x(), second_rect.get_y()), fourth_rect.get_x() + fourth_rect.get_width() - second_rect.get_x(), rect_height_sum_1,
                                           linewidth=1, linestyle='dashed', edgecolor='black', facecolor='none')
        ax.add_patch(transparent_rect_1)

        rect_height_sum_2 = sum(heights[5:7])
        fifth_rect = rectangles[5]
        transparent_rect_2 = patches.Rectangle((fifth_rect.get_x(), fifth_rect.get_y()), rectangles[6].get_x() + rectangles[6].get_width() - fifth_rect.get_x(), rect_height_sum_2,
                                           linewidth=1, linestyle='dashed', edgecolor='black', facecolor='none')
        ax.add_patch(transparent_rect_2)

        rect_height_sum_3 = sum(heights[7:10])
        rect_width_sum_3 = sum(widths[7:10])
        transparent_rect_3 = patches.Rectangle((rectangles[7].get_x(), rectangles[7].get_y()), rect_width_sum_3, rect_height_sum_3,
                                               linewidth=1, linestyle='dashed', edgecolor='black', facecolor='none')
        ax.add_patch(transparent_rect_3)

        rect_height_sum_4 = sum(heights[10:12])
        transparent_rect_4 = patches.Rectangle((rectangles[10].get_x(), rectangles[10].get_y()), rectangles[11].get_x() + rectangles[11].get_width() - rectangles[10].get_x(), rect_height_sum_4,
                                               linewidth=1, linestyle='dashed', edgecolor='black', facecolor='none')
        ax.add_patch(transparent_rect_4)

        # add vertical line
        ax.axvline(sum(widths[1:11]), color='black', linestyle='-')
        ax.axvline(0, color='black', linestyle='-')
    
        # Set the x-axis limits based on the maximum x position
        ax.set_xlim( - widths[0], x_pos)
        ax.set_ylim(0, max(rect_height_sum_1, rect_height_sum_2, rect_height_sum_3, rect_height_sum_4)*1.05) # 

        ax2 = ax.twiny()
        ax2.set_xlim( - widths[0]*10, x_pos*10)
        ax2.set_xlabel('Thickness [um]')

        # Add labels and title to the chart
        ax.set_xlabel('Volume loading [uL cm-2]')
        ax.set_ylabel('Mass loading [mg cm-2]')
        #ax.set_title('Connected Rectangles Chart')

        # Create a legend for the chart
        label_indexes = [i for i in range(1, len(labels)-1) if heights[i] != 0 and widths[i] != 0]
        legend_labels = [labels[i] for i in label_indexes]
        legend_handles = [patches.Patch(color=color, label=label) for color, label in zip(colors[1:-1], legend_labels)]
        ax.legend(handles=legend_handles, loc='upper left', bbox_to_anchor=(1.05, 1))

        # Display the chart
        plt.show()


param_lfp = pybamm.ParameterValues("Prada2013")
param_nmc = pybamm.ParameterValues("Chen2020")
param_nca = pybamm.ParameterValues("NCA_Kim2011")
param_lco = pybamm.ParameterValues("Marquis2019")
param_lco_ = pybamm.ParameterValues("Ramadass2004")

# no densities in Prada2013 (-> guess values)
results = {
     "Negative electrode density [kg.m-3]": 1675,  # Graphite
     "Positive electrode density [kg.m-3]": 2400,  # LFP
     "Separator density [kg.m-3]": 1000,
}

# no active material true densities in most parameter-sets -> create input data-sets?
# if active material volume fraction + porosity = 1
# active material true density = electrode composite "true" density
lfp_input_data = {
    "Negative electrode active material true density [kg.m-3]": 2230,  # Graphite
    "Positive electrode active material true density [kg.m-3]": 3600,  # LFP
}
lco_input_data = {
    "Negative electrode active material true density [kg.m-3]": 2230,  # Graphite
    "Positive electrode active material true density [kg.m-3]": 5050,  # LCO
}
nca_input_data = {
    "Negative electrode active material true density [kg.m-3]": 2230,  # Graphite
    "Positive electrode active material true density [kg.m-3]": 4450,  # NCA
}

print("Chen2020")
nmc = TEA(parameter_values=param_nmc)
energy_densities_NMC = nmc.stack_energy_densities(
    print_values = True
)
print("Volumetric stack energy density [Wh.L-1]: {}\nGravimetric stack energy density [Wh.kg-1]: {}".format(energy_densities_NMC[0], energy_densities_NMC[1]))
nmc.plot_stack_breakdown(print_values = True)

print("Prada2013")
lfp = TEA(parameter_values=param_lfp, results=results)
energy_densities_LFP = lfp.stack_energy_densities(
    inputs = lfp_input_data, print_values = True
)
print("Volumetric stack energy density [Wh.L-1]: {}\nGravimetric stack energy density [Wh.kg-1]: {}".format(energy_densities_LFP[0], energy_densities_LFP[1]))
lfp.plot_stack_breakdown(inputs = lfp_input_data, print_values = True)

print("Marquis2019")
lco = TEA(parameter_values=param_lco)
energy_densities_LCO = lco.stack_energy_densities(
    inputs = lco_input_data, print_values = True
)
print("Volumetric stack energy density [Wh.L-1]: {}\nGravimetric stack energy density [Wh.kg-1]: {}".format(energy_densities_LCO[0], energy_densities_LCO[1]))
lco.plot_stack_breakdown(inputs = lco_input_data, print_values = True)

print("Ramadas2004") #
lco_ = TEA(parameter_values=param_lco_)
energy_densities_LCO_ = lco_.stack_energy_densities(
    inputs = lco_input_data, print_values = True
)
print("Volumetric stack energy density [Wh.L-1]: {}\nGravimetric stack energy density [Wh.kg-1]: {}".format(energy_densities_LCO_[0], energy_densities_LCO_[1]))
lco_.plot_stack_breakdown(inputs = lco_input_data, print_values = True)

print("NCA_Kim2011") #
nca = TEA(parameter_values=param_nca)
energy_densities_NCA = nca.stack_energy_densities(
    inputs = nca_input_data, print_values = True
)
print("Volumetric stack energy density [Wh.L-1]: {}\nGravimetric stack energy density [Wh.kg-1]: {}".format(energy_densities_NCA[0], energy_densities_NCA[1]))
nca.plot_stack_breakdown(inputs = lco_input_data, print_values = True)