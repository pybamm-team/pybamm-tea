#
# TEA class
#

import pybamm
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import pandas as pd
import warnings


class TEA:
    """
    A Techno-Economic Analysis class for estimation of cell metrics.

    Parameters
    ----------
    parameter_values : dict
        A dictionary of parameters and their corresponding numerical values.
        Default is NoneParameters
    inputs : dict, optional
        A dictionary of inputs and their corresponding numerical values.
        Default is None.
    """

    def __init__(self, parameter_values=None, inputs=None):
        """Initialize class by updating parameters with inputs."""
        self.inputs_ = inputs.copy() if inputs else {}
        self.parameter_values_ = parameter_values.copy() if parameter_values else {}
        self._reset_attributes()

    def __call__(self):
        """Reset all attributes to their initial values and update with new inputs."""
        self._reset_attributes()

    def _reset_attributes(self):
        """Reset all attributes to their initial values and update with new inputs."""
        self.parameter_values = pybamm.ParameterValues({})
        self.parameter_values = {**self.parameter_values, **self.parameter_values_}
        self.parameter_values = {**self.parameter_values, **self.inputs_}
        if self.parameter_values.get("Electrolyte density [kg.m-3]") is None:
            raise ValueError("Missing 'Electrolyte density [kg.m-3]'")
        self._stack_breakdown = None
        self._stack_breakdown_dataframe = None
        self._stack_energy_densities = None
        self._stack_energy_densities_dataframe = None
        self._capacities_and_potentials_dataframe = None
        self.initialize()

    @property
    def stack_breakdown(self):
        """A breakdown of volume- and mass loadings on stack level."""
        if self._stack_breakdown is not None:
            return self._stack_breakdown
        else:
            self._stack_breakdown = self.calculate_stack_breakdown()
            return self._stack_breakdown

    @property
    def stack_breakdown_dataframe(self):
        """
        A dataframe with components, volume-, mass loadings and densities on stack
        level.
        """
        if self._stack_breakdown_dataframe is not None:
            return self._stack_breakdown_dataframe
        else:
            self._stack_breakdown_dataframe = self.print_stack_breakdown()
            return self._stack_breakdown_dataframe

    @property
    def stack_energy_densities(self):
        """Energy densities and parameters for calculation on stack level."""
        if self._stack_energy_densities is not None:
            return self._stack_energy_densities
        else:
            self._stack_energy_densities = self.calculate_stack_energy_densities()
            return self._stack_energy_densities

    @property
    def stack_energy_densities_dataframe(self):
        """
        A dataframe with energy densities and summary variables for their
        calculation.
        """
        if self._stack_energy_densities_dataframe is not None:
            return self._stack_energy_densities_dataframe
        else:
            self._stack_energy_densities_dataframe = self.print_stack_energy_densities()
            return self._stack_energy_densities_dataframe

    @property
    def capacities_and_potentials_dataframe(self):
        """A dataframe with potentials and capacities."""
        if self._capacities_and_potentials_dataframe is not None:
            return self._capacities_and_potentials_dataframe
        else:
            self._capacities_and_potentials_dataframe = (
                self.print_capacities_and_potentials()
            )
            return self._capacities_and_potentials_dataframe

    def initialize(self):
        """
        Initialize class by calculating/updating densities, mass and volume
        fractions.
        """
        pava = self.parameter_values
        if pava.get("Separator dry density [kg.m-3]") is not None:
            pava["Separator density [kg.m-3]"] = pava.get(
                "Separator porosity"
            ) * pava.get("Electrolyte density [kg.m-3]", 0) + pava.get(
                "Separator dry density [kg.m-3]", 0
            )
        if pava.get("Separator material density [kg.m-3]") is not None:
            pava["Separator density [kg.m-3]"] = pava.get(
                "Separator porosity"
            ) * pava.get("Electrolyte density [kg.m-3]", 0) + (
                1 - pava.get("Separator porosity")
            ) * pava.get(
                "Separator material density [kg.m-3]", 0
            )
        electrodes = ["Negative electrode", "Positive electrode"]
        for electrode in electrodes:
            if (
                (
                    pava.get(f"{electrode} active material volume fraction", 0)
                    + pava.get(f"{electrode} porosity", 0)
                    == 1
                )
                and pava.get(f"{electrode} binder dry mass fraction") is None
                and pava.get(f"{electrode} conductive additive dry mass fraction")
                is None
                and pava.get(f"{electrode} active material dry mass fraction") is None
            ):
                pava[f"{electrode} dry density [kg.m-3]"] = pava.get(
                    f"{electrode} density [kg.m-3]"
                ) - pava.get(f"{electrode} porosity") * pava.get(
                    "Electrolyte density [kg.m-3]", 0
                )
                pava[f"{electrode} active material density [kg.m-3]"] = pava.get(
                    f"{electrode} dry density [kg.m-3]"
                )
                print(
                    f"Warning: '{electrode} active material density [kg.m-3]' and '{electrode} dry density [kg.m-3]' have been calulated from;'Electrolyte density [kg.m-3]', '{electrode} porosity' and '{electrode} density [kg.m-3]'"
                )
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
                pava.get(f"{electrode} active material capacity [mA.h.g-1]") is not None
                and pava.get(f"{electrode} active material density [kg.m-3]")
                is not None
            ):
                if electrode == "Negative electrode":
                    pava["Maximum concentration in negative electrode [mol.m-3]"] = (
                        pava.get(f"{electrode} active material capacity [mA.h.g-1]")
                        * pava.get(f"{electrode} active material density [kg.m-3]")
                        * 3600
                        / 96485
                    )
                elif electrode == "Positive electrode":
                    pava["Maximum concentration in positive electrode [mol.m-3]"] = (
                        pava.get(f"{electrode} active material capacity [mA.h.g-1]")
                        * pava.get(f"{electrode} active material density [kg.m-3]")
                        * 3600
                        / 96485
                    )
            else:
                if (
                    electrode == "Negative electrode"
                    and pava.get(f"{electrode} active material density [kg.m-3]")
                    is not None
                ):
                    pava[f"{electrode} active material capacity [mA.h.g-1]"] = (
                        pava.get(
                            "Maximum concentration in negative electrode [mol.m-3]"
                        )
                        / pava.get(f"{electrode} active material density [kg.m-3]")
                        * 96485
                        / 3600
                    )
                elif (
                    electrode == "Positive electrode"
                    and pava.get(f"{electrode} active material density [kg.m-3]")
                    is not None
                ):
                    pava[f"{electrode} active material capacity [mA.h.g-1]"] = (
                        pava.get(
                            "Maximum concentration in positive electrode [mol.m-3]"
                        )
                        / pava.get(f"{electrode} active material density [kg.m-3]")
                        * 96485
                        / 3600
                    )
        if (
            pava.get("Theoretical n/p ratio") is not None
            and pava.get("Negative electrode thickness [m]") is not None
            and pava.get("Positive electrode thickness [m]") is not None
        ) or (
            pava.get("Theoretical n/p ratio") is not None
            and pava.get("Negative electrode thickness [m]") is None
            and pava.get("Positive electrode thickness [m]") is not None
        ):
            pava["Negative electrode thickness [m]"] = (
                pava.get("Theoretical n/p ratio")
                * pava.get("Positive electrode thickness [m]")
                * pava.get("Positive electrode active material volume fraction")
                * pava.get("Maximum concentration in positive electrode [mol.m-3]")
                / (
                    pava.get("Negative electrode active material volume fraction")
                    * pava.get("Maximum concentration in negative electrode [mol.m-3]")
                )
            )
            warnings.warn(
                "Warning: 'Negative electrode thickness [m]' has been calculated from "
                "'Theoretical n/p ratio' and 'Positive electrode thickness [m]'"
            )
        if (
            pava.get("Theoretical n/p ratio") is not None
            and pava.get("Negative electrode thickness [m]") is not None
            and pava.get("Positive electrode thickness [m]") is None
        ):
            pava["Positive electrode thickness [m]"] = (
                pava.get("Negative electrode thickness [m]")
                * pava.get("Negative electrode active material volume fraction")
                * pava.get("Maximum concentration in negative electrode [mol.m-3]")
            ) / (
                pava.get("Theoretical n/p ratio")
                * pava.get("Positive electrode active material volume fraction")
                * pava.get("Maximum concentration in positive electrode [mol.m-3]")
            )
            warnings.warn(
                "Warning: 'Negative electrode thickness [m]' has been calculated from "
                "'Theoretical n/p ratio' and 'Positive electrode thickness [m]'"
            )
        if (
            pava.get("Negative electrode thickness [m]") is not None
            and pava.get("Positive electrode thickness [m]") is not None
        ):
            pava["Theoretical n/p ratio"] = (
                pava.get("Negative electrode thickness [m]")
                * pava.get("Negative electrode active material volume fraction")
                * pava.get("Maximum concentration in negative electrode [mol.m-3]")
                / (
                    pava.get("Positive electrode thickness [m]")
                    * pava.get("Positive electrode active material volume fraction")
                    * pava.get("Maximum concentration in positive electrode [mol.m-3]")
                )
            )
        self.parameter_values = {**self.parameter_values, **pava}

    def print_stack_breakdown(self):
        """
        A dataframe with components, volume-, mass loadings and densities on stack
        level.
        """
        stack_bd = self.stack_breakdown

        # Create a dataframe with columns for components, volume- and mass- loadings
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

    def print_stack_energy_densities(self):
        """
        A dataframe with capacities, energy densities, stoichiometry- and potential-
        windows, n/p ratios, (single-)stack thickness and stack density.
        """
        stack_ed = self.stack_energy_densities
        data = [
            {
                "Parameter": "Volumetric energy density",
                "Unit": "Wh.L-1",
                "Value": stack_ed.get("Volumetric stack energy density [Wh.L-1]"),
            },
            {
                "Parameter": "Gravimetric energy density",
                "Unit": "Wh.kg-1",
                "Value": stack_ed.get("Gravimetric stack energy density [Wh.kg-1]"),
            },
            {
                "Parameter": "Stack average OCP",
                "Unit": "V",
                "Value": stack_ed.get("Stack average OCP [V]"),
            },
            {
                "Parameter": "Capacity",
                "Unit": "mA.h.cm-2",
                "Value": stack_ed.get("Capacity [mA.h.cm-2]"),
            },
            {
                "Parameter": "(Single-) stack thickness",
                "Unit": "um",
                "Value": 10**6 * stack_ed.get("Stack thickness [m]"),
            },
            {
                "Parameter": "Stack density",
                "Unit": "kg.L-1",
                "Value": 10**-3 * stack_ed.get("Stack density [kg.m-3]"),
            },
        ]
        # Create the DataFrame from the list of dictionaries
        df = pd.DataFrame(data)
        return df

    def print_capacities_and_potentials(self):
        """
        A dataframe with capacities, energy densities, stoichiometry- and potential
        windows, n/p ratios, (single-)stack thickness and stack density.
        """
        stack_ed = self.stack_energy_densities
        data = [
            # stack potentials
            {"Parameter": "Stack potentials", "Unit": "", "Value": ""},
            {
                "Parameter": "Stack average OCP",
                "Unit": "V",
                "Value": stack_ed.get("Stack average OCP [V]"),
            },
            {
                "Parameter": "Maximal OCP",
                "Unit": "V",
                "Value": stack_ed.get("Maximal OCP [V]"),
            },
            {
                "Parameter": "Minimal OCP",
                "Unit": "V",
                "Value": stack_ed.get("Minimal OCP [V]"),
            },
            # electrode potentials
            {"Parameter": "Electrode potentials", "Unit": "", "Value": ""},
            {
                "Parameter": "Negative electrode average OCP",
                "Unit": "V",
                "Value": stack_ed.get("Negative electrode average OCP [V]"),
            },
            {
                "Parameter": "Positive electrode average OCP",
                "Unit": "V",
                "Value": stack_ed.get("Positive electrode average OCP [V]"),
            },
            # n/p ratio
            {"Parameter": "n/p ratio's", "Unit": "", "Value": ""},
            {
                "Parameter": "Practical n/p ratio",
                "Unit": "-",
                "Value": stack_ed.get("Practical n/p ratio"),
            },
            {
                "Parameter": "Theoretical n/p ratio",
                "Unit": "-",
                "Value": self.parameter_values.get("Theoretical n/p ratio"),
            },
            # stack capacities
            {"Parameter": "Stack capacities", "Unit": "", "Value": ""},
            {
                "Parameter": "Volumetric stack capacity",
                "Unit": "Ah.L-1",
                "Value": stack_ed.get("Volumetric stack capacity [Ah.L-1]"),
            },
            {
                "Parameter": "Gravimetric stack capacity",
                "Unit": "Ah.kg-1",
                "Value": stack_ed.get("Gravimetric stack capacity [Ah.kg-1]"),
            },
            {
                "Parameter": "Capacity",
                "Unit": "mA.h.cm-2",
                "Value": stack_ed.get("Capacity [mA.h.cm-2]"),
            },
            # electrode capacities
            {"Parameter": "Electrode capacities", "Unit": "", "Value": ""},
            {
                "Parameter": "Negative electrode theoretical capacity",
                "Unit": "mA.h.cm-2",
                "Value": stack_ed.get(
                    "Negative electrode theoretical capacity [mA.h.cm-2]"
                ),
            },
            {
                "Parameter": "Positive electrode theoretical capacity",
                "Unit": "mA.h.cm-2",
                "Value": stack_ed.get(
                    "Positive electrode theoretical capacity [mA.h.cm-2]"
                ),
            },
            {
                "Parameter": "Negative electrode volumetric capacity",
                "Unit": "mA.h.cm-3",
                "Value": stack_ed.get(
                    "Negative electrode volumetric capacity [mA.h.cm-3]"
                ),
            },
            {
                "Parameter": "Positive electrode volumetric capacity",
                "Unit": "mA.h.cm-3",
                "Value": stack_ed.get(
                    "Positive electrode volumetric capacity [mA.h.cm-3]"
                ),
            },
            {
                "Parameter": "Negative electrode gravimetric capacity",
                "Unit": "mA.h.g-1",
                "Value": stack_ed.get(
                    "Negative electrode gravimetric capacity [mA.h.g-1]"
                ),
            },
            {
                "Parameter": "Positive electrode gravimetric capacity",
                "Unit": "mA.h.g-1",
                "Value": stack_ed.get(
                    "Positive electrode gravimetric capacity [mA.h.g-1]"
                ),
            },
            # active material capacities
            {"Parameter": "Active material capacities", "Unit": "", "Value": ""},
            {
                "Parameter": "Negative electrode active material practical capacity",
                "Unit": "mA.h.g-1",
                "Value": stack_ed.get(
                    "Negative electrode active material practical capacity [mA.h.g-1]"
                ),
            },
            {
                "Parameter": "Positive electrode active material practical capacity",
                "Unit": "mA.h.g-1",
                "Value": stack_ed.get(
                    "Positive electrode active material practical capacity [mA.h.g-1]"
                ),
            },
            {
                "Parameter": "Negative electrode active material theoretical capacity",
                "Unit": "mA.h.g-1",
                "Value": self.parameter_values.get(
                    "Negative electrode active material capacity [mA.h.g-1]"
                ),
            },
            {
                "Parameter": "Positive electrode active material theoretical capacity",
                "Unit": "mA.h.g-1",
                "Value": self.parameter_values.get(
                    "Positive electrode active material capacity [mA.h.g-1]"
                ),
            },
            # stoichiometries
            {"Parameter": "Stoichiometries", "Unit": "", "Value": ""},
            {
                "Parameter": "Negative electrode stoichiometry at 0% SoC",
                "Unit": "-",
                "Value": stack_ed.get("Negative electrode stoichiometry at 0% SoC"),
            },
            {
                "Parameter": "Negative electrode stoichiometry at 100% SoC",
                "Unit": "-",
                "Value": stack_ed.get("Negative electrode stoichiometry at 100% SoC"),
            },
            {
                "Parameter": "Positive electrode stoichiometry at 100% SoC",
                "Unit": "-",
                "Value": stack_ed.get("Positive electrode stoichiometry at 100% SoC"),
            },
            {
                "Parameter": "Positive electrode stoichiometry at 0% SoC",
                "Unit": "-",
                "Value": stack_ed.get("Positive electrode stoichiometry at 0% SoC"),
            },
        ]
        # Create the DataFrame from the list of dictionaries
        df = pd.DataFrame(data)
        return df

    def calculate_stack_energy_densities(self):
        """
        Calculate ideal volumetric and gravimetric energy densities on stack level.
        """
        stack_ed = {}  # stack energy densities dict
        pava = None
        pava = self.parameter_values  # parameter values

        # stoichiometries - calculation based on input stoichiometries or cell
        # potential limits
        if (
            pava.get("Negative electrode stoichiometry at 0%") is not None
            and pava.get("Negative electrode stoichiometry at 100%") is not None
            and pava.get("Positive electrode stoichiometry at 100%") is not None
            and pava.get("Positive electrode stoichiometry at 0%") is not None
        ) or (
            pava.get("Negative electrode stoichiometry at 0%") is None
            and pava.get("Negative electrode stoichiometry at 100%") is None
            and pava.get("Positive electrode stoichiometry at 100%") is not None
            and pava.get("Positive electrode stoichiometry at 0%") is not None
        ):
            y100 = pava.get("Positive electrode stoichiometry at 100% SoC")
            y0 = pava.get("Positive electrode stoichiometry at 0% SoC")
            # x0, x100 = self.get_stoichiometries(pava, y0, y100)
            # update cut-off voltages if voltage curve(s) are provided
        elif (
            pava.get("Negative electrode stoichiometry at 0%") is not None
            and pava.get("Negative electrode stoichiometry at 100%") is not None
            and pava.get("Positive electrode stoichiometry at 100%") is None
            and pava.get("Positive electrode stoichiometry at 0%") is None
        ):
            x100 = pava.get("Negative electrode stoichiometry at 100% SoC")
            x0 = pava.get("Negative electrode stoichiometry at 0% SoC")
            # y0, y100 = self.get_stoichiometries(pava, x0, x100)
            # update cut-off voltages if voltage curve(s) are provided
        elif (
            pava.get("Negative electrode OCP [V]") is not None
            and pava.get("Positive electrode OCP [V]") is not None
            and pava.get("Lower voltage cut-off [V]") is not None
            and pava.get("Upper voltage cut-off [V]") is not None
        ):
            x0, x100, y100, y0 = pybamm.lithium_ion.get_min_max_stoichiometries(
                pybamm.ParameterValues(pava)
            )  # stoichiometries at 0 and 100% SOC based on cell potential limits
        else:
            raise ValueError("Error: Stoichiometry calculation failed.")
        stack_ed["Negative electrode stoichiometry at 0% SoC"] = x0
        stack_ed["Negative electrode stoichiometry at 100% SoC"] = x100
        stack_ed["Positive electrode stoichiometry at 100% SoC"] = y100
        stack_ed["Positive electrode stoichiometry at 0% SoC"] = y0

        # capacities - per electrode area, volume and mass and per active material mass
        electrodes = ["Negative electrode", "Positive electrode"]
        electrodes_ = ["negative electrode", "positive electrode"]
        for electrode, electrode_ in zip(electrodes, electrodes_):
            stack_ed[f"{electrode} volumetric capacity [mA.h.cm-3]"] = (
                pava.get(f"Maximum concentration in {electrode_} [mol.m-3]")
                * 96485
                / 3.6
                / 1000000
                * pava.get(  # C.mol-1 / mA.h.C-1 / cm-3.m-3
                    f"{electrode} active material volume fraction"
                )
                * (
                    max(
                        stack_ed.get(f"{electrode} stoichiometry at 100% SoC"),
                        stack_ed.get(f"{electrode} stoichiometry at 0% SoC"),
                    )
                    - min(
                        stack_ed.get(f"{electrode} stoichiometry at 100% SoC"),
                        stack_ed.get(f"{electrode} stoichiometry at 0% SoC"),
                    )
                )
            )
            stack_ed[f"{electrode} gravimetric capacity [mA.h.g-1]"] = (
                stack_ed.get(f"{electrode} volumetric capacity [mA.h.cm-3]")
                / pava.get(f"{electrode} density [kg.m-3]")
                * 1000
            )  # cm3.L-1
            stack_ed[f"{electrode} active material practical capacity [mA.h.g-1]"] = (
                stack_ed.get(f"{electrode} volumetric capacity [mA.h.cm-3]")
                / pava.get(f"{electrode} active material volume fraction")
                / pava.get(f"{electrode} active material density [kg.m-3]")
                * 1000
            )  # cm3.L-1
            stack_ed[f"{electrode} capacity [mA.h.cm-2]"] = pava.get(
                f"{electrode} capacity [mA.h.cm-2]"
            ) or (
                stack_ed.get(f"{electrode} volumetric capacity [mA.h.cm-3]")
                * pava.get(f"{electrode} thickness [m]")
                * 100
            )  # cm.m-1
            stack_ed[f"{electrode} theoretical capacity [mA.h.cm-2]"] = (
                pava.get(f"Maximum concentration in {electrode_} [mol.m-3]")
                * pava.get(f"{electrode} active material volume fraction")
                * pava.get(f"{electrode} thickness [m]")
                * 100
                * 96485
                / 3.6
                / 1000000
            )  # cm.m-1 * C.mol-1 / mA.h.C-1 / cm-3.m-3
        stack_ed["Capacity [mA.h.cm-2]"] = min(
            stack_ed.get("Negative electrode capacity [mA.h.cm-2]"),
            stack_ed.get("Positive electrode capacity [mA.h.cm-2]"),
        )

        # practical n/p ratio
        stack_ed["Practical n/p ratio"] = (
            (1 - x0)
            / (y0 - y100)
            * pava.get("Negative electrode active material volume fraction")
            * pava.get("Negative electrode thickness [m]")
            * pava.get("Maximum concentration in negative electrode [mol.m-3]")
            / (
                pava.get("Positive electrode active material volume fraction")
                * pava.get("Positive electrode thickness [m]")
                * pava.get("Maximum concentration in positive electrode [mol.m-3]")
            )
        )

        # potentials
        soc = pybamm.linspace(0, 1)
        x = x0 + soc * (x100 - x0)
        y = y0 - soc * (y0 - y100)
        if pava.get("Negative electrode average OCP [V]") is not None:
            stack_ed["Negative electrode average OCP [V]"] = pava.get(
                "Negative electrode average OCP [V]"
            )
            ne_0 = pava.get("Negative electrode average OCP [V]")
            ne_100 = pava.get("Negative electrode average OCP [V]")
        elif (
            pava.get("Negative electrode OCP [V]") is not None
            and pava.get("Negative electrode average OCP [V]") is None
        ):
            ne_ocv = pava["Negative electrode OCP [V]"]
            stack_ed["Negative electrode average OCP [V]"] = ne_ocv(x).evaluate().mean()
            ne_0 = ne_ocv(x0).evaluate()
            ne_100 = ne_ocv(x100).evaluate()
        else:
            raise ValueError("Error: Negative electrode OCP calculation failed.")
        if pava.get("Positive electrode average OCP [V]") is not None:
            stack_ed["Positive electrode average OCP [V]"] = pava.get(
                "Positive electrode average OCP [V]"
            )
            pe_0 = pava.get("Positive electrode average OCP [V]")
            pe_100 = pava.get("Positive electrode average OCP [V]")
        elif (
            pava.get("Positive electrode OCP [V]") is not None
            and pava.get("Positive electrode average OCP [V]") is None
        ):
            pe_ocv = pava["Positive electrode OCP [V]"]
            stack_ed["Positive electrode average OCP [V]"] = pe_ocv(y).evaluate().mean()
            pe_100 = pe_ocv(y100).evaluate()
            pe_0 = pe_ocv(y0).evaluate()
        else:
            raise ValueError("Error: Positive electrode OCP calculation failed.")
        if pava.get("Stack average OCP [V]") is not None:
            stack_ed["Stack average OCP [V]"] = pava.get("Stack average OCP [V]")
        else:
            stack_ed["Stack average OCP [V]"] = stack_ed.get(
                "Positive electrode average OCP [V]"
            ) - stack_ed.get("Negative electrode average OCP [V]")
        stack_ed["Minimal OCP [V]"] = pe_0 - ne_0
        stack_ed["Maximal OCP [V]"] = pe_100 - ne_100

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

        # volumetric stack capacity in [Ah.L-1] and volumetric stack energy density in
        # [Wh.L-1]
        stack_ed["Volumetric stack capacity [Ah.L-1]"] = (
            stack_ed.get("Capacity [mA.h.cm-2]")
            / stack_ed.get("Stack thickness [m]")
            / 100
        )
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

        # gravimetric stack capacity in [Ah.L-1] and gravimetric stack energy density
        # in [Wh.L-1]
        stack_ed["Gravimetric stack capacity [Ah.kg-1]"] = (
            stack_ed.get("Volumetric stack capacity [Ah.L-1]")
            / stack_ed.get("Stack density [kg.m-3]")
            * 1000
        )
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
        stack_bd["Separator material volume fraction"] = 1 - stack_bd.get(
            "Separator electrolyte volume fraction"
        )
        stack_bd["Separator volume fraction"] = 1
        stack_bd["Separator dry volume fraction"] = 1

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
            if (
                pava.get(f"{electrode} active material density [kg.m-3]") is None
                and stack_bd.get(f"{electrode} inactive material volume fraction") != 0
            ):
                warnings.warn(
                    f"Warning: Missing '{electrode} active material density [kg.m-3]'"
                )
        for component in [
            "Negative electrode",
            "Positive electrode",
            "Separator",
            "Negative current collector",
            "Positive current collector",
        ]:
            if pava.get(f"{component} density [kg.m-3]") is None:
                warnings.warn(f"Warning: Missing '{component} density [kg.m-3]'")

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
                warnings.warn(
                    f"Warning: {electrode} inactive material volume fraction is 0, "
                    f"{electrode} inactive material density is set to 0"
                )
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
            stack_bd["Separator material density [mg.uL-1]"] = 0
            warnings.warn(
                "Warning: Separator porosity is 1, separator material density is "
                "set to 0"
            )
        else:
            stack_bd["Separator material density [mg.uL-1]"] = (
                (
                    pava.get("Separator density [kg.m-3]", 0)
                    - pava.get("Separator porosity")
                    * pava.get("Electrolyte density [kg.m-3]", 0)
                )
                / (1 - pava.get("Separator porosity"))
                / 1000
            )
            stack_bd["Separator dry density [mg.uL-1]"] = (
                pava.get("Separator density [kg.m-3]", 0)
                - pava.get("Separator porosity")
                * pava.get("Electrolyte density [kg.m-3]", 0)
            ) / 1000
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

    def plot_stack_breakdown(self, testing=False):
        stack_bd = self.stack_breakdown

        # Data for colored rectangle heights, widths, labels, and colors
        components = [
            "Negative current collector",
            "Negative current collector",
            "Negative electrode active material",
            "Negative electrode inactive material",
            "Negative electrode electrolyte",
            "Separator material",
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
        plt.tight_layout()
        if testing is False:
            plt.show()

        # Return the figure and axis objects
        return fig
