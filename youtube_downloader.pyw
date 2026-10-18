import os
import threading
import traceback
import tkinter as tk
from concurrent.futures import ThreadPoolExecutor, as_completed
from tkinter import filedialog, messagebox, ttk

from yt_dlp import YoutubeDL

WORKERS = 4

# ================================================================
# KOLORY (zgodne z motywem pro-audio / DAW)
# ================================================================

COLOR_BG = "#121212"           # tło okna (głęboka czerń)
COLOR_CARD = "#1C1C1C"         # karty, panele (ciemny grafit)
COLOR_ENTRY_BG = "#2A2A2A"     # tła pól tekstowych, combobox

COLOR_BTN = "#007AFF"          # główne przyciski "Wybierz" (niebieski Serato)
COLOR_BTN_HOVER = "#005CE6"

COLOR_BTN_ALT = "#2A2A2A"      # subtelniejsze przyciski (wybór języka)
COLOR_BTN_ALT_HOVER = "#3A3A3A"

COLOR_ACCENT = "#00E5FF"       # przycisk Pobierz, pasek postępu (neonowy cyjan)
COLOR_ACCENT_DARK = "#00B3CC"

COLOR_RED = "#FF3366"          # kolory dla błędów
COLOR_RED_DARK = "#D81B60"

COLOR_TEXT = "#F0F0F0"
COLOR_TEXT_DIM = "#8A8A8A"


# ================================================================
# TŁUMACZENIA
# ================================================================

TEXTS = {
    "pl": {
        "title": "YouTube Audio Downloader",
        "header": "YT DOWNLOADER",
        "url": "Link YouTube (film lub playlista):",
        "folder": "Katalog docelowy:",
        "browse": "Wybierz...",
        "format": "Format:",
        "quality": "Jakość:",
        "download": "Pobierz",
        "ready": "Gotowy",
        "fetching": "Pobieranie listy filmów...",
        "progress": "Pobrano {d}/{t}",
        "done": "Gotowe: {ok}/{t}",
        "error_status": "Błąd!",
        "no_url_t": "Brak danych",
        "no_url": "Wklej link!",
        "bad_folder_t": "Błąd",
        "bad_folder": "Folder nie istnieje.",
        "end_t": "Koniec",
        "end": "Pobrano {ok}/{t}.",
        "failed": "Nie udało się:",
        "err_t": "Błąd",
    },
    "en": {
        "title": "YouTube Audio Downloader",
        "header": "YT DOWNLOADER",
        "url": "YouTube link (video or playlist):",
        "folder": "Target folder:",
        "browse": "Browse...",
        "format": "Format:",
        "quality": "Quality:",
        "download": "Download",
        "ready": "Ready",
        "fetching": "Fetching video list...",
        "progress": "Downloaded {d}/{t}",
        "done": "Done: {ok}/{t}",
        "error_status": "Error!",
        "no_url_t": "Missing data",
        "no_url": "Paste a link!",
        "bad_folder_t": "Error",
        "bad_folder": "Folder does not exist.",
        "end_t": "Finished",
        "end": "Downloaded {ok}/{t}.",
        "failed": "Failed:",
        "err_t": "Error",
    },
}


# ================================================================
# LOGIKA POBIERANIA (YT-DLP)
# ================================================================

def get_entries(url):
    opts = {"quiet": True, "extract_flat": True, "skip_download": True}
    with YoutubeDL(opts) as ydl:
        info = ydl.extract_info(url, download=False)
    if info.get("entries"):
        urls = []
        for e in info["entries"]:
            if not e:
                continue
            u = e.get("url") or e.get("webpage_url")
            if u and not u.startswith("http"):
                u = f"https://www.youtube.com/watch?v={e['id']}"
            if u:
                urls.append(u)
        return urls
    return [info.get("webpage_url") or url]


def download_one(url, folder, fmt, quality):
    opts = {
        "format": "bestaudio/best",
        "outtmpl": os.path.join(folder, "%(title)s.%(ext)s"),
        "noplaylist": True,
        "quiet": True,
        "no_warnings": True,
        "concurrent_fragment_downloads": 4,
        "postprocessors": [
            {
                "key": "FFmpegExtractAudio",
                "preferredcodec": fmt,
                "preferredquality": quality,
            }
        ],
    }
    with YoutubeDL(opts) as ydl:
        ydl.download([url])


