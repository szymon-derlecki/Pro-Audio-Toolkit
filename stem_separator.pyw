from __future__ import annotations

# ================================================================
# FIX: w trybie .pyw (bez konsoli) sys.stdout/sys.stderr = None,
# a tqdm (używany przez audio-separator) próbuje na nie pisać.
# Musi być PRZED importem audio_separator.
# ================================================================
import os
import sys

if sys.stdout is None:
    sys.stdout = open(os.devnull, "w", encoding="utf-8")
if sys.stderr is None:
    sys.stderr = open(os.devnull, "w", encoding="utf-8")

import shutil
import threading
import traceback
from pathlib import Path

import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from audio_separator.separator import Separator


# ================================================================
# KONFIGURACJA
# ================================================================

MODELS = {
    "BS-RoFormer": "model_bs_roformer_ep_317_sdr_12.9755.ckpt",
    "Mel-RoFormer": "model_mel_band_roformer_ep_3005_sdr_11.4360.ckpt",
    "MDX23C": "MDX23C-8KFFT-InstVoc_HQ.ckpt",
    "MDX-Net": "UVR-MDX-NET-Inst_HQ_4.onnx",
}

AUDIO_EXTENSIONS = (".wav", ".mp3", ".flac", ".m4a", ".ogg", ".aac")

# Kolory (zgodne z motywem pro-audio / DAW)
COLOR_BG = "#121212"           # tło okna (głęboka czerń)
COLOR_CARD = "#1C1C1C"         # karty, panele, log (ciemny grafit)
COLOR_ENTRY_BG = "#2A2A2A"     # tła pól tekstowych, combobox, nagłówki

COLOR_BTN = "#007AFF"          # główne przyciski - "Wybierz" (niebieski Serato/macOS)
COLOR_BTN_HOVER = "#005CE6"

COLOR_BTN_ALT = "#2A2A2A"      # subtelniejsze przyciski (wybór języka, scrollbar)
COLOR_BTN_ALT_HOVER = "#3A3A3A"

COLOR_ACCENT = "#00E5FF"       # przycisk START, tytuł, pasek postępu (neonowy cyjan)
COLOR_ACCENT_DARK = "#00B3CC"  # START po kliknięciu

COLOR_TEXT = "#F0F0F0"
COLOR_TEXT_DIM = "#8A8A8A"


# ================================================================
# TŁUMACZENIA
# ================================================================

TRANSLATIONS = {
    "pl": {
        "title": "Vocal Separator",
        "input_label": "Plik audio:",
        "output_label": "Folder zapisu:",
        "name_label": "Nazwa pliku:",
        "name_hint": "(bez rozszerzenia)",
        "model_label": "Model:",
        "mode_label": "Co wyciągnąć",
        "browse": "Wybierz…",
        "vocals": "Acapella",
        "instrumental": "Instrumental",
        "both": "Oba",
        "start": "START",
        "status_ready": "Gotowe.",
        "status_loading": "Ładuję model i separuję… (pierwszy raz pobierze model, to potrwa)",
        "audio_files": "Pliki audio",
        "all_files": "Wszystkie pliki",
        "log_selected_input": "Wybrano plik: {path}",
        "log_selected_output": "Wybrano folder: {path}",
        "log_start": "Start separacji: {file}",
        "log_model": "Model: {model}",
        "log_mode": "Tryb: {mode}",
        "log_saved": "Zapisano: {files}",
        "log_done": "Zakończono.",
        "err_no_file": "Wybierz poprawny plik audio.",
        "err_no_output": "Wybierz folder zapisu.",
        "err_no_results": "Brak plików wynikowych. Separacja nic nie zwróciła.",
        "title_error": "Błąd",
        "title_done": "Gotowe",
        "suffix_acapella": "acapella",
        "suffix_instrumental": "instrumental",
    },
    "en": {
        "title": "Vocal Separator",
        "input_label": "Audio file:",
        "output_label": "Output folder:",
        "name_label": "File name:",
        "name_hint": "(without extension)",
        "model_label": "Model:",
        "mode_label": "What to extract",
        "browse": "Browse…",
        "vocals": "Vocals",
        "instrumental": "Instrumental",
        "both": "Both",
        "start": "START",
        "status_ready": "Ready.",
        "status_loading": "Loading model and separating… (first run downloads the model, may take a while)",
        "audio_files": "Audio files",
        "all_files": "All files",
        "log_selected_input": "Selected file: {path}",
        "log_selected_output": "Selected folder: {path}",
        "log_start": "Separation started: {file}",
        "log_model": "Model: {model}",
        "log_mode": "Mode: {mode}",
        "log_saved": "Saved: {files}",
        "log_done": "Finished.",
        "err_no_file": "Select a valid audio file.",
        "err_no_output": "Select an output folder.",
        "err_no_results": "No output files. Separation returned nothing.",
        "title_error": "Error",
        "title_done": "Done",
        "suffix_acapella": "vocals",
        "suffix_instrumental": "instrumental",
    },
}


