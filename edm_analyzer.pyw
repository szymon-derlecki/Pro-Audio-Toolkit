from __future__ import annotations

import csv
import logging
import math
import queue
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable

import customtkinter as ctk
import librosa
import mutagen
import numpy as np
from tkinter import filedialog, messagebox, ttk

try:
    from madmom.features.key import KEY_LABELS, CNNKeyRecognitionProcessor

    HAS_MADMOM = True
    MADMOM_IMPORT_ERROR = ""
except Exception as _exc:  # brak pakietu albo nieudana kompilacja
    KEY_LABELS = []
    CNNKeyRecognitionProcessor = None
    HAS_MADMOM = False
    MADMOM_IMPORT_ERROR = f"{type(_exc).__name__}: {_exc}"


# ================================================================
# KONFIGURACJA
# ================================================================

SAMPLE_RATE = 22_050
HOP = 512

AUDIO_EXTS = {".mp3", ".wav", ".flac", ".m4a", ".ogg", ".opus", ".aac"}

MAX_WORKERS = 3
MIN_AUDIO_SEC = 3.0

MIN_BPM = 70.0
MAX_BPM = 200.0

# Druga tonacja jest pokazywana, gdy p1 - p2 < SECOND_KEY_MARGIN.
SECOND_KEY_MARGIN = 0.40

# Paleta: Ciemny motyw pro-audio (w stylu DAW - Ableton / Rekordbox).
# Głęboki grafit/czerń w tle, ciemnoszare panele, ostre neonowe akcenty zapobiegające zmęczeniu wzroku w studiu/klubie.
COLOR_BG = "#121212"      # tło okna (minimalistyczna głęboka czerń)
COLOR_CARD = "#1C1C1C"    # karty, log, tabela (nieco jaśniejsze od tła dla separacji)
COLOR_CARD2 = "#2A2A2A"   # nagłówki tabeli, segmenty
COLOR_ACCENT = "#00E5FF"  # tytuł, pasek postępu (neonowy cyjan dla ostrego kontrastu)
COLOR_BLUE = "#007AFF"    # przyciski główne, zaznaczenie w tabeli (klasyczny "Serato/macOS blue")
COLOR_BLUE_HOVER = "#005CE6"
COLOR_WAVE = "#00FF9D"    # waveform (bardzo jasny, jaskrawy seledyn/mint - świetna widoczność)
COLOR_RED = "#FF3366"     # Clear All (nowoczesny, wyrazisty różo-czerwony)
COLOR_GRAY = "#8A8A8A"
COLOR_TEXT = "#F0F0F0"
COLOR_UNSURE = "#FF9800"  # pomarańczowy (ostrzegawczy dla niepewnych tonacji)

NOTES = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]

CAMELOT = {
    "major": [8, 3, 10, 5, 12, 7, 2, 9, 4, 11, 6, 1],
    "minor": [5, 12, 7, 2, 9, 4, 11, 6, 1, 8, 3, 10],
}

LABEL_NOTE_PC = {
    "C": 0, "C#": 1, "Db": 1, "D": 2, "D#": 3, "Eb": 3, "E": 4, "F": 5,
    "F#": 6, "Gb": 6, "G": 7, "G#": 8, "Ab": 8, "A": 9, "A#": 10,
    "Bb": 10, "B": 11,
}

log = logging.getLogger("edm_analyzer")
logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")


# ================================================================
# TŁUMACZENIA (PL / EN)
# ================================================================

