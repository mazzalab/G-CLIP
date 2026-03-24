import tkinter as tk
from tkinter import filedialog, messagebox
import threading
import os

from tools.generatefileRun_core import mapping_slims_emedgene, convertitore_samplesheet_WES


class GeneratefileRun(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent)

        self.excel_path = None
        self.csv_path = None
        self._last_dir = None  # ricorda l'ultima cartella usata

        # ── Title ──────────────────────────────────────────────────────────
        tk.Label(
            self,
            text="SampleSheet Run Validator",
            font=("Arial", 15, "bold")
        ).pack(pady=(18, 2))

        tk.Label(
            self,
            text="1) Carica Slims Extraction  ·  2) Carica SampleSheet  ·  3) Inserisci Run Name",
            font=("Arial", 10),
            fg="#555555"
        ).pack(pady=(0, 10))

        # ── File loading ───────────────────────────────────────────────────
        files_frame = tk.LabelFrame(self, text="File di Input", padx=12, pady=10)
        files_frame.pack(fill="x", padx=20, pady=(0, 8))

        # Row 0 – Excel
        tk.Button(
            files_frame,
            text="📂  Carica Slims Extraction (.xlsx)",
            width=38,
            command=self.load_excel
        ).grid(row=0, column=0, sticky="w", pady=4)

        self.excel_label = tk.Label(
            files_frame, text="Nessun file selezionato",
            fg="#888888", font=("Arial", 9), anchor="w"
        )
        self.excel_label.grid(row=0, column=1, padx=10, sticky="w")

        # Row 1 – CSV
        tk.Button(
            files_frame,
            text="📂 Carica SampleSheet (.csv)",
            width=38,
            command=self.load_csv
        ).grid(row=1, column=0, sticky="w", pady=4)

        self.csv_label = tk.Label(
            files_frame, text="Nessun file selezionato",
            fg="#888888", font=("Arial", 9), anchor="w"
        )
        self.csv_label.grid(row=1, column=1, padx=10, sticky="w")

        # ── Options ────────────────────────────────────────────────────────
        options_frame = tk.LabelFrame(self, text="Opzioni", padx=12, pady=10)
        options_frame.pack(fill="x", padx=20, pady=(0, 8))

        tk.Label(options_frame, text="Run Name:", font=("Arial", 10)).grid(
            row=0, column=0, sticky="w", pady=4
        )

        self.run_name_var = tk.StringVar()
        self.run_name_entry = tk.Entry(
            options_frame, width=32, font=("Arial", 10),
            textvariable=self.run_name_var
        )
        self.run_name_entry.grid(row=0, column=1, padx=10, pady=4, sticky="w")

        tk.Label(
            options_frame,
            text="(estratto dal nome del SampleSheet, modificabile)",
            font=("Arial", 8), fg="#999999"
        ).grid(row=0, column=2, padx=4, sticky="w")

        # ── Generate button ────────────────────────────────────────────────
        self.generate_btn = tk.Button(
            self,
            text="⚙️ Genera File",
            font=("Arial", 12, "bold"),
            bg="#2e86de",
            fg="black",
            activebackground="#1a5fa8",
            activeforeground="white",
            width=20,
            relief="flat",
            cursor="hand2",
            command=self.on_generate
        )
        self.generate_btn.pack(pady=(6, 4))

        # ── Status bar ─────────────────────────────────────────────────────
        self.status_var = tk.StringVar(value="In attesa…")
        self.status_label = tk.Label(
            self,
            textvariable=self.status_var,
            font=("Arial", 9, "italic"),
            fg="#555555"
        )
        self.status_label.pack(pady=(0, 4))

        # ── Progress bar ───────────────────────────────────────────────────
        self.progress_canvas = tk.Canvas(self, height=8, bg="#e0e0e0",
                                         highlightthickness=0)
        self.progress_canvas.pack(fill="x", padx=20, pady=(0, 8))
        self._progress_bar = None

        # ── Warning box campioni mancanti (nascosta finché non serve) ──────
        self.warning_frame = tk.LabelFrame(
            self,
            text="⚠️  Campioni non trovati nell'Excel",
            padx=10, pady=10,
            fg="#e67e22",
            font=("Arial", 9, "bold")
        )
        # non viene packato subito: appare solo se ci sono campioni mancanti

        self.warning_text = tk.Text(
            self.warning_frame,
            height=10,
            font=("Arial", 9),
            fg="#c0392b",
            bg="#fff8f0",
            relief="flat",
            state="disabled",
            wrap="word"
        )
        self.warning_text.pack(fill="x")

    # ── Run name: estrai dal nome file ─────────────────────────────────────
    def _extract_run_name(self, filepath: str) -> str:
        basename = os.path.splitext(os.path.basename(filepath))[0]
        return basename

    # ── File pickers ───────────────────────────────────────────────────────
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
            self.excel_label.config(text=os.path.basename(path), fg="#222222")

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
            self.csv_label.config(text=os.path.basename(path), fg="#222222")

            extracted = self._extract_run_name(path)
            self.run_name_var.set(extracted)
            self.run_name_entry.config(fg="#2e86de")
            self.run_name_entry.bind("<Key>", self._on_run_name_edit)

            # Nasconde warning di eventuali run precedenti
            self._hide_warnings()

    def _on_run_name_edit(self, event=None):
        self.run_name_entry.config(fg="#000000")
        self.run_name_entry.unbind("<Key>")

    # ── Warning box helpers ────────────────────────────────────────────────
    def _show_warnings(self, missing: list):
        """Mostra nell'UI la lista dei campioni non trovati nell'Excel."""
        content = "\n".join(f"• {s}" for s in missing)
        self.warning_text.config(state="normal")
        self.warning_text.delete("1.0", "end")
        self.warning_text.insert("end", content)
        self.warning_text.config(state="disabled")
        self.warning_frame.pack(fill="x", padx=20, pady=(0, 10))

    def _hide_warnings(self):
        """Nasconde la warning box."""
        self.warning_frame.pack_forget()

    # ── Validation ─────────────────────────────────────────────────────────
    def _validate_inputs(self):
        if not self.excel_path:
            messagebox.showwarning("Input mancante", "Carica il file Slims Extraction (.xlsx).")
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
            0, 0, int(w * fraction), 8, fill="#2e86de", outline=""
        )

    def _set_status(self, msg: str, color: str = "#555555"):
        self.status_var.set(msg)
        self.status_label.config(fg=color)

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
        self.generate_btn.config(state="disabled")
        self._set_progress(0)
        self._set_status("Elaborazione in corso…")

        threading.Thread(
            target=self._run_pipeline,
            args=(output_dir,),
            daemon=True
        ).start()

    def _run_pipeline(self, output_dir: str):
        run_name = self.run_name_var.get().strip()

        try:
            # ── Step 1: Mapping ────────────────────────────────────────────
            self._set_status("Step 1/2 – Mapping Slims Extraction…")
            self._set_progress(0.15)

            mapping_output = os.path.join(output_dir, f"{run_name}_mapping.csv")
            mapping_slims_emedgene(self.excel_path, mapping_output, run_name)

            self._set_progress(0.55)

            # ── Step 2: SampleSheet conversion ────────────────────────────
            self._set_status("Step 2/2 – Conversione SampleSheet…")

            samplesheet_output = os.path.join(
                output_dir, f"{run_name}_samplesheet_converted.csv"
            )
            missing = convertitore_samplesheet_WES(
                self.csv_path, samplesheet_output, self.excel_path, run_name
            )

            self._set_progress(1.0)

            # ── Aggiorna status e mostra warning inline se necessario ──────
            if missing:
                self._set_status(
                    f"✅ File generati · ⚠️ {len(missing)} campioni non trovati nell'Excel",
                    color="#e67e22"
                )
                self._show_warnings(missing)
            else:
                self._set_status(f"✅ File generati in: {output_dir}", color="#27ae60")

            messagebox.showinfo(
                "Completato",
                f"File generati con successo in:\n{output_dir}\n\n"
                f"• {os.path.basename(mapping_output)}\n"
                f"• {os.path.basename(samplesheet_output)}"
            )

        except Exception as e:
            self._set_status(f"❌ Errore: {e}", color="#e74c3c")
            messagebox.showerror("Errore", f"Errore durante l'elaborazione:\n{e}")

        finally:
            self.generate_btn.config(state="normal")