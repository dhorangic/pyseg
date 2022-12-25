#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Dec  1 11:20:56 2022

@author: dirac
"""

import code
import json
import argparse
import sys 
import os
import time
import csv
import matplotlib.pyplot as plt
import numpy as np
from scipy.integrate import simps as simpson
from scipy.interpolate import interp1d

from utils import gaussian, planck, getCSVFloats, getTransmissionAngle, partialReflection_p, partialReflection_s

__all__ = ['ContrastLoader', 'Contrast']

class ContrastLoader:
    def __init__(self, refraction, camera_file, source_spectrum, source_angle, **kwargs):
        refractive_data = []
        for n in refraction:
            try:
                c = complex(n)
                refractive_data.append(c)
            except:
                rows = getCSVFloats(n)
                wv   = np.array([i[0] for i in rows]) * 1e-6
                n0   = np.array([i[1] for i in rows])
                try:
                    k0   = np.array([i[2] for i in rows])
                except:
                    k0 = np.ones(len(n0)) * 0.0
                n0 = [complex(n0[i], k0[i]) for i in range(len(n0))]
                refractive_data.append({'lambda': wv, 'n': n0})
        color_data = getCSVFloats(camera_file)
        
        wv = [i[0] for i in color_data]
        r = [i[1] for i in color_data]
        g = [i[2] for i in color_data]
        b = [i[3] for i in color_data]
        camera = {
            'r' : {'lambda':wv, 'I':r},
            'g' : {'lambda':wv, 'I':g},
            'b' : {'lambda':wv, 'I':b}
            }
        try:
            s=float(source_spectrum)
            source_spectrum = s
        except:
            if ',' not in source_spectrum:
                data = getCSVFloats(source_spectrum)
                wv = [i[0] for i in data]
                I = [i[1] for i in data]
                source_spectrum = {'lambda':wv, "I":I}
        
        try:
            g = float(source_angle)
            source_angle = g
        except:
            data = getCSVFloats(source_angle)
            angle = [i[0] for i in data]
            I = [i[1] for i in data]
            source_angle = (wv, I)
        source = {
            'spectrum' : source_spectrum,
            'angle_dependence' : source_angle}
        self.args = {
            'materials' : refractive_data,
            'camera' : camera,
            'source' : source,
            **kwargs}
    
    def getCalculator(self):
        return Contrast(**self.args)
    


class Contrast:
    def __init__(self, materials, heights, camera, lens, 
                 source = {'spectrum': 300, 'angle_dependence': 0.1},
                 medium = complex(1.0003, 0.0), # Air 
                 wavelength_resolution = 128, 
                 angle_resolution = 128,
                 mode = 'cubic'):
        self.materials = materials
        self.heights = heights
        self.camera = camera
        self.source = source
        self.lens = lens
        self.medium = medium
        self.wavelength_resolution = wavelength_resolution
        self.angle_resolution = angle_resolution
        self.mode = mode

        #Angle bounds:
        NA = self.lens['NA']
        self.angle_domain = np.linspace(0.0, np.arcsin(NA/self.medium.real), self.wavelength_resolution)
        
        #Wavelength bounds:
        _min, _max = self.wavelength_dom()
        self.wavelength_domain = np.linspace(_min, _max, self.wavelength_resolution)
        
        #Interpolate wavelength-dependent data and resample it:
        self.resample_w()        
     
    def wavelength_dom(self):
         #Calculates the wavelength domain.
         
         wvmin= 0.0
         wvmax = 1.0
         
         for ni in self.materials:
             if not type(ni) is complex:
                 lower = np.array(ni['lambda']).min()
                 upper = np.array(ni['lambda']).max()
                 wvmin = max(wvmin, lower)
                 wvmax = min(wvmax, upper)
                 
         R_min = np.array(self.camera['r']['lambda']).min()
         R_max = np.array(self.camera['r']['lambda']).max()
         G_min = np.array(self.camera['g']['lambda']).min()
         G_max = np.array(self.camera['g']['lambda']).max()
         B_min = np.array(self.camera['b']['lambda']).min()
         B_max = np.array(self.camera['b']['lambda']).max()
         wvMin = max(wvmin, R_min)
         wvMin = max(wvmin, G_min)
         wvMin = max(wvmin, B_min)

         wvMax = min(wvmax, R_max)
         wvMax = min(wvmax, G_max)
         wvMax = min(wvmax, B_max)
         
         # Check the wavelength domain of the source spectrum, if it is provided as wavelength 
         # dependent values. Otherwise it is a color temperature and the domain is (0, inf).
         if isinstance(self.source['spectrum'], tuple):
             sourceMin = np.array(self.source['spectrum']['lambda']).min()
             sourceMax = np.array(self.source['spectrum']['lambda']).max()
             wvMin = max(wvMin, sourceMin)
             wvMax = min(wvMax, sourceMax)
             
         # Constrain the bounds based on the range of wavelengths that the objective lens is 
         # transparent to.
         wvMin = max(wvMin, self.lens['spectral_domain'][0])
         wvMax = min(wvMax, self.lens['spectral_domain'][1])
         return [wvMin, wvMax]
     
    def resample_w(self):
         #Resamples wavelength-dependent data so that indices match up.
         
         refractive_indices= []
         
         for ni in self.materials:
             if type(ni) is complex:
                 x = self.wavelength_domain
                 y = np.ones(self.wavelength_resolution) * ni
                 refractive_indices.append({'lambda' : x, 'n' : y})
             else:
                 refractive_indices.append(ni)
         
         source_spectrum = None
         if not isinstance(self.source['spectrum'], tuple):
             if isinstance(self.source['spectrum'], str):
                 print("Using Gaussian spectrum.")
                 center, fwhm = [float(i) for i in self.source['spectrum'].split(',')]
                 s = fwhm / np.sqrt(2*np.log(2.0))
                 source_spectrum = (self.wavelength_domain, gaussian(self.wavelength_domain, s, center))
             else:
                 print("Using Planck spectrum.")
                 source_spectrum = (self.wavelength_domain, planck(self.wavelength_domain, self.source['spectrum']))
         else:
             print("Skipping source refinement.")
             source_spectrum = self.source['spectrum']
             
         self.refractive_data = []
         for ni in refractive_indices:
             interp = interp1d(ni['lambda'], ni['n'], kind=self.mode)
             self.refractive_data.append(interp(self.wavelength_domain))
         
         Rinterp = interp1d(self.camera['r']['lambda'], self.camera['r']['I'], kind=self.mode)
         Ginterp = interp1d(self.camera['g']['lambda'], self.camera['g']['I'], kind=self.mode)
         Binterp = interp1d(self.camera['b']['lambda'], self.camera['b']['I'], kind=self.mode)
         self.redresponse = Rinterp(self.wavelength_domain)
         self.greenresponse = Ginterp(self.wavelength_domain)
         self.blueresponse = Binterp(self.wavelength_domain)
         
         spectrumInterp = interp1d(source_spectrum[0], source_spectrum[1], kind = self.mode)
         self.source_spectrum = spectrumInterp(self.wavelength_domain)
         
         self.source_intensity = np.exp(-2.0*np.square(np.sin(self.angle_domain/np.square(np.sin(self.angle_domain[-1])))))
         self.normalize()
    
    def normalize(self):
        #Normalizes the red, green, and blue responses, along with the source spectrum and source intensity.
        
        redC = simpson(self.redresponse, self.wavelength_domain)
        greenC = simpson(self.greenresponse, self.wavelength_domain)
        blueC = simpson(self.blueresponse, self.wavelength_domain)
        self.norm_RR = self.redresponse / redC
        self.norm_GR = self.greenresponse / greenC
        self.norm_BR = self.blueresponse / blueC
        spectrum_constant = simpson(self.source_spectrum, self.wavelength_domain)
        self.norm_source_spectrum = self.source_spectrum / spectrum_constant
        intensity_constant = simpson(self.source_intensity, self.angle_domain)
        self.norm_source_intensity = self.source_intensity / intensity_constant
    
    def weberContrast(self, material_index):
        r_bg, g_bg, b_bg = self.getIntensity(material_index) #last material
        r_s, g_s, b_s = self.getIntensity(0) #first material
        
        #Weber contrast:
        r_w = (r_bg - r_s) / r_s
        g_w = (g_bg - g_s) / g_s
        b_w = (b_bg - b_s) / b_s 
        
        list_check = [self.wavelength_domain, self.norm_source_spectrum, 
                      self.norm_source_intensity, self.refractive_data,
                      self.saved_indices]
        
        return [r_w, g_w, b_w], list_check
    
    def getContrast(self, material_index):
        self.saved = {}
        r_bg, g_bg, b_bg = self.getIntensity(material_index) #next, last material
        r_s, g_s, b_s = self.getIntensity(0) #first material
        
        #Not sure what type of contrast this is:
        r = (r_bg - r_s) / r_bg
        g = (g_bg - g_s) / g_bg
        b = (b_bg - b_s) / b_bg

        list_check = [self.saved, self.wavelength_domain, self.norm_source_spectrum, 
                      self.norm_source_intensity, self.refractive_data,
                      self.saved_indices]
        
        return [r, g, b], list_check
        
    def getIntensity(self, idx):
        rawIntensity = []
        for w in self.wavelength_domain:
            rawIntensity.append(self.angleIntegral(idx, w))
        rawIntensity = np.array(rawIntensity)
        r = self.getChannel('r', rawIntensity)
        g = self.getChannel('g', rawIntensity)
        b = self.getChannel('b', rawIntensity)
        return r, g, b
    
    def angleIntegral(self, idx, w):
        index = np.where(self.wavelength_domain == w)[0][0]
        indices = np.array([layer[index] for layer in self.refractive_data])
        y = self.innerIntegrand(idx, self.angle_domain, indices, w)
        #DELETE
        self.saved_indices = indices #DELETE THIS
        return simpson(y, self.angle_domain)
             
    def reflectionCoefficient_p(self, idx, t0, indices, w):
        n0  = self.medium
        n1  = indices[idx]
        t1  = getTransmissionAngle(t0, n0, n1)
        r0  = partialReflection_p(t0, t1, n0, n1)

        if idx == len(self.refractive_data) - 1:
            return r0

        phi = (4 * np.pi * n1 * np.cos(t1) * self.heights[idx]) / w
        inner = self.rcp(indices, t1, w, n1, idx + 1)
        ex = np.exp(-1j * phi)
        return (r0 + (inner * ex)) / (1 + (r0 * inner * ex)) 
        
    def reflectionCoefficient_s(self, idx, t0, indices, w):
        n0  = self.medium
        n1  = indices[idx]
        t1  = getTransmissionAngle(t0, n0, n1)
        r0  = partialReflection_s(t0, t1, n0, n1)

        if idx == len(self.refractive_data) - 1:
            return r0
        
        phi = 4 * np.pi * n1 * np.cos(t1) * self.heights[idx] / w
        inner = self.rcs(indices, t1, w, n1, idx + 1)
        ex = np.exp(-1j * phi)
        return (r0 + (inner * ex)) / (1 + (r0 * inner * ex))

    def innerIntegrand(self, idx, t, indices, w):
        Rp = self.reflectionCoefficient_p(idx, t, indices, w)
        Rs = self.reflectionCoefficient_s(idx, t, indices, w)
        I = Rp.real**2 + Rp.imag**2 + Rs.real**2 + Rs.imag**2
        return I * self.norm_source_intensity * np.sin(t)
    
    def getChannel(self, channel, rawIntensity):
        if channel == 'r':
            channelIntensity= self.norm_RR
        elif channel == 'g':
            channelIntensity= self.norm_GR
        elif channel == 'b':
            channelIntensity= self.norm_BR
        integrand = rawIntensity * channelIntensity * self.norm_source_spectrum
        
        self.saved[channel] = integrand
        
        return simpson(integrand, self.wavelength_domain)
        
    def rcp(self, indices, t0, w, n0, i):
        N = len(self.refractive_data)

        n1 = indices[i]
        t1 = getTransmissionAngle(t0, n0, n1)
        r0 = partialReflection_p(t0, t1, n0, n1)

        if i == N - 1:
            return r0
        else:
            phi   = 4 * np.pi * n1 * np.cos(t1) * self.heights[i] / w
            inner = self.rcp(indices, t1, w, n1, i + 1)
            ex    = np.exp(-1j * phi)

        return (r0 + inner * ex) / (1 + r0 * inner * ex)

    def rcs(self, indices, t0, w, n0, i):
        N = len(self.refractive_data)

        n1 = indices[i]
        t1 = getTransmissionAngle(t0, n0, n1)
        r0 = partialReflection_s(t0, t1, n0, n1)

        if i == N - 1:
            return r0
        else:
            phi   = 4 * np.pi * n1 * np.cos(t1) * self.heights[i] / w
            inner = self.rcs(indices, t1, w, n1, i + 1)
            ex    = np.exp(-1j * phi)

        return (r0 + inner * ex) / (1 + r0 * inner * ex)
    
    def set_heights(self, heights):
        self.heights = heights
        
             
                 
