import os
import sys

# Guard dla trybu .pyw (bez konsoli): stdout/stderr bywają None
if sys.stdout is None:
    sys.stdout = open(os.devnull, "w", encoding="utf-8")
if sys.stderr is None:
    sys.stderr = open(os.devnull, "w", encoding="utf-8")

import threading
import traceback
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

from pydub import AudioSegment


# ================================================================
# KOLORY (zgodne z motywem pro-audio / DAW)
# ================================================================

COLOR_BG = "#121212"           # tło okna (głęboka czerń)
COLOR_CARD = "#1C1C1C"         # karty, panele (ciemny grafit)
COLOR_ENTRY_BG = "#2A2A2A"     # tła pól tekstowych, combobox

COLOR_BTN = "#007AFF"          # główne przyciski "Plik/Folder" (niebieski Serato)
COLOR_BTN_HOVER = "#005CE6"

COLOR_BTN_ALT = "#2A2A2A"      # subtelniejsze przyciski (wybór języka)
COLOR_BTN_ALT_HOVER = "#3A3A3A"

COLOR_ACCENT = "#00E5FF"       # przycisk Konwertuj, pasek postępu (neonowy cyjan)
COLOR_ACCENT_DARK = "#00B3CC"

COLOR_RED = "#FF3366"          # przycisk folderu docelowego (nowoczesna czerwień/róż)
COLOR_RED_DARK = "#D81B60"

COLOR_TEXT = "#F0F0F0"
COLOR_TEXT_DIM = "#8A8A8A"


# ================================================================
# TŁUMACZENIA
# ================================================================

TRANSLATIONS = {
    "pl": {
        "title": "WAV → MP3 Converter",
        "header": "WAV → MP3",
        "input_label": "Plik WAV lub folder z plikami WAV:",
        "file_btn": "Plik...",
        "folder_btn": "Folder...",
        "output_label": "Katalog docelowy:",
        "browse": "Wybierz...",
        "bitrate_label": "Bitrate:",
        "start": "Konwertuj",
        "status_ready": "Gotowy",
        "status_progress": "({i}/{total}) {name}",
        "status_done": "Gotowe: {ok}/{total}",
        "status_error": "Błąd!",
        "warn_title": "Błąd",
        "warn_no_input": "Wybierz istniejący plik/folder.",
        "warn_not_wav": "Plik musi mieć rozszerzenie .wav",
        "info_empty_title": "Brak plików",
        "info_empty": "Nie znaleziono plików WAV.",
        "done_title": "Koniec",
        "done_msg": "Przekonwertowano {ok}/{total} plików.\nZapisano w: {out}",
        "done_errors": "Błędy:",
        "pick_wav": "Pliki WAV",
        "pick_all": "Wszystkie",
    },
    "en": {
        "title": "WAV → MP3 Converter",
        "header": "WAV → MP3",
        "input_label": "WAV file or folder with WAV files:",
        "file_btn": "File...",
        "folder_btn": "Folder...",
        "output_label": "Output folder:",
        "browse": "Browse...",
        "bitrate_label": "Bitrate:",
        "start": "Convert",
        "status_ready": "Ready",
        "status_progress": "({i}/{total}) {name}",
        "status_done": "Done: {ok}/{total}",
        "status_error": "Error!",
        "warn_title": "Error",
        "warn_no_input": "Select an existing file/folder.",
        "warn_not_wav": "File must have a .wav extension.",
        "info_empty_title": "No files",
        "info_empty": "No WAV files found.",
        "done_title": "Finished",
        "done_msg": "Converted {ok}/{total} files.\nSaved to: {out}",
        "done_errors": "Errors:",
        "pick_wav": "WAV files",
        "pick_all": "All files",
    },
}


# ================================================================
# LOGIKA KONWERSJI
# ================================================================

def convert_wav_to_mp3(input_path: Path, output_dir: Path, bitrate: str):
    output_dir.mkdir(parents=True, exist_ok=True)
    output_file = output_dir / f"{input_path.stem}.mp3"
    audio = AudioSegment.from_wav(input_path)
    audio.export(output_file, format="mp3", bitrate=bitrate)
    return output_file


# ================================================================
# GUI
# ================================================================

