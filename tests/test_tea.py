import unittest
import pybamm
from pybamm_tea import tea
import matplotlib.pyplot as plt
import pandas as pd 
import numpy as np


class TestTEA(unittest.TestCase):
    # load example model
    def ExampleModel(self):
        input = {
            "Electrolyte density [kg.m-3]": 1276,
            "Negative electrode active material density [kg.m-3]": 2266,  # Graphite
            "Positive electrode active material density [kg.m-3]": 4750,  # NCO
            "Initial loss of lithium inventory": 0.02,
        }
        base = pybamm.ParameterValues("Ecker2015")
        tea_class = tea.TEA(base, input)
        return tea_class
    
    # test stack breakdown
    def test_stack_breakdown(self):

        # load example model
        tea_class = self.ExampleModel()

        # check if pandas dataframe and dict
        self.assertIsInstance(tea_class.masses_and_volumes, dict)
        self.assertIsInstance(tea_class.masses_and_volumes_dataframe, pd.DataFrame)

        # import stack breakdown dataframe from csv
        ref_masses_and_volumes_dataframe = pd.read_csv("tests/masses_and_volumes_dataframe.csv", index_col=0)

        # replace NaN values with empty string
        ref_masses_and_volumes_dataframe.replace(np.nan, "", inplace=True)
        tea_class.masses_and_volumes_dataframe.replace(np.nan, "", inplace=True)

        # compare each cell of the dataframe
        for i in ref_masses_and_volumes_dataframe.columns:
            for j in ref_masses_and_volumes_dataframe.index:
                if isinstance(tea_class.masses_and_volumes_dataframe[i][j], str):
                    self.assertEqual(
                        tea_class.masses_and_volumes_dataframe[i][j],
                        ref_masses_and_volumes_dataframe[i][j],
                    )
                else:
                    self.assertAlmostEqual(
                        round(tea_class.masses_and_volumes_dataframe[i][j], 7),
                        round(ref_masses_and_volumes_dataframe[i][j], 7),
                        )

    # test stack energy densities
    def test_stack_energy(self):

        # load example model
        tea_class = self.ExampleModel()

        # check if pandas dataframe and dict
        self.assertIsInstance(tea_class.stack_energy, dict)
        self.assertIsInstance(tea_class.stack_energy_dataframe, pd.DataFrame)

        # import stack energy densities dataframe from csv
        ref_stack_energy_dataframe = pd.read_csv("tests/stack_energy_dataframe.csv", index_col=0)

        # replace NaN values with empty string
        ref_stack_energy_dataframe.replace(np.nan, "", inplace=True)
        tea_class.stack_energy_dataframe.replace(np.nan, "", inplace=True)

        # compare each cell of the dataframe
        for i in ref_stack_energy_dataframe.columns:
            for j in ref_stack_energy_dataframe.index:
                if isinstance(tea_class.stack_energy_dataframe[i][j], str):
                    self.assertEqual(
                        tea_class.stack_energy_dataframe[i][j],
                        ref_stack_energy_dataframe[i][j],
                    )
                else:
                    self.assertAlmostEqual(
                        round(tea_class.stack_energy_dataframe[i][j], 7),
                        round(ref_stack_energy_dataframe[i][j], 7),
                        )

    def test_capacities_and_potentials(self):

        # load example model
        tea_class = self.ExampleModel()

        # check if pandas dataframe and dict
        self.assertIsInstance(tea_class.capacities_and_potentials_dataframe, pd.DataFrame)

        # import stack breakdown dataframe from csv
        ref_capacities_and_potentials = pd.read_csv("tests/capacities_and_potentials_dataframe.csv", index_col=0)

        # replace NaN values with empty string
        ref_capacities_and_potentials.replace(np.nan, "", inplace=True)
        tea_class.capacities_and_potentials_dataframe.replace(np.nan, "", inplace=True)

        # compare each cell of the dataframe
        for i in ref_capacities_and_potentials.columns:
            for j in ref_capacities_and_potentials.index:
                if isinstance(tea_class.capacities_and_potentials_dataframe[i][j], str):
                    self.assertEqual(
                        tea_class.capacities_and_potentials_dataframe[i][j],
                        ref_capacities_and_potentials[i][j],
                    )
                else:
                    self.assertAlmostEqual(
                        round(tea_class.capacities_and_potentials_dataframe[i][j], 7),
                        round(ref_capacities_and_potentials[i][j], 7),
                        )


    # test stack breakdown plot
    def test_plot_masses_and_volumes(self):
        tea_class = self.ExampleModel()
        self.assertIsInstance(tea_class.plot_masses_and_volumes(testing=True), plt.Figure)


if __name__ == "__main__":
    unittest.main()