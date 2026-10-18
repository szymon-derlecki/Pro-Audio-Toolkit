import os
import sys

# Guard dla trybu .pyw (bez konsoli): stdout/stderr bywają None
if sys.stdout is None:
    sys.stdout = open(os.devnull, "w", encoding="utf-8")
if sys.stderr is None:
    sys.stderr = open(os.devnull, "w", encoding="utf-8")

import json
import re
import threading
import traceback
import urllib.parse
import urllib.request
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from yt_dlp import YoutubeDL

UA = {"User-Agent": "Mozilla/5.0"}

# ================================================================
# KOLORY (zgodne z motywem pro-audio / DAW)
# ================================================================

COLOR_BG = "#121212"           # tło okna (głęboka czerń)
COLOR_CARD = "#1C1C1C"         # karty, panele (ciemny grafit)
COLOR_ENTRY_BG = "#2A2A2A"     # tła pól tekstowych

COLOR_BTN = "#007AFF"          # główne przyciski (niebieski Serato/macOS)
COLOR_BTN_HOVER = "#005CE6"

COLOR_BTN_ALT = "#2A2A2A"      # subtelniejsze przyciski (wybór języka)
COLOR_BTN_ALT_HOVER = "#3A3A3A"

COLOR_ACCENT = "#00E5FF"       # przycisk Pobierz, pasek postępu (neonowy cyjan)
COLOR_ACCENT_DARK = "#00B3CC"

COLOR_RED = "#FF3366"          # przycisk wyboru folderu / błędy
COLOR_RED_DARK = "#D81B60"

COLOR_TEXT = "#F0F0F0"
COLOR_TEXT_DIM = "#8A8A8A"


# ================================================================
# TŁUMACZENIA
# ================================================================

TRANSLATIONS = {
    "pl": {
        "title": "Spotify MP3 Downloader",
        "header": "SPOTIFY MP3",
        "url_label": "Spotify URL (pojedynczy utwór):",
        "folder_label": "Katalog docelowy:",
        "browse": "Wybierz...",
        "start": "Pobierz MP3",
        "status_ready": "Gotowy",
        "status_fetching": "Pobieranie danych utworu...",
        "status_downloading": "Pobieranie: {query}",
        "status_done": "Gotowe!",
        "status_error": "Błąd!",
        "done_title": "Sukces",
        "done_msg": "Pobrano: {query}",
        "error_title": "Błąd",
        "warn_title": "Brak danych",
        "warn_no_url": "Wklej link!",
        "warn_no_folder": "Folder nie istnieje.",
        "err_only_track": "Obsługuję tylko pojedyncze utwory Spotify.",
    },
    "en": {
        "title": "Spotify MP3 Downloader",
        "header": "SPOTIFY MP3",
        "url_label": "Spotify URL (single track):",
        "folder_label": "Target folder:",
        "browse": "Browse...",
        "start": "Download MP3",
        "status_ready": "Ready",
        "status_fetching": "Fetching track info...",
        "status_downloading": "Downloading: {query}",
        "status_done": "Done!",
        "status_error": "Error!",
        "done_title": "Success",
        "done_msg": "Downloaded: {query}",
        "error_title": "Error",
        "warn_title": "Missing data",
        "warn_no_url": "Paste a link!",
        "warn_no_folder": "Folder does not exist.",
        "err_only_track": "Only single Spotify tracks are supported.",
    },
}


# ================================================================
# LOGIKA POBIERANIA
# ================================================================

def http_get(url):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=15) as r:
        return r.read().decode("utf-8", errors="replace")


def spotify_query(url, err_msg):
    """Zwraca 'Artysta - Tytuł' dla linku do utworu Spotify."""
    url = url.split("?")[0]
    if "/track/" not in url:
        raise ValueError(err_msg)

    oembed = (
        "https://open.spotify.com/oembed?url="
        + urllib.parse.quote(url, safe="")
    )
    title = json.loads(http_get(oembed))["title"]

    artist = ""
    try:
        html = http_get(url)
        m = re.search(
            r'<meta property="og:description" content="([^"]+)"', html
        )
        if m:
            # format: "Artysta · Album · Song · 2020"
            artist = m.group(1).split("·")[0].strip()
    except Exception:
        traceback.print_exc()

    return f"{artist} - {title}" if artist else title


def download_one(query, folder):
    safe = "".join(c for c in query if c not in '\\/:*?"<>|')
    opts = {
        "format": "bestaudio/best",
        "outtmpl": os.path.join(folder, f"{safe}.%(ext)s"),
        "noplaylist": True,
        "quiet": True,
        "no_warnings": True,
        "postprocessors": [
            {
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "192",
            }
        ],
    }
    with YoutubeDL(opts) as ydl:
        ydl.download([f"ytsearch1:{query} audio"])
    return safe


# ================================================================
# GUI
# ================================================================