STRINGS = {
    "en": {
        "app_title": "EDM Audio Analyzer",
        "brand": "EDM ANALYZER",
        "lang": "Language",
        "start": "START ANALYSIS",
        "file": "File",
        "folder": "Folder",
        "recursive": "Include subfolders",
        "export_csv": "Export CSV",
        "clear": "Clear All",
        "path_placeholder": "Select folder or file...",
        "ready": "Ready",
        "warn_select": "Select a file or folder first.",
        "err_no_path": "Path does not exist:\n{path}",
        "err_read": "Could not read path:\n{err}",
        "err_madmom": "madmom is not available:\n{err}",
        "info_no_files": "No supported audio files found.",
        "log_start": "Start: {n} file(s)",
        "processing": "Processing",
        "complete": "Analysis complete",
        "finished": "Analysis finished.",
        "worker_error": "WORKER ERROR: {err}",
        "error": "ERROR",
        "ok": "OK",
        "nothing_export": "Nothing to export.",
        "export_error": "Export error",
        "success": "Success",
        "export_ok": "CSV exported successfully!",
        "col_file": "Filename",
        "col_title": "Title / Artist",
        "col_bpm": "BPM",
        "col_key1": "Key 1",
        "col_key2": "Key 2",
        "col_db": "Volume (dB)",
        "col_prob1": "Key 1 prob.",
        "col_prob2": "Key 2 prob.",
        "col_camelot1": "Camelot 1",
        "col_camelot2": "Camelot 2",
        "artist": "Artist",
        "title": "Title",
        "engine_madmom": "Key engine: madmom CNN",
        "engine_missing": "madmom NOT available – key analysis disabled",
    },
    "pl": {
        "app_title": "Analizator Audio EDM",
        "brand": "EDM ANALIZATOR",
        "lang": "Język",
        "start": "ROZPOCZNIJ ANALIZĘ",
        "file": "Plik",
        "folder": "Folder",
        "recursive": "Uwzględnij podfoldery",
        "export_csv": "Eksportuj CSV",
        "clear": "Wyczyść wszystko",
        "path_placeholder": "Wybierz folder lub plik...",
        "ready": "Gotowy",
        "warn_select": "Wybierz najpierw plik lub folder.",
        "err_no_path": "Ścieżka nie istnieje:\n{path}",
        "err_read": "Nie można odczytać ścieżki:\n{err}",
        "err_madmom": "madmom jest niedostępny:\n{err}",
        "info_no_files": "Nie znaleziono obsługiwanych plików audio.",
        "log_start": "Start: {n} plików",
        "processing": "Przetwarzanie",
        "complete": "Analiza zakończona",
        "finished": "Analiza zakończona.",
        "worker_error": "BŁĄD WORKERA: {err}",
        "error": "BŁĄD",
        "ok": "OK",
        "nothing_export": "Nie ma czego eksportować.",
        "export_error": "Błąd eksportu",
        "success": "Sukces",
        "export_ok": "Pomyślnie wyeksportowano CSV!",
        "col_file": "Plik",
        "col_title": "Tytuł / Wykonawca",
        "col_bpm": "BPM",
        "col_key1": "Tonacja 1",
        "col_key2": "Tonacja 2",
        "col_db": "Głośność (dB)",
        "col_prob1": "Prawdop. 1",
        "col_prob2": "Prawdop. 2",
        "col_camelot1": "Camelot 1",
        "col_camelot2": "Camelot 2",
        "artist": "Wykonawca",
        "title": "Tytuł",
        "engine_madmom": "Silnik tonacji: madmom CNN",
        "engine_missing": "madmom NIEDOSTĘPNY – analiza tonacji wyłączona",
    },
}


# ================================================================
# MODEL DANYCH
# ================================================================

@dataclass
class KeyCandidate:
    tonic: int
    mode: str
    prob: float

    @property
    def name(self) -> str:
        return f"{NOTES[self.tonic]} {self.mode}"

    @property
    def camelot(self) -> str:
        suffix = "B" if self.mode == "major" else "A"
        return f"{CAMELOT[self.mode][self.tonic]}{suffix}"

    def display(self) -> str:
        return f"{self.name} ({self.camelot}) – {self.prob:.0%}"


@dataclass
class TrackResult:
    file: str
    artist: str
    title: str
    bpm: float
    key1: KeyCandidate
    key2: KeyCandidate | None = None
    volume_db: float = -120.0
    peak_db: float = -120.0
    peaks: list[tuple[float, float]] = field(default_factory=list, repr=False)


# ================================================================
# AUDIO
# ================================================================

def warmup_librosa() -> None:
    dummy = np.zeros(SAMPLE_RATE * 2, dtype=np.float32)
    dummy[::100] = 0.5
    librosa.onset.onset_strength(y=dummy, sr=SAMPLE_RATE, hop_length=HOP)


def load_audio(path: Path) -> tuple[np.ndarray, int]:
    y, sr = librosa.load(str(path), sr=SAMPLE_RATE, mono=True)
    if len(y) < int(sr * MIN_AUDIO_SEC):
        raise ValueError(f"Audio shorter than {MIN_AUDIO_SEC:.0f}s.")
    if not np.all(np.isfinite(y)):
        raise ValueError("Audio contains invalid numeric values.")
    if np.max(np.abs(y)) < 1e-8:
        raise ValueError("Audio is silent or almost silent.")
    return y.astype(np.float32), sr


