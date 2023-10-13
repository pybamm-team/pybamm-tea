import unittest
import pybamm
from pybamm_tea import TEA
import matplotlib.pyplot as plt
import pandas as pd


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

    # test stack energy densities dict
    def test_stack_energy_densities(self):
        tea_nco = self.ExampleModel()
        self.assertIsInstance(tea_nco.stack_energy_densities, dict)
        self.assertEqual(len(list(tea_nco.stack_energy_densities.keys())), 32)
        self.assertEqual(
            tea_nco.stack_energy_densities.get(
                "Gravimetric stack energy density [Wh.kg-1]"
            ).round(),
            200.0,
        )

    # test stack breakdown dict
    def test_stack_breakdown(self):
        tea_nco = self.ExampleModel()
        self.assertIsInstance(tea_nco.stack_breakdown, dict)
        self.assertEqual(len(list(tea_nco.stack_breakdown.keys())), 62)

    # test stack breakdown dataframe
    def test_stack_breakdown_dataframe(self):
        tea_nco = self.ExampleModel()
        self.assertIsInstance(tea_nco.stack_breakdown_dataframe, pd.DataFrame)
        self.assertEqual(
            list(tea_nco.stack_breakdown_dataframe.columns),
            ["Volume loading [uL.cm-2]", "Mass loading [mg.cm-2]", "Density [mg.uL-1]"],
        ), "stack_breakdown_dataframe columns are correct"

    # test stack breakdown plot
    def test_plot_stack_breakdown(self):
        tea_nco = self.ExampleModel()
        self.assertIsInstance(tea_nco.plot_stack_breakdown(testing=True), plt.Figure)


if __name__ == "__main__":
    unittest.main()