class App:
    def __init__(self, root):
        self.root = root
        self.lang = "pl"
        self.busy = False

        root.geometry("560x340")
        root.resizable(False, False)
        root.configure(bg=COLOR_BG)

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
        self.url_label.config(text=t("url_label"))
        self.folder_label.config(text=t("folder_label"))
        self.choose_btn.config(text=t("browse"))
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

        self.url_label = tk.Label(
            body, bg=COLOR_CARD, fg=COLOR_TEXT, anchor="w",
        )
        self.url_label.pack(fill="x", padx=15, pady=(12, 4))

        self.url_entry = tk.Entry(
            body, bg=COLOR_ENTRY_BG, fg=COLOR_TEXT,
            insertbackground=COLOR_TEXT, relief="flat", bd=0,
        )
        self.url_entry.pack(fill="x", padx=15, ipady=7)

        self.folder_label = tk.Label(
            body, bg=COLOR_CARD, fg=COLOR_TEXT, anchor="w",
        )
        self.folder_label.pack(fill="x", padx=15, pady=(12, 4))

        frame = tk.Frame(body, bg=COLOR_CARD)
        frame.pack(fill="x", padx=15)

        self.folder_var = tk.StringVar(value=os.path.expanduser("~/Music"))
        tk.Entry(
            frame, textvariable=self.folder_var, bg=COLOR_ENTRY_BG,
            fg=COLOR_TEXT, insertbackground=COLOR_TEXT, relief="flat", bd=0,
        ).pack(side="left", fill="x", expand=True, ipady=7, padx=(0, 8))

        self.choose_btn = tk.Button(
            frame, bg=COLOR_RED, fg="white", font=("Segoe UI", 9, "bold"),
            activebackground=COLOR_RED_DARK, activeforeground="white",
            relief="flat", bd=0, cursor="hand2", command=self.choose,
        )
        self.choose_btn.pack(side="left", ipadx=10, ipady=6)

        self.progress = ttk.Progressbar(body, mode="indeterminate")
        self.progress.pack(fill="x", padx=15, pady=(18, 6))

        self.status = tk.Label(
            body, bg=COLOR_CARD, fg=COLOR_TEXT_DIM, anchor="w",
        )
        self.status.pack(fill="x", padx=15)

        self.btn = tk.Button(
            body, command=self.start,
            bg=COLOR_ACCENT, fg="#000000", activebackground=COLOR_ACCENT_DARK,
            activeforeground="#000000", relief="flat", bd=0, cursor="hand2",
            font=("Segoe UI", 10, "bold"),
        )
        self.btn.pack(pady=(12, 0), ipadx=30, ipady=6)

    # ------------------------------------------------------------
    # Akcje
    # ------------------------------------------------------------

    def choose(self):
        d = filedialog.askdirectory(initialdir=self.folder_var.get())
        if d:
            self.folder_var.set(d)

    def set_status(self, text, color=COLOR_ACCENT):
        self.root.after(0, lambda: self.status.config(text=text, fg=color))

    def start(self):
        if self.busy:
            return
        url = self.url_entry.get().strip()
        folder = self.folder_var.get().strip()
        if not url:
            messagebox.showwarning(self.t("warn_title"), self.t("warn_no_url"))
            return
        if not os.path.isdir(folder):
            messagebox.showwarning(
                self.t("warn_title"), self.t("warn_no_folder"))
            return

        self.busy = True
        self.btn.config(state="disabled", bg=COLOR_ENTRY_BG, fg=COLOR_TEXT_DIM)
        self.progress.start(12)
        self.status.config(text=self.t("status_fetching"), fg=COLOR_ACCENT)

        threading.Thread(
            target=self.work, args=(url, folder, self.lang), daemon=True
        ).start()

    def work(self, url, folder, lang):
        # lang przekazany z zewnątrz, żeby wątek nie zależał od stanu GUI
        tr = TRANSLATIONS[lang]
        try:
            if "open.spotify.com" in url:
                query = spotify_query(url, tr["err_only_track"])
            else:
                query = url  # zwykła fraza wyszukiwania

            self.set_status(
                tr["status_downloading"].format(query=query[:50]))
            download_one(query, folder)
            self.root.after(0, lambda: self.finish(query, lang))
        except Exception as e:
            traceback.print_exc()
            msg = f"{type(e).__name__}: {e}"
            self.root.after(0, lambda: self.error(msg, lang))

    def finish(self, query, lang):
        tr = TRANSLATIONS[lang]
        self.busy = False
        self.progress.stop()
        self.btn.config(state="normal", bg=COLOR_ACCENT, fg="#000000")
        self.status.config(text=tr["status_done"], fg=COLOR_ACCENT)
        messagebox.showinfo(
            tr["done_title"], tr["done_msg"].format(query=query))

    def error(self, msg, lang):
        tr = TRANSLATIONS[lang]
        self.busy = False
        self.progress.stop()
        self.btn.config(state="normal", bg=COLOR_ACCENT, fg="#000000")
        self.status.config(text=tr["status_error"], fg=COLOR_RED)
        messagebox.showerror(tr["error_title"], msg[:400])


if __name__ == "__main__":
    root = tk.Tk()
    App(root)
    root.mainloop()