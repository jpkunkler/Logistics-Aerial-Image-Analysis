# from tkinter import Button, Frame, Tk  # Python 3
from tkinter import Button, Frame, Tk    # Python 2
import pandas as pd
import sys

from selenium import webdriver
from selenium.webdriver.common.keys import Keys
#driver = webdriver.Firefox(executable_path=r'/opt/geckodriver') # UBUNTU
driver = webdriver.Firefox(executable_path=r'C:\git\geckodriver') # WINDOWS

BASE_URL = "https://www.google.com/maps/@?api=1&map_action=map&center={lat},{lng}&zoom=12&basemap=satellite"
INPUT_FILE = r"Standorte_labeled.xlsx"
OUTPUT_FILE = r"Standorte_labeled.xlsx"

class MyClass:
    def __init__(self, master):
        self.openFile()
        frame = Frame(master)
        frame.pack()
        self.next_row()
    
        try:
            
            self.button_very_good = Button(frame, text="Sehr Gut", command=self.label_very_good)
            self.button_very_good.pack(side='left')
            
            self.button_good = Button(frame, text="Gut", command=self.label_good)
            self.button_good.pack(side='left')
           
            self.button_avg = Button(frame, text="Moderat", command=self.label_avg)
            self.button_avg.pack(side='left')
           
            self.button_bad = Button(frame, text="Schlecht", command=self.label_bad)
            self.button_bad.pack(side='left')
           
            self.button_mark = Button(frame, text="Mark", command=self.mark)
            self.button_mark.pack(side='left')
            
            self.button_next = Button(frame, text="Exit", command=self.finish)
            self.button_next.pack(side='left')
        
            master.bind('1', self.label_very_good)
            master.bind('2', self.label_good)
            master.bind('3', self.label_avg)
            master.bind('4', self.label_bad)
        except:
            pass
    
    def label(self, label):
        print("Image labeled as {}".format(label))
        self.df.iloc[self.counter, self.df.columns.get_loc("Kategorie")] = label
        print(self.df.iloc[self.counter])
        self.save()
        self.next_row()
    
    def label_very_good(self, _event=None):
        self.label("Sehr Gut")
        
    def label_good(self, _event=None):
        self.label("Gut")
    
    def label_avg(self, _event=None):
        self.label("Mittel")
    
    def label_bad(self, _event=None):
        self.label("Schlecht")
    
    def mark(self, _event=None):
        self.df.iloc[self.counter, self.df.columns.get_loc("Markiert")] = "x"
        self.save()
        
    def next_row(self, _event=None):
        self.counter += 1
        try:
            lat = self.df.iloc[self.counter]["Lat"]
            lng = self.df.iloc[self.counter]["Lon"]
            elem = driver.find_element_by_id("searchboxinput")
            elem.clear()
            elem.send_keys("{},{}".format(lat,lng))
            elem.send_keys(Keys.RETURN)
        except IndexError as e:
            print("Arrived at last line!", e)
            self.finish()
        
    def openFile(self):
        self.filename = INPUT_FILE
        self.df = pd.read_excel(self.filename)
        try:
            self.counter = self.df["Kategorie"].last_valid_index()
            if self.counter == None:
                self.counter = -1
        except:
            self.counter = -1
    
    def save(self):
        self.df.to_excel(OUTPUT_FILE)
        
    def finish(self):
        print("Saving and finishing.")
        self.save()
        root.destroy()
        driver.quit()

driver.get(BASE_URL.format(lat="48.999940", lng="12.094889"))

root = Tk()
abc = MyClass(root)
try:
    root.wm_attributes("-topmost", 1)
    root.mainloop()
except:
    sys.exit()