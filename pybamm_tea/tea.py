#
# TEA class
# 

import pybamm
import matplotlib.pyplot as plt
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

    @property
    def stack_breakdown(self):
        """A breakdown of volume- and mass loadings on stack level."""
        try:
            return self._stack_breakdown
        except AttributeError:
            self._stack_breakdown = self.calculate_stack_breakdown()
            return self._stack_breakdown
    
    @property
    def stack_breakdown_dataframe(self):
        """A dataframe with components, volume-, mass loadings and densities on stack level."""
        try:
            return self._stack_breakdown_dataframe
        except AttributeError:
            self._stack_breakdown_dataframe = self.print_stack_breakdown()
            return self._stack_breakdown_dataframe
        
    @property
    def stack_energy_densities(self):
        """Energy densities and parameters for calculation on stack level."""
        try:
            return self._stack_energy_densities
        except AttributeError:
            self._stack_energy_densities = self.calculate_stack_energy_densities()
            return self._stack_energy_densities
    
    def print_stack_breakdown(self):
        """A dataframe with components, volume-, mass loadings and densities on stack level."""
        stack_bd = self.stack_breakdown
        
        # Create a dataframe with columns for components, volume- and mass loadings and densities
        components = pd.DataFrame([c.replace(" volume loading [uL.cm-2]", "") for c in stack_bd.keys() if " volume loading [uL.cm-2]" in c], columns=["Components"])
        volumes = pd.DataFrame([stack_bd.get(f"{c} volume loading [uL.cm-2]") for c in components["Components"]], columns=["Volume loading [uL.cm-2]"])
        masses = pd.DataFrame([stack_bd.get(f"{c} mass loading [mg.cm-2]") for c in components["Components"]], columns=["Mass loading [mg.cm-2]"])
        densities = pd.DataFrame([stack_bd.get(f"{c} density [mg.uL-1]") for c in components["Components"]], columns=["Density [mg.uL-1]"])
        
        # Concatenate the dataframes side by side
        df = pd.concat([components, volumes, masses, densities], axis=1)
        df.set_index('Components', inplace=True)
        df.index.name = None
        return df

    def calculate_stack_energy_densities(self):
        """Calculate ideal volumetric and gravimetric energy densities on stack level."""
        stack_ed = {}  # stack energy densities dict
        pava = self.parameter_values  # parameter values

        # ocv's
        ne_ocv = pava["Negative electrode OCP [V]"]
        pe_ocv = pava["Positive electrode OCP [V]"]
        x0, x100, y100, y0 = pybamm.lithium_ion.get_min_max_stoichiometries(pava)
        soc = pybamm.linspace(0, 1)
        x = x0 + soc * (x100 - x0)
        y = y0 - soc * (y0 - y100)

        stack_ed["Negative electrode average OCP [V]"] = pava.get("Negative electrode average OCP [V]") or ne_ocv(x).entries.mean()
        stack_ed["Positive electrode average OCP [V]"] = pava.get("Positive electrode average OCP [V]") or pe_ocv(y).entries.mean()
        stack_ed["Stack average OCP [V]"] = pava.get("Stack average OCP [V]") or (stack_ed.get(
            "Positive electrode average OCP [V]") - stack_ed.get("Negative electrode average OCP [V]"))

        # areal capacity
        param = pybamm.LithiumIonParameters()
        esoh_solver = pybamm.lithium_ion.ElectrodeSOHSolver(
            pava, param
        )
        Q_n = pava.evaluate(param.n.Q_init)
        Q_p = pava.evaluate(param.p.Q_init)
        Q_Li = pava.evaluate(param.Q_Li_particles_init)
        inputs_ = {"Q_Li": Q_Li, "Q_n": Q_n, "Q_p": Q_p}
        sol = esoh_solver.solve(inputs_)
        stack_ed["Capacity [mA.h.cm-2]"] = pava.get("Capacity [mA.h.cm-2]") or sol["Capacity [mA.h.cm-2]"]

        # thicknesses
        compartments = ["Negative current collector", "Negative electrode", "Separator", "Positive electrode", "Positive current collector"]
        stack_ed["Stack thickness [m]"] = 0
        for compartment in compartments:
            if pava.get(f"{compartment} thickness [m]") is None:
                print(f"Warning: Missing '{compartment} thickness [m]'")
            elif "current collector" in compartment:
                stack_ed["Stack thickness [m]"] += pava.get(f"{compartment} thickness [m]") / 2
            else:
                stack_ed["Stack thickness [m]"] += pava.get(f"{compartment} thickness [m]")
        
        # volumetric stack capacity in [Ah.L-1]
        stack_ed["Volumetric stack capacity [Ah.L-1]"] = stack_ed.get("Capacity [mA.h.cm-2]") / stack_ed.get("Stack thickness [m]") / 100
        
        # volumetric stack energy density in [Wh.L-1]
        stack_ed["Volumetric stack energy density [Wh.L-1]"] = stack_ed.get("Stack average OCP [V]") * stack_ed["Volumetric stack capacity [Ah.L-1]"]
        
        # stack density
        stack_ed["Stack density [kg.m-3]"] = 0
        for compartment in compartments:
            if pava.get(f"{compartment} density [kg.m-3]") is None:
                print(f"Warning: Missing '{compartment} density [kg.m-3]'")
            else:
                stack_ed[f"{compartment} density [kg.m-3]"] = pava.get(f"{compartment} density [kg.m-3]")
            if "current collector" in compartment:
                stack_ed["Stack density [kg.m-3]"] += pava.get(f"{compartment} thickness [m]") / 2 * pava.get(f"{compartment} density [kg.m-3]")
            else:
                stack_ed["Stack density [kg.m-3]"] += pava.get(f"{compartment} thickness [m]") * pava.get(f"{compartment} density [kg.m-3]")
        stack_ed["Stack density [kg.m-3]"] = stack_ed.get("Stack density [kg.m-3]") / stack_ed.get("Stack thickness [m]")

        # gravimetric stack energy density in [Ah.kg-1]
        stack_ed["Gravimetric stack capacity [Ah.kg-1]"] = stack_ed.get(
            "Volumetric stack capacity [Ah.L-1]") / stack_ed.get("Stack density [kg.m-3]") * 1000
        
        # gravimetric stack energy density in [Wh.kg-1]
        stack_ed["Gravimetric stack energy density [Wh.kg-1]"] = stack_ed.get(
            "Volumetric stack energy density [Wh.L-1]") / stack_ed.get("Stack density [kg.m-3]") * 1000

        return stack_ed

    def calculate_stack_breakdown(self):
        """Breakdown volume- and mass loadings on stack level."""
        stack_bd = {}  # stack energy densities dict
        pava = self.parameter_values  # parameter values

        # volume fractions
        for charge in ["Negative", "Positive"]:
            stack_bd[f"{charge} electrode electrolyte volume fraction"] = pava.get(f"{charge} electrode porosity")
            stack_bd[f"{charge} electrode active material volume fraction"] = pava.get(f"{charge} electrode active material volume fraction")
            stack_bd[f"{charge} electrode inactive material volume fraction"] = 1 - stack_bd.get(f"{charge} electrode electrolyte volume fraction") - stack_bd.get(f"{charge} electrode active material volume fraction")
            stack_bd[f"{charge} electrode dry volume fraction"] = 1
        stack_bd["Separator electrolyte volume fraction"] = pava.get("Separator porosity")
        stack_bd["Separator dry volume fraction"] = 1 - stack_bd.get("Separator electrolyte volume fraction")

        # volume loadings
        for components in list(stack_bd.keys()):
            if "Negative" in components:
                stack_bd[components.replace(" volume fraction", " volume loading [uL.cm-2]")] = stack_bd.get(components) * pava.get("Negative electrode thickness [m]") * 100000
            elif "Positive" in components:
                stack_bd[components.replace(" volume fraction", " volume loading [uL.cm-2]")] = stack_bd.get(components) * pava.get("Positive electrode thickness [m]") * 100000
            elif "Separator" in components:
                stack_bd[components.replace(" volume fraction", " volume loading [uL.cm-2]")] = stack_bd.get(components) * pava.get("Separator thickness [m]") * 100000
        stack_bd["Negative current collector volume loading [uL.cm-2]"] = pava.get("Negative current collector thickness [m]", 0) * 100000
        stack_bd["Positive current collector volume loading [uL.cm-2]"] = pava.get("Positive current collector thickness [m]", 0) * 100000

        # densities
        for charge in ["Negative", "Positive"]:
            stack_bd[f"{charge} electrode electrolyte density [mg.uL-1]"] = pava.get("Electrolyte density [kg.m-3]",0) / 1000
            stack_bd[f"{charge} electrode dry density [mg.uL-1]"] = (pava.get(f"{charge} electrode density [kg.m-3]",0)
            - pava.get(f"{charge} electrode porosity") * pava.get("Electrolyte density [kg.m-3]",0)) / 1000
            if stack_bd.get(f"{charge} electrode inactive material volume fraction") == 0:
                stack_bd[f"{charge} electrode inactive material density [mg.uL-1]"] = 0
                stack_bd[f"{charge} electrode active material density [mg.uL-1]"] = stack_bd[f"{charge} electrode dry density [mg.uL-1]"]
            else:
                stack_bd[f"{charge} electrode inactive material density [mg.uL-1]"] = (
                    pava.get(f"{charge} electrode density [kg.m-3]",0) - 
                    pava.get(f"{charge} electrode porosity") * pava.get("Electrolyte density [kg.m-3]",0) - 
                    pava.get(f"{charge} electrode active material volume fraction",0) * 
                    pava.get(f"{charge} electrode active material density [kg.m-3]",0)
                ) / stack_bd.get(f"{charge} electrode inactive material volume fraction") / 1000
                stack_bd[f"{charge} electrode active material density [mg.uL-1]"] = pava.get(f"{charge} electrode active material density [kg.m-3]",0) / 1000
        stack_bd["Separator electrolyte density [mg.uL-1]"] = pava.get("Electrolyte density [kg.m-3]",0) / 1000
        if pava.get("Separator porosity") == 1:
            stack_bd["Separator dry density [mg.uL-1]"] = 0
        else:
            stack_bd["Separator dry density [mg.uL-1]"] = (pava.get("Separator density [kg.m-3]",0) - pava.get("Separator porosity") * pava.get("Electrolyte density [kg.m-3]",0)) / (1 - pava.get("Separator porosity")) / 1000
        stack_bd["Negative current collector density [mg.uL-1]"] = pava.get("Negative current collector density [kg.m-3]",0) / 1000
        stack_bd["Positive current collector density [mg.uL-1]"] = pava.get("Positive current collector density [kg.m-3]",0) / 1000

        if pava.get("Electrolyte density [kg.m-3]") is None:
            print("Error: Missing 'Electrolyte density [kg.m-3]'")
        if pava.get("Negative current collector density [kg.m-3]") is None:
            print("Error: Missing 'Negative current collector density [kg.m-3]'")
        if pava.get("Positive current collector density [kg.m-3]") is None:
            print("Error: Missing 'Positive current collector density [kg.m-3]'")
        if pava.get("Negative electrode density [kg.m-3]") is None:
            print("Error: Missing 'Negative electrode density [kg.m-3]'")
        if pava.get("Negative electrode active material density [kg.m-3]") is None:
            print("Error: Missing 'Negative electrode active material density [kg.m-3]'")
        if pava.get("Positive electrode density [kg.m-3]") is None:
            print("Error: Missing 'Positive electrode density [kg.m-3]'")
        if pava.get("Positive electrode active material density [kg.m-3]") is None:
            print("Error: Missing 'Positive electrode active material density [kg.m-3]'")
        if pava.get("Separator density [kg.m-3]") is None:
            print("Error: Missing 'Separator density [kg.m-3]'")

        # mass loadings
        for components in list(stack_bd.keys()):
            if " volume loading [uL.cm-2]" in components:
                stack_bd[components.replace(" volume loading [uL.cm-2]", " mass loading [mg.cm-2]")] = stack_bd.get(components) * stack_bd.get(components.replace(" volume loading [uL.cm-2]", " density [mg.uL-1]"))

        return stack_bd

    def plot_stack_breakdown(self):

        stack_bd = self.stack_breakdown

        heights = [
        stack_bd["Negative current collector mass loading [mg.cm-2]"]/2,
        stack_bd["Negative current collector mass loading [mg.cm-2]"]/2,
        stack_bd["Negative electrode active material mass loading [mg.cm-2]"],
        stack_bd["Negative electrode inactive material mass loading [mg.cm-2]"],
        stack_bd["Negative electrode electrolyte mass loading [mg.cm-2]"],
        stack_bd["Separator dry mass loading [mg.cm-2]"],
        stack_bd["Separator electrolyte mass loading [mg.cm-2]"],
        stack_bd["Positive electrode active material mass loading [mg.cm-2]"],
        stack_bd["Positive electrode inactive material mass loading [mg.cm-2]"],
        stack_bd["Positive electrode electrolyte mass loading [mg.cm-2]"],
        stack_bd["Positive current collector mass loading [mg.cm-2]"]/2,
        stack_bd["Positive current collector mass loading [mg.cm-2]"]/2
        ]
        widths = [
        stack_bd["Negative current collector volume loading [uL.cm-2]"]/2,
        stack_bd["Negative current collector volume loading [uL.cm-2]"]/2,
        stack_bd["Negative electrode active material volume loading [uL.cm-2]"],
        stack_bd["Negative electrode inactive material volume loading [uL.cm-2]"],
        stack_bd["Negative electrode electrolyte volume loading [uL.cm-2]"],
        stack_bd["Separator dry volume loading [uL.cm-2]"],
        stack_bd["Separator electrolyte volume loading [uL.cm-2]"],
        stack_bd["Positive electrode active material volume loading [uL.cm-2]"],
        stack_bd["Positive electrode inactive material volume loading [uL.cm-2]"],
        stack_bd["Positive electrode electrolyte volume loading [uL.cm-2]"],
        stack_bd["Positive current collector volume loading [uL.cm-2]"]/2,
        stack_bd["Positive current collector volume loading [uL.cm-2]"]/2
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

        # Return the figure and axis objects
        return fig