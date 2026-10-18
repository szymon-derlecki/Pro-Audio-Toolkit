# 🎵 Pro Audio & DJ Toolkit

🇵🇱 [Wersja polska](#polski) | 🇬🇧 [English version](#english)

---

<a name="polski"></a>

# 🇵🇱 Pro Audio & DJ Toolkit

Zestaw 5 aplikacji w języku Python, stworzonych z myślą o ułatwieniu
pracy DJ-om, producentom muzycznym i pasjonatom audio. Każde z narzędzi posiada
spójny, ciemny interfejs graficzny, idealny do pracy w studiu
i w klubowych warunkach.

## 🛠️ Narzędzia

1. **Analizator Audio EDM**
   - Oblicza BPM oraz głośność utworów (RMS/Peak).
   - Wykrywa tonację przy użyciu sieci neuronowych (biblioteka `madmom`)
     i konwertuje ją na system Camelot.
   - Rysuje kształt fali (waveform) i eksportuje wyniki zbiorczej analizy do CSV.
2. **Vocal Separator (ekstraktor wokalu)**
   - Separacja ścieżek oparta na AI, z użyciem nowoczesnych modeli
     (BS-RoFormer, Mel-RoFormer, MDX23C).
   - Wyodrębnia Acapellę i Instrumental z dowolnego pliku audio.
3. **Konwerter WAV → MP3**
   - Prosty konwerter zbiorczy bazujący na `pydub`.
   - Konwertuje całe foldery z wyborem bitrate'u (128k–320k).
4. **YouTube Audio Downloader**
   - Pobiera dźwięk w najwyższej jakości z pojedynczych filmów lub całych playlist.
   - Automatycznie konwertuje do MP3, M4A, FLAC, OPUS lub WAV.
5. **Spotify MP3 Downloader**
   - Pobiera metadane (wykonawcę i tytuł) z linku do utworu na Spotify.
   - Automatycznie wyszukuje utwór na YouTube i pobiera najlepsze dopasowanie
     (Spotify nie udostępnia samego pliku audio).

## ⚙️ Wymagania

- **Python 3.10+**
- **FFmpeg** – **absolutnie niezbędny** do konwersji, separacji i pobierania.
  - **Windows:** pobierz z [gyan.dev](https://www.gyan.dev/ffmpeg/builds/),
    rozpakuj i dodaj folder `bin` do zmiennej środowiskowej `PATH`.
  - **macOS:** `brew install ffmpeg`
  - **Linux (Debian/Ubuntu):** `sudo apt install ffmpeg`
- **Git** – wymagany do instalacji biblioteki `madmom` z GitHuba.
- _(Tylko Windows)_ **Microsoft C++ Build Tools** – wymagane do skompilowania
  biblioteki `madmom`
  ([pobierz](https://visualstudio.microsoft.com/visual-cpp-build-tools/)).

Sprawdzenie, czy FFmpeg działa:

```bash
ffmpeg -version
```

## 🚀 Instalacja

1. Sklonuj repozytorium:

   ```bash
   git clone https://github.com/szymon-derlecki/Pro-Audio-Toolkit.git
   cd pro-audio-toolkit
   ```

2. Utwórz i aktywuj wirtualne środowisko (zalecane):

   ```bash
   python -m venv venv
   # Windows:
   venv\Scripts\activate
   # macOS/Linux:
   source venv/bin/activate
   ```

3. Zainstaluj najpierw `numpy` i `Cython` (wymagane do kompilacji `madmom`),
   a potem resztę pakietów:

   ```bash
   pip install --upgrade pip
   pip install numpy Cython
   pip install -r requirements.txt
   ```

   > **GPU (NVIDIA):** w `requirements.txt` zamień `audio-separator[cpu]`
   > na `audio-separator[gpu]` i zainstaluj PyTorch z obsługą CUDA
   > zgodnie z instrukcją na [pytorch.org](https://pytorch.org/get-started/locally/).

4. Uruchom dowolny skrypt, np.:

   ```bash
   python vocal_separator.py
   ```

> **Uwaga:** Przy pierwszym uruchomieniu Vocal Separatora modele AI
> (np. BS-RoFormer) zostaną pobrane automatycznie. Może to potrwać kilka minut,
> w zależności od prędkości internetu.

## 📄 Licencje i podziękowania

Projekt opiera się na fantastycznych narzędziach open-source. Proszę
o przestrzeganie ich licencji:

| Biblioteka                                                          | Licencja      | Zastosowanie                              |
| ------------------------------------------------------------------- | ------------- | ----------------------------------------- |
| [yt-dlp](https://github.com/yt-dlp/yt-dlp)                          | The Unlicense | Pobieranie audio (YouTube)                |
| [audio-separator](https://github.com/nomadkaraoke/python-audio-separator) | MIT     | Obsługa modeli AI do separacji            |
| [madmom](https://github.com/CPJKU/madmom)                           | BSD-3-Clause  | Wykrywanie tonacji                        |
| [librosa](https://github.com/librosa/librosa)                       | ISC           | Ekstrakcja BPM i wczytywanie audio        |
| [pydub](https://github.com/jiaaro/pydub)                            | MIT           | Konwersja WAV → MP3                       |
| [mutagen](https://github.com/quodlibet/mutagen)                     | GPL-2.0+      | Odczyt/zapis tagów audio                  |
| [customtkinter](https://github.com/TomSchimansky/CustomTkinter)     | MIT           | Interfejs graficzny                       |

> ⚠️ **Modele AI:** wytrenowane modele (np. z rodziny UVR/MDX) mogą mieć własne
> licencje, w tym zakaz użytku komercyjnego – sprawdź warunki autora modelu.
>
> ⚠️ **Prawa autorskie:** pobieraj tylko treści, do których masz prawa.
> Pobieranie z YouTube może naruszać regulamin serwisu.

---

<a name="english"></a>

# 🇬🇧 Pro Audio & DJ Toolkit

A suite of 5 Python-based desktop applications designed to streamline the
workflow of DJs, music producers and audio enthusiasts. Each tool features
a consistent, dark-themed GUI tailored for studio and low-light environments.

## 🛠️ The Tools

1. **EDM Audio Analyzer**
   - Estimates BPM and measures track loudness (RMS/Peak).
   - Detects musical key using `madmom`'s CNN model and maps it to the
     Camelot wheel.
   - Draws waveforms and exports batch analysis results to CSV.
2. **Vocal Separator**
   - AI-powered stem separation using state-of-the-art models
     (BS-RoFormer, Mel-RoFormer, MDX23C).
   - Extracts Acapella and Instrumental stems from any audio file.
3. **WAV → MP3 Converter**
   - Simple batch converter powered by `pydub`.
   - Processes entire folders with adjustable bitrate (128k–320k).
4. **YouTube Audio Downloader**
   - Downloads the highest-quality audio from single videos or whole playlists.
   - Auto-converts to MP3, M4A, FLAC, OPUS or WAV.
5. **Spotify MP3 Downloader**
   - Fetches track metadata (Artist & Title) from Spotify URLs.
   - Automatically searches YouTube and downloads the best audio match
     (Spotify does not provide the audio file itself).

## ⚙️ Prerequisites

- **Python 3.10+**
- **FFmpeg** – **strictly required** for conversion, separation and downloading.
  - **Windows:** download from [gyan.dev](https://www.gyan.dev/ffmpeg/builds/),
    extract it and add the `bin` folder to your system `PATH`.
  - **macOS:** `brew install ffmpeg`
  - **Linux (Debian/Ubuntu):** `sudo apt install ffmpeg`
- **Git** – required to install `madmom` from GitHub.
- _(Windows only)_ **Microsoft C++ Build Tools** – required to compile `madmom`
  ([download](https://visualstudio.microsoft.com/visual-cpp-build-tools/)).

Verify FFmpeg is available:

```bash
ffmpeg -version
```

## 🚀 Installation

1. Clone the repository:

   ```bash
   git clone https://github.com/yourusername/pro-audio-toolkit.git
   cd pro-audio-toolkit
   ```

2. Create and activate a virtual environment (recommended):

   ```bash
   python -m venv venv
   # Windows:
   venv\Scripts\activate
   # macOS/Linux:
   source venv/bin/activate
   ```

3. Install `numpy` and `Cython` first (needed to build `madmom`), then the rest:

   ```bash
   pip install --upgrade pip
   pip install numpy Cython
   pip install -r requirements.txt
   ```

   > **GPU (NVIDIA):** in `requirements.txt` replace `audio-separator[cpu]`
   > with `audio-separator[gpu]` and install a CUDA-enabled PyTorch build
   > following [pytorch.org](https://pytorch.org/get-started/locally/).

4. Run any of the scripts, e.g.:

   ```bash
   python vocal_separator.py
   ```

> **Note:** The Vocal Separator automatically downloads the required AI models
> (e.g. BS-RoFormer) on first use. This may take several minutes depending on
> your connection.

## 📄 Licenses & Acknowledgments

This toolkit is built upon several incredible open-source projects. Please
respect their licenses:

| Library                                                             | License       | Used for                                  |
| ------------------------------------------------------------------- | ------------- | ----------------------------------------- |
| [yt-dlp](https://github.com/yt-dlp/yt-dlp)                          | The Unlicense | Audio downloading (YouTube)               |
| [audio-separator](https://github.com/nomadkaraoke/python-audio-separator) | MIT     | AI separation model wrapper               |
| [madmom](https://github.com/CPJKU/madmom)                           | BSD-3-Clause  | Key detection                             |
| [librosa](https://github.com/librosa/librosa)                       | ISC           | BPM extraction and audio loading          |
| [pydub](https://github.com/jiaaro/pydub)                            | MIT           | WAV → MP3 conversion                      |
| [mutagen](https://github.com/quodlibet/mutagen)                     | GPL-2.0+      | Reading/writing audio tags                |
| [customtkinter](https://github.com/TomSchimansky/CustomTkinter)     | MIT           | Graphical user interface                  |

> ⚠️ **AI models:** pre-trained models (e.g. UVR/MDX family) may have their own
> licenses, including non-commercial restrictions – check the model author's terms.
>
> ⚠️ **Copyright:** only download content you have the rights to. Downloading
> from YouTube may violate its Terms of Service.
