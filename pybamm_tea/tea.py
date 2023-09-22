#
# TEA class
#

import pybamm
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import pandas as pd


class TEA:
    """
    A Techno-Economic Analysis class for estimation of cell metrics.

    Parameters
    ----------
    parameter_values : :class:pybamm.ParameterValues, optional
        A dictionary of parameters and their corresponding numerical values.
    inputs : dict
        A dictionary of inputs (additional parameters) and their corresponding
        numerical values.
    """

    def __init__(self, parameter_values=None, inputs=None):
        self.parameter_values = parameter_values or pybamm.ParameterValues({})
        self.inputs = inputs or {}

        # Update parameter values with inputs
        self.parameter_values.update(self.inputs, check_already_exists=False)
        pava = self.parameter_values

        # Raise error if electrolyte density is missing
        if pava.get("Electrolyte density [kg.m-3]") is None:
            raise ValueError(
                "The parameter 'Electrolyte density [kg.m-3]' must be provided"
            )

        # Update inactive material density, active material volume fraction, dry
        # density, density, maximum concentration in/excluding non-stoichiometric
        # loss of capacity
        if pava.get("Separator dry density [kg.m-3]") is not None:
            pava["Separator density [kg.m-3]"] = pava.get(
                "Separator porosity"
            ) * pava.get("Electrolyte density [kg.m-3]", 0) + (
                1 - pava.get("Separator porosity")
            ) * pava.get(
                "Separator dry density [kg.m-3]", 0
            )
        electrodes = ["Negative electrode", "Positive electrode"]
        for electrode in electrodes:
            if (
                pava.get(f"{electrode} binder dry mass fraction") is not None
                and pava.get(f"{electrode} conductive additive dry mass fraction")
                is not None
                and pava.get(f"{electrode} binder density [kg.m-3]") is not None
                and pava.get(f"{electrode} conductive additive density [kg.m-3]")
                is not None
            ):
                pava[f"{electrode} active material dry mass fraction"] = (
                    1
                    - pava.get(f"{electrode} binder dry mass fraction")
                    - pava.get(f"{electrode} conductive additive dry mass fraction")
                )
                pava[f"{electrode} inactive material density [kg.m-3]"] = (
                    pava.get(f"{electrode} binder dry mass fraction")
                    + pava.get(f"{electrode} conductive additive dry mass fraction")
                ) / (
                    pava.get(f"{electrode} binder dry mass fraction")
                    / pava.get(f"{electrode} binder density [kg.m-3]")
                    + pava.get(f"{electrode} conductive additive dry mass fraction")
                    / pava.get(f"{electrode} conductive additive density [kg.m-3]")
                )
            if (
                pava.get(f"{electrode} active material dry mass fraction") is not None
                and pava.get(f"{electrode} active material density [kg.m-3]")
                is not None
                and pava.get(f"{electrode} inactive material density [kg.m-3]")
                is not None
            ):
                pava[f"{electrode} active material volume fraction"] = (
                    1 - pava.get(f"{electrode} porosity")
                ) * (
                    pava.get(f"{electrode} active material dry mass fraction")
                    / pava.get(f"{electrode} active material density [kg.m-3]")
                    / (
                        pava.get(f"{electrode} active material dry mass fraction")
                        / pava.get(f"{electrode} active material density [kg.m-3]")
                        + (
                            1
                            - pava.get(f"{electrode} active material dry mass fraction")
                        )
                        / pava.get(f"{electrode} inactive material density [kg.m-3]")
                    )
                )
                pava[f"{electrode} dry density [kg.m-3]"] = pava.get(
                    f"{electrode} active material volume fraction"
                ) * pava.get(f"{electrode} active material density [kg.m-3]") + (
                    1
                    - pava.get(f"{electrode} active material volume fraction")
                    - pava.get(f"{electrode} porosity")
                ) * pava.get(
                    f"{electrode} inactive material density [kg.m-3]"
                )
                pava[f"{electrode} density [kg.m-3]"] = pava.get(
                    f"{electrode} dry density [kg.m-3]"
                ) + pava.get(f"{electrode} porosity") * pava.get(
                    "Electrolyte density [kg.m-3]"
                )
            if (
                pava.get(f"{electrode} active material capacity [mAh.g-1]") is not None
                and pava.get(f"{electrode} active material density [kg.m-3]")
                is not None
            ):
                if electrode == "Negative electrode":
                    pava["Maximum concentration in negative electrode [mol.m-3]"] = (
                        pava.get(f"{electrode} active material capacity [mAh.g-1]")
                        * pava.get(f"{electrode} active material density [kg.m-3]")
                        * 3600
                        / 96485
                    )
                elif electrode == "Positive electrode":
                    pava["Maximum concentration in positive electrode [mol.m-3]"] = (
                        pava.get(f"{electrode} active material capacity [mAh.g-1]")
                        * pava.get(f"{electrode} active material density [kg.m-3]")
                        * 3600
                        / 96485
                    )
            if pava.get(f"{electrode} non-stoichiometric loss of capacity") is not None:
                if electrode == "Negative electrode":
                    pava[
                        "Maximum concentration in negative electrode [mol.m-3]"
                    ] = pava.get(
                        "Maximum concentration in negative electrode [mol.m-3]"
                    ) * (
                        1
                        - pava.get(
                            f"{electrode} non-stoichiometric loss of capacity", 0
                        )
                    )
                elif electrode == "Positive electrode":
                    pava[
                        "Maximum concentration in positive electrode [mol.m-3]"
                    ] = pava.get(
                        "Maximum concentration in positive electrode [mol.m-3]"
                    ) * (
                        1
                        - pava.get(
                            f"{electrode} non-stoichiometric loss of capacity", 0
                        )
                    )
            self.parameter_values.update(pava, check_already_exists=False)

    @property
    def stack_breakdown(self):
        """A breakdown of volume- and mass- loadings on stack level."""
        try:
            return self._stack_breakdown
        except AttributeError:
            self._stack_breakdown = self.calculate_stack_breakdown()
            return self._stack_breakdown

    @property
    def stack_breakdown_dataframe(self):
        """
        A dataframe with components, volume-, mass- loadings and densities on stack
        level.
        """
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
        """
        A dataframe with components, volume-, mass loadings and densities on stack
        level.
        """
        stack_bd = self.stack_breakdown

        # Create a dataframe with columns for components, volume- and mass loadings
        # and densities
        components = pd.DataFrame(
            [
                c.replace(" volume loading [uL.cm-2]", "")
                for c in stack_bd.keys()
                if " volume loading [uL.cm-2]" in c
            ],
            columns=["Components"],
        )
        volumes = pd.DataFrame(
            [
                stack_bd.get(f"{c} volume loading [uL.cm-2]")
                for c in components["Components"]
            ],
            columns=["Volume loading [uL.cm-2]"],
        )
        masses = pd.DataFrame(
            [
                stack_bd.get(f"{c} mass loading [mg.cm-2]")
                for c in components["Components"]
            ],
            columns=["Mass loading [mg.cm-2]"],
        )
        densities = pd.DataFrame(
            [stack_bd.get(f"{c} density [mg.uL-1]") for c in components["Components"]],
            columns=["Density [mg.uL-1]"],
        )

        # Concatenate the dataframes side by side
        df = pd.concat([components, volumes, masses, densities], axis=1)
        df.set_index("Components", inplace=True)
        df.index.name = None
        return df

    def calculate_stack_energy_densities(self):
        """
        Calculate ideal volumetric and gravimetric energy densities on stack
        level.
        """
        stack_ed = {}  # stack energy densities dict
        pava = self.parameter_values  # parameter values

        # stoichiometries at 0 and 100% SOC
        try:
            x0, x100, y100, y0 = pybamm.lithium_ion.get_min_max_stoichiometries(pava)
        except:
            x0, x100, y100, y0 = 0, 1, 0, 1

        # theoretical min&max stoichiometries, in negative electrode assumed to be 1
        # eq 27 of Weng2023:
        # Q_n_excess = Q_n * (1 - x_100) -> NPR_practical = 1 + Q_n_excess / Q
        stack_ed["Negative electrode minimum stoichiometry"] = pava.get(
            "Negative electrode minimum stoichiometry", x0
        )
        stack_ed["Negative electrode maximum stoichiometry"] = pava.get(
            "Negative electrode maximum stoichiometry", 1
        )
        stack_ed["Positive electrode minimum stoichiometry"] = pava.get(
            "Positive electrode minimum stoichiometry", y100
        )
        stack_ed["Positive electrode maximum stoichiometry"] = pava.get(
            "Positive electrode maximum stoichiometry", y0
        )

        # electrode total capacities
        if pava.get("Negative electrode practical capacity [mA.h.cm-2]") is None:
            stack_ed["Negative electrode capacity [mA.h.cm-2]"] = pava.get(
                "Negative electrode capacity [mA.h.cm-2]"
            ) or (
                pava.get("Maximum concentration in negative electrode [mol.m-3]")
                * 96485
                / 3.6
                / 10000
                * pava.get(  # C.mol-1 * mA.h.C-1 * m2.cm-2
                    "Negative electrode active material volume fraction"
                )
                * pava.get("Negative electrode thickness [m]")
            )
        if pava.get("Positive electrode practical capacity [mA.h.cm-2]") is None:
            stack_ed["Positive electrode capacity [mA.h.cm-2]"] = pava.get(
                "Positive electrode capacity [mA.h.cm-2]"
            ) or (
                pava.get("Maximum concentration in positive electrode [mol.m-3]")
                * 96485
                / 3.6
                / 10000
                * pava.get(  # C.mol-1 * mA.h.C-1 * m2.cm-2
                    "Positive electrode active material volume fraction"
                )
                * pava.get("Positive electrode thickness [m]")
            )

        # electrode practical capacities
        electrodes = ["Negative electrode", "Positive electrode"]
        for electrode in electrodes:
            stack_ed[f"{electrode} practical capacity [mA.h.cm-2]"] = pava.get(
                f"{electrode} practical capacity [mA.h.cm-2]"
            ) or (
                stack_ed.get(f"{electrode} capacity [mA.h.cm-2]")
                * (
                    stack_ed.get(f"{electrode} maximum stoichiometry")
                    - stack_ed.get(f"{electrode} minimum stoichiometry")
                )
            )

        # practical n/p ratio
        stack_ed["Practical n/p ratio"] = stack_ed.get(
            "Negative electrode practical capacity [mA.h.cm-2]"
        ) / stack_ed.get("Positive electrode practical capacity [mA.h.cm-2]")

        # stack total capacity
        stack_ed["Capacity [mA.h.cm-2]"] = min(
            stack_ed.get("Negative electrode practical capacity [mA.h.cm-2]"),
            stack_ed.get("Positive electrode practical capacity [mA.h.cm-2]"),
        )

        # check if an ocp function is supplied
        if pava.get("Negative electrode OCP [V]") is not None:
            ne_ocv = pava["Negative electrode OCP [V]"]
            pe_ocv = pava["Positive electrode OCP [V]"]
            soc = pybamm.linspace(0, 1)
            x = x0 + soc * (x100 - x0)
            y = y0 - soc * (y0 - y100)

        # ocp's
        if pava.get("Negative electrode average OCP [V]") is None:
            stack_ed["Negative electrode average OCP [V]"] = ne_ocv(x).evaluate().mean()
        else:
            stack_ed["Negative electrode average OCP [V]"] = pava.get(
                "Negative electrode average OCP [V]"
            )
        if pava.get("Positive electrode average OCP [V]") is None:
            stack_ed["Positive electrode average OCP [V]"] = pe_ocv(y).evaluate().mean()
        else:
            stack_ed["Positive electrode average OCP [V]"] = pava.get(
                "Positive electrode average OCP [V]"
            )
        if pava.get("Stack average OCP [V]") is None:
            stack_ed["Stack average OCP [V]"] = stack_ed.get(
                "Positive electrode average OCP [V]"
            ) - stack_ed.get("Negative electrode average OCP [V]")
        else:
            stack_ed["Stack average OCP [V]"] = pava.get("Stack average OCP [V]")

        # thicknesses
        compartments = [
            "Negative current collector",
            "Negative electrode",
            "Separator",
            "Positive electrode",
            "Positive current collector",
        ]
        stack_ed["Stack thickness [m]"] = 0
        for compartment in compartments:
            if pava.get(f"{compartment} thickness [m]") is None:
                print(f"Warning: Missing '{compartment} thickness [m]'")
            elif "current collector" in compartment:
                stack_ed["Stack thickness [m]"] += (
                    pava.get(f"{compartment} thickness [m]") / 2
                )
            else:
                stack_ed["Stack thickness [m]"] += pava.get(
                    f"{compartment} thickness [m]"
                )

        # volumetric stack capacity in [Ah.L-1]
        stack_ed["Volumetric stack capacity [Ah.L-1]"] = (
            stack_ed.get("Capacity [mA.h.cm-2]")
            / stack_ed.get("Stack thickness [m]")
            / 100
        )

        # volumetric stack energy density in [Wh.L-1]
        stack_ed["Volumetric stack energy density [Wh.L-1]"] = (
            stack_ed.get("Stack average OCP [V]")
            * stack_ed["Volumetric stack capacity [Ah.L-1]"]
        )

        # stack density
        stack_ed["Stack density [kg.m-3]"] = 0
        for compartment in compartments:
            if pava.get(f"{compartment} density [kg.m-3]") is None:
                print(f"Warning: Missing '{compartment} density [kg.m-3]'")
            else:
                stack_ed[f"{compartment} density [kg.m-3]"] = pava.get(
                    f"{compartment} density [kg.m-3]"
                )
            if "current collector" in compartment:
                stack_ed["Stack density [kg.m-3]"] += (
                    pava.get(f"{compartment} thickness [m]")
                    / 2
                    * pava.get(f"{compartment} density [kg.m-3]")
                )
            else:
                stack_ed["Stack density [kg.m-3]"] += pava.get(
                    f"{compartment} thickness [m]"
                ) * pava.get(f"{compartment} density [kg.m-3]")
        stack_ed["Stack density [kg.m-3]"] = stack_ed.get(
            "Stack density [kg.m-3]"
        ) / stack_ed.get("Stack thickness [m]")

        # gravimetric stack capacity in [Ah.L-1]
        stack_ed["Gravimetric stack capacity [Ah.kg-1]"] = (
            stack_ed.get("Volumetric stack capacity [Ah.L-1]")
            / stack_ed.get("Stack density [kg.m-3]")
            * 1000
        )

        # gravimetric stack energy density in [Wh.kg-1]
        stack_ed["Gravimetric stack energy density [Wh.kg-1]"] = (
            stack_ed.get("Volumetric stack energy density [Wh.L-1]")
            / stack_ed.get("Stack density [kg.m-3]")
            * 1000
        )

        return stack_ed

    def calculate_stack_breakdown(self):
        """Breakdown volume- and mass loadings on stack level."""
        stack_bd = {}  # stack energy densities dict
        pava = self.parameter_values  # parameter values

        # volume fractions
        for electrode in ["Negative electrode", "Positive electrode"]:
            stack_bd[f"{electrode} electrolyte volume fraction"] = pava.get(
                f"{electrode} porosity"
            )
            stack_bd[f"{electrode} active material volume fraction"] = pava.get(
                f"{electrode} active material volume fraction"
            )
            stack_bd[f"{electrode} inactive material volume fraction"] = (
                1
                - stack_bd.get(f"{electrode} electrolyte volume fraction")
                - stack_bd.get(f"{electrode} active material volume fraction")
            )
            stack_bd[f"{electrode} dry volume fraction"] = 1
            stack_bd[f"{electrode} volume fraction"] = 1
        stack_bd["Separator electrolyte volume fraction"] = pava.get(
            "Separator porosity"
        )
        stack_bd["Separator dry volume fraction"] = 1 - stack_bd.get(
            "Separator electrolyte volume fraction"
        )
        stack_bd["Separator volume fraction"] = 1

        # volume loadings
        for components in list(stack_bd.keys()):
            if "Negative" in components:
                stack_bd[
                    components.replace(" volume fraction", " volume loading [uL.cm-2]")
                ] = (
                    stack_bd.get(components)
                    * pava.get("Negative electrode thickness [m]")
                    * 100000
                )
            elif "Positive" in components:
                stack_bd[
                    components.replace(" volume fraction", " volume loading [uL.cm-2]")
                ] = (
                    stack_bd.get(components)
                    * pava.get("Positive electrode thickness [m]")
                    * 100000
                )
            elif "Separator" in components:
                stack_bd[
                    components.replace(" volume fraction", " volume loading [uL.cm-2]")
                ] = (
                    stack_bd.get(components)
                    * pava.get("Separator thickness [m]")
                    * 100000
                )
        stack_bd["Negative current collector volume loading [uL.cm-2]"] = (
            pava.get("Negative current collector thickness [m]", 0) * 100000
        )
        stack_bd["Positive current collector volume loading [uL.cm-2]"] = (
            pava.get("Positive current collector thickness [m]", 0) * 100000
        )

        # densities
        for electrode in ["Negative electrode", "Positive electrode"]:
            for component in ["", " active material"]:
                if pava.get(f"{electrode}{component} density [kg.m-3]") is None:
                    raise ValueError(
                        f"Warning: Missing '{electrode}{component} density [kg.m-3]'"
                    )
        for component in [
            "Separator",
            "Negative current collector",
            "Positive current collector",
        ]:
            if pava.get(f"{component} density [kg.m-3]") is None:
                raise ValueError(f"Warning: Missing '{component} density [kg.m-3]'")

        for electrode in ["Negative electrode", "Positive electrode"]:
            stack_bd[f"{electrode} electrolyte density [mg.uL-1]"] = (
                pava.get("Electrolyte density [kg.m-3]", 0) / 1000
            )
            stack_bd[f"{electrode} density [mg.uL-1]"] = (
                pava.get(f"{electrode} density [kg.m-3]", 0) / 1000
            )
            stack_bd[f"{electrode} dry density [mg.uL-1]"] = (
                pava.get(f"{electrode} density [kg.m-3]", 0)
                - pava.get(f"{electrode} porosity")
                * pava.get("Electrolyte density [kg.m-3]", 0)
            ) / 1000
            if stack_bd.get(f"{electrode} inactive material volume fraction") == 0:
                stack_bd[f"{electrode} inactive material density [mg.uL-1]"] = 0
                stack_bd[f"{electrode} active material density [mg.uL-1]"] = stack_bd[
                    f"{electrode} dry density [mg.uL-1]"
                ]
            else:
                stack_bd[f"{electrode} inactive material density [mg.uL-1]"] = (
                    (
                        pava.get(f"{electrode} density [kg.m-3]", 0)
                        - pava.get(f"{electrode} porosity")
                        * pava.get("Electrolyte density [kg.m-3]", 0)
                        - pava.get(f"{electrode} active material volume fraction", 0)
                        * pava.get(f"{electrode} active material density [kg.m-3]", 0)
                    )
                    / stack_bd.get(f"{electrode} inactive material volume fraction")
                    / 1000
                )
                stack_bd[f"{electrode} active material density [mg.uL-1]"] = (
                    pava.get(f"{electrode} active material density [kg.m-3]", 0) / 1000
                )
        stack_bd["Separator electrolyte density [mg.uL-1]"] = (
            pava.get("Electrolyte density [kg.m-3]", 0) / 1000
        )
        stack_bd["Separator density [mg.uL-1]"] = (
            pava.get("Separator density [kg.m-3]", 0) / 1000
        )
        if pava.get("Separator porosity") == 1:
            stack_bd["Separator dry density [mg.uL-1]"] = 0
        else:
            stack_bd["Separator dry density [mg.uL-1]"] = (
                (
                    pava.get("Separator density [kg.m-3]", 0)
                    - pava.get("Separator porosity")
                    * pava.get("Electrolyte density [kg.m-3]", 0)
                )
                / (1 - pava.get("Separator porosity"))
                / 1000
            )
        stack_bd["Negative current collector density [mg.uL-1]"] = (
            pava.get("Negative current collector density [kg.m-3]", 0) / 1000
        )
        stack_bd["Positive current collector density [mg.uL-1]"] = (
            pava.get("Positive current collector density [kg.m-3]", 0) / 1000
        )

        # mass loadings
        for components in list(stack_bd.keys()):
            if " volume loading [uL.cm-2]" in components:
                stack_bd[
                    components.replace(
                        " volume loading [uL.cm-2]", " mass loading [mg.cm-2]"
                    )
                ] = stack_bd.get(components) * stack_bd.get(
                    components.replace(
                        " volume loading [uL.cm-2]", " density [mg.uL-1]"
                    )
                )

        return stack_bd

    def plot_stack_breakdown(self):
        """
        Plot a breakdown of volume- and mass- loadings on stack level.
        """
        stack_bd = self.stack_breakdown

        # Data for colored rectangle heights, widths, labels, and colors
        components = [
            "Negative current collector",
            "Negative current collector",
            "Negative electrode active material",
            "Negative electrode inactive material",
            "Negative electrode electrolyte",
            "Separator dry",
            "Separator electrolyte",
            "Positive electrode active material",
            "Positive electrode inactive material",
            "Positive electrode electrolyte",
            "Positive current collector",
            "Positive current collector",
        ]

        heights = []
        widths = []
        labels = []
        for component in components:
            heights.append(stack_bd.get(f"{component} mass loading [mg.cm-2]"))
            widths.append(stack_bd.get(f"{component} volume loading [uL.cm-2]"))
            labels.append(component)
        for i in [0, 1, 10, 11]:  # half cc's out of stack
            heights[i] = heights[i] / 2
            widths[i] = widths[i] / 2
        for i in [0, 11]:  # no label for the half cc's out of stack
            labels[i] = None

        # RGB + transparency
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
            (1, 0, 0, 0.5),
        ]

        # Data for transparent rectangle heights and widths
        components = [
            "Negative current collector",
            "Negative electrode",
            "Separator",
            "Positive electrode",
            "Positive current collector",
        ]

        compartment_heights = []
        compartment_widths = []

        for component in components:
            compartment_heights.append(
                stack_bd.get(f"{component} mass loading [mg.cm-2]")
            )
            compartment_widths.append(
                stack_bd.get(f"{component} volume loading [uL.cm-2]")
            )

        # Set up the figure and axis objects
        fig = plt.figure(figsize=(8, 4), facecolor="white")
        ax = fig.add_axes([0.1, 0.25, 0.8, 0.6])

        # Initialize the x position
        x_pos = -widths[0]

        # Add the colored rectangles to the plot
        for i, (h, w, color) in enumerate(zip(heights, widths, colors)):
            rect = patches.Rectangle(
                (x_pos, 0), w, h, linewidth=1, edgecolor="black", facecolor=color
            )
            ax.add_patch(rect)
            x_pos += w

        # Initialize the x position
        x_pos = -widths[0]

        # Add the transparent rectangles to the plot
        for i, (h, w) in enumerate(zip(compartment_heights, compartment_widths)):
            rect = patches.Rectangle(
                (x_pos, 0),
                w,
                h,
                linewidth=1,
                linestyle="dashed",
                edgecolor="black",
                facecolor="none",
            )
            ax.add_patch(rect)
            x_pos += w

        # add vertical line
        ax.axvline(sum(widths[1:11]), color="black", linestyle="-")
        ax.axvline(0, color="black", linestyle="-")

        # Set the x-axis limits based on the maximum x position
        ax.set_xlim(-widths[0], x_pos)
        ax.set_ylim(0, max(compartment_heights) * 1.05)

        ax2 = ax.twiny()
        ax2.set_xlim(-widths[0] * 10, x_pos * 10)
        ax2.set_xlabel("Thickness [um]")

        # Add labels and title to the chart
        ax.set_xlabel("Volume loading [uL cm-2]")
        ax.set_ylabel("Mass loading [mg cm-2]")

        # Create a legend for the chart
        label_indexes = [
            i for i in range(1, len(labels) - 1) if heights[i] != 0 and widths[i] != 0
        ]
        legend_labels = [labels[i] for i in label_indexes]
        legend_handles = [
            patches.Patch(color=color, label=label)
            for color, label in zip(colors[1:-1], legend_labels)
        ]
        ax.legend(handles=legend_handles, loc="upper left", bbox_to_anchor=(1.05, 1))

        # Display the chart
        plt.show()

        # Return the figure and axis objects
        return fig
