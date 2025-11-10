import tkinter as tk
from tkinter import Menu, Toplevel, messagebox
from PIL import Image, ImageTk
import os
import sys
import time
import threading
import urllib.request

# import tools and components
from tools.emedgene_csv_converter import CSVConverterPage
from welcome_page import WelcomePage


# ---------------- APP VERSION & RELEASES ----------------
APP_VERSION = "1.0.0"
W_WIDTH = 600
W_HEIGHT = 480
TITLE = f"G-CLIP - Gemelli Clinical Informatics Platform v{APP_VERSION}"
GITHUB_REPO = "https://github.com/mazzalab/G-CLIP"
RELEASES_PAGE = f"{GITHUB_REPO}/releases"


# ---------------- RESOURCE PATH (PyInstaller Safe) ----------------
def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)


logo_path = resource_path(os.path.join("assets", "bfx_logo.png"))


# ---------------- MANUAL UPDATE OF HPO (HELP MENU) ----------------
def update_hpo():
    try:
        url = "https://raw.githubusercontent.com/obophenotype/human-phenotype-ontology/master/hp.obo"
        save_path = resource_path(os.path.join("assets", "hp.obo"))

        messagebox.showinfo(
            "HPO Update", "Downloading the latest HPO ontology...")

        urllib.request.urlretrieve(url, save_path)

        messagebox.showinfo(
            "HPO Update", "✅ HPO ontology updated successfully!")

    except Exception as e:
        messagebox.showerror("Error", f"Failed to update HPO ontology:\n{e}")


# ---------------- ABOUT WINDOW ----------------
def show_about():
    try:
        about = Toplevel(root)
        about.title(f"About - v{APP_VERSION}")
        about.resizable(False, False)
        about.geometry("460x380")
    except Exception:
        return

    try:
        img = Image.open(logo_path)
        img = img.resize((120, 120))
        logo = ImageTk.PhotoImage(img)
        tk.Label(about, text="", pady=10).pack()
        tk.Label(about, image=logo).pack()
        about.logo = logo
    except Exception as e:
        tk.Label(about, text="(Logo loading failed)").pack()
        print("Logo error in About:", e)

    # Show date of local HPO file if available
    hpo_file = resource_path(os.path.join("assets", "hp.obo"))
    hpo_status = ""
    try:
        if os.path.exists(hpo_file):
            ts = time.ctime(os.path.getmtime(hpo_file))
            hpo_status = f"\nHPO ontology last updated: {ts}"
    except Exception:
        pass

    text = (
        f"\n {TITLE}\n"
        "UOS Computational Biology and Bioinformatics\n"
        "Fondazione Policlinico Universitario Agostino Gemelli IRCCS\n"
        "Università Cattolica del Sacro Cuore\n\n"
        "Largo Agostino Gemelli, 8, 00168 Roma\n"
        "www.policlinicogemelli.it\n"
        f"{hpo_status}\n"
    )

    tk.Label(
        about, text=text, justify="center", font=("Arial", 10)
    ).pack(pady=10)


# ---------------- SPLASH SCREEN ----------------
def show_splash(root):
    try:
        splash = tk.Toplevel()
        splash.overrideredirect(True)

        width, height = 450, 340
        x = (root.winfo_screenwidth() - width) // 2
        y = (root.winfo_screenheight() - height) // 2
        splash.geometry(f"{width}x{height}+{x}+{y}")

        try:
            img = Image.open(logo_path)
            img = img.resize((120, 120))
            logo = ImageTk.PhotoImage(img)
            tk.Label(splash, text="", pady=10).pack()
            tk.Label(splash, image=logo).pack()
            splash.logo = logo
        except Exception as e:
            tk.Label(splash, text="(Logo loading failed)").pack()
            print("Splash logo error:", e)

        tk.Label(
            splash,
            text=(
                "UOS Computational Biology and Bioinformatics\n"
                "Fondazione Policlinico Universitario Agostino Gemelli IRCCS\n"
                "Università Cattolica del Sacro Cuore\n\n"
                "Largo Agostino Gemelli, 8, 00168 Roma\n"
                "www.policlinicogemelli.it"
            ),
            font=("Arial", 10),
            justify="center",
            padx=15,
            pady=15
        ).pack()

        def close_splash():
            time.sleep(2.5)
            splash.destroy()
            root.deiconify()

        threading.Thread(target=close_splash).start()

    except Exception as e:
        print("Splash error:", e)
        root.deiconify()


# ---------------- CENTER WINDOW UTILITY ----------------
def center_window(win, width, height):
    win.update_idletasks()
    sw = win.winfo_screenwidth()
    sh = win.winfo_screenheight()
    x = (sw // 2) - (width // 2)
    y = (sh // 2) - (height // 2)
    win.geometry(f"{width}x{height}+{x}+{y}")


# ---------------- MAIN WINDOW ----------------
root = tk.Tk()
root.title(TITLE)
root.geometry(f"{W_WIDTH}x{W_HEIGHT}")
root.resizable(False, False)
center_window(root, W_WIDTH, W_HEIGHT)

# Show splash
root.withdraw()
show_splash(root)

# Workspace
container = tk.Frame(root)
container.pack(fill="both", expand=True)

tool_pages = {}

# Default page: welcome screen
welcome_page = WelcomePage(container, logo_path)
welcome_page.pack(fill="both", expand=True)


def show_tool(name):
    """Hide welcome page, show requested tool safely."""
    try:
        # hide welcome page
        welcome_page.pack_forget()

        # create tool page if not created yet
        if name not in tool_pages:
            if name == "csv":
                tool_pages[name] = CSVConverterPage(container)
            # Future tools:
            # elif name == "qc":
            #     tool_pages[name] = QCToolPage(container)

            tool_pages[name].pack(fill="both", expand=True)

        # hide others
        for t, page in tool_pages.items():
            page.pack_forget()

        # show the requested tool
        tool_pages[name].pack(fill="both", expand=True)

    except Exception as e:
        print("Error showing tool:", e)
        messagebox.showerror("Error", f"Could not load tool:\n{e}")


# ---------------- MENUBAR ----------------
menu_bar = Menu(root)

# Tools menu
tools_menu = Menu(menu_bar, tearoff=0)
tools_menu.add_command(
    label="Excel to Emedgene CSV Converter", command=lambda: show_tool("csv"))
menu_bar.add_cascade(label="Tools", menu=tools_menu)

# Help menu
help_menu = Menu(menu_bar, tearoff=0)
help_menu.add_command(label="Update HPO Ontology", command=update_hpo)
help_menu.add_command(label="About", command=show_about)
menu_bar.add_cascade(label="Help", menu=help_menu)

root.config(menu=menu_bar)

# ---------------- RUN APP ----------------
try:
    root.mainloop()
except Exception as e:
    print("Mainloop Error:", e)
    sys.exit(1)
