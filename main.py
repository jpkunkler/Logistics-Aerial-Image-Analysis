#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Mar 22 13:23:36 2019

@author: kunkler
"""

import BoundingBox as bb
import pandas as pd
import subprocess
import runGeocode as gc

def main():
    
    excel_file = r"Standorte.xlsx"
    
    df = pd.read_excel(excel_file)
    script = r"Satellite-Aerial-Image-Retrieval-by-llgeek/aerialImageRetrieval.py"
    
    # Check if any rows need geocoding
    if df["Lat"].isnull().values.any() or df["Lon"].isnull().values.any():
        print("Empty Coordinate Values found. Starting Geocoding Process!")
        gc.arcgisGeocode(excel_file)
        df = pd.read_excel(excel_file) # reload updated dataset
        
    # Go through dataset row by row
    for index, row in df.iterrows():
        
        # calculate bounding box
        upper_left, lower_right = bb.boundingBox(row["Lat"], row["Lon"])
        
        # run satellite image retrieval script
        p = subprocess.Popen(['python', script, str(upper_left[0]), str(upper_left[1]), str(lower_right[0]), str(lower_right[1])])
        p.wait()
        
        # Update values in dataframe aka Excel Sheet
        #df.loc[index, 'Bilddatei'] = "FULL-PATH-TO-FILE-HERE"
        print("Proceeding to next row. Please stand bye.")
    
    # Save dataframe back to Excel as Excel Sheet
    df.to_excel(excel_file)
    print("Finished!")

if __name__ == '__main__':  main()
    