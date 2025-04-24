# main.py
import tkinter as tk
from simulator_gui import SimulatorGUI

if __name__ == "__main__":
    print("Starting LEGv8 Simulator Application...")
    root = tk.Tk()
    app = SimulatorGUI(root)
    root.mainloop()
    print("LEGv8 Simulator Application Closed.")