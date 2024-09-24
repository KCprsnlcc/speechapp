# Speech Recognition and Translation Application

This project is a speech recognition web application that allows users to transcribe spoken words into text and translate those transcriptions between **English** and **Tagalog** (Filipino). The application also offers accessibility features like **Color Blind Mode** and supports text-to-speech functionality for reading transcriptions aloud.

The application is built using **Flask** (backend), **SpeechRecognition** (for speech-to-text), and **Googletrans** (for translations). It also utilizes **SQLite** as the database for storing transcriptions.

## Features

- **Speech-to-Text**: Convert speech into text using the `SpeechRecognition` library.
- **Translate Transcriptions**: Translate between **English** and **Tagalog** using the `googletrans` library.
- **Text-to-Speech**: Listen to transcriptions read aloud.
- **Edit and Delete Transcriptions**: Modify or remove transcriptions as needed.
- **Search Transcriptions**: Quickly search through saved transcriptions.
- **Download Transcriptions**: Export transcriptions as a text file.
- **Color Blind Mode**: Toggle a color-blind-friendly interface.
- **Responsive Design**: Works seamlessly on both desktop and mobile devices.

## Prerequisites

Ensure **Python 3.x** is installed on your system.

### Required Python Packages

- `Flask`
- `SpeechRecognition`
- `pyaudio`
- `flask-cors`
- `googletrans==4.0.0-rc1`

Installation of these packages is explained in the **Installation** section below.

### Note

- **pyaudio** requires additional setup depending on your operating system:
  - **Windows**: Download the appropriate wheel file from [PyAudio Windows Wheels](https://www.lfd.uci.edu/~gohlke/pythonlibs/#pyaudio) and install using `pip install <wheel_file>`.
  - **macOS**: Install PortAudio via Homebrew using `brew install portaudio`, then install pyaudio with `pip install pyaudio`.
  - **Linux**: Install PortAudio with `sudo apt-get install portaudio19-dev`, followed by installing pyaudio via `pip`.

## Installation

### Step 1: Clone the Repository

```bash
git clone <repository-url>
cd <repository-folder>
```

### Step 2: Set Up a Virtual Environment

To avoid conflicts with other Python projects, it's recommended to use a virtual environment.

Create a virtual environment:

```bash
python -m venv .venv
```

Activate the virtual environment:

- **Windows**:
  ```bash
  .venv\Scripts\activate
  ```
- **macOS/Linux**:
  ```bash
  source .venv/bin/activate
  ```

Once the virtual environment is activated, your terminal prompt will change, indicating that you're working within the `.venv` environment.

### Step 3: Install Dependencies

With the virtual environment activated, install the required packages:

```bash
pip install Flask SpeechRecognition pyaudio flask-cors googletrans==4.0.0-rc1
```

### Step 4: Run the Application

Start the Flask server:

```bash
python app.py
```

### Step 5: Access the Application

Open your web browser and navigate to:

```text
http://localhost:5000
```

### Step 6: Deactivate the Virtual Environment

When finished, deactivate the virtual environment by running:

```bash
deactivate
```

This returns your terminal to the global Python environment.

## Usage

### Recording Speech

1. Click the "Record" button to start recording.
2. Click the "Stop" button to end the recording. The transcription will be displayed automatically.

### Translating Transcriptions

1. Click the "Translate" button.
2. Select the translation direction (English to Tagalog or Tagalog to English).
3. Click "Translate" to see the translated text.

### Additional Features

- **Edit/Download Transcriptions**: Modify or export transcriptions easily.
- **Color Blind Mode**: Toggle color-blind-friendly UI settings.