# ================================================================
# GUI
# ================================================================

class App:
    def __init__(self, root):
        self.root = root
        self.lang = "pl"
        
        root.geometry("560x440")
        root.resizable(False, False)
        root.configure(bg=COLOR_BG)

        self.url_var = tk.StringVar()
        self.folder_var = tk.StringVar(value=os.path.expanduser("~/Music"))
        self.fmt_var = tk.StringVar(value="mp3")
        self.q_var = tk.StringVar(value="192")

        self.status_key = "ready"
        self._kw = {}

        self._build_style()
        self._build_ui()
        self.apply_lang()

    # ------------------------------------------------------------
    # Styl (ttk)
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
    # Interfejs
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
                command=lambda l=lang: self.set_lang(l),
            ).pack(side="left", padx=4)

        # Główny kontener
        body = tk.Frame(self.root, bg=COLOR_CARD)
        body.pack(fill="both", expand=True, padx=20, pady=20)

        # URL
        self.url_lbl = tk.Label(body, bg=COLOR_CARD, fg=COLOR_TEXT, anchor="w")
        self.url_lbl.pack(fill="x", padx=15, pady=(12, 4))

        url_row = tk.Frame(body, bg=COLOR_CARD)
        url_row.pack(fill="x", padx=15)
        
        self.url_entry = tk.Entry(
            url_row, textvariable=self.url_var, bg=COLOR_ENTRY_BG,
            fg=COLOR_TEXT, insertbackground=COLOR_TEXT, relief="flat", bd=0,
        )
        self.url_entry.pack(side="left", fill="x", expand=True, ipady=7)

        # Folder
        self.folder_lbl = tk.Label(body, bg=COLOR_CARD, fg=COLOR_TEXT, anchor="w")
        self.folder_lbl.pack(fill="x", padx=15, pady=(12, 4))

        folder_row = tk.Frame(body, bg=COLOR_CARD)
        folder_row.pack(fill="x", padx=15)
        
        tk.Entry(
            folder_row, textvariable=self.folder_var, bg=COLOR_ENTRY_BG,
            fg=COLOR_TEXT, insertbackground=COLOR_TEXT, relief="flat", bd=0,
        ).pack(side="left", fill="x", expand=True, ipady=7, padx=(0, 8))

        self.browse_btn = tk.Button(
            folder_row, bg=COLOR_BTN, fg=COLOR_TEXT, font=("Segoe UI", 9, "bold"),
            activebackground=COLOR_BTN_HOVER, activeforeground=COLOR_TEXT,
            relief="flat", bd=0, cursor="hand2", command=self.choose,
        )
        self.browse_btn.pack(side="left", ipadx=8, ipady=6)

        # Opcje (Format + Jakość)
        opt_row = tk.Frame(body, bg=COLOR_CARD)
        opt_row.pack(fill="x", padx=15, pady=(16, 0))

        self.fmt_lbl = tk.Label(opt_row, bg=COLOR_CARD, fg=COLOR_TEXT)
        self.fmt_lbl.pack(side="left", padx=(0, 4))
        
        ttk.Combobox(
            opt_row, textvariable=self.fmt_var,
            values=["mp3", "m4a", "opus", "wav", "flac"],
            state="readonly", width=7, font=("Segoe UI", 9)
        ).pack(side="left", padx=(0, 16))
        
        self.q_lbl = tk.Label(opt_row, bg=COLOR_CARD, fg=COLOR_TEXT)
        self.q_lbl.pack(side="left", padx=(0, 4))
        
        ttk.Combobox(
            opt_row, textvariable=self.q_var,
            values=["128", "192", "256", "320"],
            state="readonly", width=6, font=("Segoe UI", 9)
        ).pack(side="left")

        # Pasek postępu i status
        self.progress = ttk.Progressbar(body, mode="determinate")
        self.progress.pack(fill="x", padx=15, pady=(20, 6))

        self.status = tk.Label(body, bg=COLOR_CARD, fg=COLOR_TEXT_DIM, anchor="w")
        self.status.pack(fill="x", padx=15)

        # Przycisk pobierania
        self.btn = tk.Button(
            body, command=self.start,
            bg=COLOR_ACCENT, fg="#000000", activebackground=COLOR_ACCENT_DARK,
            activeforeground="#000000", relief="flat", bd=0, cursor="hand2",
            font=("Segoe UI", 10, "bold"),
        )
        self.btn.pack(pady=(12, 0), ipadx=30, ipady=6)

    # ------------------------------------------------------------
    # Tłumaczenia
    # ------------------------------------------------------------
    def t(self, key, **kw):
        return TEXTS[self.lang][key].format(**kw)

    def set_lang(self, lang):
        self.lang = lang
        self.apply_lang()

    def apply_lang(self):
        self.root.title(self.t("title"))
        self.header_label.config(text=self.t("header"))
        self.url_lbl.config(text=self.t("url"))
        self.folder_lbl.config(text=self.t("folder"))
        self.browse_btn.config(text=self.t("browse"))
        self.fmt_lbl.config(text=self.t("format"))
        self.q_lbl.config(text=self.t("quality"))
        self.btn.config(text=self.t("download"))
        self.status.config(text=self.t(self.status_key, **self._kw))

    def set_status(self, key, color=COLOR_ACCENT, **kw):
        def apply():
            self.status_key = key
            self._kw = kw
            self.status.config(text=self.t(key, **kw), fg=color)
        self.root.after(0, apply)

    # ------------------------------------------------------------
    # Logika GUI
    # ------------------------------------------------------------
    def choose(self):
        d = filedialog.askdirectory(initialdir=self.folder_var.get())
        if d:
            self.folder_var.set(d)

    def start(self):
        url = self.url_var.get().strip()
        folder = self.folder_var.get().strip()
        
        if not url:
            messagebox.showwarning(self.t("no_url_t"), self.t("no_url"))
            return
        if not os.path.isdir(folder):
            messagebox.showwarning(self.t("bad_folder_t"), self.t("bad_folder"))
            return
            
        self.btn.config(state="disabled", bg=COLOR_ENTRY_BG, fg=COLOR_TEXT_DIM)
        self.progress.config(value=0)
        self.set_status("fetching", color=COLOR_TEXT)
        
        threading.Thread(
            target=self.work,
            args=(url, folder, self.fmt_var.get(), self.q_var.get()),
            daemon=True,
        ).start()

    def work(self, url, folder, fmt, quality):
        try:
            urls = get_entries(url)
            total = len(urls)
            self.root.after(0, lambda: self.progress.config(maximum=total, value=0))
            done, failed = 0, []

            with ThreadPoolExecutor(max_workers=WORKERS) as pool:
                futures = {
                    pool.submit(download_one, u, folder, fmt, quality): u
                    for u in urls
                }
                for f in as_completed(futures):
                    try:
                        f.result()
                    except Exception:
                        traceback.print_exc()
                        failed.append(futures[f])
                    done += 1
                    self.root.after(0, lambda d=done: self.progress.config(value=d))
                    self.set_status("progress", color=COLOR_ACCENT, d=done, t=total)

            self.root.after(0, lambda: self.finish(total, failed))
        except Exception as e:
            traceback.print_exc()
            msg = f"{type(e).__name__}: {e}"
            self.root.after(0, lambda: self.error(msg))

    def finish(self, total, failed):
        self.btn.config(state="normal", bg=COLOR_ACCENT, fg="#000000")
        ok = total - len(failed)
        
        if failed:
            self.set_status("done", COLOR_RED, ok=ok, t=total)
        else:
            self.set_status("done", COLOR_ACCENT, ok=ok, t=total)
            
        msg = self.t("end", ok=ok, t=total)
        if failed:
            msg += "\n\n" + self.t("failed") + "\n" + "\n".join(failed[:10])
        messagebox.showinfo(self.t("end_t"), msg)

    def error(self, msg):
        self.btn.config(state="normal", bg=COLOR_ACCENT, fg="#000000")
        self.set_status("error_status", COLOR_RED)
        messagebox.showerror(self.t("err_t"), msg[:400])


if __name__ == "__main__":
    root = tk.Tk()
    App(root)
    root.mainloop()