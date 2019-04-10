# from tkinter import Button, Frame, Tk  # Python 3
from tkinter import Button, Frame, Tk    # Python 2
import webbrowser
import pandas as pd

BASE_URL = "https://www.google.com/maps/search/?api=1&query={lat},{lng}"

class MyClass:
    def __init__(self, master):
        self.openFile()
        frame = Frame(master)
        frame.pack()
        self.counter = -1
        self.next_row()
    
        self.button_good = Button(frame, text="Gut", command=self.label_good)
        self.button_good.pack(side='left')
       
        self.button_avg = Button(frame, text="Moderat", command=self.label_avg)
        self.button_avg.pack(side='left')
       
        self.button_bad = Button(frame, text="Schlecht", command=self.label_bad)
        self.button_bad.pack(side='left')
       
        self.button_next = Button(frame, text="Skip", command=self.next_row)
        self.button_next.pack(side='left')
       
    
        master.bind('1', self.label_good)
        master.bind('2', self.label_avg)
        master.bind('3', self.label_bad)

    def label_good(self, _event=None):
        print("Image labeled as good")
        # ERROR HERE: A Valze is trying to be set on a copy of a slice from a DataFrame
        self.df.iloc[self.counter, "Kategorie"] = "Gut"
        print(self.df.iloc[self.counter])
        self.next_row()
    
    def label_avg(self, _event=None):
        print("Image labeled as moderate")
    
    def label_bad(self, _event=None):
        print("Image labeled as bad")
    
    def next_row(self, _event=None):
        self.counter += 1
        webbrowser.open(BASE_URL.format(lat=self.df.iloc[self.counter]["Lat"],lng=self.df.iloc[self.counter]["Lon"]))
    
    def openFile(self):
        self.filename = r"Standorte_original.xlsx"
        self.df = pd.read_excel(self.filename)
    
    

root = Tk()
abc = MyClass(root)
root.mainloop()