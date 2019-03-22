#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Mar 22 14:06:50 2019

@author: kunkler
"""
import pandas as pd
import geocoder

def arcgisGeocode(excel_file):
    df = pd.read_excel(excel_file)
    
    df_new = df[df.isnull().any(axis=1)]
    
    
    for index, row in df_new.iterrows():
        # geocode address strings to coordinate pairs
        g = geocoder.arcgis(str(row["PLZ"]) + "," + " " + row["Straße"] + "," + "Germany")
    
        # Update values in dataframe aka Excel Sheet
        df_new.loc[index, 'Lat'] = g.json["lat"]
        df_new.loc[index, 'Lon'] = g.json["lng"]
        print("Proceeding to next row. Please stand bye.")
    
    # Save dataframe back to Excel as Excel Sheet
    df.update(df_new)
    df.to_excel(excel_file)
    print("Finished Geocoding!")
    

def main():
    arcgisGeocode(r"Standorte.xlsx")
    
if __name__ == '__main__':  main()