# ================================================================
# BPM
# ================================================================

def normalize_edm_bpm(bpm: float) -> float:
    if not np.isfinite(bpm) or bpm <= 0:
        raise ValueError("Could not estimate a valid BPM.")
    while bpm < MIN_BPM:
        bpm *= 2.0
    while bpm > MAX_BPM:
        bpm /= 2.0
    return bpm


def estimate_bpm(y: np.ndarray, sr: int) -> float:
    onset_env = librosa.onset.onset_strength(y=y, sr=sr, hop_length=HOP)
    if len(onset_env) < 4 or np.max(onset_env) <= 1e-8:
        raise ValueError("Not enough rhythmic information for BPM.")

    tempo, beat_frames = librosa.beat.beat_track(
        onset_envelope=onset_env, sr=sr, hop_length=HOP, units="frames"
    )
    bpm = float(np.atleast_1d(tempo)[0])

    if len(beat_frames) >= 4:
        beat_times = librosa.frames_to_time(beat_frames, sr=sr, hop_length=HOP)
        idx = np.arange(len(beat_times), dtype=float)
        slope, _ = np.polyfit(idx, beat_times, 1)
        if slope > 0:
            refined = 60.0 / slope
            if abs(refined - bpm) / max(bpm, 1.0) < 0.15:
                bpm = refined

    return round(float(normalize_edm_bpm(bpm)), 1)


# ================================================================
# TONACJA: madmom CNN
# ================================================================

_MADMOM_LOCK = threading.Lock()
_madmom_proc = None


def _get_madmom():
    """Model ładowany raz; wywoływać tylko pod _MADMOM_LOCK."""
    global _madmom_proc
    if _madmom_proc is None:
        _madmom_proc = CNNKeyRecognitionProcessor()
    return _madmom_proc


def _candidate(label_idx: int, probs: np.ndarray) -> KeyCandidate:
    note, mode = KEY_LABELS[label_idx].split()
    return KeyCandidate(LABEL_NOTE_PC[note], mode, float(probs[label_idx]))


def detect_key_madmom(path: Path) -> tuple[KeyCandidate, KeyCandidate | None]:
    """Zwraca (tonacja 1, tonacja 2 lub None, jeśli 1 wyraźnie wygrywa)."""
    with _MADMOM_LOCK:
        pred = _get_madmom()(str(path))

    probs = np.asarray(pred, dtype=float).reshape(-1)
    if probs.shape != (24,) or not np.all(np.isfinite(probs)):
        raise ValueError(f"Unexpected madmom output: {probs.shape}")

    order = np.argsort(probs)[::-1]
    key1 = _candidate(order[0], probs)
    key2 = _candidate(order[1], probs)

    log.info(
        "madmom %s: %s",
        path.name,
        "  |  ".join(f"{KEY_LABELS[i]} ({probs[i]:.2f})" for i in order[:3]),
    )

    if key1.prob - key2.prob < SECOND_KEY_MARGIN:
        return key1, key2
    return key1, None


# ================================================================
# GŁOŚNOŚĆ + WAVEFORM + METADANE
# ================================================================

def estimate_volume(y: np.ndarray) -> tuple[float, float]:
    if len(y) == 0:
        return -120.0, -120.0
    rms = float(np.sqrt(np.mean(y.astype(np.float64) ** 2)))
    peak = float(np.max(np.abs(y)))
    rms_db = 20.0 * math.log10(rms) if rms > 0 else -120.0
    peak_db = 20.0 * math.log10(peak) if peak > 0 else -120.0
    return round(rms_db, 1), round(peak_db, 1)


def extract_peaks(
    y: np.ndarray, num_peaks: int = 1000
) -> list[tuple[float, float]]:
    if len(y) == 0:
        return []
    scale = float(np.max(np.abs(y)))
    if scale < 1e-12:
        return [(0.0, 0.0)] * min(num_peaks, len(y))

    count = min(num_peaks, len(y))
    edges = np.linspace(0, len(y), count + 1, dtype=int)
    peaks = []
    for start, end in zip(edges[:-1], edges[1:]):
        block = y[start:end]
        if len(block):
            peaks.append(
                (float(np.min(block) / scale), float(np.max(block) / scale))
            )
    return peaks