class App:
    def __init__(self, root):
        self.root = root
        self.lang = "pl"
        self.busy = False

        root.geometry("560x400")
        root.resizable(False, False)
        root.configure(bg=COLOR_BG)

        self.input_var = tk.StringVar()
        self.output_var = tk.StringVar(
            value=os.path.join(os.path.expanduser("~/Music"), "converted")
        )
        self.bitrate = tk.StringVar(value="320k")

        self._build_style()
        self._build_ui()
        self._apply_language()

    # ------------------------------------------------------------
    # Tłumaczenia
    # ------------------------------------------------------------

    def t(self, key):
        return TRANSLATIONS[self.lang][key]

    def set_language(self, lang):
        self.lang = lang
        self._apply_language()

    def _apply_language(self):
        t = self.t
        self.root.title(t("title"))
        self.header_label.config(text=t("header"))
        self.input_label.config(text=t("input_label"))
        self.file_btn.config(text=t("file_btn"))
        self.folder_btn.config(text=t("folder_btn"))
        self.output_label.config(text=t("output_label"))
        self.out_btn.config(text=t("browse"))
        self.bitrate_label.config(text=t("bitrate_label"))
        self.btn.config(text=t("start"))
        if not self.busy:
            self.status.config(text=t("status_ready"), fg=COLOR_TEXT_DIM)

    # ------------------------------------------------------------
    # Styl
    # ------------------------------------------------------------

    def _build_style(self):
        style = ttk.Style(self.root)
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass
        style.configure(
            "TCombobox", fieldbackground=COLOR_ENTRY_BG,
            background=COLOR_ENTRY_BG, foreground=COLOR_TEXT,
            arrowcolor=COLOR_TEXT, borderwidth=1,
        )
        style.map(
            "TCombobox",
            fieldbackground=[("readonly", COLOR_ENTRY_BG)],
            foreground=[("readonly", COLOR_TEXT)],
        )
        style.configure(
            "TProgressbar", background=COLOR_ACCENT,
            troughcolor=COLOR_ENTRY_BG, borderwidth=0,
        )

    # ------------------------------------------------------------
    # Layout
    # ------------------------------------------------------------

    def _build_ui(self):
        # Nagłówek
        header = tk.Frame(self.root, bg=COLOR_CARD)
        header.pack(fill="x")

        self.header_label = tk.Label(
            header, bg=COLOR_CARD, fg=COLOR_ACCENT,
            font=("Segoe UI", 16, "bold"),
        )
        self.header_label.pack(side="left", padx=20, pady=14)

        lang_frame = tk.Frame(header, bg=COLOR_CARD)
        lang_frame.pack(side="right", padx=12, pady=14)

        for flag, lang in (("🇵🇱", "pl"), ("🇬🇧", "en")):
            tk.Button(
                lang_frame, text=flag, width=4, bg=COLOR_BTN_ALT, fg=COLOR_TEXT,
                activebackground=COLOR_BTN_ALT_HOVER, activeforeground=COLOR_TEXT,
                relief="flat", bd=0, cursor="hand2",
                command=lambda l=lang: self.set_language(l),
            ).pack(side="left", padx=4)

        # Panel główny
        body = tk.Frame(self.root, bg=COLOR_CARD)
        body.pack(fill="both", expand=True, padx=20, pady=20)

        # Wejście
        self.input_label = tk.Label(body, bg=COLOR_CARD, fg=COLOR_TEXT,
                                    anchor="w")
        self.input_label.pack(fill="x", padx=15, pady=(12, 4))

        in_row = tk.Frame(body, bg=COLOR_CARD)
        in_row.pack(fill="x", padx=15)

        tk.Entry(
            in_row, textvariable=self.input_var, bg=COLOR_ENTRY_BG,
            fg=COLOR_TEXT, insertbackground=COLOR_TEXT, relief="flat", bd=0,
        ).pack(side="left", fill="x", expand=True, ipady=7, padx=(0, 8))

        self.file_btn = tk.Button(
            in_row, bg=COLOR_BTN, fg=COLOR_TEXT, font=("Segoe UI", 9, "bold"),
            activebackground=COLOR_BTN_HOVER, activeforeground=COLOR_TEXT,
            relief="flat", bd=0, cursor="hand2", command=self.pick_file,
        )
        self.file_btn.pack(side="left", ipadx=8, ipady=6, padx=(0, 4))

        self.folder_btn = tk.Button(
            in_row, bg=COLOR_BTN, fg=COLOR_TEXT, font=("Segoe UI", 9, "bold"),
            activebackground=COLOR_BTN_HOVER, activeforeground=COLOR_TEXT,
            relief="flat", bd=0, cursor="hand2", command=self.pick_dir,
        )
        self.folder_btn.pack(side="left", ipadx=8, ipady=6)

        # Wyjście
        self.output_label = tk.Label(body, bg=COLOR_CARD, fg=COLOR_TEXT,
                                     anchor="w")
        self.output_label.pack(fill="x", padx=15, pady=(12, 4))

        out_row = tk.Frame(body, bg=COLOR_CARD)
        out_row.pack(fill="x", padx=15)

        tk.Entry(
            out_row, textvariable=self.output_var, bg=COLOR_ENTRY_BG,
            fg=COLOR_TEXT, insertbackground=COLOR_TEXT, relief="flat", bd=0,
        ).pack(side="left", fill="x", expand=True, ipady=7, padx=(0, 8))

        self.out_btn = tk.Button(
            out_row, bg=COLOR_RED, fg="white", font=("Segoe UI", 9, "bold"),
            activebackground=COLOR_RED_DARK, activeforeground="white",
            relief="flat", bd=0, cursor="hand2", command=self.pick_out,
        )
        self.out_btn.pack(side="left", ipadx=10, ipady=6)

        # Bitrate
        br_row = tk.Frame(body, bg=COLOR_CARD)
        br_row.pack(fill="x", padx=15, pady=(14, 0))

        self.bitrate_label = tk.Label(br_row, bg=COLOR_CARD, fg=COLOR_TEXT)
        self.bitrate_label.pack(side="left", padx=(0, 8))

        ttk.Combobox(
            br_row, textvariable=self.bitrate,
            values=["128k", "192k", "256k", "320k"],
            state="readonly", width=8, font=("Segoe UI", 9)
        ).pack(side="left")

        # Pasek i status
        self.progress = ttk.Progressbar(body, mode="determinate")
        self.progress.pack(fill="x", padx=15, pady=(18, 6))

        self.status = tk.Label(body, bg=COLOR_CARD, fg=COLOR_TEXT_DIM,
                               anchor="w")
        self.status.pack(fill="x", padx=15)

        self.btn = tk.Button(
            body, command=self.start,
            bg=COLOR_ACCENT, fg="#000000", activebackground=COLOR_ACCENT_DARK,
            activeforeground="#000000", relief="flat", bd=0, cursor="hand2",
            font=("Segoe UI", 10, "bold"),
        )
        self.btn.pack(pady=(12, 0), ipadx=20, ipady=6)

    # ------------------------------------------------------------
    # Wybór
    # ------------------------------------------------------------

    def pick_file(self):
        f = filedialog.askopenfilename(filetypes=[
            (self.t("pick_wav"), "*.wav"),
            (self.t("pick_all"), "*.*"),
        ])
        if f:
            self.input_var.set(f)

    def pick_dir(self):
        d = filedialog.askdirectory()
        if d:
            self.input_var.set(d)

    def pick_out(self):
        d = filedialog.askdirectory(initialdir=self.output_var.get())
        if d:
            self.output_var.set(d)

    # ------------------------------------------------------------
    # Start / worker
    # ------------------------------------------------------------

    def set_status(self, text, color=COLOR_ACCENT):
        self.root.after(0, lambda: self.status.config(text=text, fg=color))

    def start(self):
        if self.busy:
            return

        src = Path(self.input_var.get().strip())
        out = Path(self.output_var.get().strip())

        if not src.exists():
            messagebox.showwarning(self.t("warn_title"),
                                   self.t("warn_no_input"))
            return
        if src.is_file():
            if src.suffix.lower() != ".wav":
                messagebox.showwarning(self.t("warn_title"),
                                       self.t("warn_not_wav"))
                return
            files = [src]
        else:
            files = sorted(src.glob("*.wav"))
            if not files:
                messagebox.showinfo(self.t("info_empty_title"),
                                    self.t("info_empty"))
                return

        self.busy = True
        self.btn.config(state="disabled", bg=COLOR_ENTRY_BG, fg=COLOR_TEXT_DIM)
        self.progress.config(maximum=len(files), value=0)

        threading.Thread(
            target=self.work,
            args=(files, out, self.bitrate.get(), self.lang),
            daemon=True,
        ).start()

    def work(self, files, out, bitrate, lang):
        tr = TRANSLATIONS[lang]
        failed = []
        total = len(files)

        for i, f in enumerate(files, 1):
            self.set_status(tr["status_progress"].format(i=i, total=total,
                                                         name=f.name))
            try:
                convert_wav_to_mp3(f, out, bitrate)
            except Exception:
                traceback.print_exc()
                failed.append(f.name)
            self.root.after(0, lambda v=i: self.progress.config(value=v))

        self.root.after(0, lambda: self.finish(total, failed, out, lang))

    def finish(self, total, failed, out, lang):
        tr = TRANSLATIONS[lang]
        self.busy = False
        self.btn.config(state="normal", bg=COLOR_ACCENT, fg="#000000")

        ok = total - len(failed)
        if failed:
            self.status.config(text=tr["status_done"].format(ok=ok, total=total),
                               fg=COLOR_RED)
        else:
            self.status.config(text=tr["status_done"].format(ok=ok, total=total),
                               fg=COLOR_ACCENT)

        msg = tr["done_msg"].format(ok=ok, total=total, out=out)
        if failed:
            msg += "\n\n" + tr["done_errors"] + "\n" + "\n".join(failed[:10])
        messagebox.showinfo(tr["done_title"], msg)


if __name__ == "__main__":
    root = tk.Tk()
    App(root)
    root.mainloop()