#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Dec  6 13:48:27 2022

@author: dirac
"""
import copy
import numpy as np
import matplotlib.pyplot as plt
from Contrast_Calculator import *
from utils import graphene_thickness
from experimental import *

if __name__ == '__main__':
    #CONTRAST CLASS:
    #materials - list of materials, .csv files, should be stacked from flake down to substrate
    #heights - assuming the height of the substrate?
    #camera
    #lens
    #DEFAULTS EXIST:
    #source, medium, wavelength_resolution, angle_resolution, mode (of interpolation)
    
    #CONTRASTLOADER CLASS:
    #refraction
    #camera_file
    #source_spectrum
    #source_angle
    #DEFAULTS FOR THE KWARGS
    
    #list_c will contain:
        #[self.wavelength_domain, self.norm_source_spectrum, self.norm_source_intensity]
        #(128,)   (128, )   (128,)
    
    materials = ["/Users/dirac/Documents/QPRESS/pyseg/material_csv/silicondioxide.csv",
                 "/Users/dirac/Documents/QPRESS/pyseg/material_csv/graphene.csv"]
    camera = "/Users/dirac/Documents/QPRESS/pyseg/IMX264.csv"
    source_spectrum= 2600 #temperature of the source, used in Planck distribution, set this to a 
    #string if you want a Gaussian distribution, and a tuple if you want something custom
    source_angle = 1.0 
    heights = [ 900.0e-9, graphene_thickness(2)] #height of substrate, to this is added the thickness of 1,2,3... layers of graphene
    lens = {'NA':0.42, 
            'spectral_domain' : [400e-9, 700e-9]} #NA used to calculate angle domain, spectral domain is 
                                                        #visible light boundaries
    
    Loaded_Variables = ContrastLoader(refraction = materials, camera_file = camera, source_spectrum = source_spectrum,
                          source_angle = source_angle, heights = heights, lens = lens)
    
    Calculator = Loaded_Variables.getCalculator()
    returned_values, list_c = Calculator.getContrast(1) #Using graphene values
    
    integrand = list_c[0]
    wavelg = list_c[1]

    fig = plt.figure(figsize=(10,8))
    plt.plot(wavelg*1e9, integrand['r'], color='red', label = "Red Channel")
    #plt.plot(wavelg**1e9, integrand['g'], color='green', label="Green Channel")
    #plt.plot(wavelg**1e9, integrand['b'], color='blue', label="Blue Channel")
    #plt.axvline(90, label= "90 nm SiO2", color='fuchsia', linewidth = 3, linestyle='dashed')
    #plt.axvline(300, label= "300 nm SiO2", color='cyan', linewidth = 3, linestyle='dashed')
    plt.xlabel("Wavelength (nm)", fontsize=23)
    plt.ylabel("Integrand", fontsize=23)
    plt.title("Integrand of Red Color Channel", fontsize=23)
    plt.legend(fontsize=12, loc = 'upper right')
    plt.show()
    
    r, g, b = [returned_values[0]], [returned_values[1]], [returned_values[2]]
    print(r,g,b)
    
    thickness_layers = np.linspace(0, graphene_thickness(20))
    
    for idx, thickness in enumerate(thickness_layers[1:]):
        heights = copy.deepcopy(Calculator.heights)
        heights[1] = thickness
        Calculator.set_heights(heights)
        rgb, junk = Calculator.getContrast(1)
        r.append((rgb[0]))
        g.append((rgb[1]))
        b.append((rgb[2]))
        
    fig = plt.figure(figsize=(10,8))
    plt.plot(thickness_layers*1e9, r, color='red', label = "Red Channel")
    plt.plot(thickness_layers*1e9, g, color='green', label="Green Channel")
    plt.plot(thickness_layers*1e9, b, color='blue', label="Blue Channel")
    #plt.axvline(90, label= "90 nm SiO2", color='fuchsia', linewidth = 3, linestyle='dashed')
    #plt.axvline(300, label= "300 nm SiO2", color='cyan', linewidth = 3, linestyle='dashed')
    plt.xlabel("Thickness (nm) of SiO2", fontsize=23)
    plt.ylabel("Michelson Optical Contrast", fontsize=23)
    plt.title("Silicon Dioxide, 0 nm to 500 nm, Monolayer of Graphene", fontsize=23)
    plt.legend(fontsize=12, loc = 'upper right')
    plt.show()
    
    
    #print("Ground truth contrast of red: 7.03, green: -0.27, and blue: 5.30.")
    #re, ge, be = round(r[0], 2), round(g[0],2), round(b[0], 2)
    #print("Experimental contrast of red: {}, green: {}, and blue: {}".format(re, ge, be))
    
    
    #thickness_layers = np.linspace(10.0e-9, 500.0e-9, 100) #from 0 nm to 500 nm
    
    #for idx, thickness in enumerate(thickness_layers[1:]):
    #    heights = copy.deepcopy(Calculator.heights)
    #    heights[1] = thickness
    #    Calculator.set_heights(heights)
    #    rgb, junk = Calculator.getContrast(2)
    #    r.append((rgb[0]))
    #    g.append((rgb[1]))
    #    b.append((rgb[2]))
    #    list_extras.append(junk)
        
    #fig = plt.figure(figsize=(10,8))
    #plt.plot(thickness_layers*1e9, r, color='red', label = "Red Channel")
    #plt.plot(thickness_layers*1e9, g, color='green', label="Green Channel")
    #plt.plot(thickness_layers*1e9, b, color='blue', label="Blue Channel")
    #plt.axvline(90, label= "90 nm SiO2", color='orangered', linewidth = 3, linestyle='dashed')
    #plt.axvline(300, label= "300 nm SiO2", color='orangered', linewidth = 3, linestyle='dashed')
    #plt.xlabel("Thickness (nm) of SiO2")
    #plt.ylabel("Michelson Optical Contrast")
    #plt.title("Silicon thickness 100 nm, SiO2 0 nm to 500 nm, monolayer of graphene")
    #plt.legend()
    #plt.show()

        
    