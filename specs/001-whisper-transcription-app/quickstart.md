# Quickstart: Whisper Transcription App

## Prerequisites

- Python 3.11+
- pip
- PortAudio system library (for sounddevice):
  - Linux: `sudo apt install libportaudio2`
  - macOS: `brew install portaudio`
  - Windows: bundled in the sounddevice wheel

### Optional: NVIDIA GPU acceleration

- NVIDIA drivers up to date
- CUDA 12.3+ and cuDNN v9 installed
- If using older CUDA: pin `ctranslate2` to a compatible version (see research.md)

## Setup

```bash
# Clone and enter the repo
git clone <repo-url>
cd speech-to-text

# Create virtual environment
python -m venv .venv
source .venv/bin/activate       # Windows: .venv\Scripts\activate

# Install dependencies
pip install -e ".[dev]"
```

## Run the app

```bash
python -m src.app
```

The app starts in IDLE state. The status bar shows whether GPU or CPU is
being used for transcription.

## Run tests

```bash
# All tests
pytest

# Single test file
pytest tests/unit/test_recorder.py

# Integration tests only
pytest tests/integration/
```

## Lint and format

```bash
ruff check src/ tests/
ruff format src/ tests/
```

## Validate first-run experience

1. Launch the app: `python -m src.app`
2. Click **Record** — status changes to "Recording…"
3. Speak a sentence
4. Click **Accept** — spinner appears, status shows "Transcribing…"
5. Text appears in the output area
6. Click **Copy** — paste elsewhere to verify clipboard contents
7. Click **Clear** — output area empties
8. Click the gear icon — Settings window opens, model selector visible
9. Change model to `small`, close Settings
10. Record and Accept again — transcription completes using the new model
