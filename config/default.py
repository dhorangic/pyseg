#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Jul 19 11:43:37 2022

@author: dirac
"""
from .cfg_node import NODE as CN

_C = CN()

_C.PREPROCESSING = CN()
_C.PREPROCESSING.FILTER = 'gaussian_blur' 
_C.PREPROCESSING.INTERPOLATION = 'bilinear'
#NOTE: Some sort of dictionary storing the different options for each config must be made
#Think about how to do this automatically instead of having to manually put each option in