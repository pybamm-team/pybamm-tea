import unittest
import pybamm
import pybamm_tea
import matplotlib.pyplot as plt
import pandas as pd 
import numpy as np


class TestTEA(unittest.TestCase):
    # load example model and reference data
    def ExampleModel(self):
        # load model
        input = {
            "Electrolyte density [kg.m-3]": 1276,
            "Negative electrode active material density [kg.m-3]": 2266,  # Graphite
            "Positive electrode active material density [kg.m-3]": 4750,  # NCO
            "Loss of lithium inventory [%]": 0.05,
            "Loss of negative electrode active material [%]": 0.05,
            "Negative electrode stoichiometry at LAM": 0.5,
        }
        base = pybamm.ParameterValues("Ecker2015")
        tea_class = pybamm_tea.TEA(base, input)
        # import dataframes
        self.ref_masses_and_volumes_dataframe = pd.read_csv("tests/masses_and_volumes.csv", index_col=0)
        self.ref_stack_energy_dataframe = pd.read_csv("tests/stack_energy.csv", index_col=0)
        self.ref_capacities_and_potentials = pd.read_csv("tests/capacities_and_potentials.csv", index_col=0)

        return tea_class
    
    # test masses and volumes
    def test_masses_and_volumes(self):

        # load example model
        tea_class = self.ExampleModel()

        # check if pandas dataframe and dict
        self.assertIsInstance(tea_class.masses_and_volumes, dict)
        self.assertIsInstance(tea_class.masses_and_volumes_dataframe, pd.DataFrame)

        # replace NaN values with empty string
        self.ref_masses_and_volumes_dataframe.replace(np.nan, "", inplace=True)
        tea_class.masses_and_volumes_dataframe.replace(np.nan, "", inplace=True)

        # compare each cell of the dataframe
        for i in self.ref_masses_and_volumes_dataframe.columns:
            for j in self.ref_masses_and_volumes_dataframe.index:
                if isinstance(tea_class.masses_and_volumes_dataframe[i][j], str):
                    self.assertEqual(
                        tea_class.masses_and_volumes_dataframe[i][j],
                        self.ref_masses_and_volumes_dataframe[i][j],
                    )
                else:
                    self.assertAlmostEqual(
                        round(tea_class.masses_and_volumes_dataframe[i][j], 7),
                        round(self.ref_masses_and_volumes_dataframe[i][j], 7),
                        )

    # test stack energy densities
    def test_stack_energy(self):

        # load example model
        tea_class = self.ExampleModel()

        # check if pandas dataframe and dict
        self.assertIsInstance(tea_class.stack_energy, dict)
        self.assertIsInstance(tea_class.stack_energy_dataframe, pd.DataFrame)

        # replace NaN values with empty string
        self.ref_stack_energy_dataframe.replace(np.nan, "", inplace=True)
        tea_class.stack_energy_dataframe.replace(np.nan, "", inplace=True)

        # compare each cell of the dataframe
        for i in self.ref_stack_energy_dataframe.columns:
            for j in self.ref_stack_energy_dataframe.index:
                if isinstance(tea_class.stack_energy_dataframe[i][j], str):
                    self.assertEqual(
                        tea_class.stack_energy_dataframe[i][j],
                        self.ref_stack_energy_dataframe[i][j],
                    )
                else:
                    self.assertAlmostEqual(
                        round(tea_class.stack_energy_dataframe[i][j], 7),
                        round(self.ref_stack_energy_dataframe[i][j], 7),
                        )

    # test capacities and potentials
    def test_capacities_and_potentials(self):

        # load example model
        tea_class = self.ExampleModel()

        # check if pandas dataframe and dict
        self.assertIsInstance(tea_class.capacities_and_potentials_dataframe, pd.DataFrame)

        # replace NaN values with empty string
        self.ref_capacities_and_potentials.replace(np.nan, "", inplace=True)
        tea_class.capacities_and_potentials_dataframe.replace(np.nan, "", inplace=True)

        # compare each cell of the dataframe
        for i in self.ref_capacities_and_potentials.columns:
            for j in self.ref_capacities_and_potentials.index:
                if isinstance(tea_class.capacities_and_potentials_dataframe[i][j], str):
                    self.assertEqual(
                        tea_class.capacities_and_potentials_dataframe[i][j],
                        self.ref_capacities_and_potentials[i][j],
                    )
                else:
                    self.assertAlmostEqual(
                        round(tea_class.capacities_and_potentials_dataframe[i][j], 7),
                        round(self.ref_capacities_and_potentials[i][j], 7),
                        )


    # test masses and volumes plot
    def test_plot_masses_and_volumes(self):
        tea_class = self.ExampleModel()
        self.assertIsInstance(tea_class.plot_masses_and_volumes(show_plot=False), plt.Figure)
    
    # test lithiation plot
    def test_lithiation_plot(self):
        tea_class = self.ExampleModel()
        self.assertIsInstance(tea_class.lithiation_plot(show_plot=False), plt.Figure)    
    
    # test differential lithiation plot
    def test_differential_lithiation_plot(self):
        tea_class = self.ExampleModel()
        self.assertIsInstance(tea_class.differential_lithiation_plot(show_plot=False), plt.Figure)
    
    # test Ragone plot
    def test_ragone_plot(self):
        tea_class = self.ExampleModel()
        self.assertIsInstance(pybamm_tea.plot_ragone([tea_class], C_rates = [1,2], plot_capacities_and_potentials=True, show_plot=False), plt.Figure)


if __name__ == "__main__":
    unittest.main()