def read_tags(path: Path) -> tuple[str, str]:
    try:
        meta = mutagen.File(path, easy=True)
        if meta and meta.tags:
            artist_value = meta.tags.get("artist", [""])
            title_value = meta.tags.get("title", [path.stem])
            artist = str(artist_value[0]) if artist_value else ""
            title = str(title_value[0]) if title_value else path.stem
            return artist, title
    except Exception:
        log.debug("Could not read tags for %s", path.name)
    return "", path.stem


# ================================================================
# PEŁNA ANALIZA PLIKU
# ================================================================

def analyze_file(path: Path) -> TrackResult:
    y, sr = load_audio(path)
    bpm = estimate_bpm(y, sr)
    key1, key2 = detect_key_madmom(path)
    artist, title = read_tags(path)
    volume_db, peak_db = estimate_volume(y)

    return TrackResult(
        file=path.name, artist=artist, title=title, bpm=bpm,
        key1=key1, key2=key2, volume_db=volume_db, peak_db=peak_db,
        peaks=extract_peaks(y),
    )


def collect_files(src: Path, recursive: bool) -> list[Path]:
    if src.is_file():
        return [src] if src.suffix.lower() in AUDIO_EXTS else []
    iterator = src.rglob("*") if recursive else src.iterdir()
    return sorted(
        p for p in iterator if p.is_file() and p.suffix.lower() in AUDIO_EXTS
    )


# ================================================================
# GUI
# ================================================================

