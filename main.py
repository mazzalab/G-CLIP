import tkinter as tk
from tkinter import Menu, Toplevel, messagebox, simpledialog
from PIL import Image, ImageTk
import os
import sys
import time
import json
import threading
import urllib.request
import webbrowser

# import tools and components
from tools.emedgene_csv_converter import CSVConverterPage
from tools.generatefileRun import GeneratefileRun
from tools.samplesheet_converter import SampleSheetConverterPage
from welcome_page import WelcomePage


# ---------------- APP VERSION & RELEASES ----------------
APP_VERSION = "1.0.1"
W_WIDTH = 760
W_HEIGHT = 640
TITLE = f"G-CLIP - Gemelli Clinical Informatics Platform v{APP_VERSION}"
GITHUB_REPO = "https://api.github.com/repos/mazzalab/G-CLIP/releases/latest"
GITHUB_LATEST_RELEASE = "https://github.com/mazzalab/G-CLIP/releases/latest"

# ---------------- DEV-ONLY TOOLS (nascosti da menu/welcome page) ----------------
# Sblocco con Ctrl+Shift+D + codice. Cambia questo valore per usare un codice tuo.
DEV_UNLOCK_CODE = "1234"


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


# ---------------- CHECK FOR NEW VERSION ----------------
def check_for_updates():
    try:
        response = urllib.request.urlopen(GITHUB_REPO, timeout=3)
        data = json.load(response)
        latest = data.get("tag_name", "").replace("v", "")

        if latest and latest != APP_VERSION:
            messagebox.showinfo(
                "Update Available",
                f"A newer version ({latest}) of G-CLIP is available.\n"
                f"Current version: {APP_VERSION}\n\n"
                "Visit GitHub Releases page to download the update."
            )
    except Exception:
        # Silent fail — no internet or GitHub unavailable
        pass


def manual_check_updates():
    try:
        response = urllib.request.urlopen(GITHUB_REPO, timeout=3)
        data = json.load(response)
        latest = data.get("tag_name", "").replace("v", "")

        if latest and latest != APP_VERSION:
            answer = messagebox.askyesno(
                "Update Available",
                f"A newer version ({latest}) of G-CLIP is available.\n"
                f"Current version: {APP_VERSION}\n\n"
                "Do you want to open the download page?"
            )
            if answer:
                webbrowser.open(GITHUB_LATEST_RELEASE)
        else:
            messagebox.showinfo(
                "Up to Date",
                f"You already have the latest version ({APP_VERSION})."
            )

    except Exception:
        messagebox.showerror(
            "Update Check Failed",
            "Unable to check for updates.\n"
            "You might be offline or GitHub is unavailable."
        )


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
            check_for_updates()

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

try:
    icon_img = Image.open(logo_path)
    icon_img = icon_img.resize((64, 64))
    icon_photo = ImageTk.PhotoImage(icon_img)
    root.iconphoto(True, icon_photo)
    root._icon = icon_photo  # impedisce al garbage collector di eliminarla

    if sys.platform == "win32":
        ico_path = resource_path(os.path.join("assets", "bfx_logo.ico"))
        if os.path.exists(ico_path):
            root.iconbitmap(ico_path)
except Exception as e:
    print(f"Icona non caricata: {e}")


# Show splash
root.withdraw()
show_splash(root)

# ---------------- TOP BAR (Home navigation) ----------------
HOME_BG = "#eef2ff"
HOME_BG_HOVER = "#e0e7ff"
HOME_BG_DISABLED = "#ffffff"
HOME_FG = "#4f46e5"
HOME_FG_DISABLED = "#c3c9d6"

topbar = tk.Frame(root, bg="#ffffff", height=44)
topbar.pack(side="top", fill="x")
topbar.pack_propagate(False)

home_btn = tk.Button(
    topbar, text="🏠  Home", font=("Arial", 10, "bold"),
    bg=HOME_BG, fg=HOME_FG,
    activebackground=HOME_BG_HOVER, activeforeground=HOME_FG,
    disabledforeground=HOME_FG_DISABLED,
    relief="flat", bd=0, cursor="arrow",
    padx=14, pady=6,
    command=lambda: show_welcome()
)
home_btn.pack(side="left", padx=12, pady=7)


