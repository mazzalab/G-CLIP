import tkinter as tk
from PIL import Image, ImageTk


class WelcomePage(tk.Frame):
    def __init__(self, parent, logo_path: str):
        super().__init__(parent)

        tk.Label(self, text="", pady=15).pack()

        # Logo
        try:
            img = Image.open(logo_path)
            img = img.resize((150, 150))
            logo = ImageTk.PhotoImage(img)
            tk.Label(self, image=logo).pack()
            self.logo = logo   # keep ref
        except Exception:
            tk.Label(self, text="(Logo missing)").pack()

        tk.Label(
            self,
            text=(
                "Welcome to G-CLIP\n"
                "Gemelli Clinical Informatics Platform\n\n"
                "A collection of tools for clinicians and researchers at:\n"
                "Fondazione Policlinico Universitario Agostino Gemelli IRCCS\n"
                "and Università Cattolica del Sacro Cuore"
            ),
            font=("Arial", 12),
            justify="center",
            pady=20
        ).pack()

        tk.Label(
            self,
            text="\n",
            font=("Arial", 10)
        ).pack()

        tk.Label(
            self,
            text="\nUse the Tools menu to access more features.",
            font=("Arial", 10)
        ).pack()
