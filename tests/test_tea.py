import unittest
import pybamm
from pybamm_tea import TEA
import matplotlib.pyplot as plt
import pandas as pd 
import numpy as np


class TestTEA(unittest.TestCase):
    # load example model
    def ExampleModel(self):
        nco_input_data = {
            "Electrolyte density [kg.m-3]": 1276,
            "Negative electrode active material density [kg.m-3]": 2266,  # Graphite
            "Positive electrode active material density [kg.m-3]": 4750,  # NCO
        }
        param_nco = pybamm.ParameterValues("Ecker2015")
        param_nco.update(nco_input_data, check_already_exists=False)
        tea_nco = TEA(param_nco, nco_input_data)
        return tea_nco
    
    # test stack breakdown
    def test_stack_breakdown(self):

        # load example model
        tea_nco = self.ExampleModel()

        # check if pandas dataframe and dict
        self.assertIsInstance(tea_nco.stack_breakdown, dict)
        self.assertIsInstance(tea_nco.stack_breakdown_dataframe, pd.DataFrame)

        # import stack breakdown dataframe from csv
        ref_stack_breakdown_dataframe = pd.read_csv("tests/stack_breakdown.csv", index_col=0)

        # replace NaN values with empty string
        ref_stack_breakdown_dataframe.replace(np.nan, "", inplace=True)
        tea_nco.stack_breakdown_dataframe.replace(np.nan, "", inplace=True)

        # compare each cell of the dataframe
        for i in ref_stack_breakdown_dataframe.columns:
            for j in ref_stack_breakdown_dataframe.index:
                if isinstance(tea_nco.stack_breakdown_dataframe[i][j], str):
                    self.assertEqual(
                        tea_nco.stack_breakdown_dataframe[i][j],
                        ref_stack_breakdown_dataframe[i][j],
                    )
                else:
                    self.assertAlmostEqual(
                        round(tea_nco.stack_breakdown_dataframe[i][j], 7),
                        round(ref_stack_breakdown_dataframe[i][j], 7),
                        )

    # test stack energy densities
    def test_stack_energy_densities(self):

        # load example model
        tea_nco = self.ExampleModel()

        # check if pandas dataframe and dict
        self.assertIsInstance(tea_nco.stack_energy_densities, dict)
        self.assertIsInstance(tea_nco.stack_energy_densities_dataframe, pd.DataFrame)

        # import stack energy densities dataframe from csv
        ref_stack_energy_densities_dataframe = pd.read_csv("tests/stack_energy_densities.csv", index_col=0)

        # replace NaN values with empty string
        ref_stack_energy_densities_dataframe.replace(np.nan, "", inplace=True)
        tea_nco.stack_energy_densities_dataframe.replace(np.nan, "", inplace=True)

        # compare each cell of the dataframe
        for i in ref_stack_energy_densities_dataframe.columns:
            for j in ref_stack_energy_densities_dataframe.index:
                if isinstance(tea_nco.stack_energy_densities_dataframe[i][j], str):
                    self.assertEqual(
                        tea_nco.stack_energy_densities_dataframe[i][j],
                        ref_stack_energy_densities_dataframe[i][j],
                    )
                else:
                    self.assertAlmostEqual(
                        round(tea_nco.stack_energy_densities_dataframe[i][j], 7),
                        round(ref_stack_energy_densities_dataframe[i][j], 7),
                        )

    def test_capacities_and_potentials(self):

        # load example model
        tea_nco = self.ExampleModel()

        # check if pandas dataframe and dict
        self.assertIsInstance(tea_nco.capacities_and_potentials_dataframe, pd.DataFrame)

        # import stack breakdown dataframe from csv
        ref_capacities_and_potentials = pd.read_csv("tests/capacities_and_potentials.csv", index_col=0)

        # replace NaN values with empty string
        ref_capacities_and_potentials.replace(np.nan, "", inplace=True)
        tea_nco.capacities_and_potentials_dataframe.replace(np.nan, "", inplace=True)

        # compare each cell of the dataframe
        for i in ref_capacities_and_potentials.columns:
            for j in ref_capacities_and_potentials.index:
                if isinstance(tea_nco.capacities_and_potentials_dataframe[i][j], str):
                    self.assertEqual(
                        tea_nco.capacities_and_potentials_dataframe[i][j],
                        ref_capacities_and_potentials[i][j],
                    )
                else:
                    self.assertAlmostEqual(
                        round(tea_nco.capacities_and_potentials_dataframe[i][j], 7),
                        round(ref_capacities_and_potentials[i][j], 7),
                        )


    # test stack breakdown plot
    def test_plot_stack_breakdown(self):
        tea_nco = self.ExampleModel()
        self.assertIsInstance(tea_nco.plot_stack_breakdown(testing=True), plt.Figure)


if __name__ == "__main__":
    unittest.main()
