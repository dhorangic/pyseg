#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Jul 12 14:20:04 2022

@author: Diana Horangic
"""
import cv2 as cv
import os
import numpy as np
from background import stack_opened, residual_img, fground
from utils import return_opened, resize_show, stdize_img_size, histogram_per_ch

#Need to remove opencv dependence

if __name__ == '__main__':
    #This file so far only contains median filter background subtraction
    
    #file_dir = "/Users/dirac/Documents/QPRESS/SUBSTRATE_SCAN/"
    #individual_loc = "/Users/dirac/Documents/QPRESS/" + "TEST_SEG.tiff"
    file_dir = "/Users/dirac/Documents/QPRESS/SIM_BACKGROUND/"
    individual_loc = "/Users/dirac/Documents/QPRESS/chip2.jpg"

    all_opened = return_opened(file_dir)
    print(type(all_opened[0]))
    stacked = stack_opened(all_opened)
    opened_img, residual, type_ = residual_img(stacked, individual_loc)
    
    assert opened_img.shape == residual.shape, "Shapes of opened image and residual do not match!"
    
    foregr = fground(residual, type_, stacked)
    mask_FORE = foregr[:, :, 0] + foregr[:, :, 1] + foregr[:, :, 2]
    mask_BACK = (np.where(mask_FORE == 0, 255, 0)).astype(type_)

    background_seg = cv.bitwise_and(opened_img, opened_img, mask = mask_BACK)    
    foreground_seg = cv.bitwise_and(opened_img, opened_img, mask = mask_FORE)
    
    #Masking original image, first with only background, then with only foreground
    resize_show(background_seg)
    resize_show(foreground_seg)
    resize_show(opened_img)
    

else:
    raise BaseException("Script not being run on import, user will need to run __main__ manually.")