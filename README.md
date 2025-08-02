# Maximum PDF Compressor

A simple yet powerful desktop application for Windows to compress PDF files with various compression levels, built with Python and CustomTkinter.



---

## ✨ Features

- **Multiple Compression Levels:** Choose from several presets, from "Extreme" for maximum file size reduction push to "Prepress" for the highest quality.
- **Batch Processing:** Compress multiple PDF files at once.
- **Custom Output Folder:** Select where you want to save your compressed files.
- **Professional UI:** A clean, modern, and responsive user interface built with CustomTkinter.
- **Asynchronous Processing:** The app's UI remains responsive and won't freeze, even when compressing large files.
- **Visual Progress:** A progress bar shows the status of the batch compression.
- **Standalone Executable:** The project can be compiled into a single `.exe` file that runs on Windows without needing Python or any libraries installed.

## ⚙️ How It Works

The application uses **Ghostscript** as its backend engine, which is one of the most powerful and reliable tools for PDF manipulation. The Python script provides a user-friendly graphical interface (GUI) to interact with Ghostscript's powerful compression capabilities.

## 🚀 Getting Started

### Using the Executable (`.exe`)

1.  Go to the Releases page.
2.  Download the latest `PDFCompressor.exe` file.
3.  Run the application. No installation is needed.

### How to Use the Application

1.  Click **"Pilih File PDF..."** to select one or more PDF files you want to compress.
2.  The selected files will appear in the list box.
3.  (Optional) Click the **"..."** button to choose a different output folder. By default, it uses the same folder as the input files.
4.  Select your desired **"Level Kompresi"** from the dropdown menu.
5.  Click **"Mulai Kompresi"**.
6.  The progress bar will show the progress, and a success message will appear when finished.

---

## 🛠️ Building from Source

If you want to run or modify the project from the source code, follow these steps.

### Prerequisites

- Python 3.8+
- Ghostscript (AGPL Release)

### Setup

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/bondeto/MaximumPDFCompressor.git
    cd MaximumPDFCompressor
    ```

2.  **Create and activate a virtual environment:**
    ```bash
    # For Windows
    python -m venv venv
    .\venv\Scripts\activate
    ```

3.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Add Ghostscript:**
    Find the `gswin64c.exe` file from your Ghostscript installation (e.g., `C:\Program Files\gs\gs10.03.2\bin\`) and copy it into the root of the project folder.

5.  **Run the application:**
    ```bash
    python main.py
    ```

### Compiling to an `.exe`

To create a standalone executable, run the following command:
```bash
pyinstaller --onefile --windowed --name "PDFCompressor" --add-data "gswin64c.exe;." --add-data "assets;assets" --icon="assets/compressor.ico" main.py
```
The final `.exe` will be located in the `dist` folder.