def _home_btn_enter(event=None):
    if home_btn["state"] != "disabled":
        home_btn.config(bg=HOME_BG_HOVER)


def _home_btn_leave(event=None):
    if home_btn["state"] != "disabled":
        home_btn.config(bg=HOME_BG)


home_btn.bind("<Enter>", _home_btn_enter)
home_btn.bind("<Leave>", _home_btn_leave)

# Si parte sulla welcome page: il pulsante è disattivato finché non si apre un tool
home_btn.config(state="disabled", bg=HOME_BG_DISABLED, cursor="arrow")

tk.Frame(root, bg="#e2e8f0", height=1).pack(side="top", fill="x")

# Workspace
container = tk.Frame(root)
container.pack(fill="both", expand=True)

tool_pages = {}

# Default page: welcome screen
welcome_page = WelcomePage(
    container, logo_path, on_select_tool=lambda name: show_tool(name))
welcome_page.pack(fill="both", expand=True)


def show_tool(name):
    """Hide welcome page, show requested tool safely."""
    try:
        # hide welcome page
        welcome_page.pack_forget()

        # create tool page if not created yet
        if name not in tool_pages:
            # if name == "csv":
            #     tool_pages[name] = CSVConverterPage(container)
            if name == "samplesheetConverter":
                 tool_pages[name] = SampleSheetConverterPage(container)
            elif name == "FileRunWES":
                 # Tool nascosto: accessibile solo tramite lo sblocco sviluppatore (Ctrl+Shift+D)
                 tool_pages[name] = GeneratefileRun(container)
            # Future tools:
            # elif name == "qc":
            #     tool_pages[name] = QCToolPage(container)

            tool_pages[name].pack(fill="both", expand=True)

        # hide others
        for t, page in tool_pages.items():
            page.pack_forget()

        # show the requested tool
        tool_pages[name].pack(fill="both", expand=True)

        # su un tool: il pulsante Home diventa attivo
        home_btn.config(state="normal", bg=HOME_BG, cursor="hand2")

    except Exception as e:
        print("Error showing tool:", e)
        messagebox.showerror("Error", f"Could not load tool:\n{e}")


def show_welcome():
    """Hide any visible tool page and show the welcome screen."""
    for t, page in tool_pages.items():
        page.pack_forget()
    welcome_page.pack(fill="both", expand=True)

    # già sulla welcome page: il pulsante Home si disattiva
    home_btn.config(state="disabled", bg=HOME_BG_DISABLED, cursor="arrow")


# ---------------- DEV-ONLY TOOL UNLOCK ----------------
def unlock_dev_tool(event=None):
    """Sblocco nascosto: Ctrl+Shift+D chiede un codice e, se corretto,
    apre il tool 'Generate files Run WES' (non presente in menu/welcome)."""
    code = simpledialog.askstring(
        "Accesso sviluppatore", "Codice:", show="*", parent=root
    )
    if code is None:
        return
    if code == DEV_UNLOCK_CODE:
        show_tool("FileRunWES")
    else:
        messagebox.showerror("Accesso negato", "Codice non valido.")


root.bind_all("<Control-Shift-D>", unlock_dev_tool)


# ---------------- MENUBAR ----------------
menu_bar = Menu(root)

# Tools menu
tools_menu = Menu(menu_bar, tearoff=0)
# tools_menu.add_command(
#     label="Excel to Emedgene CSV Converter", command=lambda: show_tool("csv"))
# tools_menu.add_command(
#     label="Generate files Run WES", command=lambda: show_tool("FileRunWES"))
tools_menu.add_command(
    label="Generate SampleSheet for BaseSpace", command=lambda: show_tool("samplesheetConverter"))
menu_bar.add_cascade(label="Tools", menu=tools_menu)

# Help menu
help_menu = Menu(menu_bar, tearoff=0)
help_menu.add_command(label="Check for Updates", command=manual_check_updates)
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