# ================================================================
# GUI
# ================================================================

class App(tk.Tk):
    def __init__(self):
        super().__init__()

        self.lang = "pl"

        self.input_var = tk.StringVar()
        self.output_var = tk.StringVar()
        self.name_var = tk.StringVar()
        self.mode_var = tk.StringVar(value="both")
        self.model_var = tk.StringVar(value=list(MODELS)[0])

        self.working = False

        self.configure(bg=COLOR_BG)
        self.geometry("820x620")
        self.minsize(720, 560)

        self._build_style()
        self._build_ui()
        self._apply_language()

        self.log(self.t("status_ready"))

    # ------------------------------------------------------------
    # Tłumaczenia
    # ------------------------------------------------------------

    def t(self, key: str) -> str:
        return TRANSLATIONS[self.lang][key]

    def set_language(self, lang: str) -> None:
        self.lang = lang
        self._apply_language()

    def _apply_language(self) -> None:
        t = self.t

        self.title(t("title"))
        self.input_label.config(text=t("input_label"))
        self.output_label.config(text=t("output_label"))
        self.name_label.config(text=t("name_label"))
        self.name_hint.config(text=t("name_hint"))
        self.model_label.config(text=t("model_label"))
        self.mode_frame.config(text=t("mode_label"))
        self.input_browse.config(text=t("browse"))
        self.output_browse.config(text=t("browse"))
        self.vocals_radio.config(text=t("vocals"))
        self.instr_radio.config(text=t("instrumental"))
        self.both_radio.config(text=t("both"))
        self.start_btn.config(text=t("start"))

        if not self.working:
            self.status_label.config(text=t("status_ready"))

    # ------------------------------------------------------------
    # Styl (ciemny motyw dla ttk)
    # ------------------------------------------------------------

    def _build_style(self) -> None:
        style = ttk.Style(self)
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass

        style.configure("TButton", background=COLOR_BTN, foreground=COLOR_TEXT,
                        borderwidth=0, focusthickness=0, padding=6,
                        font=("Segoe UI", 9))
        style.map("TButton", background=[("active", COLOR_BTN_HOVER)])

        style.configure("Accent.TButton", background=COLOR_ACCENT,
                        foreground="#000000", font=("Segoe UI", 10, "bold"))
        style.map("Accent.TButton",
                  background=[("active", COLOR_ACCENT_DARK),
                              ("disabled", COLOR_ENTRY_BG)],
                  foreground=[("disabled", COLOR_TEXT_DIM)])

        style.configure("TCombobox", background=COLOR_ENTRY_BG,
                        fieldbackground=COLOR_ENTRY_BG,
                        foreground=COLOR_TEXT, arrowcolor=COLOR_TEXT,
                        borderwidth=1)
        style.map("TCombobox",
                  fieldbackground=[("readonly", COLOR_ENTRY_BG)],
                  foreground=[("readonly", COLOR_TEXT)])

        style.configure("TScrollbar", background=COLOR_BTN_ALT,
                        troughcolor=COLOR_CARD, borderwidth=0,
                        arrowcolor=COLOR_TEXT)
        style.map("TScrollbar", background=[("active", COLOR_BTN_ALT_HOVER)])

        style.configure("TProgressbar", background=COLOR_ACCENT,
                        troughcolor=COLOR_ENTRY_BG, borderwidth=0)

    # ------------------------------------------------------------
    # Layout
    # ------------------------------------------------------------

    def _build_ui(self) -> None:
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        # ===== Górny pasek =====
        top = tk.Frame(self, bg=COLOR_CARD)
        top.grid(row=0, column=0, sticky="ew")

        tk.Label(
            top, text="VOCAL SEPARATOR", bg=COLOR_CARD,
            fg=COLOR_ACCENT, font=("Segoe UI", 18, "bold"),
        ).pack(side="left", padx=20, pady=16)

        lang_frame = tk.Frame(top, bg=COLOR_CARD)
        lang_frame.pack(side="right", padx=10, pady=16)

        for flag, lang in (("🇵🇱", "pl"), ("🇬🇧", "en")):
            tk.Button(
                lang_frame, text=flag, width=4, bg=COLOR_BTN_ALT, fg=COLOR_TEXT,
                activebackground=COLOR_BTN_ALT_HOVER, activeforeground=COLOR_TEXT,
                relief="flat", bd=0, cursor="hand2",
                command=lambda l=lang: self.set_language(l),
            ).pack(side="left", padx=4)

        self.start_btn = ttk.Button(
            top, text="START", style="Accent.TButton", command=self.start
        )
        self.start_btn.pack(side="right", padx=20, pady=16)

        # ===== Główny obszar =====
        main = tk.Frame(self, bg=COLOR_BG)
        main.grid(row=1, column=0, sticky="nsew", padx=20, pady=20)
        main.grid_columnconfigure(1, weight=1)
        main.grid_rowconfigure(0, weight=1)

        # Lewy panel (ustawienia)
        left = tk.Frame(main, bg=COLOR_CARD)
        left.grid(row=0, column=0, sticky="nsew", padx=(0, 15))
        left.grid_columnconfigure(0, weight=1)

        # Plik wejściowy
        self.input_label = tk.Label(left, bg=COLOR_CARD, fg=COLOR_TEXT, anchor="w")
        self.input_label.grid(row=0, column=0, sticky="ew", padx=15, pady=(15, 4))

        input_row = tk.Frame(left, bg=COLOR_CARD)
        input_row.grid(row=1, column=0, sticky="ew", padx=15)
        input_row.grid_columnconfigure(0, weight=1)

        tk.Entry(
            input_row, textvariable=self.input_var,
            bg=COLOR_ENTRY_BG, fg=COLOR_TEXT, insertbackground=COLOR_TEXT,
            relief="flat", bd=0,
        ).grid(row=0, column=0, sticky="ew", padx=(0, 8), ipady=7)

        self.input_browse = tk.Button(
            input_row, bg=COLOR_BTN, fg=COLOR_TEXT, font=("Segoe UI", 9, "bold"),
            activebackground=COLOR_BTN_HOVER, activeforeground=COLOR_TEXT,
            relief="flat", bd=0, cursor="hand2", command=self.pick_input,
        )
        self.input_browse.grid(row=0, column=1, ipadx=10, ipady=6)

        # Folder wyjściowy
        self.output_label = tk.Label(left, bg=COLOR_CARD, fg=COLOR_TEXT, anchor="w")
        self.output_label.grid(row=2, column=0, sticky="ew", padx=15, pady=(14, 4))

        output_row = tk.Frame(left, bg=COLOR_CARD)
        output_row.grid(row=3, column=0, sticky="ew", padx=15)
        output_row.grid_columnconfigure(0, weight=1)

        tk.Entry(
            output_row, textvariable=self.output_var,
            bg=COLOR_ENTRY_BG, fg=COLOR_TEXT, insertbackground=COLOR_TEXT,
            relief="flat", bd=0,
        ).grid(row=0, column=0, sticky="ew", padx=(0, 8), ipady=7)

        self.output_browse = tk.Button(
            output_row, bg=COLOR_BTN, fg=COLOR_TEXT, font=("Segoe UI", 9, "bold"),
            activebackground=COLOR_BTN_HOVER, activeforeground=COLOR_TEXT,
            relief="flat", bd=0, cursor="hand2", command=self.pick_output,
        )
        self.output_browse.grid(row=0, column=1, ipadx=10, ipady=6)

        # Nazwa pliku
        self.name_label = tk.Label(left, bg=COLOR_CARD, fg=COLOR_TEXT, anchor="w")
        self.name_label.grid(row=4, column=0, sticky="ew", padx=15, pady=(14, 4))

        name_row = tk.Frame(left, bg=COLOR_CARD)
        name_row.grid(row=5, column=0, sticky="ew", padx=15)
        name_row.grid_columnconfigure(0, weight=1)

        tk.Entry(
            name_row, textvariable=self.name_var,
            bg=COLOR_ENTRY_BG, fg=COLOR_TEXT, insertbackground=COLOR_TEXT,
            relief="flat", bd=0,
        ).grid(row=0, column=0, sticky="ew", padx=(0, 8), ipady=7)

        self.name_hint = tk.Label(name_row, bg=COLOR_CARD, fg=COLOR_TEXT_DIM)
        self.name_hint.grid(row=0, column=1)

        # Model
        self.model_label = tk.Label(left, bg=COLOR_CARD, fg=COLOR_TEXT, anchor="w")
        self.model_label.grid(row=6, column=0, sticky="ew", padx=15, pady=(14, 4))

        ttk.Combobox(
            left, textvariable=self.model_var, values=list(MODELS),
            state="readonly", font=("Segoe UI", 9)
        ).grid(row=7, column=0, sticky="ew", padx=15, ipady=3)

        # Tryb
        self.mode_frame = tk.LabelFrame(
            left, bg=COLOR_CARD, fg=COLOR_TEXT, bd=1, relief="solid",
            highlightbackground=COLOR_ENTRY_BG, highlightcolor=COLOR_ENTRY_BG,
        )
        self.mode_frame.grid(row=8, column=0, sticky="ew", padx=15, pady=(16, 15))

        radio_row = tk.Frame(self.mode_frame, bg=COLOR_CARD)
        radio_row.pack(fill="x", padx=10, pady=8)

        radio_opts = {
            "bg": COLOR_CARD, "fg": COLOR_TEXT, "selectcolor": COLOR_ENTRY_BG,
            "activebackground": COLOR_CARD, "activeforeground": COLOR_TEXT,
            "cursor": "hand2",
        }
        self.vocals_radio = tk.Radiobutton(
            radio_row, value="vocals", variable=self.mode_var, **radio_opts)
        self.vocals_radio.pack(side="left", padx=(0, 16))

        self.instr_radio = tk.Radiobutton(
            radio_row, value="instrumental", variable=self.mode_var, **radio_opts)
        self.instr_radio.pack(side="left", padx=(0, 16))

        self.both_radio = tk.Radiobutton(
            radio_row, value="both", variable=self.mode_var, **radio_opts)
        self.both_radio.pack(side="left")

        # ===== Prawy panel (log) =====
        right = tk.Frame(main, bg=COLOR_CARD)
        right.grid(row=0, column=1, sticky="nsew")
        right.grid_columnconfigure(0, weight=1)
        right.grid_rowconfigure(0, weight=1)

        self.log_box = tk.Text(
            right, bg=COLOR_CARD, fg="#cccccc", relief="flat", bd=0,
            wrap="word", font=("Consolas", 9),
        )
        self.log_box.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)

        scroll = ttk.Scrollbar(right, orient="vertical",
                               command=self.log_box.yview)
        scroll.grid(row=0, column=1, sticky="ns", pady=10)
        self.log_box.configure(yscrollcommand=scroll.set)

        # ===== Dolny pasek =====
        bottom = tk.Frame(self, bg=COLOR_BG)
        bottom.grid(row=2, column=0, sticky="ew", padx=20, pady=(0, 12))
        bottom.grid_columnconfigure(0, weight=1)

        self.status_label = tk.Label(
            bottom, bg=COLOR_BG, fg=COLOR_TEXT_DIM, anchor="w")
        self.status_label.grid(row=0, column=0, sticky="w")

        self.progress = ttk.Progressbar(bottom, mode="indeterminate", length=180)
        self.progress.grid(row=0, column=1, sticky="e")

    # ------------------------------------------------------------
    # Pomocnicze
    # ------------------------------------------------------------

    def log(self, msg: str) -> None:
        self.log_box.insert("end", msg + "\n")
        self.log_box.see("end")

    # ------------------------------------------------------------
    # Wybór plików
    # ------------------------------------------------------------

    def pick_input(self) -> None:
        filetypes = [
            (self.t("audio_files"), "*.mp3 *.wav *.flac *.m4a *.ogg *.aac"),
            (self.t("all_files"), "*.*"),
        ]
        path = filedialog.askopenfilename(filetypes=filetypes)
        if path:
            self.input_var.set(path)
            if not self.name_var.get():
                self.name_var.set(Path(path).stem)
            if not self.output_var.get():
                self.output_var.set(str(Path(path).parent))
            self.log(self.t("log_selected_input").format(path=path))

    def pick_output(self) -> None:
        path = filedialog.askdirectory()
        if path:
            self.output_var.set(path)
            self.log(self.t("log_selected_output").format(path=path))

    # ------------------------------------------------------------
    # Start / worker
    # ------------------------------------------------------------

    def start(self) -> None:
        if self.working:
            return

        inp = Path(self.input_var.get().strip())
        out = Path(self.output_var.get().strip())
        name = self.name_var.get().strip()

        if not inp.is_file():
            messagebox.showerror(self.t("title_error"), self.t("err_no_file"))
            return
        if not out.is_dir():
            messagebox.showerror(self.t("title_error"), self.t("err_no_output"))
            return
        if not name:
            name = inp.stem

        self.working = True
        self.start_btn.config(state="disabled")
        self.progress.start(12)
        self.status_label.config(text=self.t("status_loading"))

        mode_display = {
            "vocals": self.t("vocals"),
            "instrumental": self.t("instrumental"),
            "both": self.t("both"),
        }[self.mode_var.get()]

        self.log(self.t("log_start").format(file=inp.name))
        self.log(self.t("log_model").format(model=self.model_var.get()))
        self.log(self.t("log_mode").format(mode=mode_display))

        threading.Thread(
            target=self.worker, args=(inp, out, name), daemon=True
        ).start()

    def worker(self, inp: Path, out: Path, name: str) -> None:
        try:
            mode = self.mode_var.get()
            single = {
                "vocals": "Vocals",
                "instrumental": "Instrumental",
            }.get(mode)

            tmp = out / ".separator_tmp"
            tmp.mkdir(exist_ok=True)

            sep = Separator(
                output_dir=str(tmp),
                output_format="wav",
                output_single_stem=single,
            )
            sep.load_model(model_filename=MODELS[self.model_var.get()])
            files = sep.separate(str(inp))

            # Zbierz wyniki: ścieżki zwrócone przez separate() + wszystko w tmp
            candidates = [Path(f) for f in files if Path(f).is_file()]
            for p in tmp.rglob("*"):
                if p.is_file() and p.suffix.lower() in AUDIO_EXTENSIONS \
                        and p not in candidates:
                    candidates.append(p)

            if not candidates:
                raise RuntimeError(self.t("err_no_results"))

            vocab = {
                "acapella": self.t("suffix_acapella"),
                "instrumental": self.t("suffix_instrumental"),
            }
            saved = []

            for src in candidates:
                low = src.name.lower()
                if "vocals" in low:
                    suffix = vocab["acapella"]
                elif "instrumental" in low or "no_vocals" in low:
                    suffix = vocab["instrumental"]
                else:
                    suffix = src.stem

                dst = out / f"{name}_{suffix}{src.suffix}"
                n = 1
                while dst.exists():
                    dst = out / f"{name}_{suffix}_{n}{src.suffix}"
                    n += 1

                shutil.move(str(src), str(dst))
                saved.append(dst.name)

            shutil.rmtree(tmp, ignore_errors=True)

            self.after(0, self.done,
                       self.t("log_saved").format(files=", ".join(saved)))

        except Exception:
            tb = traceback.format_exc()
            self.after(0, self.done, tb, True)

    def done(self, msg: str, error: bool = False) -> None:
        self.working = False
        self.progress.stop()
        self.start_btn.config(state="normal")
        self.status_label.config(text=msg.splitlines()[-1] if msg else "")
        self.log(msg)
        self.log(self.t("log_done"))

        if error:
            messagebox.showerror(self.t("title_error"), msg)
        else:
            messagebox.showinfo(self.t("title_done"), msg)


if __name__ == "__main__":
    app = App()
    app.mainloop()