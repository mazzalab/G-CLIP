import tkinter as tk
from tkinter import filedialog, messagebox
import threading
import os

from tools.generatefileRun_core import mapping_slims_emedgene, check_samplesheet_samples, validate_excel_content


# ── Design tokens (coerenti con le altre pagine tool) ──────────────────────
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


class GeneratefileRun(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent, bg=BG)

        self.excel_path = None
        self.csv_path = None
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

        # ── Header ───────────────────────────────────────────────────────
        header = tk.Frame(content, bg=BG)
        header.pack(fill="x", padx=28, pady=(24, 4))

        tk.Label(
            header, text="SampleSheet Run Validator",
            font=(FONT, 22, "bold"), bg=BG, fg=TEXT
        ).pack(anchor="w")

        tk.Label(
            header,
            text="Genera il mapping dall'Excel e verifica che tutti i campioni della SampleSheet siano presenti.",
            font=(FONT, 12), bg=BG, fg=TEXT_MUTED
        ).pack(anchor="w", pady=(4, 0))

        self._step_row(header, [
            "1  Slims Extraction", "2  SampleSheet", "3  Run Name", "4  Genera e valida"
        ])

        # ── Card: file input ────────────────────────────────────────────
        card = self._card(content, "FILE DI INPUT")

        self.excel_icon, self.excel_label = self._drop_zone(
            card, "📊", "Carica Slims Extraction (.xlsx)", self.load_excel
        )
        self.csv_icon, self.csv_label = self._drop_zone(
            card, "🧬", "Carica SampleSheet (.csv)", self.load_csv, pady_top=10
        )

        # ── Card: options ────────────────────────────────────────────────
        opts_card = self._card(content, "OPZIONI")

        tk.Label(
            opts_card, text="Run Name", font=(FONT, 11, "bold"),
            bg=CARD_BG, fg=TEXT_MUTED
        ).pack(anchor="w", pady=(4, 4))

        self.run_name_var = tk.StringVar()
        self.run_name_entry = tk.Entry(
            opts_card, font=(FONT, 13), textvariable=self.run_name_var,
            relief="flat", highlightthickness=1,
            highlightbackground=BORDER, highlightcolor=ACCENT,
            bg="#ffffff", fg=TEXT, insertbackground=TEXT
        )
        self.run_name_entry.pack(fill="x", ipady=7)

        tk.Label(
            opts_card,
            text="Estratto automaticamente dal nome della SampleSheet, modificabile.",
            font=(FONT, 10), bg=CARD_BG, fg=TEXT_FAINT
        ).pack(anchor="w", pady=(5, 0))

        # ── Card: BioSample Name ─────────────────────────────────────────
        biosample_card = self._card(content, "BIOSAMPLE NAME")

        tk.Label(
            biosample_card, text="Modalità di costruzione", font=(FONT, 11, "bold"),
            bg=CARD_BG, fg=TEXT_MUTED
        ).pack(anchor="w", pady=(4, 4))

        self.biosample_mode_var = tk.StringVar(value="manuale")

        mode_row = tk.Frame(biosample_card, bg=CARD_BG)
        mode_row.pack(anchor="w", pady=(0, 8))

        tk.Radiobutton(
            mode_row, text="Manuale (SampleSheet fatta manualmente)",
            variable=self.biosample_mode_var, value="manuale",
            font=(FONT, 10), bg=CARD_BG, fg=TEXT, selectcolor=CARD_BG,
            activebackground=CARD_BG, highlightthickness=0,
            command=self._on_biosample_mode_change
        ).pack(side="left", padx=(0, 16))

        tk.Radiobutton(
            mode_row, text="Routine (flusso stabilito, _DNA)",
            variable=self.biosample_mode_var, value="routine",
            font=(FONT, 10), bg=CARD_BG, fg=TEXT, selectcolor=CARD_BG,
            activebackground=CARD_BG, highlightthickness=0,
            command=self._on_biosample_mode_change
        ).pack(side="left")

        self.biosample_column_frame = tk.Frame(biosample_card, bg=CARD_BG)
        self.biosample_column_frame.pack(anchor="w", fill="x")

        tk.Label(
            self.biosample_column_frame, text="Colonna ID da usare (solo modalità Manuale)",
            font=(FONT, 10, "bold"), bg=CARD_BG, fg=TEXT_MUTED
        ).pack(anchor="w", pady=(0, 4))

        self.biosample_column_var = tk.StringVar(value="Id")

        col_row = tk.Frame(self.biosample_column_frame, bg=CARD_BG)
        col_row.pack(anchor="w")

        tk.Radiobutton(
            col_row, text="Id", variable=self.biosample_column_var, value="Id",
            font=(FONT, 10), bg=CARD_BG, fg=TEXT, selectcolor=CARD_BG,
            activebackground=CARD_BG, highlightthickness=0
        ).pack(side="left", padx=(0, 16))

        tk.Radiobutton(
            col_row, text="Original Content (cntn_id)",
            variable=self.biosample_column_var, value="Original Content (cntn_id)",
            font=(FONT, 10), bg=CARD_BG, fg=TEXT, selectcolor=CARD_BG,
            activebackground=CARD_BG, highlightthickness=0
        ).pack(side="left")

        tk.Label(
            self.biosample_column_frame, text="Suffisso da aggiungere",
            font=(FONT, 10, "bold"), bg=CARD_BG, fg=TEXT_MUTED
        ).pack(anchor="w", pady=(10, 4))

        self.biosample_suffix_var = tk.StringVar(value="iniziali")

        suffix_row = tk.Frame(self.biosample_column_frame, bg=CARD_BG)
        suffix_row.pack(anchor="w")

        tk.Radiobutton(
            suffix_row, text="Iniziali nome/cognome",
            variable=self.biosample_suffix_var, value="iniziali",
            font=(FONT, 10), bg=CARD_BG, fg=TEXT, selectcolor=CARD_BG,
            activebackground=CARD_BG, highlightthickness=0
        ).pack(side="left", padx=(0, 16))

        tk.Radiobutton(
            suffix_row, text="_DNA",
            variable=self.biosample_suffix_var, value="dna",
            font=(FONT, 10), bg=CARD_BG, fg=TEXT, selectcolor=CARD_BG,
            activebackground=CARD_BG, highlightthickness=0
        ).pack(side="left", padx=(0, 16))

        tk.Radiobutton(
            suffix_row, text="Nessuno",
            variable=self.biosample_suffix_var, value="nessuno",
            font=(FONT, 10), bg=CARD_BG, fg=TEXT, selectcolor=CARD_BG,
            activebackground=CARD_BG, highlightthickness=0
        ).pack(side="left")

        # ── Generate button ─────────────────────────────────────────────
        btn_wrap = tk.Frame(content, bg=BG)
        btn_wrap.pack(fill="x", padx=28, pady=(18, 6))

        self.generate_btn = tk.Button(
            btn_wrap,
            text="⚙  Genera File",
            font=(FONT, 13, "bold"),
            bg=ACCENT, fg="black",
            activebackground=ACCENT_ACTIVE, activeforeground="white",
            relief="flat", bd=0, cursor="hand2",
            padx=18, pady=10,
            command=self.on_generate
        )
        self.generate_btn.pack(fill="x")
        self.generate_btn.bind("<Enter>", self._on_btn_enter)
        self.generate_btn.bind("<Leave>", self._on_btn_leave)

        # ── Progress bar ────────────────────────────────────────────────
        self.progress_canvas = tk.Canvas(
            content, height=6, bg=BORDER, highlightthickness=0
        )
        self.progress_canvas.pack(fill="x", padx=28, pady=(14, 6))
        self._progress_bar = None

        # ── Status pill ──────────────────────────────────────────────────
        status_row = tk.Frame(content, bg=BG)
        status_row.pack(pady=(2, 16))

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

        # ── Warning box: campioni non trovati nell'Excel ────────────────
        # non viene "packata" subito: appare solo dopo la generazione, se serve
        self.warning_card = tk.Frame(
            content, bg="#fff8f0", highlightbackground="#f0b429", highlightthickness=1
        )

        warn_inner = tk.Frame(self.warning_card, bg="#fff8f0")
        warn_inner.pack(fill="x", padx=18, pady=14)

        tk.Label(
            warn_inner, text="⚠  Campioni non trovati nell'Excel",
            font=(FONT, 12, "bold"), bg="#fff8f0", fg="#b45309"
        ).pack(anchor="w")

        tk.Label(
            warn_inner,
            text="Il mapping è stato generato, ma questi campioni della SampleSheet non sono stati trovati nell'Excel:",
            font=(FONT, 10), bg="#fff8f0", fg="#92400e", wraplength=650, justify="left"
        ).pack(anchor="w", pady=(3, 8))

        self.warning_text = tk.Text(
            warn_inner, height=8, font=(FONT, 11),
            fg="#92400e", bg="#fffaf0", relief="flat", bd=0,
            state="disabled", wrap="word",
            highlightthickness=1, highlightbackground="#f5d9a8"
        )
        self.warning_text.pack(fill="x")

    # ── UI helpers ──────────────────────────────────────────────────────
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

        for step in steps:
            pill = tk.Label(
                row, text=step, font=(FONT, 10, "bold"),
                bg="#eef2ff", fg=ACCENT, padx=10, pady=4
            )
            pill.pack(side="left", padx=(0, 6))

    def _drop_zone(self, parent, icon, title, on_click, pady_top=4):
        zone = tk.Frame(
            parent, bg=ZONE_BG, highlightbackground=BORDER,
            highlightthickness=1, cursor="hand2"
        )
        zone.pack(fill="x", pady=(pady_top, 0))

        inner = tk.Frame(zone, bg=ZONE_BG)
        inner.pack(fill="x", padx=16, pady=14)

        icon_lbl = tk.Label(
            inner, text=icon, font=(FONT, 24), bg=ZONE_BG, fg=TEXT_MUTED
        )
        icon_lbl.pack(side="left", padx=(0, 14))

        text_col = tk.Frame(inner, bg=ZONE_BG)
        text_col.pack(side="left", fill="x", expand=True)

        title_lbl = tk.Label(
            text_col, text=title, font=(FONT, 12, "bold"),
            bg=ZONE_BG, fg=TEXT, anchor="w"
        )
        title_lbl.pack(fill="x", anchor="w")

        status_lbl = tk.Label(
            text_col, text="Nessun file selezionato — clicca per sfogliare",
            font=(FONT, 10), bg=ZONE_BG, fg=TEXT_FAINT, anchor="w"
        )
        status_lbl.pack(fill="x", anchor="w", pady=(2, 0))

        widgets = [zone, inner, icon_lbl, text_col, title_lbl, status_lbl]

        def enter(event=None):
            for w in widgets:
                w.config(bg=ZONE_BG_HOVER)

        def leave(event=None):
            for w in widgets:
                w.config(bg=ZONE_BG)

        def click(event=None):
            on_click()

        for w in widgets:
            w.bind("<Button-1>", click)
            w.bind("<Enter>", enter)
            w.bind("<Leave>", leave)

        return icon_lbl, status_lbl

    def _on_btn_enter(self, event=None):
        if self.generate_btn["state"] != "disabled":
            self.generate_btn.config(bg=ACCENT_HOVER)

    def _on_btn_leave(self, event=None):
        if self.generate_btn["state"] != "disabled":
            self.generate_btn.config(bg=ACCENT)

    def _on_biosample_mode_change(self):
        """Mostra il selettore colonna solo in modalità Manuale."""
        if self.biosample_mode_var.get() == "manuale":
            self.biosample_column_frame.pack(anchor="w", fill="x")
        else:
            self.biosample_column_frame.pack_forget()

    # ── Run name: estrai dal nome file ─────────────────────────────────
    def _extract_run_name(self, filepath: str) -> str:
        basename = os.path.splitext(os.path.basename(filepath))[0]
        return basename

    # ── File pickers ─────────────────────────────────────────────────────
    def load_excel(self):
        initial = self._last_dir or os.path.expanduser("~")
        path = filedialog.askopenfilename(
            title="Seleziona Slims Extraction",
            initialdir=initial,
            filetypes=[("Excel files", "*.xlsx *.xls"), ("All files", "*.*")]
        )
        if path:
            self.excel_path = path
            self._last_dir = os.path.dirname(path)
            self.excel_icon.config(text="✅", fg=SUCCESS)
            self.excel_label.config(text=os.path.basename(path), fg=TEXT_MUTED)

    def load_csv(self):
        initial = self._last_dir or os.path.expanduser("~")
        path = filedialog.askopenfilename(
            title="Seleziona SampleSheet CSV",
            initialdir=initial,
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
        )
        if path:
            self.csv_path = path
            self._last_dir = os.path.dirname(path)
            self.csv_icon.config(text="✅", fg=SUCCESS)
            self.csv_label.config(text=os.path.basename(path), fg=TEXT_MUTED)

            extracted = self._extract_run_name(path)
            self.run_name_var.set(extracted)
            self.run_name_entry.config(fg=ACCENT)
            self.run_name_entry.bind("<Key>", self._on_run_name_edit)

            # Nasconde warning di eventuali run precedenti
            self._hide_warnings()

    def _on_run_name_edit(self, event=None):
        self.run_name_entry.config(fg=TEXT)
        self.run_name_entry.unbind("<Key>")

    # ── Warning box helpers ──────────────────────────────────────────────
    def _show_warnings(self, missing: list):
        """Mostra nell'UI la lista dei campioni non trovati nell'Excel."""
        content = "\n".join(f"• {s}" for s in missing)
        self.warning_text.config(state="normal")
        self.warning_text.delete("1.0", "end")
        self.warning_text.insert("end", content)
        self.warning_text.config(state="disabled")
        self.warning_card.pack(fill="x", padx=28, pady=(0, 20))

    def _hide_warnings(self):
        """Nasconde la warning box."""
        self.warning_card.pack_forget()

    # ── Validation ─────────────────────────────────────────────────────────
    def _validate_inputs(self):
        if not self.excel_path:
            messagebox.showwarning("Input mancante", "Carica il file Slims Extraction (.xlsx).")
            return False
        #Controllo contenuto Excel (assicurarsi che abbia le colonne necessarie)
        is_valid, error_message = validate_excel_content(self.excel_path)
        if not is_valid:
            messagebox.showerror("Errore Validazione Excel", error_message)
            return False

        if not self.csv_path:
            messagebox.showwarning("Input mancante", "Carica la SampleSheet (.csv).")
            return False
        if not self.run_name_var.get().strip():
            messagebox.showwarning("Input mancante", "Inserisci il Run Name.")
            return False
        return True

    # ── Progress helpers ───────────────────────────────────────────────────
    def _set_progress(self, fraction: float):
        self.progress_canvas.update_idletasks()
        w = self.progress_canvas.winfo_width()
        if self._progress_bar:
            self.progress_canvas.delete(self._progress_bar)
        self._progress_bar = self.progress_canvas.create_rectangle(
            0, 0, int(w * fraction), 6, fill=ACCENT, outline=""
        )

    def _set_status(self, msg: str, color: str = TEXT_MUTED, dot: str = None):
        self.status_var.set(msg)
        self.status_label.config(fg=color)
        self.status_dot.itemconfig(self._dot_id, fill=dot or color)

    # ── Main action ────────────────────────────────────────────────────────
    def on_generate(self):
        if not self._validate_inputs():
            return

        initial_output = self._last_dir or os.path.expanduser("~")
        output_dir = filedialog.askdirectory(
            title="Scegli cartella di output",
            initialdir=initial_output
        )
        if not output_dir:
            return

        # Pulisce warning precedenti prima di ogni nuova elaborazione
        self._hide_warnings()
        self.generate_btn.config(state="disabled", bg=ACCENT_DISABLED, cursor="arrow")
        self._set_progress(0)
        self._set_status("Elaborazione in corso…", TEXT_MUTED, WARNING)

        threading.Thread(
            target=self._run_pipeline,
            args=(output_dir,),
            daemon=True
        ).start()

    def _run_pipeline(self, output_dir: str):
        # Gira in un thread separato: qui dentro NON si deve toccare alcun
        # widget Tkinter (non è thread-safe). Ogni aggiornamento UI viene
        # passato al thread principale con self.after().
        run_name = self.run_name_var.get().strip()
        biosample_mode = self.biosample_mode_var.get()
        biosample_id_column = self.biosample_column_var.get()
        biosample_suffix = self.biosample_suffix_var.get()

        try:
            # ── Step 1: Mapping ────────────────────────────────────────
            self.after(0, self._set_status, "Step 1/2 – Mapping Slims Extraction…", TEXT_MUTED, WARNING)
            self.after(0, self._set_progress, 0.15)

            mapping_output = os.path.join(output_dir, f"{run_name}_mapping.csv")
            mapping_slims_emedgene(
                self.excel_path, mapping_output, run_name,
                biosample_mode=biosample_mode,
                biosample_id_column=biosample_id_column,
                biosample_suffix=biosample_suffix,
            )

            self.after(0, self._set_progress, 0.55)

            # ── Step 2: validazione SampleSheet contro l'Excel ────────────
            # Nessun file viene generato qui: si controlla solo che tutti i
            # Sample_ID della SampleSheet siano presenti nell'Excel.
            self.after(0, self._set_status, "Step 2/2 – Validazione SampleSheet…", TEXT_MUTED, WARNING)

            missing = check_samplesheet_samples(self.csv_path, self.excel_path)

            self.after(0, self._set_progress, 1.0)
            self.after(
                0, self._on_pipeline_done,
                output_dir, mapping_output, missing, None
            )

        except Exception as e:
            self.after(0, self._on_pipeline_done, output_dir, None, None, e)

    def _on_pipeline_done(self, output_dir, mapping_output, missing, error):
        """Eseguito sul thread principale: qui è sicuro aggiornare la UI."""
        try:
            if error is not None:
                self._set_status(f"Errore: {error}", ERROR, ERROR)
                messagebox.showerror("Errore", f"Errore durante l'elaborazione:\n{error}")
                return

            if missing:
                self._set_status(
                    f"⚠️ {len(missing)} campioni della SampleSheet non trovati nell'Excel",
                    WARNING, WARNING
                )
                self._show_warnings(missing)
                messagebox.showwarning(
                    "Completato con avvisi",
                    f"Mapping generato in:\n{output_dir}\n\n"
                    f"• {os.path.basename(mapping_output)}\n\n"
                    f"{len(missing)} campioni della SampleSheet non trovati nell'Excel: vedi il riquadro sotto."
                )
            else:
                self._set_status("✅ Tutti i campioni della SampleSheet sono presenti nell'Excel", SUCCESS, SUCCESS)
                messagebox.showinfo(
                    "Completato",
                    f"Mapping generato con successo in:\n{output_dir}\n\n"
                    f"• {os.path.basename(mapping_output)}\n\n"
                    "Tutti i campioni della SampleSheet sono stati trovati nell'Excel."
                )

        finally:
            self.generate_btn.config(state="normal", bg=ACCENT, cursor="hand2")
