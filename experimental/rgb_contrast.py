#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Dec  8 14:02:58 2022

@author: dirac
"""
from PIL import Image
import numpy as np
import matplotlib.pyplot as plt

__all__ = []

def open_resize_split(image_path, size=(200,200)):
    img = Image.open(image_path)
    img = img.resize(size)
    split = Image.Image.split(img)
    r = split[0]
    g = split[1]
    b = split[2]
    plt.imshow(g)
    plt.show()
    plt.imshow(b)
    plt.show()
    plt.imshow(r)
    plt.show()
    r = np.array(r)
    g = np.array(g)
    b = np.array(b)
    return r,g,b

def weber_contrast(I_feature, I_background):
    C = (I_feature - I_background)/I_background
    return C

def michelson_contrast(I_feature, I_background):
    C = 100.0*(I_background - I_feature) / (I_background + I_feature)
    return C


if __name__ == "__main__":
    path_bg = "/Users/dirac/Documents/QPRESS/pyseg/Test_Contrast_Graphene/substrate.png"
    path_s = "/Users/dirac/Documents/QPRESS/pyseg/Test_Contrast_Graphene/monolayer.png"
    
    r_bg, g_bg, b_bg = open_resize_split(path_bg)
    r_s, g_s, b_s = open_resize_split(path_s)
    
    rc = michelson_contrast(r_s, r_bg)
    avg_rbg = np.average(r_bg.flatten())
    avg_rs = np.average(r_s.flatten())
    
    avg_gbg = np.average(g_bg.flatten())
    avg_gs = np.average(g_s.flatten())
    print(avg_rbg, avg_rs, avg_gbg, avg_gs)
    
    fig = plt.figure(figsize=(10,8))
    plt.hist(g_s.flatten(), color='limegreen')
    plt.xlabel("Pixel Values (green channel)")
    plt.ylabel("Number of Occurences")
    plt.title("Green Channel Pixel Values in a Small Patch of Monolayer")
    plt.show()
    
    r_contrast = michelson_contrast(np.average(r_s), np.average(r_bg))
    b_contrast = michelson_contrast(np.average(b_s), np.average(b_bg))
    g_contrast = michelson_contrast(np.average(g_s), np.average(g_bg))
    
    
    #avg_r = np.average(r_contrast.flatten())
    #avg_g = np.average(g_contrast.flatten())
    #avg_b = np.average(b_contrast.flatten())
    
    print("Experimental contrast of red: {}, green: {}, and blue: {}.".format(r_contrast, b_contrast, g_contrast))
    

