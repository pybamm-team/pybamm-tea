#
# TEA class
#

import pybamm
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import pandas as pd
import numpy as np
import warnings


class TEA:
    """
    A class for estimating cell metrics.

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
        if parameter_values is None:
            self.parameter_values = pybamm.ParameterValues({})
        else:
            self.parameter_values = pybamm.ParameterValues(parameter_values)
        if inputs is not None:
            self.parameter_values.update(inputs, check_already_exists=False)
        self._masses_and_volumes = None
        self._masses_and_volumes_dataframe = None
        self._stack_energy = None
        self._stack_energy_dataframe = None
        self._capacities_and_potentials_dataframe = None
        self._electrolyte_dataframe = None
        self.initialize()

    @property
    def masses_and_volumes(self):
        """A breakdown of volume- and mass loadings on stack level."""
        if self._masses_and_volumes is not None:
            return self._masses_and_volumes
        else:
            self._masses_and_volumes = self.calculate_masses_and_volumes()
            return self._masses_and_volumes

    @property
    def masses_and_volumes_dataframe(self):
        """
        A dataframe with components, volume-, mass loadings and densities on stack
        level.
        """
        if self._masses_and_volumes_dataframe is not None:
            return self._masses_and_volumes_dataframe
        else:
            self._masses_and_volumes_dataframe = self.print_masses_and_volumes()
            return self._masses_and_volumes_dataframe

    @property
    def stack_energy(self):
        """Energy densities and parameters for calculation on stack level."""
        if self._stack_energy is not None:
            return self._stack_energy
        else:
            self._stack_energy = self.calculate_stack_energy()
            return self._stack_energy

    @property
    def stack_energy_dataframe(self):
        """
        A dataframe with energy densities and summary variables for their
        calculation.
        """
        if self._stack_energy_dataframe is not None:
            return self._stack_energy_dataframe
        else:
            self._stack_energy_dataframe = self.print_stack_energy()
            return self._stack_energy_dataframe

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
        
    @property
    def electrolyte_dataframe(self):
        """A dataframe with electrolyte metrics."""
        if self._electrolyte_dataframe is not None:
            return self._electrolyte_dataframe
        else:
            self._electrolyte_dataframe = (
                self.print_electrolyte()
            )
            return self._electrolyte_dataframe

    def initialize(self):
        """
        Initialize class by calculating/updating densities, mass and volume
        fractions.
        """
        pava = dict(self.parameter_values)
        ### separator density
        if pava.get("Separator dry density [kg.m-3]") is not None and pava.get("Separator material density [kg.m-3]") is None:
            # calculate separator density based on dry density, porosity and electrolyte density
            pava["Separator density [kg.m-3]"] = pava.get(
                "Separator porosity"
            ) * pava.get("Electrolyte density [kg.m-3]") + pava.get(
                "Separator dry density [kg.m-3]"
            )
        if pava.get("Separator material density [kg.m-3]") is not None and pava.get("Separator dry density [kg.m-3]") is None:
            # calculate separator density based on material density, porosity and electrolyte density
            pava["Separator density [kg.m-3]"] = pava.get(
                "Separator porosity"
            ) * pava.get("Electrolyte density [kg.m-3]") + (
                1 - pava.get("Separator porosity")
            ) * pava.get(
                "Separator material density [kg.m-3]"
            )
        if pava.get("Separator material density [kg.m-3]") is not None and pava.get("Separator dry density [kg.m-3]") is not None:
            # calculate separator porosity based on dry density and material density
            pava["Separator porosity"] = 1 - pava.get(
                "Separator dry density [kg.m-3]"
            ) / pava.get(
                "Separator material density [kg.m-3]"
            )
            warnings.warn(
                    f"'Separator porosity [kg.m-3]' has been calulated from; 'Separator dry density [kg.m-3]' and 'Separator material density [kg.m-3]'"
                )
            # calculate separator density based on material density, porosity and electrolyte density
            pava["Separator density [kg.m-3]"] = pava.get(
                "Separator porosity"
            ) * pava.get("Electrolyte density [kg.m-3]") + (
                1 - pava.get("Separator porosity")
            ) * pava.get(
                "Separator material density [kg.m-3]"
            )
        ### electrode densities
        electrodes = ["Negative electrode", "Positive electrode"]
        for electrode in electrodes:
            ## dense metal electrode
            if (pava.get(f"{electrode} active material volume fraction", 1e10) == 1
                and pava.get(f"{electrode} active material density [kg.m-3]") is not None):
                pava[f"{electrode} dry density [kg.m-3]"] = pava.get(
                    f"{electrode} active material density [kg.m-3]")
                pava[f"{electrode} density [kg.m-3]"] = pava.get(
                    f"{electrode} active material density [kg.m-3]")
                warnings.warn(
                    f"'{electrode} density [kg.m-3]' and '{electrode} dry density [kg.m-3]' have been calulated from; '{electrode} active material volume fraction' and '{electrode} active material density [kg.m-3]'"
                )
            ## densities without inactive material
            if (
                (
                    pava.get(f"{electrode} active material volume fraction", 1e10)
                    + pava.get(f"{electrode} porosity", 1e10)
                    == 1
                )
                and pava.get(f"{electrode} binder dry mass fraction") is None
                and pava.get(f"{electrode} conductive additive dry mass fraction")
                is None
                and pava.get(f"{electrode} active material dry mass fraction") is None
            ):
                if (pava.get(f"{electrode} active material density [kg.m-3]") is not None
                    and pava.get(f"{electrode} dry density [kg.m-3]") is None):
                    # calculate electrode dry density based on active material density and porosity
                    pava[f"{electrode} dry density [kg.m-3]"] = pava.get(
                        f"{electrode} active material density [kg.m-3]"
                    ) * (1 - pava.get(f"{electrode} porosity"))
                    # calculate electrode density based on dry density, porosity and electrolyte density
                    pava[f"{electrode} density [kg.m-3]"] = pava.get(
                        f"{electrode} dry density [kg.m-3]"
                    ) + pava.get(f"{electrode} porosity") * pava.get(
                        "Electrolyte density [kg.m-3]"
                    )
                    warnings.warn(
                        f"'{electrode} density [kg.m-3]' and '{electrode} dry density [kg.m-3]' have been calulated from; 'Electrolyte density [kg.m-3]', '{electrode} porosity' and '{electrode} active material density [kg.m-3]'"
                    )
                elif (pava.get(f"{electrode} active material density [kg.m-3]") is None
                    and pava.get(f"{electrode} dry density [kg.m-3]") is not None):
                    # calculate electrode density based on dry density, porosity and electrolyte density
                    pava[f"{electrode} density [kg.m-3]"] = pava.get(
                        f"{electrode} dry density [kg.m-3]"
                    ) + pava.get(f"{electrode} porosity") * pava.get(
                        "Electrolyte density [kg.m-3]"
                    )
                    # calculate electrode active material density based on electrode density, porosity and electrolyte density
                    pava[f"{electrode} active material density [kg.m-3]"] = pava.get(
                        f"{electrode} density [kg.m-3]"
                    ) - pava.get(f"{electrode} porosity") * pava.get(
                        "Electrolyte density [kg.m-3]"
                    )
                    warnings.warn(
                        f"'{electrode} active material density [kg.m-3]' and '{electrode} dry density [kg.m-3]' have been calulated from; 'Electrolyte density [kg.m-3]', '{electrode} porosity' and '{electrode} density [kg.m-3]'"
                    )
                else:
                    # calculate electrode active material and dry density based on electrode density, porosity and electrolyte density
                    pava[f"{electrode} dry density [kg.m-3]"] = pava.get(
                        f"{electrode} density [kg.m-3]"
                    ) - pava.get(f"{electrode} porosity") * pava.get(
                        "Electrolyte density [kg.m-3]"
                    )
                    pava[f"{electrode} active material density [kg.m-3]"] = pava.get(
                        f"{electrode} dry density [kg.m-3]"
                    ) / (1 - pava.get(f"{electrode} porosity"))
                    warnings.warn(
                        f"'{electrode} active material density [kg.m-3]' and '{electrode} dry density [kg.m-3]' have been calculated from; 'Electrolyte density [kg.m-3]', '{electrode} porosity' and '{electrode} density [kg.m-3]'"
                    )
            ## inactive material density based on binder and conductive additive densities
            if (
                pava.get(f"{electrode} binder dry mass fraction") is not None
                and pava.get(f"{electrode} conductive additive dry mass fraction")
                is not None
                and pava.get(f"{electrode} binder density [kg.m-3]") is not None
                and pava.get(f"{electrode} conductive additive density [kg.m-3]")
                is not None
            ):
                # calculate inactive material density based on binder and conductive additive dry mass fractions and densities
                pava[f"{electrode} inactive material density [kg.m-3]"] = (
                    pava.get(f"{electrode} binder dry mass fraction")
                    + pava.get(f"{electrode} conductive additive dry mass fraction")
                ) / (
                    pava.get(f"{electrode} binder dry mass fraction")
                    / pava.get(f"{electrode} binder density [kg.m-3]")
                    + pava.get(f"{electrode} conductive additive dry mass fraction")
                    / pava.get(f"{electrode} conductive additive density [kg.m-3]")
                )
                # calculate active material dry mass fraction based on binder and conductive additive dry mass fractions
                pava[f"{electrode} active material dry mass fraction"] = (
                    1
                    - pava.get(f"{electrode} binder dry mass fraction")
                    - pava.get(f"{electrode} conductive additive dry mass fraction")
                    )
            ## porosity based on densities and dry mass fraction
            if (
                pava.get(f"{electrode} active material dry mass fraction") is not None
                and pava.get(f"{electrode} active material density [kg.m-3]")
                is not None
                and pava.get(f"{electrode} inactive material density [kg.m-3]")
                is not None
                and pava.get(f"{electrode} dry density [kg.m-3]")
                is not None
            ):
                # calculate porosity based on active material dry mass fraction, active- and inactive material density and dry electrode density
                pava[f"{electrode} porosity"] = (1 - pava.get(f"{electrode} dry density [kg.m-3]")
                                                 * (pava.get(f"{electrode} active material dry mass fraction")
                                                    / pava.get(f"{electrode} active material density [kg.m-3]")
                                                    + (1 - pava.get(f"{electrode} active material dry mass fraction"))
                                                    / pava.get(f"{electrode} inactive material density [kg.m-3]")))
                warnings.warn(
                    f"'{electrode} porosity' has been calulated from; '{electrode} dry density [kg.m-3]', {electrode} active material dry mass fraction', '{electrode} active material density [kg.m-3]' and '{electrode} inactive material density [kg.m-3]'"
                )
            ## inactive material density based on densities and dry mass fraction
            if (
                pava.get(f"{electrode} active material dry mass fraction") is not None
                and pava.get(f"{electrode} active material density [kg.m-3]")
                is not None
                and pava.get(f"{electrode} inactive material density [kg.m-3]")
                is None
                and pava.get(f"{electrode} dry density [kg.m-3]")
                is not None
            ):
                # calculate inactive material density based on active material dry mass fraction, porosity and active material density and dry electrode density
                pava[f"{electrode} inactive material density [kg.m-3]"] = ((1 - pava.get(f"{electrode} active material dry mass fraction"))
                                                                           / ((1 - pava.get(f"{electrode} porosity"))
                                                                              / pava.get(f"{electrode} dry density [kg.m-3]")
                                                                              - pava.get(f"{electrode} active material dry mass fraction")
                                                                              / pava.get(f"{electrode} active material density [kg.m-3]")))
            ## active material density based on densities and dry mass fraction
            if (
                pava.get(f"{electrode} active material dry mass fraction") is not None
                and pava.get(f"{electrode} active material density [kg.m-3]")
                is None
                and pava.get(f"{electrode} inactive material density [kg.m-3]")
                is not None
                and pava.get(f"{electrode} dry density [kg.m-3]")
                is not None
            ):
                # calculate active material density based on inactive material dry mass fraction, porosity and active material density and dry electrode density
                pava[f"{electrode} active material density [kg.m-3]"] = (pava.get(f"{electrode} active material dry mass fraction")
                                                                           / ((1 - pava.get(f"{electrode} porosity"))
                                                                              / pava.get(f"{electrode} dry density [kg.m-3]")
                                                                              - (1 - pava.get(f"{electrode} active material dry mass fraction"))
                                                                              / pava.get(f"{electrode} inactive material density [kg.m-3]")))
            ## active material volume fraction, dry density, wet density
            if (
                pava.get(f"{electrode} active material dry mass fraction") is not None
                and pava.get(f"{electrode} active material density [kg.m-3]")
                is not None
                and pava.get(f"{electrode} inactive material density [kg.m-3]")
                is not None
            ):
                # calculate active material volume fraction based on active material dry mass fraction, porosity and active&inactive material densities
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
                # calculate electrode dry density based on active material dry mass fraction, porosity and active&inactive material densities
                pava[f"{electrode} dry density [kg.m-3]"] = pava.get(
                    f"{electrode} active material volume fraction"
                ) * pava.get(f"{electrode} active material density [kg.m-3]") + (
                    1
                    - pava.get(f"{electrode} active material volume fraction")
                    - pava.get(f"{electrode} porosity")
                ) * pava.get(
                    f"{electrode} inactive material density [kg.m-3]"
                )
                # calculate electrode density based on dry density, porosity and electrolyte density
                pava[f"{electrode} density [kg.m-3]"] = pava.get(
                    f"{electrode} dry density [kg.m-3]"
                ) + pava.get(f"{electrode} porosity") * pava.get(
                    "Electrolyte density [kg.m-3]"
                )
            ## gravimetric active material capacity
            if (
                pava.get(f"{electrode} active material theoretical capacity [mA.h.g-1]") is not None
                and pava.get(f"{electrode} active material density [kg.m-3]")
                is not None
            ):
                # calculate maximum concentration based on gravimetric capacity and density of active material
                if electrode == "Negative electrode":
                    pava["Maximum concentration in negative electrode [mol.m-3]"] = (
                        pava.get(f"{electrode} active material theoretical capacity [mA.h.g-1]")
                        * pava.get(f"{electrode} active material density [kg.m-3]")
                        * 3600
                        / 96485
                    )
                elif electrode == "Positive electrode":
                    pava["Maximum concentration in positive electrode [mol.m-3]"] = (
                        pava.get(f"{electrode} active material theoretical capacity [mA.h.g-1]")
                        * pava.get(f"{electrode} active material density [kg.m-3]")
                        * 3600
                        / 96485
                    )
            else:
                # calculate gravimetric active material capacity based on maximum concentration and density of active material
                if (
                    electrode == "Negative electrode"
                    and pava.get(f"{electrode} active material density [kg.m-3]")
                    is not None
                ):
                    pava[f"{electrode} active material theoretical capacity [mA.h.g-1]"] = (
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
                    pava[f"{electrode} active material theoretical capacity [mA.h.g-1]"] = (
                        pava.get(
                            "Maximum concentration in positive electrode [mol.m-3]"
                        )
                        / pava.get(f"{electrode} active material density [kg.m-3]")
                        * 96485
                        / 3600
                    )
        ## Theoretical n/p ratio
        if (
            pava.get("Theoretical n/p ratio") is not None
            and pava.get("Negative electrode thickness [m]") is not None
            and pava.get("Positive electrode thickness [m]") is not None
        ) or (
            pava.get("Theoretical n/p ratio") is not None
            and pava.get("Negative electrode thickness [m]") is None
            and pava.get("Positive electrode thickness [m]") is not None
        ):
            # calculate negative electrode thickness based on theoretical NPR and positive electrode thickness
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
                "'Negative electrode thickness [m]' has been calculated from "
                "'Theoretical n/p ratio' and 'Positive electrode thickness [m]'"
            )
        if (
            pava.get("Theoretical n/p ratio") is not None
            and pava.get("Negative electrode thickness [m]") is not None
            and pava.get("Positive electrode thickness [m]") is None
        ):
            # calculate positive electrode thickness based on theoretical NPR and negative electrode thickness
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
                "'Positive electrode thickness [m]' has been calculated from "
                "'Theoretical n/p ratio' and 'Negative electrode thickness [m]'"
            )
        if (
            pava.get("Negative electrode thickness [m]") is not None
            and pava.get("Positive electrode thickness [m]") is not None
        ):
            # calculate theoretical NPR based on negative and positive electrode thickness
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
        ### Loss of lithium inventory and active materials
        # initial concentrations (for calculation of lithium inventory, set to 100% SoC later)
        if (
            pava.get("Initial concentration in negative electrode [mol.m-3]") is None
            and pava.get("Initial concentration in positive electrode [mol.m-3]") is None
        ):
            raise ValueError("Error: Please, supply 'Initial concentration in negative electrode [mol.m-3]' and 'Initial concentration in positive electrode [mol.m-3]'.")
        if ((pava.get("Initial concentration in negative electrode [mol.m-3]") is None) ^ 
            (pava.get("Initial concentration in positive electrode [mol.m-3]") is None)
        ):
            raise ValueError("Error: Please, supply both of 'Initial concentration in negative electrode [mol.m-3]' and 'Initial concentration in positive electrode [mol.m-3]'.")
        # initial lithium inventory without losses
        pava["Initial lithium inventory [mA.h.cm-2]"] = (pava.get("Negative electrode thickness [m]") * 
                                                         pava.get("Negative electrode active material volume fraction") * 
                                                         pava.get("Initial concentration in negative electrode [mol.m-3]") + 
                                                         pava.get("Positive electrode thickness [m]") * 
                                                         pava.get("Positive electrode active material volume fraction") * 
                                                         pava.get("Initial concentration in positive electrode [mol.m-3]")) * 96485 / 3.6 / 10000
        # initial lithium inventory without losses, normalized by positive electrode theoretical capacity without losses
        pava["Positive electrode initial stoichiometry"] = (pava.get("Initial lithium inventory [mA.h.cm-2]") / 
                                                                                       (pava.get("Maximum concentration in positive electrode [mol.m-3]") * 
                                                                                        pava.get("Positive electrode thickness [m]") * 
                                                                                        pava.get("Positive electrode active material volume fraction") * 
                                                                                        96485 / 3.6 / 10000))
        ## loss of lithium inventory from input
        if (pava.get("Loss of lithium inventory [%]") is None
            and pava.get("Loss of lithium inventory [mA.h.cm-2]") is None):
            # initialize loss of lithium inventory if not provided
            pava["Loss of lithium inventory [%]"] = 0
            pava["Loss of lithium inventory [mA.h.cm-2]"] = 0
            warnings.warn("Loss of lithium inventory, apart from LAM has been set to 0.")
        elif (pava.get("Loss of lithium inventory [%]") is None
              and pava.get("Loss of lithium inventory [mA.h.cm-2]") is not None):
            # calculate loss of lithium inventory from absolute value
            pava["Loss of lithium inventory [%]"] = pava.get("Loss of lithium inventory [mA.h.cm-2]") / pava.get("Initial lithium inventory [mA.h.cm-2]") * 100
        elif (pava.get("Loss of lithium inventory [%]") is not None
              and pava.get("Loss of lithium inventory [mA.h.cm-2]") is None):
            # calculate loss of lithium inventory from relative value
            pava["Loss of lithium inventory [mA.h.cm-2]"] = pava.get("Loss of lithium inventory [%]") / 100 * pava.get("Initial lithium inventory [mA.h.cm-2]")
        ## loss of lithium inventory from loss of active material
        pava["Total loss of lithium inventory [%]"] = pava.get("Loss of lithium inventory [%]")
        electrodes = ["negative electrode", "positive electrode"]
        for electrode in electrodes:
            if (pava.get(f"Loss of {electrode} active material [%]") is None
                and pava.get(f"{electrode.capitalize()} stoichiometry at LAM") is None):
                # initialize loss of active material if not provided
                pava[f"Loss of {electrode} active material [%]"] = 0
                pava[f"{electrode.capitalize()} stoichiometry at LAM"] = 0
                warnings.warn(f"'Loss of {electrode} active material [%]' and '{electrode.capitalize()} stoichiometry at LAM' has been set to 0.")
            elif ((pava.get(f"Loss of {electrode} active material [%]") is None) ^ 
                  (pava.get(f"{electrode.capitalize()} stoichiometry at LAM") is None)):
                raise ValueError(f"'Loss of {electrode} active material [%]' and '{electrode.capitalize()} stoichiometry at LAM' must be provided together.")
            # calculate loss of lithium inventory due to loss of active material
            pava["Total loss of lithium inventory [%]"] += (pava.get(f"{electrode.capitalize()} stoichiometry at LAM") *
                                                       pava.get(f"Loss of {electrode} active material [%]") *
                                                       pava.get(f"Maximum concentration in {electrode} [mol.m-3]") *
                                                       pava.get(f"{electrode.capitalize()} thickness [m]") *
                                                       pava.get(f"{electrode.capitalize()} active material volume fraction") /
                                                       pava.get("Initial lithium inventory [mA.h.cm-2]") *
                                                       96485 / 3.6 / 10000)
        # save lithium inventory and total loss of lithium inventory
        pava["Total loss of lithium inventory [mA.h.cm-2]"] = pava.get("Initial lithium inventory [mA.h.cm-2]") * pava.get("Total loss of lithium inventory [%]") / 100
        pava["Lithium inventory [mA.h.cm-2]"] = pava.get("Initial lithium inventory [mA.h.cm-2]") - pava.get("Total loss of lithium inventory [mA.h.cm-2]")
        self.parameter_values.update(pava, check_already_exists=False)
        self.stack_energy

    def print_masses_and_volumes(self):
        """
        A dataframe with components, volume-, mass loadings and densities on stack
        level.
        """
        stack_bd = self.masses_and_volumes

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

    def print_stack_energy(self):
        """
        A dataframe with capacities, energy densities, (single-)stack thickness and stack density.
        """
        stack_ed = self.stack_energy

        parameters = [
            "Volumetric stack energy [W.h.L-1]",
            "Gravimetric stack energy [W.h.kg-1]",
            "Areal stack energy [W.h.m-2]",
            "Stack average OCP [V]",
            "Capacity [mA.h.cm-2]",
            "Stack density [kg.L-1]",
            "Single stack thickness [um]",
        ]

        names = []
        units = []
        values = []

        for parameter in parameters:
            name, unit = parameter.split("[")
            names.append(name.strip())
            units.append(unit.rstrip(']'))
            values.append(stack_ed.get(parameter))

        data = {
            "Parameter": names,
            "Unit": units,
            "Value": values,
            }
        
        df = pd.DataFrame(data)
        return df

    def print_capacities_and_potentials(self):
        """
        A dataframe with potentials and stoichiometries.
        """
        stack_ed = self.stack_energy

        parameters = [
            "Stack average OCP [V]",
            "Negative electrode average OCP [V]",
            "Positive electrode average OCP [V]",
            "Negative electrode active material practical capacity [mA.h.g-1]",
            "Positive electrode active material practical capacity [mA.h.g-1]",      
            "Practical n/p ratio",
            "Capacity [mA.h.cm-2]",
            "Total loss of lithium inventory [mA.h.cm-2]",
            "Total loss of lithium inventory [%]",
            "First cycle coulombic efficiency",  
            "Positive electrode initial stoichiometry",
            "Negative electrode stoichiometry at 0% SoC",
            "Negative electrode stoichiometry at 100% SoC",
            "Positive electrode stoichiometry at 0% SoC",
            "Positive electrode stoichiometry at 100% SoC",
        ]

        names = []
        units = []
        values = []
        for parameter in parameters:
            if "[" in parameter:
                name, unit = parameter.split("[")
                names.append(name.strip())
                units.append(unit.rstrip(']'))
            else:
                names.append(parameter.strip())
                units.append("-")
            values.append(stack_ed.get(parameter))

        data = {
            "Parameter": names,
            "Unit": units,
            "Value": values,
            }
        
        df = pd.DataFrame(data)
        return df
        
    def print_electrolyte(self):
        """
        A dataframe with excess electrolyte metrics.
        """
        
        stack_ed = self.calculate_excess_electrolyte()

        parameters = [
            "Electrolyte volume per total pore volume",
            "Electrolyte volume per unit area [uL.cm-2]",
            "Electrolyte volume per capacity [uL.mA.h-1]",
            "Electrolyte volume per negative electrode active material mass [uL.mg-1]",
            "Electrolyte volume per positive electrode active material mass [uL.mg-1]",
        ]

        names = []
        units = []
        values = []

        for parameter in parameters:
            if "[" in parameter:
                name, unit = parameter.split("[")
                names.append(name.strip())
                units.append(unit.rstrip(']'))
            else:
                names.append(parameter.strip())
                units.append("-")
            values.append(stack_ed.get(parameter))

        data = {
            "Parameter": names,
            "Unit": units,
            "Value": values,
            }
        
        df = pd.DataFrame(data)
        return df
    
    def calculate_stack_energy(self):
        """
        Calculate ideal volumetric and gravimetric energy densities on stack level.
        Updates initial conditions and parameter values.
        """
        stack_ed = {}  # stack energy densities dict
        pava = dict(self.parameter_values)  # parameter values
        
        # constant OCP
        if isinstance(pava.get("Negative electrode OCP [V]"), (int, float)):
            ne_OCP = pava.get("Negative electrode OCP [V]")
            def negative_ocp(variables):
                return pybamm.Scalar(ne_OCP)
            #return pybamm.Vector([ne_OCP] * variables.shape[0])
            pava["Negative electrode OCP [V]"] = negative_ocp
        if isinstance(pava.get("Positive electrode OCP [V]"), (int, float)):
            pe_OCP = pava.get("Positive electrode OCP [V]")
            def positive_ocp(variables):
                return pybamm.Scalar(pe_OCP)
            #return pybamm.Vector([pe_OCP] * variables.shape[0])
            pava["Positive electrode OCP [V]"] = positive_ocp
            
        # calculate stoichiometries based on input for one electrode
        def calculate_stoichiometry_based_on_stoichiometry_limits(pava, input_electrode, output_electrode):
            input_100 = pava.get(f"{input_electrode} stoichiometry at 100% SoC")
            input_0 = pava.get(f"{input_electrode} stoichiometry at 0% SoC")
            # calculate maximum electrode capacities in mA.h.cm-2
            n_input = (pava.get(f"Maximum concentration in {input_electrode.lower()} [mol.m-3]")
                           * pava.get(f"{input_electrode} thickness [m]")
                           * pava.get(f"{input_electrode} active material volume fraction")
                           * 96485 / 3.6 / 10000)
            n_output = (pava.get(f"Maximum concentration in {output_electrode.lower()} [mol.m-3]")
                            * pava.get(f"{output_electrode} thickness [m]")
                            * pava.get(f"{output_electrode} active material volume fraction")
                            * 96485 / 3.6 / 10000)
            # calculate capacities at 100% and 0% SoC for input electrode in mA.h.cm-2
            n_input_0 = input_0 * n_input
            n_input_100 = input_100 * n_input
            if n_input_0 > pava.get("Lithium inventory [mA.h.cm-2]"):
                raise ValueError(f"Stoichiometry calculation failed. Lithium inventory in {input_electrode.lower()} at 0% SoC > Lithium inventory [mA.h.cm-2] ({n_input_0}>{pava.get('Lithium inventory [mA.h.cm-2]')})")
            # calculate capacities at 100% and 0% SoC for output electrode in mA.h.cm-2
            output_0 = (pava.get("Lithium inventory [mA.h.cm-2]") - n_input_0) / n_output
            output_100 = (pava.get("Lithium inventory [mA.h.cm-2]") - n_input_100) / n_output
            if output_0 < -1e-5 or output_100 < -1e-5 or output_0 > 1 + 1e-5 or output_100 > 1 + 1e-5:
                raise ValueError(f"Stoichiometry calculation for {output_electrode.lower()} failed. (0% SoC = {output_0}, 100% SoC = {output_100})")
            # return stoichiometries in x0, x100, y100, y0 format
            if input_electrode == "Positive electrode":
                return output_0, output_100, input_100, input_0
            elif input_electrode == "Negative electrode":
                return input_0, input_100, output_100, output_0
            
        def update_potential_limits(pava, x0, x100, y100, y0):
            try:
                pava["Lower voltage cut-off [V]"] = pava.get("Positive electrode OCP [V]")(y0).evaluate() - pava.get("Negative electrode OCP [V]")(x0).evaluate()
            except (AttributeError, TypeError):
                pava["Lower voltage cut-off [V]"] = pava.get("Positive electrode OCP [V]")(y0) - pava.get("Negative electrode OCP [V]")(x0)
            try:
                pava["Upper voltage cut-off [V]"] = pava.get("Positive electrode OCP [V]")(y100).evaluate() - pava.get("Negative electrode OCP [V]")(x100).evaluate()
            except (AttributeError, TypeError):
                pava["Upper voltage cut-off [V]"] = pava.get("Positive electrode OCP [V]")(y100) - pava.get("Negative electrode OCP [V]")(x100)
            
        # calculate stoichiometries
        def calculate_stoichiometries(pava):
            if (
                pava.get("Negative electrode stoichiometry at 0% SoC") is None
                and pava.get("Negative electrode stoichiometry at 100% SoC") is None
                and pava.get("Positive electrode stoichiometry at 100% SoC") is not None
                and pava.get("Positive electrode stoichiometry at 0% SoC") is not None
                ):
                # based on positive electrode stoichiometries
                x0, x100, y100, y0 = calculate_stoichiometry_based_on_stoichiometry_limits(
                    pava, input_electrode="Positive electrode", output_electrode="Negative electrode"
                    )
                update_potential_limits(pava, x0, x100, y100, y0)
            elif (
                pava.get("Negative electrode stoichiometry at 0% SoC") is not None
                and pava.get("Negative electrode stoichiometry at 100% SoC") is not None
                and pava.get("Positive electrode stoichiometry at 100% SoC") is None
                and pava.get("Positive electrode stoichiometry at 0% SoC") is None
                ):
                # based on negative electrode stoichiometries
                x0, x100, y100, y0 = calculate_stoichiometry_based_on_stoichiometry_limits(
                    pava, input_electrode="Negative electrode", output_electrode="Positive electrode"
                   )
                update_potential_limits(pava, x0, x100, y100, y0)         
            elif (
                pava.get("Negative electrode OCP [V]") is not None
                and pava.get("Positive electrode OCP [V]") is not None
                and pava.get("Lower voltage cut-off [V]") is not None
                and pava.get("Upper voltage cut-off [V]") is not None
                and pava.get("Negative electrode stoichiometry at 0% SoC") is None
                and pava.get("Negative electrode stoichiometry at 100% SoC") is None
                and pava.get("Positive electrode stoichiometry at 100% SoC") is None
                and pava.get("Positive electrode stoichiometry at 0% SoC") is None
                ):
                # based on cell potential limits
                x0, x100, y100, y0 = pybamm.lithium_ion.get_min_max_stoichiometries(
                    pybamm.ParameterValues(pava)
                    )
            else:
                raise ValueError("Stoichiometry calculation failed.")
            return x0, x100, y100, y0
        
        # calc initial min max stoichiometries for coulombic efficiency calculation
        x0_initial, x100_initial, y100_initial, y0_initial = calculate_stoichiometries(pava)
        # save initial condition
        y_initialized = pava.get("Initial concentration in positive electrode [mol.m-3]") / pava.get("Maximum concentration in positive electrode [mol.m-3]")
        
        # update concentrations and active material volume fractions
        electrodes = ["negative electrode", "positive electrode"]
        for electrode in electrodes:
            pava[f"Initial concentration in {electrode} [mol.m-3]"] = pava.get(f"Initial concentration in {electrode} [mol.m-3]") * (1 - pava.get("Total loss of lithium inventory [%]") / 100)
            pava[f"{electrode.capitalize()} active material volume fraction"] = pava.get(f"{electrode.capitalize()} active material volume fraction") * (1 - pava.get(f"Loss of {electrode} active material [%]") / 100)
        
        # update min max stoichiometries
        x0, x100, y100, y0 = calculate_stoichiometries(pava)
        
        # save stoichiometries
        stack_ed["Negative electrode stoichiometry at 0% SoC"] = x0
        stack_ed["Negative electrode stoichiometry at 100% SoC"] = x100
        stack_ed["Positive electrode stoichiometry at 100% SoC"] = y100
        stack_ed["Positive electrode stoichiometry at 0% SoC"] = y0
        
        # save min max OCVs
        try:
            stack_ed["Negative electrode OCV at 0% SoC [V]"] = pava.get("Negative electrode OCP [V]")(x0).evaluate()
            stack_ed["Negative electrode OCV at 100% SoC [V]"] = pava.get("Negative electrode OCP [V]")(x100).evaluate()
        except AttributeError:
            stack_ed["Negative electrode OCV at 0% SoC [V]"] = pava.get("Negative electrode OCP [V]")(x0)
            stack_ed["Negative electrode OCV at 100% SoC [V]"] = pava.get("Negative electrode OCP [V]")(x100)
        except TypeError:
            stack_ed["Negative electrode OCV at 0% SoC [V]"] = pava.get("Negative electrode OCP [V]")([x0]).evaluate()[0,0]
            stack_ed["Negative electrode OCV at 100% SoC [V]"] = pava.get("Negative electrode OCP [V]")([x100]).evaluate()[0,0]
        try:
            stack_ed["Positive electrode OCV at 0% SoC [V]"] = pava.get("Positive electrode OCP [V]")(x0).evaluate()
            stack_ed["Positive electrode OCV at 100% SoC [V]"] = pava.get("Positive electrode OCP [V]")(x100).evaluate()
        except AttributeError:
            stack_ed["Positive electrode OCV at 0% SoC [V]"] = pava.get("Positive electrode OCP [V]")(x0)
            stack_ed["Positive electrode OCV at 100% SoC [V]"] = pava.get("Positive electrode OCP [V]")(x100)
        except TypeError:
            stack_ed["Positive electrode OCV at 0% SoC [V]"] = pava.get("Positive electrode OCP [V]")([x0]).evaluate()[0,0]
            stack_ed["Positive electrode OCV at 100% SoC [V]"] = pava.get("Positive electrode OCP [V]")([x100]).evaluate()[0,0]            

        # initialize SoC = 1
        pava["Initial concentration in negative electrode [mol.m-3]"] = x100 * pava.get("Maximum concentration in negative electrode [mol.m-3]")
        pava["Initial concentration in positive electrode [mol.m-3]"] = y100 * pava.get("Maximum concentration in positive electrode [mol.m-3]")
        
        # average ocps
        soc = pybamm.linspace(0, 1)
        x = x0 + soc * (x100 - x0)
        y = y0 - soc * (y0 - y100)       
        stack_ed["Negative electrode average OCP [V]"] = pava["Negative electrode OCP [V]"](x).evaluate().mean()
        stack_ed["Positive electrode average OCP [V]"] = pava["Positive electrode OCP [V]"](y).evaluate().mean()
        stack_ed["Stack average OCP [V]"] = stack_ed["Positive electrode average OCP [V]"] - stack_ed["Negative electrode average OCP [V]"]

        # calculate electrode capacities
        electrodes = ["Negative electrode", "Positive electrode"]
        for electrode in electrodes:
            ## theoretical capacity without LAM
            # [A.h.L-1]
            stack_ed[f"{electrode} theoretical capacity [A.h.L-1]"] = (pava.get(f"Maximum concentration in {electrode.lower()} [mol.m-3]")
                                                                       * pava.get(f"{electrode} active material volume fraction")
                                                                       / (1 - pava.get(f"Loss of {electrode.lower()} active material [%]") / 100)
                                                                       * 96485 / 3.6 / 1000000)
            # [mA.h.g-1]
            stack_ed[f"{electrode} theoretical capacity [mA.h.g-1]"] = stack_ed.get(f"{electrode} theoretical capacity [A.h.L-1]") / pava.get(f"{electrode} density [kg.m-3]") * 1000
            # [mA.h.cm-2]
            stack_ed[f"{electrode} theoretical capacity [mA.h.cm-2]"] = stack_ed.get(f"{electrode} theoretical capacity [A.h.L-1]") * pava.get(f"{electrode} thickness [m]") * 100
            ## practical capacity with LAM
            if electrode == "Negative electrode":
                correction = (1 - x0) * (1 - pava.get(f"Loss of {electrode.lower()} active material [%]") / 100)
            elif electrode == "Positive electrode":
                correction = (y0 - y100) * (1 - pava.get(f"Loss of {electrode.lower()} active material [%]") / 100)
            # [mA.h.cm-2]
            stack_ed[f"{electrode} practical capacity [mA.h.cm-2]"] = stack_ed.get(f"{electrode} theoretical capacity [mA.h.cm-2]") * correction
            # [A.h.L-1]
            stack_ed[f"{electrode} practical capacity [A.h.L-1]"] = stack_ed.get(f"{electrode} theoretical capacity [A.h.L-1]") * correction
            # [mA.h.g-1]
            stack_ed[f"{electrode} practical capacity [mA.h.g-1]"] = stack_ed.get(f"{electrode} theoretical capacity [mA.h.g-1]") * correction
            # active material [mA.h.g-1]
            stack_ed[f"{electrode} active material practical capacity [mA.h.g-1]"] = pava.get(f"{electrode} active material theoretical capacity [mA.h.g-1]") * correction
            stack_ed[f"{electrode} active material practical capacity [mA.h.g-1]"] = stack_ed.get(f"{electrode} active material practical capacity [mA.h.g-1]")
            # active material [A.h.L-1]
            stack_ed[f"{electrode} active material practical capacity [A.h.L-1]"] = (stack_ed.get(f"{electrode} active material practical capacity [mA.h.g-1]")
                                                                                     * pava.get(f"{electrode} active material density [kg.m-3]") / 1000)
        
        # stack capacity
        stack_ed["Capacity [mA.h.cm-2]"] = stack_ed.get("Positive electrode practical capacity [mA.h.cm-2]")
        
        # initial charge capacity
        stack_ed["Initial charge capacity [mA.h.cm-2]"] = (y_initialized - y100_initial) * stack_ed.get(f"Positive electrode theoretical capacity [mA.h.cm-2]")

        # calculate first cycle coulombic efficiency
        stack_ed["First cycle coulombic efficiency"] = stack_ed.get(f"Capacity [mA.h.cm-2]") / stack_ed.get("Initial charge capacity [mA.h.cm-2]")

        # practical n/p ratio
        stack_ed["Practical n/p ratio"] = stack_ed.get("Negative electrode practical capacity [mA.h.cm-2]") / stack_ed.get("Positive electrode practical capacity [mA.h.cm-2]")
        
        # calculate areal stack energy density based on stack average OCP, areal capacity
        stack_ed["Areal stack energy [mW.h.cm-2]"] = stack_ed.get("Stack average OCP [V]") * stack_ed.get("Capacity [mA.h.cm-2]")
        stack_ed["Areal stack energy [W.h.m-2]"] = stack_ed.get("Areal stack energy [mW.h.cm-2]") * 10
        
        ## single stack thickness
        compartments = [
            "Negative current collector",
            "Negative electrode",
            "Separator",
            "Positive electrode",
            "Positive current collector",
        ]
        stack_ed["Single stack thickness [m]"] = 0
        for compartment in compartments:
            if pava.get(f"{compartment} thickness [m]") is None:
                warnings.warn(f"Missing '{compartment} thickness [m]'")
            elif "current collector" in compartment:
                stack_ed["Single stack thickness [m]"] += (
                    pava.get(f"{compartment} thickness [m]") / 2
                )
            else:
                stack_ed["Single stack thickness [m]"] += pava.get(
                    f"{compartment} thickness [m]"
                )

        # calculate volumetric stack capacity based on stack thickness and areal capacity
        stack_ed["Volumetric stack capacity [A.h.L-1]"] = (
            stack_ed.get("Capacity [mA.h.cm-2]")
            / stack_ed.get("Single stack thickness [m]")
            / 100
        )
        # calculate volumetric stack energy density based on volumetric stack capacity and stack average OCP
        stack_ed["Volumetric stack energy [W.h.L-1]"] = (
            stack_ed.get("Stack average OCP [V]")
            * stack_ed["Volumetric stack capacity [A.h.L-1]"]
        )

        # calculate stack density as the sum of the ratio's of compartment to stack thickness times the compartment density
        stack_ed["Stack density [kg.m-3]"] = 0
        for compartment in compartments:
            if pava.get(f"{compartment} density [kg.m-3]") is None:
                warnings.warn(f"Missing '{compartment} density [kg.m-3]'")
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
        ) / stack_ed.get("Single stack thickness [m]")

        # calculate gravimetric stack capacity based on volumetric stack capacity and stack density
        stack_ed["Gravimetric stack capacity [mA.h.g-1]"] = (
            stack_ed.get("Volumetric stack capacity [A.h.L-1]")
            / stack_ed.get("Stack density [kg.m-3]")
            * 1000
        )
        # calculate gravimetric stack energy density based on volumetric stack energy density and stack density
        stack_ed["Gravimetric stack energy [W.h.kg-1]"] = (
            stack_ed.get("Volumetric stack energy [W.h.L-1]")
            / stack_ed.get("Stack density [kg.m-3]")
            * 1000
        )

        # Add parameter for the dataframes
        stack_ed["Upper voltage cut-off [V]"] = pava.get("Upper voltage cut-off [V]")
        stack_ed["Lower voltage cut-off [V]"] = pava.get("Lower voltage cut-off [V]")
        stack_ed["Single stack thickness [um]"] = 10**6 * stack_ed.get("Single stack thickness [m]")
        stack_ed["Stack density [kg.L-1]"] = 10**-3 * stack_ed.get("Stack density [kg.m-3]")
        stack_ed["Initial lithium inventory [mA.h.cm-2]"] = pava.get("Initial lithium inventory [mA.h.cm-2]")
        stack_ed["Positive electrode initial stoichiometry"] = pava.get("Positive electrode initial stoichiometry")
        stack_ed["Lithium inventory [mA.h.cm-2]"] = pava.get("Lithium inventory [mA.h.cm-2]")
        stack_ed["Total loss of lithium inventory [mA.h.cm-2]"] = pava.get("Total loss of lithium inventory [mA.h.cm-2]")
        stack_ed["Total loss of lithium inventory [%]"] = pava.get("Total loss of lithium inventory [%]")
        stack_ed["Negative electrode active material theoretical capacity [mA.h.g-1]"] = pava.get("Negative electrode active material theoretical capacity [mA.h.g-1]")
        stack_ed["Positive electrode active material theoretical capacity [mA.h.g-1]"] = pava.get("Positive electrode active material theoretical capacity [mA.h.g-1]")
        stack_ed["Theoretical n/p ratio"] = pava.get("Theoretical n/p ratio")
        
        self.parameter_values.update(pava, check_already_exists=False)

        return stack_ed
    
    def calculate_excess_electrolyte(self):
        """
        Calculate electrolyte metrics.
        """
        stack_ed = self.stack_energy
        pava = dict(self.parameter_values)  # parameter values        
        
        # total pore volume
        stack_ed["Total pore volume per unit area [uL.cm-2]"] = (
            pava.get("Negative electrode porosity") *
            pava.get("Negative electrode thickness [m]") +
            pava.get("Separator porosity") *
            pava.get("Separator thickness [m]") +
            pava.get("Positive electrode porosity") *
            pava.get("Positive electrode thickness [m]")
        ) * 100000 # uL.cm-2 / m
        
        # calculate electrolyte relative to total pore volume from given input
        if pava.get("Electrolyte volume per total pore volume") is not None:
            stack_ed["Electrolyte volume per total pore volume"] = pava.get("Electrolyte volume per total pore volume")
        elif pava.get("Electrolyte volume per unit area [uL.cm-2]") is not None:
            stack_ed["Electrolyte volume per total pore volume"] = (
                pava.get("Electrolyte volume per unit area [uL.cm-2]") /
                stack_ed.get("Total pore volume per unit area [uL.cm-2]")
            )
        elif pava.get("Electrolyte volume per capacity [uL.mA.h-1]") is not None:
            stack_ed["Electrolyte volume per total pore volume"] = (
                pava.get("Electrolyte volume per capacity [uL.mA.h-1]") *
                stack_ed.get("Capacity [mA.h.cm-2]") /
                stack_ed.get("Total pore volume per unit area [uL.cm-2]")
            )
        elif pava.get("Electrolyte volume per negative electrode active material mass [uL.mg-1]") is not None:
            stack_ed["Electrolyte volume per total pore volume"] = (
                pava.get("Electrolyte volume per negative electrode active material mass [uL.mg-1]") *
                pava.get("Negative electrode active material volume fraction") /
                (1 - pava.get("Loss of negative electrode active material [%]") / 100) *
                pava.get("Negative electrode thickness [m]") *
                pava.get("Negative electrode density [kg.m-3]") /
                stack_ed.get("Total pore volume per unit area [uL.cm-2]")
            ) * 100
        elif pava.get("Electrolyte volume per positive electrode active material mass [uL.mg-1]") is not None:
            stack_ed["Electrolyte volume per total pore volume"] = (
                pava.get("Electrolyte volume per positive electrode active material mass [uL.mg-1]") *
                pava.get("Positive electrode active material volume fraction") /
                (1 - pava.get("Loss of positive electrode active material [%]") / 100) *
                pava.get("Positive electrode thickness [m]") *
                pava.get("Positive electrode density [kg.m-3]") /
                stack_ed.get("Total pore volume per unit area [uL.cm-2]")
            ) * 100
        else:
            stack_ed["Electrolyte volume per total pore volume"] = 1.0
            warnings.warn("'Electrolyte volume per total pore volume' is set to 1.0.")
            
        # calculate electrolyte metrics from electrolyte relative to total pore volume
        stack_ed["Electrolyte volume per unit area [uL.cm-2]"] = (
            stack_ed.get("Electrolyte volume per total pore volume") *
            stack_ed.get("Total pore volume per unit area [uL.cm-2]")
        )
        stack_ed["Electrolyte volume per capacity [uL.mA.h-1]"] = (
            stack_ed.get("Electrolyte volume per total pore volume") *
            stack_ed.get("Total pore volume per unit area [uL.cm-2]") /
            stack_ed.get("Capacity [mA.h.cm-2]")
        )
        stack_ed["Electrolyte volume per negative electrode active material mass [uL.mg-1]"] = (
            stack_ed.get("Electrolyte volume per total pore volume") *
            stack_ed.get("Total pore volume per unit area [uL.cm-2]") /
            pava.get("Negative electrode active material volume fraction") *
            (1 - pava.get("Loss of negative electrode active material [%]") / 100) /
            pava.get("Negative electrode thickness [m]") /
            pava.get("Negative electrode density [kg.m-3]")
        ) / 100
        stack_ed["Electrolyte volume per positive electrode active material mass [uL.mg-1]"] = (
            stack_ed.get("Electrolyte volume per total pore volume") *
            stack_ed.get("Total pore volume per unit area [uL.cm-2]") /
            pava.get("Positive electrode active material volume fraction") *
            (1 - pava.get("Loss of positive electrode active material [%]") / 100) /
            pava.get("Positive electrode thickness [m]") /
            pava.get("Positive electrode density [kg.m-3]")
        ) / 100

        return stack_ed

    def calculate_masses_and_volumes(self):
        """Breakdown volume- and mass loadings on stack level."""
        stack_bd = {}  # stack energy densities dict
        pava = self.parameter_values  # parameter values

        # volume fractions
        for electrode in ["Negative electrode", "Positive electrode"]:
            stack_bd[f"{electrode} electrolyte volume fraction"] = pava.get(
                f"{electrode} porosity"
            )
            stack_bd[f"{electrode} active material volume fraction"] = (pava.get(f"{electrode} active material volume fraction") /
                                                                        (1 - pava.get(f"Loss of {electrode.lower()} active material [%]") / 100))
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

        ## volume loadings
        # calculate volume loadings based on volume fractions and thicknesses
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
            pava.get("Negative current collector thickness [m]") * 100000
        )
        stack_bd["Positive current collector volume loading [uL.cm-2]"] = (
            pava.get("Positive current collector thickness [m]") * 100000
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
                warnings.warn(f"Missing '{component} density [kg.m-3]'")

        for electrode in ["Negative electrode", "Positive electrode"]:
            stack_bd[f"{electrode} electrolyte density [mg.uL-1]"] = (
                pava.get("Electrolyte density [kg.m-3]") / 1000
            )
            stack_bd[f"{electrode} density [mg.uL-1]"] = (
                pava.get(f"{electrode} density [kg.m-3]") / 1000
            )
            stack_bd[f"{electrode} dry density [mg.uL-1]"] = (
                pava.get(f"{electrode} density [kg.m-3]")
                - pava.get(f"{electrode} porosity")
                * pava.get("Electrolyte density [kg.m-3]")
            ) / 1000
            if stack_bd.get(f"{electrode} inactive material volume fraction") == 0:
                stack_bd[f"{electrode} inactive material density [mg.uL-1]"] = 0
                stack_bd[f"{electrode} active material density [mg.uL-1]"] = (
                    pava.get(f"{electrode} active material density [kg.m-3]") / 1000
                )
                warnings.warn(
                    f"{electrode} inactive material volume fraction is 0, "
                    f"{electrode} inactive material density is set to 0"
                )
            else:
                # calculate inactive material density as the remainder from electrode without active material and electrolyte
                stack_bd[f"{electrode} inactive material density [mg.uL-1]"] = (
                    (
                        pava.get(f"{electrode} density [kg.m-3]")
                        - pava.get(f"{electrode} porosity")
                        * pava.get("Electrolyte density [kg.m-3]")
                        - pava.get(f"{electrode} active material volume fraction") /
                        (1 - pava.get(f"Loss of {electrode.lower()} active material [%]") / 100)
                        * pava.get(f"{electrode} active material density [kg.m-3]")
                    )
                    / stack_bd.get(f"{electrode} inactive material volume fraction")
                    / 1000
                )
                stack_bd[f"{electrode} active material density [mg.uL-1]"] = (
                    pava.get(f"{electrode} active material density [kg.m-3]") / 1000
                )
        stack_bd["Separator electrolyte density [mg.uL-1]"] = (
            pava.get("Electrolyte density [kg.m-3]") / 1000
        )
        stack_bd["Separator density [mg.uL-1]"] = (
            pava.get("Separator density [kg.m-3]") / 1000
        )
        if pava.get("Separator porosity") == 1:
            stack_bd["Separator material density [mg.uL-1]"] = 0
            warnings.warn(
                "Separator porosity is 1, separator material density is "
                "set to 0"
            )
        else:
            # calculate separator material density as the remainder from separator without electrolyte
            stack_bd["Separator material density [mg.uL-1]"] = (
                (
                    pava.get("Separator density [kg.m-3]")
                    - pava.get("Separator porosity")
                    * pava.get("Electrolyte density [kg.m-3]")
                )
                / (1 - pava.get("Separator porosity"))
                / 1000
            )
            # calculate separator dry density based on separator and electrolyte density
            stack_bd["Separator dry density [mg.uL-1]"] = (
                pava.get("Separator density [kg.m-3]")
                - pava.get("Separator porosity")
                * pava.get("Electrolyte density [kg.m-3]")
            ) / 1000
        stack_bd["Negative current collector density [mg.uL-1]"] = (
            pava.get("Negative current collector density [kg.m-3]") / 1000
        )
        stack_bd["Positive current collector density [mg.uL-1]"] = (
            pava.get("Positive current collector density [kg.m-3]") / 1000
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

    def plot_masses_and_volumes(self, show_plot=False, axes=None):
        stack_bd = self.masses_and_volumes

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

        # Create the figure and axes objects
        if axes is None:
            fig = plt.figure(figsize=(12, 4), facecolor="white")
            ax = fig.add_axes([0.1, 0.2, 0.6, 0.6])
        else:
            ax = axes.inset_axes([0.1, 0.2, 0.6, 0.6])

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
        if show_plot is True:
            plt.show()
    
    def lithiation_plot(self, negative_active_material=None, positive_active_material=None, show_plot=False, axes=None, title=None):
        stack_energy = self.stack_energy
        
        if negative_active_material is None:
            negative_active_material = "-"
        if positive_active_material is None:
            positive_active_material = "+"
        
        # get the stoichiometries at 0% and 100% SoC
        x0 = stack_energy.get("Negative electrode stoichiometry at 0% SoC")
        x100 = stack_energy.get("Negative electrode stoichiometry at 100% SoC")
        y0 = stack_energy.get("Positive electrode stoichiometry at 0% SoC")
        y100 = stack_energy.get("Positive electrode stoichiometry at 100% SoC")
        U_p = self.parameter_values.get("Positive electrode OCP [V]")
        U_n = self.parameter_values.get("Negative electrode OCP [V]")
        
        # create vectors of stoichiometries
        soc = pybamm.linspace(0, 1, 1000)
        x = x0 + soc * (x100 - x0)
        y = y0 - soc * (y0 - y100)
        
        # create arrays of stoichiometries and OCPs
        soc_entries = soc.entries[:,0]
        u_minus_entries = U_n(soc).evaluate()[:,0]
        u_plus_entries = U_p(soc).evaluate()[:,0]
        u_stack_entries = U_p(y).evaluate()[:,0] - U_n(x).evaluate()[:,0]
        
        # create figure
        if axes is None:
            fig, ax1 = plt.subplots()
        else:
            ax1 = axes
        
        # Create plots
        ax1.plot(soc_entries, u_minus_entries, label=negative_active_material, color='orange')
        ax2 = ax1.twiny()
        ax2.spines['top'].set_position(('axes', 0.5))
        ax2.plot(soc_entries, u_stack_entries, label=f'{negative_active_material} || {positive_active_material}', color='black')
        ax3 = ax1.twiny()
        ax3.plot(soc_entries, u_plus_entries, label=positive_active_material, color='blue')
        
        # Set x-axis limits to match soc range
        ax3.invert_xaxis()
        ax3.set_xlim(1, 0)
        ax2.set_xlim(0 - (1 - y0) / (y0 - y100), 1 + (y100 - 0) / (y0 - y100))
        ax1.set_xlim(x0 - (x100 - x0) / (y0 - y100) * (1 - y0), x100 + (x100 - x0) / (y0 - y100) * (y100))
        
        # Add vertical lines and shaded regions for overlap
        ax3.axvline(y100, color='black', linestyle='-', linewidth=1)
        ax3.axvline(y0, color='black', linestyle='-', linewidth=1)
        ax3.axvspan(y100, y0, color='gray', alpha=0.2)
        
        # Set x-axis ticks
        ticks = [0, 0.2, 0.4, 0.6, 0.8, 1]
        ax1.set_xticks(ticks)
        ax2.set_xticks(ticks)
        ax3.set_xticks(ticks)
        
        # add legends
        ax1.legend(loc='lower right')
        ax2.legend(loc='center right')
        ax3.legend(loc='upper right')
        
        # add labels
        ax3.set_xlabel('Positive electrode lithiation [-]')
        ax2.set_xlabel('State of Charge [-]')
        ax1.set_xlabel('Negative electrode lithiation [-]')
        ax1.set_ylabel('Potential [V]')
        
        # add title
        if title is not None:
            ax1.set_title(title, pad=10)
            
        # layout
        plt.tight_layout()
        
        # Display the chart
        if show_plot is True:
            plt.show()

    
    def differential_lithiation_plot(self, negative_active_material=None, positive_active_material=None, show_plot=False, axes=None, title=None):
        stack_energy = self.stack_energy
        
        if negative_active_material is None:
            negative_active_material = "-"
        if positive_active_material is None:
            positive_active_material = "+"
        
        # get the stoichiometries at 0% and 100% SoC
        x0 = stack_energy.get("Negative electrode stoichiometry at 0% SoC")
        x100 = stack_energy.get("Negative electrode stoichiometry at 100% SoC")
        y0 = stack_energy.get("Positive electrode stoichiometry at 0% SoC")
        y100 = stack_energy.get("Positive electrode stoichiometry at 100% SoC")
        U_p = self.parameter_values.get("Positive electrode OCP [V]")
        U_n = self.parameter_values.get("Negative electrode OCP [V]")
        
        # create vectors of stoichiometries
        soc = pybamm.linspace(0, 1, 1000)
        x = x0 + soc * (x100 - x0)
        y = y0 - soc * (y0 - y100)
        
        # create arrays of stoichiometries and OCPs
        soc_entries = soc.entries[:,0]
        u_minus_entries = U_n(soc).evaluate()[:,0]
        u_plus_entries = U_p(soc).evaluate()[:,0]
        u_stack_entries = U_p(y).evaluate()[:,0] - U_n(x).evaluate()[:,0]
        
        # create figure
        if axes is None:
            fig, (ax1, ax2, ax3) = plt.subplots(3,1, figsize=(7,5))
        else:
            ax1, ax2, ax3 = axes
        
        # create plots
        # positive electrode
        ax1.plot(soc_entries, u_plus_entries, label=positive_active_material, color='blue')
        ax12 = ax1.twinx()
        dq_dv_plus = np.diff(soc_entries)/np.diff(u_plus_entries)
        ax12.plot(soc_entries[1:], -dq_dv_plus/np.max(-dq_dv_plus), color='blue', linestyle='--')
        # stack
        ax2.plot(soc_entries, u_stack_entries, label=f'{negative_active_material} || {positive_active_material}', color='black')
        ax22 = ax2.twinx()
        dq_dv_stack = np.diff(soc_entries)/np.diff(u_stack_entries)
        ax22.plot(soc_entries[1:], dq_dv_stack/np.max(dq_dv_stack), color='black', linestyle='--')
        # negative electrode
        ax3.plot(soc_entries, u_minus_entries, label=negative_active_material, color='orange')
        ax32 = ax3.twinx()
        dq_dv_minus = -np.diff(soc_entries)/np.diff(u_minus_entries)
        ax32.plot(soc_entries[1:], dq_dv_minus/np.max(dq_dv_minus), color='orange', linestyle='--')
        
        # set x-axis limits to match soc range
        ax1.invert_xaxis()
        ax12.invert_xaxis()
        ax1.set_xlim(1,0)
        ax12.set_xlim(ax1.get_xlim())
        ax2.set_xlim(0 - (1 - y0) / (y0 - y100), 1 + (y100 - 0) / (y0 - y100))
        ax22.set_xlim(ax2.get_xlim())
        ax3.set_xlim(x0 - (x100 - x0) / (y0 - y100) * (1 - y0), x100 + (x100 - x0) / (y0 - y100) * (y100))
        ax32.set_xlim(ax3.get_xlim())
        
        # add vertical lines and shaded regions for overlap
        ax1.axvline(y100, color='black', linestyle='-', linewidth=1)
        ax1.axvline(y0, color='black', linestyle='-', linewidth=1) 
        ax1.axvspan(y100, y0, color='gray', alpha=0.2)
        ax2.axvline(0, color='black', linestyle='-', linewidth=1)
        ax2.axvline(1, color='black', linestyle='-', linewidth=1) 
        ax2.axvspan(0, 1, color='gray', alpha=0.2)
        ax3.axvline(x0, color='black', linestyle='-', linewidth=1)
        ax3.axvline(x100, color='black', linestyle='-', linewidth=1) 
        ax3.axvspan(x0, x100, color='gray', alpha=0.2)
        
        # set other plot settings
        ax12.set_yticks([])
        ax12.set_ylabel('$dQ/dV^+ [-]$')
        ax1.set_xlabel('Positive electrode lithiation [-]')
        ax1.set_ylabel('$OCP^+ [V]$')
        ax12.set_xticks([0, 0.2, 0.4, 0.6, 0.8, 1])
        ax1.set_xticks([0, 0.2, 0.4, 0.6, 0.8, 1])
        ax22.set_yticks([])
        ax22.set_ylabel('$dQ/dV^{-||+} [-]$')
        ax2.set_xlabel('State of Charge [-]')
        ax2.set_ylabel('$OCP^{-||+} [V]$')
        ax22.set_xticks([0, 0.2, 0.4, 0.6, 0.8, 1])
        ax2.set_xticks([0, 0.2, 0.4, 0.6, 0.8, 1])
        ax32.set_yticks([])
        ax32.set_ylabel('$dQ/dV^- [-]$')
        ax3.set_xlabel('Negative electrode lithiation [-]')
        ax3.set_ylabel('$OCP^- [V]$')
        ax32.set_xticks([0, 0.2, 0.4, 0.6, 0.8, 1])
        ax3.set_xticks([0, 0.2, 0.4, 0.6, 0.8, 1])
        ax1.legend(loc='upper right')
        ax2.legend(loc='upper right')
        ax3.legend(loc='upper right')
        ax1.grid(axis='y')
        ax2.grid(axis='y')
        ax3.grid(axis='y')
        
        # adjust dQdV axis limit, if very high values are present
        if max(dq_dv_plus) > 1e4:
            percentile = 50
            threshold_value = np.percentile(dq_dv_plus, percentile)
            limit = np.max(dq_dv_plus[dq_dv_plus <= threshold_value])/np.max(dq_dv_plus)
            ax12.set_ylim(0, limit)
        if max(dq_dv_stack) > 1e4:
            percentile = 50
            threshold_value = np.percentile(dq_dv_stack, percentile)
            limit = np.max(dq_dv_stack[dq_dv_stack <= threshold_value])/np.max(dq_dv_stack)
            ax22.set_ylim(0, limit)
        if max(dq_dv_minus) > 1e4:
            percentile = 50
            threshold_value = np.percentile(dq_dv_minus, percentile)
            limit = np.max(dq_dv_minus[dq_dv_minus <= threshold_value])/np.max(dq_dv_minus)
            ax32.set_ylim(0, limit)            
        
        # add title
        if title is not None:
            ax1.set_title(title, pad=10)
        
        # add title
        plt.tight_layout()
        
        if show_plot is True:
            plt.show()

def ragone_plot(tea_class_list, C_rates, plot_capacities_and_potentials=False, label_list = None, show_plot = False, modes_list = None, model_list = None, solver_list = None, axes = None):
    
    if plot_capacities_and_potentials:
        if axes is None:
            fig, (ax1, ax2, ax3) = plt.subplots(1, 3, figsize=(15, 5))
        else:
            ax1, ax2, ax3 = axes
    else:
        if axes is None:
            fig, axs = plt.subplots(1, 1, figsize=(15, 5))
        else:
            axs = axes
    
    if label_list is None:
        label_list = ["" for _ in range(len(tea_class_list))]
    
    if modes_list is None:
        modes_list = ["CP" for _ in range(len(tea_class_list))]
    
    if model_list is None:
        model_list = [pybamm.lithium_ion.SPMe() for _ in range(len(tea_class_list))]
    
    if solver_list is None:
        solver_list = [pybamm.CasadiSolver(dt_max=120) for _ in range(len(tea_class_list))]
        
    # Generate a color array using a colormap
    colors = plt.cm.tab10(np.linspace(0, 1, len(tea_class_list)))
    line_styles = ['-', '--', '-.', ':', (5, (10, 3)), (0, (3, 1, 1, 1)), (0, (5, 5)), (0, (1, 1)), (0, (3, 1, 1, 1, 1, 1)), (0, (5, 1))]
    expanded_line_styles = (line_styles * (len(tea_class_list) // len(line_styles) + 1))[:len(tea_class_list)]
    
    for tea_class_, label_, color_, linestyle_, mode, model, solver_ in zip(tea_class_list, label_list, colors, expanded_line_styles, modes_list, model_list, solver_list):
        # get stack properties
        stack_thickness = tea_class_.stack_energy["Single stack thickness [m]"]
        stack_density = tea_class_.stack_energy["Stack density [kg.m-3]"]
        stack_area = tea_class_.parameter_values["Electrode height [m]"] * tea_class_.parameter_values["Electrode width [m]"]
        stack_grav_energy = tea_class_.stack_energy["Gravimetric stack energy [W.h.kg-1]"]
        stack_capacity = tea_class_.stack_energy["Capacity [mA.h.cm-2]"]
        stack_average_potential = tea_class_.stack_energy["Stack average OCP [V]"]
        total_capacity = stack_capacity * stack_area * 10
        # initialize arrays
        capacities = np.zeros_like(C_rates)
        currents_av = np.zeros_like(C_rates)
        voltage_av = np.zeros_like(C_rates)
        # solve the model for different C-rates
        for i, C_rate in enumerate(C_rates):
            if mode == "CC":
                experiment = pybamm.Experiment(
                    ["Discharge at {:.4f}A until {:.2f}V".format(total_capacity * C_rate, tea_class_.parameter_values.get("Lower voltage cut-off [V]"))],
                    period="{:.14f} seconds".format(10 / C_rate)
                    )
            elif mode == "CP":
                experiment = pybamm.Experiment(
                    ["Discharge at {:.4f}W until {:.2f}V".format(total_capacity * C_rate * stack_average_potential, tea_class_.parameter_values.get("Lower voltage cut-off [V]"))],
                    period="{:.14f} seconds".format(10 / C_rate)
                    )
            sim = pybamm.Simulation(
                model,
                experiment=experiment,
                solver=solver_,
                parameter_values=tea_class_.parameter_values
            )
            sim.solve()
            # extract the solution
            time = sim.solution["Time [s]"].entries
            capacity = sim.solution["Discharge capacity [A.h]"]
            current = sim.solution["Current [A]"]
            voltage = sim.solution["Voltage [V]"]
            capacities[i] = capacity(time[-1])
            currents_av[i] = np.mean(current(time))
            voltage_av[i] = np.mean(voltage(time))

        # plot the Ragone plot and capacities and potentials if desired
        if plot_capacities_and_potentials:
            ax1.plot(currents_av * voltage_av / stack_area / stack_thickness / stack_density, capacities * voltage_av / stack_area / stack_thickness / stack_density, color=color_, linestyle = linestyle_)
            ax1.set_xlabel('Stack power [W.kg-1]')
            ax1.set_ylabel('Stack energy [W.h.kg-1]')
            ax1.axhline(y=stack_grav_energy, color=color_)
            ax2.plot(currents_av / total_capacity, capacities / stack_area / 10, color=color_, linestyle = linestyle_, label=label_)
            ax2.axhline(y=stack_capacity, color=color_)
            ax2.set_xlabel('C-rate [h-1]')
            ax2.set_ylabel('Stack capacity [mA.h.cm-2]')
            ax3.plot(currents_av / total_capacity, voltage_av, color=color_, linestyle = linestyle_)
            ax3.axhline(y=stack_average_potential, color=color_)
            ax3.set_ylabel('Average voltage [V]')
            ax3.set_xlabel('C-rate [h-1]')
        else:
            axs.plot(currents_av * voltage_av / stack_area / stack_thickness / stack_density, capacities * voltage_av / stack_area / stack_thickness / stack_density, label=label_, color=color_, linestyle = linestyle_)
            axs.set_xlabel('Stack power [W.kg-1]')
            axs.set_ylabel('Stack energy [W.h.kg-1]')
            axs.axhline(y=stack_grav_energy, color=color_)
            
    # create a an array of c-rates for the grid
    c_rates_array = [1/10, 1, 2, 3, 6, 12, 60] # 10h, 1h, 30min, 10min, 3min
    label_rate = ["10h.", "1h.", "30min.", "20min.", "10min.", "5min.", "1min."]
    
    for rate, rate_label in zip(c_rates_array, label_rate):
        if plot_capacities_and_potentials:
            x_min, x_max = ax1.get_xlim()
            y_min, y_max = ax1.get_ylim()
            ax1.axline((0, 0), slope= 1 / rate, color="black", linestyle='-', alpha=0.25)
            if x_max/rate < y_max:
                ax1.text(x_max + (x_max-x_min) / 100 , x_max/rate, f'{rate_label}', fontsize=10, color='black', ha='left', va='center', alpha=0.5)
            elif y_max*rate < x_max and y_max*rate > x_min:
                ax1.text(y_max*rate, y_max + (y_max-y_min) / 50, f'{rate_label}', fontsize=10, color='black', ha='center', va='center', alpha=0.5)                
            ax1.set_xlim(x_min, x_max)
            ax1.set_ylim(y_min, y_max)
            if any(label != "" for label in label_list):
              ax2.legend(loc='upper center', bbox_to_anchor=(0.5, 1.15), ncol=len(tea_class_list))
            if axes is None:
                plt.subplots_adjust(wspace=0.35)
        else:
            x_min, x_max = axs.get_xlim()
            y_min, y_max = axs.get_ylim()
            axs.axline((0, 0), slope= 1 / rate, color="black", linestyle='-', alpha=0.25)
            if x_max/rate < y_max:
                axs.text(x_max + (x_max-x_min) / 100, x_max/rate, f'{rate_label}', fontsize=10, color='black', ha='left', va='center', alpha=0.5)
            elif y_max*rate < x_max and y_max*rate > x_min:
                axs.text(y_max*rate, y_max + (y_max-y_min) / 50, f'{rate_label}', fontsize=10, color='black', ha='center', va='center', alpha=0.5)
            axs.set_xlim(x_min, x_max)
            axs.set_ylim(y_min, y_max)
            if any(label != "" for label in label_list):
              axs.legend(loc='upper right')
                    
    if show_plot is True:
            plt.show()