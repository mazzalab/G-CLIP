import tkinter as tk
from PIL import Image, ImageTk


# ── Design tokens (coerenti con le pagine tool) ────────────────────────────
FONT = "Segoe UI"

BG = "#f4f6fb"
CARD_BG = "#ffffff"
BORDER = "#e2e8f0"
CARD_BG_HOVER = "#eef2ff"

TEXT = "#1e293b"
TEXT_MUTED = "#64748b"
TEXT_FAINT = "#94a3b8"

ACCENT = "#4f46e5"


TOOLS = [
    # {
    #     "id": "csv",
    #     "icon": "📊",
    #     "title": "Excel to Emedgene CSV Converter",
    #     "subtitle": "Converte un Excel paziente in CSV Emedgene, con normalizzazione date e validazione HPO.",
    # },
    # {
    #     "id": "FileRunWES",
    #     "icon": "🧬",
    #     "title": "Generate files Run WES",
    #     "subtitle": "Genera il mapping Emedgene e la SampleSheet di run a partire da Slims Extraction + SampleSheet LIMS.",
    # },
    {
        "id": "samplesheetConverter",
        "icon": "📄",
        "title": "Generate SampleSheet for BaseSpace",
        "subtitle": "Converte un Excel Slims Extraction nel formato import sample template BaseSpace(Sample ID / Well Position / Project).",
    },
]


class WelcomePage(tk.Frame):
    def __init__(self, parent, logo_path: str, on_select_tool=None):
        super().__init__(parent, bg=BG)

        self.on_select_tool = on_select_tool

        tk.Label(self, text="", pady=10, bg=BG).pack()

        # Logo
        try:
            img = Image.open(logo_path)
            img = img.resize((90, 90))
            logo = ImageTk.PhotoImage(img)
            tk.Label(self, image=logo, bg=BG).pack()
            self.logo = logo   # keep ref
        except Exception:
            tk.Label(self, text="(Logo missing)", bg=BG).pack()

        tk.Label(
            self,
            text="Welcome to G-CLIP",
            font=(FONT, 22, "bold"), bg=BG, fg=TEXT,
        ).pack(pady=(12, 4))

        tk.Label(
            self,
            text="Gemelli Clinical Informatics Platform",
            font=(FONT, 13), bg=BG, fg=TEXT_MUTED,
        ).pack()

        tk.Label(
            self,
            text="Seleziona uno strumento per iniziare, oppure usa il menu Tools in alto.",
            font=(FONT, 11), bg=BG, fg=TEXT_FAINT,
        ).pack(pady=(8, 20))

        # ── Tool cards ───────────────────────────────────────────────────
        tools_frame = tk.Frame(self, bg=BG)
        tools_frame.pack(fill="x", padx=32)

        for tool in TOOLS:
            self._tool_card(tools_frame, tool)

    # ── Tool card ────────────────────────────────────────────────────────
    def _tool_card(self, parent, tool: dict):
        card = tk.Frame(
            parent, bg=CARD_BG, highlightbackground=BORDER,
            highlightthickness=1, cursor="hand2"
        )
        card.pack(fill="x", pady=6)

        inner = tk.Frame(card, bg=CARD_BG)
        inner.pack(fill="x", padx=16, pady=12)

        icon = tk.Label(
            inner, text=tool["icon"], font=(FONT, 26), bg=CARD_BG, fg=ACCENT
        )
        icon.pack(side="left", padx=(0, 14))

        text_col = tk.Frame(inner, bg=CARD_BG)
        text_col.pack(side="left", fill="x", expand=True)

        title = tk.Label(
            text_col, text=tool["title"], font=(FONT, 14, "bold"),
            bg=CARD_BG, fg=TEXT, anchor="w"
        )
        title.pack(fill="x", anchor="w")

        subtitle = tk.Label(
            text_col, text=tool["subtitle"], font=(FONT, 11),
            bg=CARD_BG, fg=TEXT_MUTED, anchor="w", justify="left", wraplength=560
        )
        subtitle.pack(fill="x", anchor="w", pady=(3, 0))

        arrow = tk.Label(
            inner, text="→", font=(FONT, 16, "bold"), bg=CARD_BG, fg=TEXT_FAINT
        )
        arrow.pack(side="right", padx=(10, 0))

        widgets = [card, inner, icon, text_col, title, subtitle, arrow]

        def select(event=None):
            if self.on_select_tool:
                self.on_select_tool(tool["id"])

        def enter(event=None):
            for w in widgets:
                w.config(bg=CARD_BG_HOVER)

        def leave(event=None):
            for w in widgets:
                w.config(bg=CARD_BG)

        for w in widgets:
            w.bind("<Button-1>", select)
            w.bind("<Enter>", enter)
            w.bind("<Leave>", leave)
