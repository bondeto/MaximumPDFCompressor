import customtkinter as ctk
from tkinter import filedialog, messagebox
import subprocess
import threading
import os
import sys
import json
from datetime import datetime

# --- Pengaturan Tampilan ---
ctk.set_appearance_mode("System")  # Will be controlled by user toggle
ctk.set_default_color_theme("blue")

class PDFCompressorApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        # --- Initialize Settings ---
        self.settings_file = "settings.json"
        self.recent_files_file = "recent_files.json"
        self.load_settings()
        self.load_recent_files()

        # --- Konfigurasi Jendela Utama ---
        self.title("Maximum PDF Compressor v1.1")
        self.geometry("600x550")  # Slightly larger for new features
        self.resizable(False, False)

        # --- Variabel ---
        self.input_file_paths = []
        self.output_folder_path = ctk.StringVar()
        self.ghostscript_path = self.get_ghostscript_path()
        self.current_theme = ctk.StringVar(value=self.settings.get("theme", "System"))

        # --- File Size Tracking ---
        self.original_sizes = {}
        self.compressed_sizes = {}

        # --- Mapping Level Kompresi ---
        self.compression_levels = {
            "Ekstrem (Perkiraan kompresi 70-95%)": [
                "-dPDFSETTINGS=/screen",
                "-dColorImageResolution=72",
                "-dGrayImageResolution=72", 
                "-dMonoImageResolution=72",
                "-dDownsampleColorImages=true",
                "-dDownsampleGrayImages=true",
                "-dDownsampleMonoImages=true",
                "-dColorImageDownsampleType=/Bicubic",
                "-dGrayImageDownsampleType=/Bicubic",
                "-dMonoImageDownsampleType=/Bicubic",
                "-dConvertCMYKImagesToRGB=true",
                "-dDetectDuplicateImages=true",
                "-dCompressFonts=true",
                "-dSubsetFonts=true",
                "-dOptimize=true"
            ],
            "Rendah (Kompresi Tinggi, ~60-85%)": "/screen",
            "Sedang (Seimbang, ~40-70%)": "/ebook",
            "Tinggi (Kualitas Cetak, ~10-30%)": "/printer",
            "Sangat Tinggi (Prepress, ~0-15%)": "/prepress"
        }

        # --- Membuat Widget GUI ---
        self.create_widgets()
        self.set_icon()

    def load_settings(self):
        """Load user settings from JSON file"""
        try:
            if os.path.exists(self.settings_file):
                with open(self.settings_file, 'r') as f:
                    self.settings = json.load(f)
            else:
                self.settings = {"theme": "System"}
        except:
            self.settings = {"theme": "System"}

    def save_settings(self):
        """Save user settings to JSON file"""
        try:
            with open(self.settings_file, 'w') as f:
                json.dump(self.settings, f)
        except:
            pass

    def load_recent_files(self):
        """Load recent files list"""
        try:
            if os.path.exists(self.recent_files_file):
                with open(self.recent_files_file, 'r') as f:
                    self.recent_files = json.load(f)
            else:
                self.recent_files = []
        except:
            self.recent_files = []

    def save_recent_files(self):
        """Save recent files list"""
        try:
            with open(self.recent_files_file, 'w') as f:
                json.dump(self.recent_files, f)
        except:
            pass

    def add_to_recent_files(self, file_paths):
        """Add files to recent list"""
        for file_path in file_paths:
            if file_path in self.recent_files:
                self.recent_files.remove(file_path)
            self.recent_files.insert(0, file_path)
        
        # Keep only last 10 files
        self.recent_files = self.recent_files[:10]
        self.save_recent_files()
        self.update_recent_files_menu()

    def update_recent_files_menu(self):
        """Update recent files dropdown"""
        if hasattr(self, 'recent_files_menu'):
            recent_display = []
            for file_path in self.recent_files:
                if os.path.exists(file_path):
                    filename = os.path.basename(file_path)
                    recent_display.append(f"{filename}")
            
            if recent_display:
                self.recent_files_menu.configure(values=recent_display)
                self.recent_files_menu.set("Pilih file terbaru...")
            else:
                self.recent_files_menu.configure(values=["Tidak ada file terbaru"])
                self.recent_files_menu.set("Tidak ada file terbaru")

    def set_icon(self):
        """Set application icon"""
        try:
            if getattr(sys, 'frozen', False):
                base_path = sys._MEIPASS
            else:
                base_path = os.path.dirname(os.path.abspath(__file__))
            
            icon_path = os.path.join(base_path, "assets", "compressor.ico")
            self.iconbitmap(icon_path)
        except Exception:
            pass

    def get_ghostscript_path(self):
        """Find Ghostscript executable path"""
        if getattr(sys, 'frozen', False):
            base_path = sys._MEIPASS
        else:
            base_path = os.path.dirname(os.path.abspath(__file__))
        
        gs_path = os.path.join(base_path, "gswin64c.exe")
        
        if not os.path.exists(gs_path):
            messagebox.showerror("Error", "gswin64c.exe tidak ditemukan!\n\nPastikan file tersebut ada di folder yang sama dengan aplikasi.")
            self.after(100, self.destroy)
            return None
        return gs_path

    def create_widgets(self):
        """Create and layout all GUI elements"""
        self.grid_columnconfigure(0, weight=1)

        # --- Header Frame with Theme Toggle ---
        header_frame = ctk.CTkFrame(self)
        header_frame.grid(row=0, column=0, padx=10, pady=(10, 5), sticky="ew")
        header_frame.grid_columnconfigure(0, weight=1)

        header_content = ctk.CTkFrame(header_frame)
        header_content.grid(row=0, column=0, padx=10, pady=10, sticky="ew")
        header_content.grid_columnconfigure(0, weight=1)

        title_label = ctk.CTkLabel(header_content, text="Maximum PDF Compressor", 
                                 font=ctk.CTkFont(size=16, weight="bold"))
        title_label.grid(row=0, column=0, sticky="w")

        theme_frame = ctk.CTkFrame(header_content)
        theme_frame.grid(row=0, column=1, sticky="e")

        ctk.CTkLabel(theme_frame, text="Theme:").grid(row=0, column=0, padx=(10,5), pady=10)
        self.theme_menu = ctk.CTkOptionMenu(theme_frame, values=["Light", "Dark", "System"],
                                          command=self.change_theme)
        self.theme_menu.set(self.current_theme.get())
        self.theme_menu.grid(row=0, column=1, padx=(0,10), pady=10)

        # --- Recent Files Frame ---
        recent_frame = ctk.CTkFrame(self)
        recent_frame.grid(row=1, column=0, padx=10, pady=5, sticky="ew")
        recent_frame.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(recent_frame, text="File Terbaru:").grid(row=0, column=0, padx=10, pady=10, sticky="w")
        self.recent_files_menu = ctk.CTkOptionMenu(recent_frame, values=["Tidak ada file terbaru"],
                                                 command=self.load_recent_file)
        self.recent_files_menu.grid(row=0, column=1, padx=(5,10), pady=10, sticky="ew")
        
        # --- File Selection Frame ---
        file_frame = ctk.CTkFrame(self)
        file_frame.grid(row=2, column=0, padx=10, pady=5, sticky="ew")
        file_frame.grid_columnconfigure(0, weight=1)

        self.file_list_textbox = ctk.CTkTextbox(file_frame, height=80, state="disabled")
        self.file_list_textbox.grid(row=0, column=0, columnspan=2, padx=10, pady=10, sticky="ew")

        self.browse_button = ctk.CTkButton(file_frame, text="Pilih File PDF...", command=self.browse_files)
        self.browse_button.grid(row=1, column=0, padx=(10,5), pady=(0,10), sticky="ew")

        self.clear_button = ctk.CTkButton(file_frame, text="Bersihkan", command=self.clear_file_list, state="disabled")
        self.clear_button.grid(row=1, column=1, padx=(5,10), pady=(0,10), sticky="ew")

        # --- Settings Frame ---
        settings_frame = ctk.CTkFrame(self)
        settings_frame.grid(row=3, column=0, padx=10, pady=5, sticky="ew")
        settings_frame.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(settings_frame, text="Folder Output:").grid(row=0, column=0, padx=10, pady=(10,0), sticky="w")
        output_entry = ctk.CTkEntry(settings_frame, textvariable=self.output_folder_path)
        output_entry.grid(row=1, column=0, padx=10, pady=(0,10), sticky="ew")
        self.output_button = ctk.CTkButton(settings_frame, text="...", width=30, command=self.select_output_folder)
        self.output_button.grid(row=1, column=1, padx=(0,10), pady=(0,10))

        ctk.CTkLabel(settings_frame, text="Level Kompresi:").grid(row=2, column=0, columnspan=2, padx=10, pady=(5,0), sticky="w")
        self.quality_menu = ctk.CTkOptionMenu(settings_frame, values=list(self.compression_levels.keys()))
        self.quality_menu.set("Sedang (Seimbang, ~40-70%)")
        self.quality_menu.grid(row=3, column=0, columnspan=2, padx=10, pady=(0,10), sticky="ew")

        # --- Action Frame ---
        action_frame = ctk.CTkFrame(self)
        action_frame.grid(row=4, column=0, padx=10, pady=5, sticky="ew")
        action_frame.grid_columnconfigure(0, weight=1)

        self.compress_button = ctk.CTkButton(action_frame, text="Mulai Kompresi", command=self.start_compression, 
                                           font=ctk.CTkFont(size=14, weight="bold"), state="disabled")
        self.compress_button.grid(row=0, column=0, padx=10, pady=10, ipady=8, sticky="ew")

        # --- Enhanced Status Frame ---
        status_frame = ctk.CTkFrame(self)
        status_frame.grid(row=5, column=0, padx=10, pady=10, sticky="ew")
        status_frame.grid_columnconfigure(0, weight=1)

        self.status_label = ctk.CTkLabel(status_frame, text="Siap untuk mengompres. Pilih file PDF untuk memulai.")
        self.status_label.grid(row=0, column=0, padx=10, pady=(10,5), sticky="w")

        self.current_file_label = ctk.CTkLabel(status_frame, text="", font=ctk.CTkFont(size=11))
        self.current_file_label.grid(row=1, column=0, padx=10, pady=(0,5), sticky="w")

        self.progressbar = ctk.CTkProgressBar(status_frame)
        self.progressbar.set(0)
        self.progressbar.grid(row=2, column=0, padx=10, pady=(0,5), sticky="ew")

        # Size comparison frame
        self.size_frame = ctk.CTkFrame(status_frame)
        self.size_frame.grid(row=3, column=0, padx=10, pady=(5,10), sticky="ew")
        self.size_frame.grid_columnconfigure(1, weight=1)

        self.size_info_label = ctk.CTkLabel(self.size_frame, text="")
        self.size_info_label.grid(row=0, column=0, columnspan=2, padx=10, pady=5, sticky="w")

        # Initialize recent files menu
        self.update_recent_files_menu()

    def change_theme(self, theme):
        """Change application theme"""
        self.current_theme.set(theme)
        self.settings["theme"] = theme
        self.save_settings()
        ctk.set_appearance_mode(theme)

    def load_recent_file(self, selection):
        """Load a recent file"""
        if selection == "Tidak ada file terbaru" or selection == "Pilih file terbaru...":
            return
        
        # Find the full path
        for file_path in self.recent_files:
            if os.path.basename(file_path) == selection:
                if os.path.exists(file_path):
                    self.input_file_paths = [file_path]
                    self.update_file_display()
                    break

    def get_file_size(self, file_path):
        """Get file size in bytes"""
        try:
            return os.path.getsize(file_path)
        except:
            return 0

    def format_file_size(self, size_bytes):
        """Format file size to human readable format"""
        if size_bytes == 0:
            return "0 B"
        
        size_names = ["B", "KB", "MB", "GB"]
        import math
        i = int(math.floor(math.log(size_bytes, 1024)))
        p = math.pow(1024, i)
        s = round(size_bytes / p, 2)
        return f"{s} {size_names[i]}"

    def update_file_display(self):
        """Update file list display and enable/disable buttons"""
        if self.input_file_paths:
            self.file_list_textbox.configure(state="normal")
            self.file_list_textbox.delete("1.0", "end")
            
            total_size = 0
            for path in self.input_file_paths:
                filename = os.path.basename(path)
                file_size = self.get_file_size(path)
                self.original_sizes[path] = file_size
                total_size += file_size
                size_str = self.format_file_size(file_size)
                self.file_list_textbox.insert("end", f"{filename} ({size_str})\n")
            
            self.file_list_textbox.configure(state="disabled")
            
            # Update status
            file_count = len(self.input_file_paths)
            total_size_str = self.format_file_size(total_size)
            self.status_label.configure(text=f"{file_count} file dipilih. Total ukuran: {total_size_str}")
            
            # Set default output folder and enable buttons
            self.output_folder_path.set(os.path.dirname(self.input_file_paths[0]))
            self.compress_button.configure(state="normal")
            self.clear_button.configure(state="normal")

    def browse_files(self):
        """Open file dialog to select PDF files"""
        file_paths = filedialog.askopenfilenames(
            title="Pilih File PDF",
            filetypes=[("PDF Files", "*.pdf")]
        )
        if file_paths:
            self.input_file_paths = list(file_paths)
            self.update_file_display()
            self.add_to_recent_files(file_paths)

    def clear_file_list(self):
        """Clear selected files list"""
        self.input_file_paths = []
        self.original_sizes = {}
        self.compressed_sizes = {}
        
        self.file_list_textbox.configure(state="normal")
        self.file_list_textbox.delete("1.0", "end")
        self.file_list_textbox.configure(state="disabled")
        
        self.output_folder_path.set("")
        self.status_label.configure(text="Daftar file dibersihkan.")
        self.current_file_label.configure(text="")
        self.size_info_label.configure(text="")
        self.progressbar.set(0)
        
        self.compress_button.configure(state="disabled")
        self.clear_button.configure(state="disabled")

    def select_output_folder(self):
        """Open folder dialog to select output folder"""
        folder_path = filedialog.askdirectory(title="Pilih Folder Output")
        if folder_path:
            self.output_folder_path.set(folder_path)

    def start_compression(self):
        """Validate input and start compression thread"""
        if not self.input_file_paths:
            messagebox.showwarning("Peringatan", "Silakan pilih file PDF terlebih dahulu.")
            return
        
        if not self.output_folder_path.get():
            messagebox.showwarning("Peringatan", "Silakan tentukan folder output.")
            return

        if not self.ghostscript_path:
            return

        # Reset size tracking
        self.compressed_sizes = {}
        self.size_info_label.configure(text="")

        # Disable widgets and start compression
        self.toggle_widgets_state("disabled")
        compression_thread = threading.Thread(target=self._compression_worker, daemon=True)
        compression_thread.start()

    def _compression_worker(self):
        """Compression worker thread"""
        selected_quality_text = self.quality_menu.get()
        quality_setting = self.compression_levels[selected_quality_text]

        total_files = len(self.input_file_paths)
        success_count = 0
        total_original_size = 0
        total_compressed_size = 0
        
        try:
            for i, input_path in enumerate(self.input_file_paths):
                filename = os.path.basename(input_path)
                status_text = f"Memproses: {filename} ({i+1}/{total_files})"
                self.after(0, lambda t=status_text: self.status_label.configure(text=t))
                self.after(0, lambda f=filename: self.current_file_label.configure(text=f"File saat ini: {f}"))
                
                output_path = self.generate_output_path(input_path)
                self.compress_pdf(input_path, output_path, quality_setting)
                
                # Track file sizes
                original_size = self.original_sizes.get(input_path, 0)
                compressed_size = self.get_file_size(output_path)
                self.compressed_sizes[input_path] = compressed_size
                
                total_original_size += original_size
                total_compressed_size += compressed_size
                
                success_count += 1
                progress = (i + 1) / total_files
                self.after(0, lambda p=progress: self.progressbar.set(p))
                
                # Update size comparison
                if original_size > 0:
                    reduction = ((original_size - compressed_size) / original_size) * 100
                    size_text = f"Original: {self.format_file_size(total_original_size)} → Compressed: {self.format_file_size(total_compressed_size)} (Penghematan: {reduction:.1f}%)"
                    self.after(0, lambda t=size_text: self.size_info_label.configure(text=t))

            # Final summary
            total_reduction = ((total_original_size - total_compressed_size) / total_original_size) * 100 if total_original_size > 0 else 0
            final_message = f"Kompresi selesai! Berhasil memproses {success_count} dari {total_files} file.\n\n"
            final_message += f"Total ukuran asli: {self.format_file_size(total_original_size)}\n"
            final_message += f"Total ukuran terkompresi: {self.format_file_size(total_compressed_size)}\n"
            final_message += f"Total penghematan: {self.format_file_size(total_original_size - total_compressed_size)} ({total_reduction:.1f}%)"
            
            self.after(0, lambda: messagebox.showinfo("Sukses", final_message))
            self.after(0, self.clear_file_list)
            self.after(0, lambda: self.status_label.configure(text="Selesai! Siap untuk tugas berikutnya."))
            self.after(0, lambda: self.current_file_label.configure(text=""))

        except Exception as e:
            error_message = f"Terjadi kesalahan saat kompresi:\n{e}"
            self.after(0, lambda: messagebox.showerror("Error", error_message))
            self.after(0, lambda: self.status_label.configure(text="Gagal! Silakan coba lagi."))
            self.after(0, lambda: self.current_file_label.configure(text=""))
        finally:
            self.after(0, lambda: self.toggle_widgets_state("normal"))
            self.after(0, lambda: self.compress_button.configure(state="disabled"))
            self.after(0, lambda: self.clear_button.configure(state="disabled"))

    def generate_output_path(self, input_path):
        """Generate unique output file path"""
        output_dir = self.output_folder_path.get()
        filename = os.path.basename(input_path)
        name, ext = os.path.splitext(filename)
        return os.path.join(output_dir, f"{name}_compressed{ext}")

    def compress_pdf(self, input_path, output_path, quality_setting):
        """Core PDF compression function using Ghostscript"""
        base_command = [
            self.ghostscript_path,
            "-sDEVICE=pdfwrite",
            "-dCompatibilityLevel=1.4",
            "-dNOPAUSE",
            "-dQUIET",
            "-dBATCH",
        ]

        if isinstance(quality_setting, str):
            quality_command = [f"-dPDFSETTINGS={quality_setting}"]
        else:
            quality_command = quality_setting

        command = base_command + quality_command + [f"-sOutputFile={output_path}", input_path]

        startupinfo = None
        if os.name == 'nt':
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        
        process = subprocess.run(command, check=True, capture_output=True, text=True, startupinfo=startupinfo)
        if process.returncode != 0:
            raise RuntimeError(f"Ghostscript error:\n{process.stderr}")

    def toggle_widgets_state(self, state="disabled"):
        """Enable or disable all interactive widgets"""
        self.browse_button.configure(state=state)
        self.clear_button.configure(state=state)
        self.output_button.configure(state=state)
        self.quality_menu.configure(state=state)
        self.compress_button.configure(state=state)
        self.theme_menu.configure(state=state)
        self.recent_files_menu.configure(state=state)


if __name__ == "__main__":
    app = PDFCompressorApp()
    app.mainloop()
