# -*- coding: utf-8 -*-
"""Titik masuk aplikasi. Jalankan:  python main.py"""
import tkinter as tk

from app import NexusHR

if __name__ == "__main__":
    root = tk.Tk()
    app = NexusHR(root)
    root.mainloop()
