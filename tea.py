import pybamm
import matplotlib.pyplot as plt
import numpy as np

class Tea(pybamm.BaseModel):
    def __init__(self, parameter_values=None):
        self.parameter_values=parameter_values
        if self.parameter_values is None:
            print("Warning: Missing parameter values, please supply parameter values to Tea()")
        super().__init__()

    def plot_ocvs(self, parameter_values=None):
        # plot ocv curves, average values against gravimetric capacity of cam and 
        # what if two different parameter sets are used? if, try, except?
        # in case it is called two times after each other, the second time it will not work
        # the solution is to call it the second time 
        parameter_values = self.parameter_values
        try:
            U_n = parameter_values["Negative electrode OCP [V]"]
            U_p = parameter_values["Positive electrode OCP [V]"]
        except KeyError:
            print("Error: Missing required parameters")
            return
        
        x0, x100, y100, y0 = pybamm.lithium_ion.get_min_max_stoichiometries(parameter_values)
        
        soc = pybamm.linspace(0, 1)  # cell level soc
        x = x0 + soc * (x100 - x0)
        y = y0 - soc * (y0 - y100)

        U_n_entries = U_n(x).entries
        U_p_entries = U_p(y).entries

        plt.clf()
        plt.figure()
        plt.plot(soc.entries, U_p_entries - U_n_entries, label='stack')
        plt.plot(soc.entries, U_p_entries, label='cathode')
        plt.plot(soc.entries, U_n_entries, label='anode')
        plt.xlabel('State of charge')
        plt.ylabel('Open circuit potential (V)')
        plt.legend()
        plt.show()

    def stack_energy_densities(self, input_parameter=None, print_values=False):
        if input_parameter is None:
            print("Warning: Missing input parameters")    

        '''if different parameter (e.g. for alloys or conversion-based cam) are of interest, all parameters can be supplied explicitly'''    
        
        # ocv's
        ne_ocv = self.parameter_values["Negative electrode OCP [V]"]
        pe_ocv = self.parameter_values["Positive electrode OCP [V]"]
        x0, x100, y100, y0 = pybamm.lithium_ion.get_min_max_stoichiometries(self.parameter_values)
        soc = pybamm.linspace(0, 1)  # cell level soc
        x = x0 + soc * (x100 - x0)
        y = y0 - soc * (y0 - y100)
        if input_parameter is None:
            ne_average_ocv = ne_ocv(x).entries.mean()
            pe_average_ocv = pe_ocv(y).entries.mean()
            stack_average_ocv = pe_average_ocv - ne_average_ocv
        else:
            try:
                ne_average_ocv = input_parameter["Negative electrode average OCP [V]"]
            except KeyError:
                ne_average_ocv = ne_ocv(x).entries.mean()
            try:
                pe_average_ocv = input_parameter["Positive electrode average OCP [V]"]
            except KeyError:
                pe_average_ocv = pe_ocv(y).entries.mean()
            try:
                stack_average_ocv = input_parameter["Stack average OCP [V]"]
            except KeyError:
                stack_average_ocv = pe_average_ocv - ne_average_ocv

        # areal capacity
        if input_parameter is None or input_parameter.get("Capacity [mA.h.cm-2]", None) is None:
            param = pybamm.LithiumIonParameters()
            esoh_solver = pybamm.lithium_ion.ElectrodeSOHSolver(self.parameter_values, param)
            Q_n = self.parameter_values.evaluate(param.n.Q_init)
            Q_p = self.parameter_values.evaluate(param.p.Q_init)
            Q_Li = self.parameter_values.evaluate(param.Q_Li_particles_init)
            inputs = {"Q_Li": Q_Li, "Q_n": Q_n, "Q_p": Q_p} # excess elyte
            sol = esoh_solver.solve(inputs)
            areal_capacity = sol["Capacity [mA.h.cm-2]"] # mA.h.cm-2 or better min(sol[Q_n * (x_100 - x_0)], sol[Q_p * (y_0 - y_100)])?
        else:
            areal_capacity = input_parameter["Capacity [mA.h.cm-2]"]

        # thicknesses
        if input_parameter is None:
            ne_thickness = self.parameter_values["Negative electrode thickness [m]"]
            pe_thickness = self.parameter_values["Positive electrode thickness [m]"]
            sep_thickness = self.parameter_values["Separator thickness [m]"]
            ne_cc_thickness = self.parameter_values["Negative current collector thickness [m]"]
            pe_cc_thickness = self.parameter_values["Positive current collector thickness [m]"]
        else:
            try:
                ne_thickness = input_parameter["Negative electrode thickness [m]"]
            except KeyError:
                ne_thickness = self.parameter_values["Negative electrode thickness [m]"]
            try:
                pe_thickness = input_parameter["Positive electrode thickness [m]"]
            except KeyError:
                pe_thickness = self.parameter_values["Positive electrode thickness [m]"]
            try:
                sep_thickness = input_parameter["Separator thickness [m]"]
            except KeyError:
                sep_thickness = self.parameter_values["Separator thickness [m]"]
            try:
                ne_cc_thickness = input_parameter["Negative current collector thickness [m]"]
            except KeyError:
                ne_cc_thickness = self.parameter_values["Negative current collector thickness [m]"]
            try:
                pe_cc_thickness = input_parameter["Positive current collector thickness [m]"]
            except KeyError:
                pe_cc_thickness = self.parameter_values["Positive current collector thickness [m]"]

        # volumetric stack energy density wh.L-1
        try:
            stack_thickness = input_parameter["Stack thickness [m]"] # better 'stack monolayer thickness'?
        except KeyError:
            stack_thickness = (ne_cc_thickness/2 + ne_thickness + sep_thickness + pe_thickness + pe_cc_thickness/2) # [m]
        volumetric_stack_energy_density = stack_average_ocv * areal_capacity / stack_thickness / 100 # [Wh.L-1]
        
        # densities
        if input_parameter is None:
            ne_density = self.parameter_values["Negative electrode density [kg.m-3]"] # density of dry electrode
            pe_density = self.parameter_values["Positive electrode density [kg.m-3]"]
            sep_density = self.parameter_values["Separator density [kg.m-3]"]
            ne_cc_density = self.parameter_values["Negative current collector density [kg.m-3]"]
            pe_cc_density = self.parameter_values["Positive current collector density [kg.m-3]"]
            elyte_density = self.parameter_values["Electrolyte density [kg.m-3]"] # density of electrolyte
            print("Warning: Missing Electrolyte density, [1276 kg.m-3] has been used") # EC:EMC 1:1
        else:
            try:
                ne_density = input_parameter["Negative electrode density [kg.m-3]"]
            except KeyError:
                try:
                    ne_density = self.parameter_values["Negative electrode density [kg.m-3]"]
                except KeyError:
                    print("Error: Missing parameter value for negative electrode density")
                    ne_density = float('-inf')
            try:
                pe_density = input_parameter["Positive electrode density [kg.m-3]"]
            except KeyError:
                try:
                    pe_density = self.parameter_values["Positive electrode density [kg.m-3]"]
                except KeyError:
                    print("Error: Missing parameter value for positive electrode density")
                    pe_density = float('-inf')
            try:
                sep_density = input_parameter["Separator density [kg.m-3]"]
            except KeyError:
                try:
                    sep_density = self.parameter_values["Separator density [kg.m-3]"]
                except KeyError:
                    print("Error: Missing parameter value for separator density")
                    sep_density = float('-inf')
            try:
                ne_cc_density = input_parameter["Negative current collector density [kg.m-3]"]
            except KeyError:
                try:
                    ne_cc_density = self.parameter_values["Negative current collector density [kg.m-3]"]
                except KeyError:
                        print("Error: Missing parameter value for negative current collector density")
                        ne_cc_density = float('-inf')
            try:
                pe_cc_density = input_parameter["Positive current collector density [kg.m-3]"]
            except KeyError:
                try:
                    pe_cc_density = self.parameter_values["Positive current collector density [kg.m-3]"]
                except KeyError:
                    print("Error: Missing parameter value for positive current collector density")
                    pe_cc_density = float('-inf')
            try:
                elyte_density = input_parameter["Electrolyte density [kg.m-3]"]
            except KeyError:
                try:
                    elyte_density = self.parameter_values["Electrolyte density [kg.m-3]"]
                except KeyError:
                    print("Warning: Missing Electrolyte density, [1276 kg.m-3] has been used")
                    elyte_density = 1276 # [kg.m-3]

        # porosities
        if input_parameter is None:
            ne_porosity = self.parameter_values["Negative electrode porosity"]
            pe_porosity = self.parameter_values["Positive electrode porosity"]
            sep_porosity = self.parameter_values["Separator porosity"]
        else:
            try:
                ne_porosity = input_parameter["Negative electrode porosity"]
            except KeyError:
                try:
                    ne_porosity = self.parameter_values["Negative electrode porosity"]
                except KeyError:
                    print("Error: Missing parameter value for negative electrode porosity")
                    ne_porosity = float('-inf')
            try:
                pe_porosity = input_parameter["Positive electrode porosity"]
            except KeyError:
                try:
                    pe_porosity = self.parameter_values["Positive electrode porosity"]
                except KeyError:
                    print("Error: Missing parameter value for positive electrode porosity")
                    pe_porosity = float('-inf')
            try:
                sep_porosity = input_parameter["Separator porosity"]
            except KeyError:
                try:
                    sep_porosity = self.parameter_values["Separator porosity"]
                except KeyError:
                    print("Error: Missing parameter value for separator porosity")
                    sep_porosity = float('-inf')

        # dry electrode composite and separator density
        try:
                ne_composite_density = input_parameter["Negative electrode composite density [kg.m-3]"]
        except KeyError:
            ne_composite_density = ne_density/(1-ne_porosity)
        try:
                pe_composite_density = input_parameter["Positive electrode composite density [kg.m-3]"]
        except KeyError:
            pe_composite_density = pe_density/(1-pe_porosity)
        try:
                sep_composite_density = input_parameter["Separator composite density [kg.m-3]"]
        except KeyError:
            sep_composite_density = sep_density/(1-sep_porosity)

        # weight fractions
        try:
                ne_composite_wt_fraction = input_parameter["Negative electrode composite weight fraction"]
                ne_elyte_wt_fraction = 1 - ne_composite_wt_fraction
        except KeyError:
            try:
                ne_elyte_wt_fraction = input_parameter["Negative electrode electrolyte weight fraction"]
                ne_composite_wt_fraction = 1 - ne_elyte_wt_fraction
            except KeyError:
                ne_composite_wt_fraction = (1-ne_porosity)*ne_composite_density/((1-ne_porosity)*ne_composite_density+ne_porosity*elyte_density)
                ne_elyte_wt_fraction = 1 - ne_composite_wt_fraction
        try:
                pe_composite_wt_fraction = input_parameter["Positive electrode composite weight fraction"]
                pe_elyte_wt_fraction = 1 - pe_composite_wt_fraction
        except KeyError:
            try:
                pe_elyte_wt_fraction = input_parameter["Positive electrode electrolyte weight fraction"]
                pe_composite_wt_fraction = 1 - pe_elyte_wt_fraction
            except KeyError:
                pe_composite_wt_fraction = (1-pe_porosity)*pe_composite_density/((1-pe_porosity)*pe_composite_density+pe_porosity*elyte_density)
                pe_elyte_wt_fraction = 1 - pe_composite_wt_fraction
        try:
                sep_composite_wt_fraction = input_parameter["Separator composite weight fraction"]
                sep_elyte_wt_fraction = 1 - sep_composite_wt_fraction
        except KeyError:
            try:
                sep_elyte_wt_fraction = input_parameter["Separator electrolyte weight fraction"]
                sep_composite_wt_fraction = 1 - sep_elyte_wt_fraction
            except KeyError:
                sep_composite_wt_fraction = (1-sep_porosity)*sep_density/((1-sep_porosity)*sep_density+sep_porosity*elyte_density)
                sep_elyte_wt_fraction = 1 - sep_composite_wt_fraction

        # electrode and separator with electrolyte density
        try:
                ne_w_elyte_density = input_parameter["Negative electrode with electrolyte density [kg.m-3]"]
        except KeyError:
            ne_w_elyte_density = ne_composite_density*ne_composite_wt_fraction + elyte_density*ne_elyte_wt_fraction
        try:
                pe_w_elyte_density = input_parameter["Positive electrode with electrolyte density [kg.m-3]"]
        except KeyError:
            pe_w_elyte_density = pe_composite_density*pe_composite_wt_fraction + elyte_density*pe_elyte_wt_fraction
        try:
                sep_w_density = input_parameter["Separator with electrolyte density [kg.m-3]"]
        except KeyError:
            sep_w_elyte_density = sep_composite_density*sep_composite_wt_fraction + elyte_density*sep_elyte_wt_fraction

        # gravimetric stack energy density wh.kg-1
        try:
            stack_density = input_parameter["Stack density [kg.m-3]"] # better 'stack mixed density'?
        except KeyError:
            stack_density = (ne_cc_thickness/2*ne_cc_density + ne_thickness*ne_w_elyte_density + sep_thickness*sep_w_elyte_density + pe_thickness*pe_w_elyte_density + pe_cc_thickness/2*pe_cc_thickness)/stack_thickness # [kg.m-3]
        
        gravimetric_stack_energy_density = volumetric_stack_energy_density / stack_density * 1000 # [Wh.kg-1]

        if print_values == True:
            print("Negative electrode average OCP [V]: ", ne_average_ocv)
            print("Positive electrode average OCP [V]: ", pe_average_ocv)
            print("Stack average OCP [V]: ", stack_average_ocv)
            print("Capacity [mA.h.cm-2]: ", areal_capacity)
            print("Negative electrode thickness [m]: ", ne_thickness)
            print("Positive electrode thickness [m]: ", pe_thickness)
            print("Separator thickness [m]: ", sep_thickness)
            print("Negative current collector thickness [m]: ", ne_cc_thickness)
            print("Positive current collector thickness [m]: ", pe_cc_thickness)
            print("Stack thickness [m]: ", stack_thickness)
            print("Negative electrode density [kg.m-3]: ", ne_density)
            print("Positive electrode density [kg.m-3]: ", pe_density)
            print("Separator density [kg.m-3]: ", sep_density)
            print("Negative current collector density [kg.m-3]: ", ne_cc_density)
            print("Positive current collector density [kg.m-3]: ", pe_cc_density)
            print("Stack density [kg.m-3]: ", stack_density)
            print("Volumetric stack energy density [Wh.L-1]: ", volumetric_stack_energy_density)
            print("Gravimetric stack energy density [Wh.kg-1]: ", gravimetric_stack_energy_density)
            print("Negative electrode composite density [kg.m-3]: ", ne_composite_density)
            print("Positive electrode composite density [kg.m-3]: ", pe_composite_density)
            print("Separator composite density [kg.m-3]: ", sep_composite_density)
            print("Negative electrode composite weight fraction: ", ne_composite_wt_fraction)
            print("Positive electrode composite weight fraction: ", pe_composite_wt_fraction)
            print("Separator composite weight fraction: ", sep_composite_wt_fraction)
            print("Negative electrode with electrolyte density [kg.m-3]: ", ne_w_elyte_density)
            print("Positive electrode with electrolyte density [kg.m-3]: ", pe_w_elyte_density)
            print("Separator with electrolyte density [kg.m-3]: ", sep_w_elyte_density)
            print("Negative electrode electrolyte weight fraction: ", ne_elyte_wt_fraction)
            print("Positive electrode electrolyte weight fraction: ", pe_elyte_wt_fraction)
            print("Separator electrolyte weight fraction: ", sep_elyte_wt_fraction)
            print("Electrolyte density [kg.m-3]: ", elyte_density)
            print("Negative electrode porosity: ", ne_porosity)
            print("Positive electrode porosity: ", pe_porosity)
            print("Separator porosity: ", sep_porosity)
            print("Negative electrode with electrolyte density [kg.m-3]: ", ne_w_elyte_density)
            print("Positive electrode with electrolyte density [kg.m-3]: ", pe_w_elyte_density)
            print("Separator with electrolyte density [kg.m-3]: ", sep_w_elyte_density)
            print("Negative electrode electrolyte weight fraction: ", ne_elyte_wt_fraction)
            print("Positive electrode electrolyte weight fraction: ", pe_elyte_wt_fraction)
            print("Separator electrolyte weight fraction: ", sep_elyte_wt_fraction)
            print("Electrolyte density [kg.m-3]: ", elyte_density)
            print("Negative electrode composite density [kg.m-3]: ", ne_composite_density)
            print("Positive electrode composite density [kg.m-3]: ", pe_composite_density)
            print("Separator composite density [kg.m-3]: ", sep_composite_density)
            print("Negative electrode composite weight fraction: ", ne_composite_wt_fraction)
            print("Positive electrode composite weight fraction: ", pe_composite_wt_fraction)
            print("Separator composite weight fraction: ", sep_composite_wt_fraction)

        return volumetric_stack_energy_density, gravimetric_stack_energy_density
        
    def stack_breakdown(self, input_parameter=None, print_values=False):
        # Assign densities based on ocv function and set electrolyte density to 1300 kg m-3?
        parameter_values = self.parameter_values
        if input_parameter is None:
            print("Error: Missing input parameters")
        else:
            # importing parameters
            # from input_parameter and if not available from parameter_values, optional to add binder/ca fration as input
            # import densities
            try:
                aam_density = input_parameter["Anode active material true density [kg.m-3]"]
            except KeyError:
                try:
                    aam_density = parameter_values["Anode active material true density [kg.m-3]"]
                except KeyError:
                    print("Error: Missing required AAM true density")
            try:
                electrolyte_density = input_parameter["Electrolyte true density [kg.m-3]"]
            except KeyError:    
                try:
                    electrolyte_density = parameter_values["Electrolyte true density [kg.m-3]"]
                except KeyError:
                    print("Error: Missing required electrolyte true density")
            try:
                cam_density = input_parameter["Cathode active material true density [kg.m-3]"]
            except KeyError:
                try:
                    cam_density = parameter_values["Cathode active material true density [kg.m-3]"]
                except KeyError:
                    print("Error: Missing required CAM true density")
            try:
                sep_density = input_parameter["Separator density [kg.m-3]"]
            except KeyError:
                try:
                    sep_density = parameter_values["Separator density [kg.m-3]"]
                except KeyError:
                    print("Error: Missing parameter value for separator density")
            try:
                ne_cc_density = input_parameter["Negative current collector density [kg.m-3]"]
            except KeyError:
                try:
                    ne_cc_density = parameter_values["Negative current collector density [kg.m-3]"]
                except KeyError:
                    print("Error: Missing parameter value for negative current collector density")
            try:
                pe_cc_density = input_parameter["Positive current collector density [kg.m-3]"]
            except KeyError:
                try:
                    pe_cc_density = parameter_values["Positive current collector density [kg.m-3]"]
                except KeyError:
                    print("Error: Missing parameter value for positive current collector density")
            try:
                pe_density = input_parameter["Positive electrode density [kg.m-3]"]
            except KeyError:
                try:
                    pe_density = parameter_values["Positive electrode density [kg.m-3]"]
                except KeyError:
                    print("Error: Missing parameter value for positive electrode density")
            try:
                ne_density = input_parameter["Negative electrode density [kg.m-3]"]
            except KeyError:
                try:
                    ne_density = parameter_values["Negative electrode density [kg.m-3]"]
                except KeyError:
                    print("Error: Missing parameter value for negative electrode density")
            # import volume fractions

        # negative electrode calculations
        ne_thickness = self.parameter_values["Negative electrode thickness [m]"]
        ne_aam_volume_fraction = self.parameter_values["Negative electrode active material volume fraction"]
        ne_aam_volume_loading = ne_aam_volume_fraction * ne_thickness
        ne_elyte_volume_fraction = self.parameter_values["Negative electrode porosity"]
        ne_elyte_volume_loading = ne_aam_volume_fraction * ne_thickness
        # "other" instead of conductive additive and binder?
        ne_ca_b_volume_fraction = self.parameter_values["Negative electrode porosity"]
        ne_ca_b_volume_loading = ne_aam_volume_fraction * ne_thickness
        # negative electrode - mass
        composite_density = self.parameter_values["Negative electrode composite density [kg.m-3]"]
        ne_mass_loading = composite_density/ne_thickness
        # density of active material & electrolyte needed
        ne_aam_mass_fraction = ne_aam_volume_fraction*aam_density
        #ne_aam_mass_loading = 
    #    ne_elyte_mass_fraction = ne_aam_volume_fraction*electrolyte_density
        #ne_elyte_mass_loading = 
        # "other" instead of conductive additive and binder?
        #ne_ca_b_mass_fraction =  
        #ne_ca_b_mass_loading = ne_mass_loading-ne_aam_mass_loading-ne_elyte_mass_loading
        # total masses & volumes of negative electrode


        # positive electrode
        #pe_aam_volume_fraction = parameter_values["Positive electrode active material volume fraction"]
        #pe_thickness = parameter_values["Positive electrode thickness [m]"]
        #pe_aam_volume_loading = pe_aam_volume_fraction * pe_thickness

param_lfp = pybamm.ParameterValues("Prada2013")
param_nmc = pybamm.ParameterValues("Chen2020")

lfp = Tea(parameter_values=param_lfp)
nmc = Tea(parameter_values=param_nmc)

# no current collector thicknesses and no densities in Prada2013
lfp_input_data = {"Negative current collector thickness [m]": 0.00001, # example
                  "Positive current collector thickness [m]": 0.00001, # example
                  "Anode active material true density [kg.m-3]": 2266, # Graphite
                  "Electrolyte material true density [kg.m-3]": 1276, # EC:EMC
                  "Cathode active material true density [kg.m-3]": 3600, # LFP
                  }
nmc_input_data = {"Anode active material true density [kg.m-3]": 2266, # Graphite
                  "Electrolyte material true density [kg.m-3]": 1276, # EC:EMC
                  "Cathode active material true density [kg.m-3]": 4870, # NMC811
              }

#lfp.plot_ocvs()
#nmc.plot_ocvs()

print("Chen2020")
energy_densities_NMC = nmc.stack_energy_densities(input_parameter=nmc_input_data, print_values=True)
print("Prada2013")
energy_densities_LFP = lfp.stack_energy_densities(input_parameter=lfp_input_data, print_values=True)