class AnalyzerApp(ctk.CTk):

    COLUMNS = [
        ("file", 200, "w"),
        ("title", 180, "w"),
        ("bpm", 65, "center"),
        ("key1", 170, "center"),
        ("key2", 170, "center"),
        ("db", 85, "center"),
    ]
    COL_HEADING_KEYS = {
        "file": "col_file", "title": "col_title", "bpm": "col_bpm",
        "key1": "col_key1", "key2": "col_key2", "db": "col_db",
    }

    def __init__(self) -> None:
        super().__init__()
        ctk.set_appearance_mode("dark")
        self.configure(fg_color=COLOR_BG)

        self.lang = "pl"
        self.results: list[TrackResult] = []
        self.selected_idx: int | None = None
        self.ui_queue: queue.Queue[Callable[[], None]] = queue.Queue()
        self.analysis_running = False

        self.geometry("1200x780")
        self.minsize(950, 600)

        self._build_ui()
        self._apply_language()
        self._poll_queue()

        if HAS_MADMOM:
            self.log(self.tr("engine_madmom"))
        else:
            self.log(f"{self.tr('engine_missing')} ({MADMOM_IMPORT_ERROR})")

    # ---------------- Tłumaczenia ----------------
    def tr(self, key: str) -> str:
        return STRINGS[self.lang].get(key, STRINGS["en"].get(key, key))

    def _apply_language(self) -> None:
        t = self.tr
        self.title(t("app_title"))
        self.brand_label.configure(text=t("brand"))
        self.lang_label.configure(text=t("lang"))
        self.analyze_btn.configure(text=t("start"))
        self.file_btn.configure(text=t("file"))
        self.folder_btn.configure(text=t("folder"))
        self.recursive_cb.configure(text=t("recursive"))
        self.export_btn.configure(text=t("export_csv"))
        self.clear_btn.configure(text=t("clear"))
        self.path_entry.configure(placeholder_text=t("path_placeholder"))
        for col, key in self.COL_HEADING_KEYS.items():
            self.tree.heading(col, text=t(key))
        if not self.analysis_running:
            self.status_label.configure(text=t("ready"))

    def on_language_change(self, value: str) -> None:
        value = value.lower()
        if value in ("pl", "en"):
            self.lang = value
            self._apply_language()

    # ---------------- Budowa UI ----------------
    def _build_ui(self) -> None:
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(1, weight=1)

        top = ctk.CTkFrame(self, fg_color=COLOR_CARD, corner_radius=0)
        top.grid(row=0, column=0, columnspan=2, sticky="ew")

        self.brand_label = ctk.CTkLabel(
            top, text="", font=ctk.CTkFont(size=22, weight="bold"),
            text_color=COLOR_ACCENT,
        )
        self.brand_label.pack(side="left", padx=20, pady=18)

        self.analyze_btn = ctk.CTkButton(
            top, text="", fg_color=COLOR_BLUE, hover_color=COLOR_BLUE_HOVER,
            text_color="#FFFFFF", font=ctk.CTkFont(weight="bold"),
            command=self.start_analysis,
        )
        self.analyze_btn.pack(side="right", padx=20, pady=18)

        self.lang_label = ctk.CTkLabel(top, text="", text_color=COLOR_GRAY)
        self.lang_label.pack(side="right", padx=(0, 8))

        self.lang_seg = ctk.CTkSegmentedButton(
            top, values=["PL", "EN"], command=self.on_language_change,
            selected_color=COLOR_BLUE, selected_hover_color=COLOR_BLUE_HOVER,
            fg_color=COLOR_CARD2,
        )
        self.lang_seg.pack(side="right", padx=(0, 12), pady=18)
        self.lang_seg.set("PL")

        left = ctk.CTkFrame(self, fg_color="transparent", width=250)
        left.grid(row=1, column=0, sticky="nsew", padx=20, pady=20)
        left.grid_columnconfigure(0, weight=1)

        self.path_entry = ctk.CTkEntry(left, placeholder_text="", height=40)
        self.path_entry.grid(row=0, column=0, sticky="ew", pady=(0, 10))

        self.file_btn = ctk.CTkButton(
            left, text="", fg_color=COLOR_BLUE, hover_color=COLOR_BLUE_HOVER,
            command=self.pick_file,
        )
        self.file_btn.grid(row=1, column=0, sticky="ew", pady=2)

        self.folder_btn = ctk.CTkButton(
            left, text="", fg_color=COLOR_BLUE, hover_color=COLOR_BLUE_HOVER,
            command=self.pick_dir,
        )
        self.folder_btn.grid(row=2, column=0, sticky="ew", pady=2)

        self.recursive_var = ctk.BooleanVar(value=False)
        self.recursive_cb = ctk.CTkCheckBox(
            left, text="", variable=self.recursive_var
        )
        self.recursive_cb.grid(row=3, column=0, sticky="w", pady=(10, 0))

        self.export_btn = ctk.CTkButton(
            left, text="", fg_color=COLOR_BLUE, hover_color=COLOR_BLUE_HOVER,
            command=self.export_csv,
        )
        self.export_btn.grid(row=4, column=0, sticky="ew", pady=(20, 0))

        self.clear_btn = ctk.CTkButton(
            left, text="", fg_color=COLOR_RED, hover_color="#D81B60",
            command=self.clear_all,
        )
        self.clear_btn.grid(row=5, column=0, sticky="ew", pady=5)

        right = ctk.CTkFrame(self, fg_color="transparent")
        right.grid(row=1, column=1, sticky="nsew", padx=(0, 20), pady=20)
        right.grid_columnconfigure(0, weight=1)
        right.grid_rowconfigure(1, weight=1)

        wave_card = ctk.CTkFrame(
            right, fg_color=COLOR_CARD, height=110, corner_radius=15
        )
        wave_card.grid(row=0, column=0, sticky="ew", pady=(0, 15))
        wave_card.pack_propagate(False)

        self.canvas = ctk.CTkCanvas(
            wave_card, bg=COLOR_CARD, highlightthickness=0
        )
        self.canvas.pack(fill="both", expand=True, padx=10, pady=10)
        self.canvas.bind("<Configure>", lambda _e: self.draw_waveform())

        self._style_treeview()

        tf = ctk.CTkFrame(right, fg_color="transparent")
        tf.grid(row=1, column=0, sticky="nsew")
        tf.grid_columnconfigure(0, weight=1)
        tf.grid_rowconfigure(0, weight=1)

        self.tree = ttk.Treeview(
            tf, columns=[c[0] for c in self.COLUMNS], show="headings"
        )
        for col, width, anchor in self.COLUMNS:
            self.tree.column(col, width=width, anchor=anchor)
        # Wiersze z dwiema tonacjami wyróżnione kolorem.
        self.tree.tag_configure("unsure", foreground=COLOR_UNSURE)

        sb = ctk.CTkScrollbar(tf, command=self.tree.yview)
        self.tree.configure(yscrollcommand=sb.set)
        self.tree.grid(row=0, column=0, sticky="nsew")
        sb.grid(row=0, column=1, sticky="ns")
        self.tree.bind("<<TreeviewSelect>>", self.on_select)

        self.log_box = ctk.CTkTextbox(
            right, height=110, fg_color=COLOR_CARD, text_color="#A0A0A0"
        )
        self.log_box.grid(row=2, column=0, sticky="ew", pady=(15, 0))

        bottom = ctk.CTkFrame(self, fg_color="transparent")
        bottom.grid(
            row=2, column=0, columnspan=2, sticky="ew", padx=20, pady=5
        )
        bottom.grid_columnconfigure(0, weight=1)

        self.status_label = ctk.CTkLabel(
            bottom, text="", text_color=COLOR_GRAY, anchor="w"
        )
        self.status_label.grid(row=0, column=0, sticky="w")

        self.progress = ctk.CTkProgressBar(
            bottom, fg_color=COLOR_CARD, progress_color=COLOR_ACCENT, width=180
        )
        self.progress.grid(row=0, column=1, sticky="e")
        self.progress.set(0)

    @staticmethod
    def _style_treeview() -> None:
        style = ttk.Style()
        style.theme_use("default")
        style.configure(
            "Treeview", background=COLOR_CARD, foreground=COLOR_TEXT,
            fieldbackground=COLOR_CARD, rowheight=32, borderwidth=0,
        )
        style.configure(
            "Treeview.Heading", background=COLOR_CARD2,
            foreground=COLOR_TEXT, relief="flat",
        )
        style.map(
            "Treeview",
            background=[("selected", COLOR_BLUE)],
            foreground=[("selected", "#FFFFFF")],
        )

    # ---------------- Pomocnicze ----------------
    def log(self, msg: str) -> None:
        self.log_box.insert("end", msg + "\n")
        self.log_box.see("end")

    def _set_path(self, value: str) -> None:
        if value:
            self.path_entry.delete(0, "end")
            self.path_entry.insert(0, value)

    def pick_file(self) -> None:
        patterns = " ".join(f"*{ext}" for ext in sorted(AUDIO_EXTS))
        path = filedialog.askopenfilename(
            filetypes=[("Audio files", patterns)]
        )
        self._set_path(path)

    def pick_dir(self) -> None:
        self._set_path(filedialog.askdirectory())

    def on_select(self, _event=None) -> None:
        selection = self.tree.selection()
        if selection:
            self.selected_idx = int(selection[0])
            self.draw_waveform()

    def draw_waveform(self) -> None:
        self.canvas.delete("all")
        if self.selected_idx is None or self.selected_idx >= len(self.results):
            return
        peaks = self.results[self.selected_idx].peaks
        width = self.canvas.winfo_width()
        height = self.canvas.winfo_height()
        if not peaks or width <= 1 or height <= 1:
            return
        mid = height / 2
        dx = width / len(peaks)
        for i, (low, high) in enumerate(peaks):
            x = i * dx
            self.canvas.create_line(
                x, mid - high * mid, x, mid - low * mid, fill=COLOR_WAVE
            )

    # ---------------- Analiza ----------------
    def start_analysis(self) -> None:
        if self.analysis_running:
            return

        if not HAS_MADMOM:
            messagebox.showerror(
                "Error", self.tr("err_madmom").format(err=MADMOM_IMPORT_ERROR)
            )
            return

        raw = self.path_entry.get().strip().strip('"')
        if not raw:
            messagebox.showwarning("Warning", self.tr("warn_select"))
            return

        src = Path(raw)
        if not src.exists():
            messagebox.showerror(
                "Error", self.tr("err_no_path").format(path=src)
            )
            return

        try:
            files = collect_files(src, self.recursive_var.get())
        except OSError as exc:
            messagebox.showerror("Error", self.tr("err_read").format(err=exc))
            return

        if not files:
            messagebox.showinfo("Info", self.tr("info_no_files"))
            return

        self.clear_all()
        self.analysis_running = True
        self.analyze_btn.configure(state="disabled")
        self.log(self.tr("log_start").format(n=len(files)))
        self.status_label.configure(
            text=f"{self.tr('processing')}: 0/{len(files)}"
        )
        threading.Thread(
            target=self._worker, args=(files,), daemon=True
        ).start()

    def _worker(self, files: list[Path]) -> None:
        total = len(files)
        try:
            warmup_librosa()
            with _MADMOM_LOCK:
                _get_madmom()  # załaduj model zanim ruszą wątki

            with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
                futures = {
                    executor.submit(analyze_file, path): path
                    for path in files
                }
                for done, future in enumerate(as_completed(futures), start=1):
                    path = futures[future]
                    try:
                        result = future.result()
                    except Exception as exc:
                        log.exception("Failed: %s", path.name)
                        result = f"{path.name}: {type(exc).__name__}: {exc}"
                    self.ui_queue.put(
                        lambda r=result, d=done, t=total: self._on_result(
                            r, d, t
                        )
                    )
        except Exception as exc:
            log.exception("Analysis worker failed")
            self.ui_queue.put(
                lambda e=str(exc): self.log(
                    self.tr("worker_error").format(err=e)
                )
            )
        finally:
            self.ui_queue.put(self._finish)

    def _on_result(
        self, result: TrackResult | str, done: int, total: int
    ) -> None:
        if isinstance(result, str):
            self.log(f"{self.tr('error')}  {result}")
        else:
            idx = len(self.results)
            self.results.append(result)

            title_artist = result.title
            if result.artist:
                title_artist += f" — {result.artist}"

            key2_text = result.key2.display() if result.key2 else "—"
            tags = ("unsure",) if result.key2 else ()

            self.tree.insert(
                "", "end", iid=str(idx), tags=tags,
                values=(
                    result.file,
                    title_artist,
                    f"{result.bpm:.0f}",
                    result.key1.display(),
                    key2_text,
                    f"{result.volume_db:.1f}",
                ),
            )

            msg = (
                f"{self.tr('ok')}  {result.file} -> {result.bpm:.0f} BPM, "
                f"{result.key1.display()}"
            )
            if result.key2:
                msg += f"  /  {result.key2.display()}"
            self.log(msg + f", {result.volume_db:.1f} dB")

            if idx == 0:
                self.tree.selection_set("0")
                self.tree.focus("0")
                self.selected_idx = 0
                self.draw_waveform()

        self.progress.set(done / total)
        self.status_label.configure(
            text=f"{self.tr('processing')}: {done}/{total}"
        )

    def _finish(self) -> None:
        self.analysis_running = False
        self.analyze_btn.configure(state="normal")
        self.status_label.configure(
            text=f"{self.tr('complete')} ({len(self.results)})"
        )
        self.log(self.tr("finished"))

    def clear_all(self) -> None:
        if self.analysis_running:
            return
        self.results.clear()
        self.selected_idx = None
        self.tree.delete(*self.tree.get_children())
        self.canvas.delete("all")
        self.progress.set(0)
        self.status_label.configure(text=self.tr("ready"))
        self.log_box.delete("1.0", "end")

    # ---------------- Eksport CSV ----------------
    def export_csv(self) -> None:
        if not self.results:
            messagebox.showinfo("Info", self.tr("nothing_export"))
            return

        path = filedialog.asksaveasfilename(
            defaultextension=".csv", filetypes=[("CSV files", "*.csv")]
        )
        if not path:
            return

        t = self.tr
        try:
            with open(path, "w", newline="", encoding="utf-8-sig") as f:
                writer = csv.writer(f, delimiter=";")
                writer.writerow([
                    t("col_file"), t("artist"), t("title"), t("col_bpm"),
                    t("col_key1"), t("col_camelot1"), t("col_prob1"),
                    t("col_key2"), t("col_camelot2"), t("col_prob2"),
                    t("col_db"),
                ])
                for r in self.results:
                    k2 = r.key2
                    writer.writerow([
                        r.file, r.artist, r.title, f"{r.bpm:.0f}",
                        r.key1.name, r.key1.camelot, f"{r.key1.prob:.0%}",
                        k2.name if k2 else "",
                        k2.camelot if k2 else "",
                        f"{k2.prob:.0%}" if k2 else "",
                        f"{r.volume_db:.1f}",
                    ])
        except OSError as exc:
            messagebox.showerror(self.tr("export_error"), str(exc))
            return

        messagebox.showinfo(self.tr("success"), self.tr("export_ok"))

    # ---------------- Kolejka UI ----------------
    def _poll_queue(self) -> None:
        try:
            while True:
                self.ui_queue.get_nowait()()
        except queue.Empty:
            pass
        self.after(50, self._poll_queue)


if __name__ == "__main__":
    app = AnalyzerApp()
    app.mainloop()