import tkinter as tk
from tkinter import filedialog, messagebox
import threading
import os

from tools.samplesheet_converter_core import convertitore_samplesheet


# ── Design tokens ─────────────────────────────────────────────────────────
FONT = "Segoe UI"

BG = "#f4f6fb"
CARD_BG = "#ffffff"
BORDER = "#e2e8f0"
ZONE_BG = "#f8fafc"
ZONE_BG_HOVER = "#eef2ff"

TEXT = "#1e293b"
TEXT_MUTED = "#64748b"
TEXT_FAINT = "#94a3b8"

ACCENT = "#4f46e5"
ACCENT_HOVER = "#4338ca"
ACCENT_ACTIVE = "#3730a3"
ACCENT_DISABLED = "#c7d2fe"

SUCCESS = "#16a34a"
ERROR = "#dc2626"
WARNING = "#d97706"
IDLE = "#94a3b8"


class SampleSheetConverterPage(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent, bg=BG)

        self.excel_path = None
        self._last_dir = None  # ricorda l'ultima cartella usata

        # ── Contenitore scorrevole (la pagina può superare l'altezza
        # della finestra, es. quando compare il box degli avvisi) ────────
        self._scroll_canvas = tk.Canvas(self, bg=BG, highlightthickness=0)
        scrollbar = tk.Scrollbar(
            self, orient="vertical", command=self._scroll_canvas.yview
        )
        self._scroll_canvas.configure(yscrollcommand=scrollbar.set)

        self._scroll_canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        content = tk.Frame(self._scroll_canvas, bg=BG)
        content_window = self._scroll_canvas.create_window(
            (0, 0), window=content, anchor="nw"
        )

        def _on_content_configure(event=None):
            self._scroll_canvas.configure(
                scrollregion=self._scroll_canvas.bbox("all")
            )

        def _on_canvas_configure(event):
            self._scroll_canvas.itemconfig(content_window, width=event.width)

        content.bind("<Configure>", _on_content_configure)
        self._scroll_canvas.bind("<Configure>", _on_canvas_configure)

        def _on_mousewheel(event):
            if self._scroll_canvas.tk.call("tk", "windowingsystem") == "aqua":
                delta = int(-1 * event.delta)
            else:
                delta = int(-1 * (event.delta / 120))
            self._scroll_canvas.yview_scroll(delta, "units")

        def _bind_mousewheel(event=None):
            self._scroll_canvas.bind_all("<MouseWheel>", _on_mousewheel)

        def _unbind_mousewheel(event=None):
            self._scroll_canvas.unbind_all("<MouseWheel>")

        self._scroll_canvas.bind("<Enter>", _bind_mousewheel)
        self._scroll_canvas.bind("<Leave>", _unbind_mousewheel)

        # ── Header ─────────────────────────────────────────────────────────
        header = tk.Frame(content, bg=BG)
        header.pack(fill="x", padx=28, pady=(24, 4))

        tk.Label(
            header, text="Generate SampleSheet for BaseSpace",
            font=(FONT, 22, "bold"), bg=BG, fg=TEXT
        ).pack(anchor="w")

        tk.Label(
            header,
            text="Carica l'Excel Slims Extraction, imposta il Project e converti — nessun altro file richiesto.",
            font=(FONT, 12), bg=BG, fg=TEXT_MUTED
        ).pack(anchor="w", pady=(4, 0))

        self._step_row(header, [
            "1  Carica Excel", "2  Project", "3  Converti"
        ])

        # ── Card: file input ──────────────────────────────────────────────
        card = self._card(content, "FILE DI INPUT")

        self.drop_zone = tk.Frame(
            card, bg=ZONE_BG, highlightbackground=BORDER,
            highlightthickness=1, cursor="hand2"
        )
        self.drop_zone.pack(fill="x", pady=(4, 0))

        zone_inner = tk.Frame(self.drop_zone, bg=ZONE_BG)
        zone_inner.pack(fill="x", padx=16, pady=16)

        self.zone_icon = tk.Label(
            zone_inner, text="📄", font=(FONT, 26), bg=ZONE_BG, fg=TEXT_MUTED
        )
        self.zone_icon.pack(side="left", padx=(0, 14))

        zone_text = tk.Frame(zone_inner, bg=ZONE_BG)
        zone_text.pack(side="left", fill="x", expand=True)

        self.zone_title = tk.Label(
            zone_text, text="Carica Excel Slims Extraction (.xlsx)",
            font=(FONT, 13, "bold"), bg=ZONE_BG, fg=TEXT, anchor="w"
        )
        self.zone_title.pack(fill="x", anchor="w")

        self.excel_label = tk.Label(
            zone_text, text="Nessun file selezionato — clicca per sfogliare",
            font=(FONT, 11), bg=ZONE_BG, fg=TEXT_FAINT, anchor="w"
        )
        self.excel_label.pack(fill="x", anchor="w", pady=(2, 0))

        self._bind_click(
            [self.drop_zone, zone_inner, zone_text,
             self.zone_icon, self.zone_title, self.excel_label],
            self.load_excel
        )
        for w in (self.drop_zone, zone_inner, zone_text,
                   self.zone_icon, self.zone_title, self.excel_label):
            w.bind("<Enter>", self._on_zone_enter)
            w.bind("<Leave>", self._on_zone_leave)

        # ── Card: options ────────────────────────────────────────────────
        opts_card = self._card(content, "OPZIONI")

        tk.Label(
            opts_card, text="Project", font=(FONT, 11, "bold"),
            bg=CARD_BG, fg=TEXT_MUTED
        ).pack(anchor="w", pady=(4, 4))

        self.project_var = tk.StringVar()
        self.project_entry = tk.Entry(
            opts_card, font=(FONT, 13), textvariable=self.project_var,
            relief="flat", highlightthickness=1,
            highlightbackground=BORDER, highlightcolor=ACCENT,
            bg="#ffffff", fg=TEXT, insertbackground=TEXT
        )
        self.project_entry.pack(fill="x", ipady=7)

        tk.Label(
            opts_card,
            text="Estratto automaticamente dal nome del file, modificabile.",
            font=(FONT, 10), bg=CARD_BG, fg=TEXT_FAINT
        ).pack(anchor="w", pady=(5, 0))

        # ── Convert button ───────────────────────────────────────────────
        btn_wrap = tk.Frame(content, bg=BG)
        btn_wrap.pack(fill="x", padx=28, pady=(18, 6))

        self.convert_btn = tk.Button(
            btn_wrap,
            text="⚙  Genera SampleSheet",
            font=(FONT, 13, "bold"),
            bg=ACCENT, fg="Black",
            activebackground=ACCENT_ACTIVE, activeforeground="white",
            relief="flat", bd=0, cursor="hand2",
            padx=18, pady=10,
            command=self.on_convert
        )
        self.convert_btn.pack(fill="x")
        self.convert_btn.bind("<Enter>", self._on_btn_enter)
        self.convert_btn.bind("<Leave>", self._on_btn_leave)

        # ── Status pill ──────────────────────────────────────────────────
        status_row = tk.Frame(content, bg=BG)
        status_row.pack(pady=(2, 20))

        self.status_dot = tk.Canvas(
            status_row, width=9, height=9, bg=BG, highlightthickness=0
        )
        self._dot_id = self.status_dot.create_oval(0, 0, 9, 9, fill=IDLE, outline="")
        self.status_dot.pack(side="left", padx=(0, 6))

        self.status_var = tk.StringVar(value="In attesa…")
        self.status_label = tk.Label(
            status_row, textvariable=self.status_var,
            font=(FONT, 11), bg=BG, fg=TEXT_MUTED
        )
        self.status_label.pack(side="left")

        # ── Warning box: campioni senza Well Position ──────────────────────
        # non viene "packata" subito: appare solo dopo la conversione, se serve
        self.warning_card = tk.Frame(
            content, bg="#fff8f0", highlightbackground="#f0b429", highlightthickness=1
        )

        warn_inner = tk.Frame(self.warning_card, bg="#fff8f0")
        warn_inner.pack(fill="x", padx=18, pady=14)

        tk.Label(
            warn_inner, text="⚠  Campioni senza Well Position",
            font=(FONT, 12, "bold"), bg="#fff8f0", fg="#b45309"
        ).pack(anchor="w")

        tk.Label(
            warn_inner,
            text="Il file è stato generato, ma questi campioni non avevano una posizione in piastra nell'Excel:",
            font=(FONT, 10), bg="#fff8f0", fg="#92400e", wraplength=650, justify="left"
        ).pack(anchor="w", pady=(3, 8))

        self.warning_text = tk.Text(
            warn_inner, height=6, font=(FONT, 11),
            fg="#92400e", bg="#fffaf0", relief="flat", bd=0,
            state="disabled", wrap="word",
            highlightthickness=1, highlightbackground="#f5d9a8"
        )
        self.warning_text.pack(fill="x")

    # ── UI helpers ────────────────────────────────────────────────────────
    def _card(self, parent, title):
        outer = tk.Frame(
            parent, bg=CARD_BG, highlightbackground=BORDER, highlightthickness=1
        )
        outer.pack(fill="x", padx=28, pady=(14, 0))

        inner = tk.Frame(outer, bg=CARD_BG)
        inner.pack(fill="x", padx=18, pady=16)

        tk.Label(
            inner, text=title, font=(FONT, 11, "bold"),
            bg=CARD_BG, fg=TEXT_FAINT
        ).pack(anchor="w")

        return inner

    def _step_row(self, parent, steps):
        row = tk.Frame(parent, bg=BG)
        row.pack(anchor="w", pady=(12, 0))

        for i, step in enumerate(steps):
            pill = tk.Label(
                row, text=step, font=(FONT, 10, "bold"),
                bg="#eef2ff", fg=ACCENT, padx=10, pady=4
            )
            pill.pack(side="left", padx=(0, 6))

    def _bind_click(self, widgets, handler):
        for w in widgets:
            w.bind("<Button-1>", lambda e: handler())

    def _on_zone_enter(self, event=None):
        self._set_zone_bg(ZONE_BG_HOVER)

    def _on_zone_leave(self, event=None):
        self._set_zone_bg(ZONE_BG)

    def _set_zone_bg(self, color):
        self.drop_zone.config(bg=color)
        for child in self.drop_zone.winfo_children():
            child.config(bg=color)
            for grandchild in child.winfo_children():
                grandchild.config(bg=color)

    def _on_btn_enter(self, event=None):
        if self.convert_btn["state"] != "disabled":
            self.convert_btn.config(bg=ACCENT_HOVER)

    def _on_btn_leave(self, event=None):
        if self.convert_btn["state"] != "disabled":
            self.convert_btn.config(bg=ACCENT)

    # ── Warning box helpers ──────────────────────────────────────────────
    def _show_warnings(self, missing: list):
        content = "\n".join(f"• {s}" for s in missing)
        self.warning_text.config(state="normal")
        self.warning_text.delete("1.0", "end")
        self.warning_text.insert("end", content)
        self.warning_text.config(state="disabled")
        self.warning_card.pack(fill="x", padx=28, pady=(0, 20))

    def _hide_warnings(self):
        self.warning_card.pack_forget()

    # ── Project: estrai dal nome file ──────────────────────────────────────
    def _extract_project_name(self, filepath: str) -> str:
        basename = os.path.splitext(os.path.basename(filepath))[0]
        return basename

    # ── File picker ────────────────────────────────────────────────────────
    def load_excel(self):
        initial = self._last_dir or os.path.expanduser("~")
        path = filedialog.askopenfilename(
            title="Seleziona Excel Slims Extraction",
            initialdir=initial,
            filetypes=[("Excel files", "*.xlsx *.xls"), ("All files", "*.*")]
        )
        if path:
            self.excel_path = path
            self._last_dir = os.path.dirname(path)
            self.zone_icon.config(text="✅", fg=SUCCESS)
            self.excel_label.config(text=os.path.basename(path), fg=TEXT_MUTED)

            extracted = self._extract_project_name(path)
            self.project_var.set(extracted)
            self.project_entry.config(fg=ACCENT)
            self.project_entry.bind("<Key>", self._on_project_edit)

            # Nasconde eventuali warning di una conversione precedente
            self._hide_warnings()

    def _on_project_edit(self, event=None):
        self.project_entry.config(fg=TEXT)
        self.project_entry.unbind("<Key>")

    # ── Validation ─────────────────────────────────────────────────────────
    def _validate_inputs(self):
        if not self.excel_path:
            messagebox.showwarning("Input mancante", "Carica il file Excel (.xlsx).")
            return False
        if not self.project_var.get().strip():
            messagebox.showwarning("Input mancante", "Inserisci il Project.")
            return False
        return True

    # ── Status helper ──────────────────────────────────────────────────────
    def _set_status(self, msg: str, color: str = TEXT_MUTED, dot: str = None):
        self.status_var.set(msg)
        self.status_label.config(fg=color)
        self.status_dot.itemconfig(self._dot_id, fill=dot or color)

    # ── Main action ────────────────────────────────────────────────────────
    def on_convert(self):
        if not self._validate_inputs():
            return

        initial_output = self._last_dir or os.path.expanduser("~")
        output_dir = filedialog.askdirectory(
            title="Scegli cartella di output",
            initialdir=initial_output
        )
        if not output_dir:
            return

        self._hide_warnings()
        self.convert_btn.config(state="disabled", bg=ACCENT_DISABLED, cursor="arrow")
        self._set_status("Elaborazione in corso…", TEXT_MUTED, WARNING)

        threading.Thread(
            target=self._run_conversion,
            args=(output_dir,),
            daemon=True
        ).start()

    def _run_conversion(self, output_dir: str):
        # Gira in un thread separato: qui dentro NON si deve toccare alcun
        # widget Tkinter (non è thread-safe). Il risultato viene passato al
        # thread principale con self.after(), che si occupa della UI.
        project = self.project_var.get().strip()

        try:
            samplesheet_output = os.path.join(
                output_dir, f"{project}_import_sample_template.csv"
            )
            missing_well = convertitore_samplesheet(
                self.excel_path, samplesheet_output, project
            )
            self.after(
                0, self._on_conversion_done,
                output_dir, samplesheet_output, missing_well, None
            )

        except Exception as e:
            self.after(0, self._on_conversion_done, output_dir, None, None, e)

    def _on_conversion_done(self, output_dir, samplesheet_output, missing_well, error):
        """Eseguito sul thread principale: qui è sicuro aggiornare la UI."""
        try:
            if error is not None:
                self._set_status(f"Errore: {error}", ERROR, ERROR)
                messagebox.showerror("Errore", f"Errore durante l'elaborazione:\n{error}")
                return

            if missing_well:
                self._set_status(
                    f"✅ File generato · ⚠️ {len(missing_well)} campioni senza Well Position",
                    WARNING, WARNING
                )
                self._show_warnings(missing_well)
                messagebox.showwarning(
                    "Completato con avvisi",
                    f"File generato in:\n{output_dir}\n\n"
                    f"• {os.path.basename(samplesheet_output)}\n\n"
                    f"{len(missing_well)} campioni senza Well Position: vedi il riquadro sotto."
                )
            else:
                self._set_status(f"File generato in: {output_dir}", SUCCESS, SUCCESS)
                messagebox.showinfo(
                    "Completato",
                    f"File generato con successo in:\n{output_dir}\n\n"
                    f"• {os.path.basename(samplesheet_output)}"
                )

        finally:
            self.convert_btn.config(state="normal", bg=ACCENT, cursor="hand2")
