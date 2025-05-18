# PDF to Video Presentation Creator (for macOS)

This Python script automates the process of converting a PDF document into a video presentation. It extracts pages as images, pulls text for narration, generates audio using OpenAI's Text-to-Speech API, and then combines these elements into a video with page transitions.

## Features

*   Converts each PDF page to an image.
*   Extracts text from each page for narration.
*   Cleans extracted text (normalizes spacing, removes page numbers).
*   Generates narration audio using OpenAI TTS.
*   Creates video clips for each page with the image and its narration.
*   Adds fade-in/fade-out transitions between page clips.
*   Concatenates all page clips into a final video presentation.

## Prerequisites (macOS)

Before you begin, ensure you have the following installed on your macOS system:

1.  **Python 3.7+**: macOS comes with Python, but it's often Python 2. It's recommended to install a newer version. You can download it from [python.org](https://www.python.org/) or install it using Homebrew:
    ```bash
    brew install python
    ```
    Using a version manager like `pyenv` is also a good option for managing multiple Python versions.
2.  **Pip**: Python's package installer (usually comes with Python 3).
3.  **Homebrew**: The missing package manager for macOS. If you don't have it, install it from [brew.sh](https://brew.sh/).
4.  **Poppler**: A PDF rendering library, required by `pdf2image`.
    ```bash
    brew install poppler
    ```
5.  **FFmpeg**: Required by MoviePy for video processing.
    ```bash
    brew install ffmpeg
    ```

## Setup Instructions (macOS)

1.  **Clone the Repository (if applicable)**
    If this project is in a Git repository, clone it:
    ```bash
    git clone <repository-url>
    cd <repository-directory>
    ```

2.  **Create and Activate a Python Virtual Environment**
    It's highly recommended to use a virtual environment to manage project dependencies.
    ```bash
    # Ensure you are using your installed Python 3, not the system Python 2
    # If 'python' links to Python 2, use 'python3' explicitly.
    python3 -m venv .venv

    # Activate the virtual environment
    source .venv/bin/activate
    ```
    Your terminal prompt should change to indicate the virtual environment is active (e.g., `(.venv) your-prompt$`).

3.  **Install Python Dependencies**
    With the virtual environment activated, install the required Python packages:
    ```bash
    pip install -r requirements.txt
    ```
    The `requirements.txt` file should include:
    ```
    PyPDF2
    pdf2image
    moviepy
    Pillow
    openai
    python-dotenv  # If you plan to use a .env file for the API key
    ```

4.  **Set Up OpenAI API Key**
    This script uses the OpenAI API for text-to-speech. You need an OpenAI API key.
    *   **Option A: Environment Variable (Recommended)**
        Set the `OPENAI_API_KEY` environment variable in your shell (e.g., Terminal using Zsh or Bash):
        ```bash
        export OPENAI_API_KEY='your_openai_api_key_here'
        ```
        To make this permanent, add this line to your shell's configuration file (e.g., `~/.zshrc` for Zsh or `~/.bash_profile` or `~/.bashrc` for Bash). After editing the file, either restart your terminal or source the file (e.g., `source ~/.zshrc`).
    *   **Option B: .env File**
        1.  Create a file named `.env` in the root directory of the project.
        2.  Add your API key to this file:
            ```
            OPENAI_API_KEY='your_openai_api_key_here'
            ```
        3.  The script `pdf_to_video.py` can be slightly modified to use `python-dotenv` to load this file (uncomment the relevant lines for `dotenv.load_dotenv()`).

## Configuration

Open the `pdf_to_video.py` script and adjust the following constants in the "CONFIGURATION" section as needed:

*   `PDF_PATH`: Path to your input PDF file (e.g., `"My Book.pdf"`).
*   `OUTPUT_DIR`: Directory where generated images, audio, and the final video will be saved (e.g., `"output_presentation"`).
*   `VIDEO_FILENAME`: Name for the final output video file (e.g., `"my_video.mp4"`).
*   `PAGE_DURATION`: Minimum duration (in seconds) for each page if there's no narration or if narration is very short. Narration time will extend this.
*   `TRANSITION_SEC`: Duration (in seconds) for fade-in and fade-out transitions.
*   `VIDEO_WIDTH`: Width of the output video in pixels. Height will be auto-scaled.
*   `OPENAI_TTS_MODEL`: The OpenAI TTS model to use (e.g., `"tts-1"`, `"tts-1-hd"`).
*   `OPENAI_TTS_VOICE`: The OpenAI TTS voice to use (e.g., `"alloy"`, `"echo"`, `"fable"`, `"onyx"`, `"nova"`, `"shimmer"`).

## Running the Script

1.  Ensure your virtual environment is activated (`source .venv/bin/activate`).
2.  Ensure your `OPENAI_API_KEY` is set or available via a `.env` file (if you configured that).
3.  Place your PDF file in the project's root directory.
4.  Update line 10 in `pdf_to_video.py` (the `PDF_PATH` variable) to match the name of your PDF file.
5.  Run the script from the project's root directory:
    ```bash
    python pdf_to_video.py
    ```
    (If `python` defaults to Python 2 on your system, use `python3 pdf_to_video.py`)

The script will print progress updates to the console. The final video will be saved in the specified `OUTPUT_DIR`.

## Troubleshooting (macOS)

*   **`AttributeError` with MoviePy methods**: Ensure you have the correct version of MoviePy installed, as API methods can change between versions. The `requirements.txt` should help manage this.
*   **`pdf2image.exceptions.PDFInfoNotInstalledError` / Poppler issues**: This usually means Poppler is not installed correctly via Homebrew or not linked properly. Try `brew doctor` and `brew reinstall poppler`.
*   **OpenAI API Errors**:
    *   Check that your `OPENAI_API_KEY` is correctly set and valid.
    *   Ensure you have sufficient credits/quota on your OpenAI account.
    *   Check your internet connection.
*   **File Not Found Errors**: Verify that the `PDF_PATH` points to an existing PDF file.

## Cleanup

The script attempts to clean up temporary audio files created during the process. Generated images for each page and the final video will remain in the `OUTPUT_DIR`.

---

This `README.md` is tailored for macOS users.
