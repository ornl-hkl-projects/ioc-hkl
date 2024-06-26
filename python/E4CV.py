import math
import numpy as np
import pandas as pd
import gi
from gi.repository import GLib
gi.require_version('Hkl', '5.0')
from gi.repository import Hkl
#from epics import PV
import inspect
from enum import IntEnum

#TODO create lists from individual values, change PVs accordingly
#TODO fix compute UB
#TODO add holds
#TODO add lattice set function [self.sample.lattice_set(lattice)], with reset of axes/pseudoaxes

class hklCalculator_E4CV():
    def __init__(self, num_axes_solns=15):
        # initials
        self.wavelength = 0.
        self.geom_name = 'E4CV'
        self.geometry = np.nan # hkl object placeholder
        self.detector = np.nan # hkl object placeholder
        self.factory = np.nan
        self.sample = np.nan # hkl object placeholder
        self.engines = np.nan # hkl object placeholder
        self.engine_hkl = np.nan # hkl object placeholder
        self.latt = [0., 0., 0., 0., 0., 0.] 
        # ^ [a1, a2, a3, alpha, beta, gamma], angstroms and radians
        self.lattice = np.nan 
        self.lattice_vol = 0.
        
        # sample orientation
        self.refl1_input = [0., 0., 0., 0., 0., 0., 0.] 
        self.refl2_input = [0., 0., 0., 0., 0., 0., 0.] 
        self.refl1 = np.nan # hkl object placeholder
        self.refl2 = np.nan # hkl object placeholder
        # ^ [h, k l, omega, chi, phi, tth]
        self.UB_matrix = np.zeros((3,3), dtype=float)
        #self.sample_rot_matrix = np.zeros((8,8), dtype=float)
        self.u_matrix = np.zeros((3,3), dtype=float)
        self.ux = 0.
        self.uy = 0.
        self.uz = 0.

        # axes
        self.num_axes_solns = num_axes_solns
        self.axes_omega = 0.
        self.axes_chi = 0.
        self.axes_phi = 0.
        self.axes_tth = 0.

        # axes for UB calculation - only used internally
        self.axes_omega_UB = 0.
        self.axes_chi_UB = 0.
        self.axes_phi_UB = 0.
        self.axes_tth_UB = 0.

        # pseduoaxes 
        self.pseudoaxes_h = 0.
        self.pseudoaxes_k = 0.
        self.pseudoaxes_l = 0.
        self.pseudoaxes_psi = 0.
        self.pseudoaxes_q = 0.
        self.pseudoaxes_incidence = 0.
        self.pseudoaxes_azimuth1 = 0.
        self.pseudoaxes_emergence = 0.
        self.pseudoaxes_azimuth2 = 0.
       
        # axes solutions 
        self.axes_solns_omega = []
        self.axes_solns_chi = []
        self.axes_solns_phi = []
        self.axes_solns_tth = []
        for _ in range(self.num_axes_solns):
            self.axes_solns_omega.append(0)
            self.axes_solns_chi.append(0)
            self.axes_solns_phi.append(0)
            self.axes_solns_tth.append(0)
        
        # pseudoaxes solutions
        self.pseudoaxes_solns_h = 0.
        self.pseudoaxes_solns_k = 0.
        self.pseudoaxes_solns_l = 0.
        self.pseudoaxes_solns_psi = 0.
        self.pseudoaxes_solns_q = 0.
        self.pseudoaxes_solns_incidence = 0.
        self.pseudoaxes_solns_azimuth1 = 0.
        self.pseudoaxes_solns_emergence = 0.
        self.pseudoaxes_solns_azimuth2 = 0.
 
    def start(self):
        self.detector = Hkl.Detector.factory_new(Hkl.DetectorType(0))
        self.factory  = Hkl.factories()[self.geom_name]
        self.geometry = self.factory.create_new_geometry()
        self.geometry.wavelength_set(self.wavelength, Hkl.UnitEnum.USER)
        
        self.sample = Hkl.Sample.new("toto")
        a,b,c,alpha,beta,gamma = [i for i in self.latt]
        alpha=math.radians(alpha)
        beta=math.radians(beta)
        gamma=math.radians(gamma)
        self.lattice = Hkl.Lattice.new(a,b,c,alpha,beta,gamma)
        #seg faults here
        self.sample.lattice_set(self.lattice)             

        self.engines = self.factory.create_new_engine_list()
        self.engines.init(self.geometry, self.detector, self.sample) # See if there's an "update" engine instead of "init"
        self.engines.get()
        self.engine_hkl = self.engines.engine_get_by_name("hkl")
    
    def forward(self):
        print("Forward function start")
        self.reset_pseudoaxes_solns()
        values_w = [float(self.axes_omega), \
                    float(self.axes_chi), \
                    float(self.axes_phi), \
                    float(self.axes_tth)] 

        try:
            self.geometry.axis_values_set(values_w, Hkl.UnitEnum.USER)
        except:
            print("invalid axes values")
            #TODO catch different types of errors
            return

        self.engines.init(self.geometry, self.detector, self.sample) # See if there's an "update" engine instead of "init"
        self.engines.get()
        self.engine_hkl = self.engines.engine_get_by_name("hkl")
 
        values_hkl = self.engine_hkl.pseudo_axis_values_get(Hkl.UnitEnum.USER)
        self.pseudoaxes_solns_h, self.pseudoaxes_solns_k, self.pseudoaxes_solns_l = values_hkl


    def forward_UB(self):
        print("Forward function start")
        values_w = [float(self.axes_omega_UB), \
                    float(self.axes_chi_UB), \
                    float(self.axes_phi_UB), \
                    float(self.axes_tth_UB)] 

        try:
            self.geometry.axis_values_set(values_w, Hkl.UnitEnum.USER)
        except:
            print("invalid axes values")
            #TODO catch different types of errors
            return


    def backward(self):
        print("Backward function start")
        self.reset_axes_solns()

        values_hkl = [float(self.pseudoaxes_h), \
                      float(self.pseudoaxes_k), \
                      float(self.pseudoaxes_l)]

        solutions = self.engine_hkl.pseudo_axis_values_set(values_hkl, Hkl.UnitEnum.USER)
        values_w_all = []
        for i, item in enumerate(solutions.items()):
            read = item.geometry_get().axis_values_get(Hkl.UnitEnum.USER)
            values_w_all.append(read)
        for i in range(self.num_axes_solns): #TODO out of index when less than max solns
            self.axes_solns_omega[i], self.axes_solns_chi[i], \
            self.axes_solns_phi[i], self.axes_solns_tth[i] = values_w_all[i]           

    def get_axes(self):
        axes = (self.axes_omega, self.axes_chi, self.axes_phi, self.axes_tth)
        print(axes)
        return axes 

    def get_pseudoaxes(self):
        pseudoaxes = (self.pseudoaxes_h, \
                      self.pseudoaxes_k, \
                      self.pseudoaxes_l)
        return pseudoaxes

    def get_axes_solns(self, cleanprint=False):
        axes = {}
        axes['omega'] = self.axes_solns_omega
        axes['chi']   = self.axes_solns_chi
        axes['phi']   = self.axes_solns_phi
        axes['tth']   = self.axes_solns_tth
        if(cleanprint==False):
            return axes
        elif(cleanprint==True):
            axes_df = pd.DataFrame(axes)
            return axes_df

    def get_pseudoaxes_solns(self):
        pseudoaxes_solns = (self.pseudoaxes_solns_h, \
                      self.pseudoaxes_solns_k, \
                      self.pseudoaxes_solns_l)
        return pseudoaxes_solns

    def reset_pseudoaxes_solns(self):
        self.pseudoaxes_solns_h = 0
        self.pseudoaxes_solns_k = 0
        self.pseudoaxes_solns_l = 0
        self.pseudoaxes_solns_psi = 0
        self.pseudoaxes_solns_q = 0
        self.pseudoaxes_solns_incidence = 0
        self.pseudoaxes_solns_azimuth1 = 0
        self.pseudoaxes_solns_emergence = 0
        self.pseudoaxes_solns_azimuth2 = 0

    def reset_axes_solns(self):
        self.axes_solns_omega = []
        self.axes_solns_chi = []
        self.axes_solns_phi = []
        self.axes_solns_tth = []
        for _ in range(self.num_axes_solns):
            self.axes_solns_omega.append(0)
            self.axes_solns_chi.append(0)
            self.axes_solns_phi.append(0)
            self.axes_solns_tth.append(0)
 
    def compute_UB_matrix(self):
        print("Computing UB matrix")
        self.add_reflection1()
        self.add_reflection2()
        self.sample.compute_UB_busing_levy(self.refl1, self.refl2)
        UB = self.sample.UB_get()
        for i in range(3):
            for j in range(3):
                self.UB_matrix[i,j] = UB.get(i,j)

    def get_UB_matrix(self):
        return self.UB_matrix


    def add_reflection1(self):
        self.axes_omega_UB = self.refl1_input[3]
        self.axes_chi_UB   = self.refl1_input[4]
        self.axes_phi_UB   = self.refl1_input[5]
        self.axes_tth_UB   = self.refl1_input[6]
        self.forward_UB() # replace with an update of sample with motor positions 
        # Hkl.SampleReflection(self.geometry, self.detector, h, k, l)
        self.refl1 = self.sample.add_reflection(self.geometry, self.detector, \
                    self.refl1_input[0], self.refl1_input[1], self.refl1_input[2])

    def add_reflection2(self):
        self.axes_omega_UB = self.refl2_input[3]
        self.axes_chi_UB   = self.refl2_input[4]
        self.axes_phi_UB   = self.refl2_input[5]
        self.axes_tth_UB   = self.refl2_input[6]
        self.forward_UB()
        # Hkl.SampleReflection(self.geometry, self.detector, h, k, l)
        self.refl2 = self.sample.add_reflection(self.geometry, self.detector, \
                    self.refl2_input[0], self.refl2_input[1], self.refl2_input[2])

    def reset(self):
        #DELETE
        # replace with conventional way
        self.__init__()

    def get_sample_rotation(self):
        rot = self.geometry.sample_rotation_get(self.sample).to_matrix()
        dim = len(self.sample_rot_matrix)
        for i in range(dim):
            for j in range(dim):
                self.sample_rot_matrix[i,j] = rot.get(i,j)     
        return self.sample_rot_matrix  

    def get_u_matrix(self):
        rot = self.sample.U_get()
        dim = len(self.u_matrix)
        for i in range(dim):
            for j in range(dim):
                self.u_matrix[i,j] = rot.get(i,j)     
        return self.u_matrix

    def get_u_xyz(self):
        self.ux = self.sample.ux_get().value_get(0)
        self.uy = self.sample.uy_get().value_get(0)
        self.uz = self.sample.uz_get().value_get(0)
        return self.ux, self.uy, self.uz

    def set_wavelength(self, wlen):
        self.wavelength = wlen

    def get_latt_vol(self):
        self.lattice_vol = self.lattice.volume_get().value_get(0)
        return self.lattice_vol

    def print_values(self):
        # Initials
        vol = self.get_latt_vol()
        # Forward
        axes = self.get_axes()
        pseudoaxes_solns = self.get_pseudoaxes_solns()
        # Backward
        pseudoaxes = self.get_pseudoaxes()
        axes_solns = self.get_axes_solns(cleanprint=True)
        # orientation
        u = self.get_u_matrix()
        ux,uy,uz = self.get_u_xyz()
        ub = self.get_UB_matrix()
        #sample_rot_m = self.get_sample_rotation()
        print("Initial conditions:")
        print("##################################")
        print(f'wavelength: {self.wavelength}')
        print(f'geometry: {self.geom_name}')
        print(f'lattice: {self.latt}')
        print(f'lattice volume: {vol}')
        print("Forward")
        print("##################################")
        print(f'input axes: {axes}') 
        print(f'pseudoaxes solutions: {pseudoaxes_solns}')
        print("Backward")
        print("##################################")
        print(f'input pseudoaxes: {pseudoaxes}')
        print(f'axes solutions: {axes_solns}')
        print("Orientation")
        print("##################################")
        print(f'reflection #1: {self.refl1_input}')
        print(f'reflection #2: {self.refl2_input}') 
        print(f'u matrix: \n {u}')
        print(f'u vector: ux, uy, uz: {ux}, {uy}, {uz}')
        print(f'UB:\n {ub}')
        #print(f'sample rotation/quaternion:\n {sample_rot_m}')

    def test(self):
        # starting sample, instrument parameters
        self.wavelength = 1.54 #Angstrom
        self.geom_name = 'E4CV' # 4-circle
        self.latt = [1.54, 1.54, 1.54,
                90.,
                90.,
                90.] # cubic
        self.start() # start hkl
        
        # forward test
        self.axes_omega = 30.
        self.axes_chi   = 0.
        self.axes_phi   = 0.
        self.axes_tth   = 60.
        
        print("\n\n\nRunning Forward\n")
        self.forward() 
        self.print_values()

        # backward test
        self.pseudoaxes_h = 0.
        self.pseudoaxes_k = 0.
        self.pseudoaxes_l = 1.
        print("\n\n\nRunning Backward\n")
        self.backward()
        self.print_values()
 
        #UB matrix test
        # reflection #1
        self.refl1_input[3] = -145.451 # omega
        self.refl1_input[4] = 0 # chi
        self.refl1_input[5] = 0 # phi
        self.refl1_input[6] = 69.0966 # tth
        self.refl1_input[0] = 4 # h
        self.refl1_input[1] = 0 # k
        self.refl1_input[2] = 0 # l
        # reflection #2
        self.refl2_input[3] = -145.451 # omega
        self.refl2_input[4] = 90 # chi
        self.refl2_input[5] = 0 # phi
        self.refl2_input[6] = 69.0966 # tth
        self.refl2_input[0] = 0 # h
        self.refl2_input[1] = 4 # k
        self.refl2_input[2] = 0 # l
        # UB calculation
        
        print("\n\n\nPre-UB Caclulation\n")
        self.print_values()
        self.compute_UB_matrix()
        print("\n\n\nPost-UB Caclulation\n")
        self.print_values()
