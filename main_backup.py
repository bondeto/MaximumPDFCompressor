import customtkinter as ctk
from tkinter import filedialog, messagebox
import subprocess
import threading
import os
import sys

# --- Pengaturan Tampilan ---
ctk.set_appearance_mode("System")  # Modes: "System" (default), "Dark", "Light"
ctk.set_default_color_theme("blue")  # Themes: "blue" (default), "green", "dark-blue"

class PDFCompressorApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        # --- Konfigurasi Jendela Utama ---
        self.title("Maximum PDF Compressor")
        self.geometry("500x420") # Tinggi jendela ditambah agar lebih lega
        self.resizable(False, False)

        # --- Variabel ---
        self.input_file_paths = [] # Menggunakan list untuk menampung banyak file
        self.output_folder_path = ctk.StringVar()
        self.ghostscript_path = self.get_ghostscript_path()

        # --- Mapping Level Kompresi ---
        # Ini menerjemahkan pilihan user ke pengaturan Ghostscript
        self.compression_levels = {
            "Ekstrem (Perkiraan kompresi 70-95%)": [
                "-dPDFSETTINGS=/screen", # Mulai dengan basis preset /screen
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

        # --- Set Icon Aplikasi ---
        try:
            # Correctly determine the base path for resources, works for dev and for PyInstaller
            if getattr(sys, 'frozen', False):
                # Running as a bundled .exe
                base_path = sys._MEIPASS
            else:
                # Running as a .py script
                base_path = os.path.dirname(os.path.abspath(__file__))
            
            icon_path = os.path.join(base_path, "assets", "compressor.ico")
            self.iconbitmap(icon_path)
        except Exception:
            pass # Jangan crash jika ikon tidak ditemukan

    def get_ghostscript_path(self):
        """Mencari path ke Ghostscript executable."""
        # Jika di-bundle oleh PyInstaller, path-nya akan berbeda
        if getattr(sys, 'frozen', False):
            # Berjalan sebagai .exe
            base_path = sys._MEIPASS
        else:
            # Berjalan sebagai skrip .py
            base_path = os.path.dirname(os.path.abspath(__file__))
        
        gs_path = os.path.join(base_path, "gswin64c.exe")
        
        if not os.path.exists(gs_path):
            messagebox.showerror("Error", "gswin64c.exe tidak ditemukan!\n\nPastikan file tersebut ada di folder yang sama dengan aplikasi.")
            # Keluar dari aplikasi jika Ghostscript tidak ditemukan
            self.after(100, self.destroy)
            return None
        return gs_path

    def create_widgets(self):
        """Membuat dan menata semua elemen GUI."""
        self.grid_columnconfigure(0, weight=1)
        # self.grid_rowconfigure(3, weight=1) # Dihapus agar panel status tidak meregang

        # --- Frame Pemilihan File ---
        file_frame = ctk.CTkFrame(self)
        file_frame.grid(row=0, column=0, padx=10, pady=(10, 5), sticky="ew")
        file_frame.grid_columnconfigure(0, weight=1)

        self.file_list_textbox = ctk.CTkTextbox(file_frame, height=80, state="disabled")
        self.file_list_textbox.grid(row=0, column=0, columnspan=2, padx=10, pady=10, sticky="ew")

        self.browse_button = ctk.CTkButton(file_frame, text="Pilih File PDF...", command=self.browse_files)
        self.browse_button.grid(row=1, column=0, padx=(10,5), pady=(0,10), sticky="ew")

        self.clear_button = ctk.CTkButton(file_frame, text="Bersihkan", command=self.clear_file_list, state="disabled")
        self.clear_button.grid(row=1, column=1, padx=(5,10), pady=(0,10), sticky="ew")

        # --- Frame Pengaturan Output & Kompresi ---
        settings_frame = ctk.CTkFrame(self)
        settings_frame.grid(row=1, column=0, padx=10, pady=5, sticky="ew")
        settings_frame.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(settings_frame, text="Folder Output:").grid(row=0, column=0, padx=10, pady=(10,0), sticky="w")
        output_entry = ctk.CTkEntry(settings_frame, textvariable=self.output_folder_path)
        output_entry.grid(row=1, column=0, padx=10, pady=(0,10), sticky="ew")
        self.output_button = ctk.CTkButton(settings_frame, text="...", width=30, command=self.select_output_folder)
        self.output_button.grid(row=1, column=1, padx=(0,10), pady=(0,10))

        ctk.CTkLabel(settings_frame, text="Level Kompresi:").grid(row=2, column=0, columnspan=2, padx=10, pady=(5,0), sticky="w")
        self.quality_menu = ctk.CTkOptionMenu(settings_frame, values=list(self.compression_levels.keys()))
        self.quality_menu.set("Sedang (Seimbang, ~40-70%)") # Nilai default
        self.quality_menu.grid(row=3, column=0, columnspan=2, padx=10, pady=(0,10), sticky="ew")

        # --- Frame Aksi (Tombol Kompres) ---
        action_frame = ctk.CTkFrame(self)
        action_frame.grid(row=2, column=0, padx=10, pady=5, sticky="ew")
        action_frame.grid_columnconfigure(0, weight=1)

        self.compress_button = ctk.CTkButton(action_frame, text="Mulai Kompresi", command=self.start_compression, font=ctk.CTkFont(size=14, weight="bold"), state="disabled")
        self.compress_button.grid(row=0, column=0, padx=10, pady=10, ipady=8, sticky="ew")

        # --- Frame Status ---
        status_frame = ctk.CTkFrame(self)
        status_frame.grid(row=3, column=0, padx=10, pady=10, sticky="ew")
        status_frame.grid_columnconfigure(0, weight=1)

        self.status_label = ctk.CTkLabel(status_frame, text="Siap untuk mengompres. Pilih file PDF untuk memulai.")
        self.status_label.grid(row=0, column=0, padx=10, pady=(5,0), sticky="w")

        self.progressbar = ctk.CTkProgressBar(status_frame)
        self.progressbar.set(0)
        self.progressbar.grid(row=1, column=0, padx=10, pady=(0,10), sticky="ew")

    def browse_files(self):
        """Membuka dialog untuk memilih BANYAK file PDF."""
        file_paths = filedialog.askopenfilenames( # Menggunakan askopenfilenames
            title="Pilih File PDF",
            filetypes=[("PDF Files", "*.pdf")]
        )
        if file_paths:
            self.input_file_paths = list(file_paths)
            self.status_label.configure(text=f"{len(self.input_file_paths)} file dipilih.")
            
            # Tampilkan daftar file di textbox
            self.file_list_textbox.configure(state="normal")
            self.file_list_textbox.delete("1.0", "end")
            for path in self.input_file_paths:
                self.file_list_textbox.insert("end", os.path.basename(path) + "\n")
            self.file_list_textbox.configure(state="disabled")
            
            # Set folder output default & aktifkan tombol
            self.output_folder_path.set(os.path.dirname(self.input_file_paths[0]))
            self.compress_button.configure(state="normal")
            self.clear_button.configure(state="normal")

    def clear_file_list(self):
        """Membersihkan daftar file yang dipilih."""
        self.input_file_paths = []
        self.file_list_textbox.configure(state="normal")
        self.file_list_textbox.delete("1.0", "end")
        self.file_list_textbox.configure(state="disabled")
        self.output_folder_path.set("")
        self.status_label.configure(text="Daftar file dibersihkan.")
        self.progressbar.set(0)
        self.compress_button.configure(state="disabled")
        self.clear_button.configure(state="disabled")

    def select_output_folder(self):
        """Membuka dialog untuk memilih folder output."""
        folder_path = filedialog.askdirectory(title="Pilih Folder Output")
        if folder_path:
            self.output_folder_path.set(folder_path)

    def start_compression(self):
        """Memvalidasi input dan memulai thread kompresi."""
        if not self.input_file_paths:
            messagebox.showwarning("Peringatan", "Silakan pilih file PDF terlebih dahulu.")
            return
        
        if not self.output_folder_path.get():
            messagebox.showwarning("Peringatan", "Silakan tentukan folder output.")
            return

        if not self.ghostscript_path:
            return # Pesan error sudah ditampilkan saat inisialisasi

        # Nonaktifkan tombol untuk mencegah input ganda
        self.toggle_widgets_state("disabled")

        # Jalankan kompresi di thread terpisah agar GUI tidak freeze
        compression_thread = threading.Thread(target=self._compression_worker, daemon=True)
        compression_thread.start()

    def _compression_worker(self):
        """Fungsi yang berjalan di thread terpisah untuk melakukan kompresi."""
        # Dapatkan level kualitas dari menu
        selected_quality_text = self.quality_menu.get()
        quality_setting = self.compression_levels[selected_quality_text]

        total_files = len(self.input_file_paths)
        success_count = 0
        
        try:
            for i, input_path in enumerate(self.input_file_paths):
                # Update GUI dari thread utama menggunakan self.after
                status_text = f"Memproses: {os.path.basename(input_path)} ({i+1}/{total_files})"
                self.after(0, lambda: self.status_label.configure(text=status_text))
                
                output_path = self.generate_output_path(input_path)
                self.compress_pdf(input_path, output_path, quality_setting)
                success_count += 1

                # Update progress bar
                progress = (i + 1) / total_files
                self.after(0, lambda p=progress: self.progressbar.set(p))

            final_message = f"Kompresi selesai! Berhasil memproses {success_count} dari {total_files} file."
            self.after(0, lambda: messagebox.showinfo("Sukses", final_message))
            self.after(0, self.clear_file_list) # Bersihkan list setelah selesai
            self.after(0, lambda: self.status_label.configure(text="Selesai! Siap untuk tugas berikutnya."))

        except Exception as e:
            error_message = f"Terjadi kesalahan saat kompresi:\n{e}"
            self.after(0, lambda: messagebox.showerror("Error", error_message))
            self.after(0, lambda: self.status_label.configure(text="Gagal! Silakan coba lagi."))
        finally:
            # Aktifkan kembali semua tombol
            self.after(0, lambda: self.toggle_widgets_state("normal"))
            self.after(0, lambda: self.compress_button.configure(state="disabled")) # Tombol kompres tetap mati sampai file baru dipilih
            self.after(0, lambda: self.clear_button.configure(state="disabled"))

    def generate_output_path(self, input_path):
        """Membuat nama file output yang unik."""
        output_dir = self.output_folder_path.get()
        filename = os.path.basename(input_path)
        name, ext = os.path.splitext(filename)
        return os.path.join(output_dir, f"{name}_compressed{ext}")

    def compress_pdf(self, input_path, output_path, quality_setting):
        """
        Fungsi inti yang memanggil Ghostscript untuk melakukan kompresi.
        -sDEVICE=pdfwrite: Memberitahu GS untuk menghasilkan output PDF.
        -dCompatibilityLevel=1.4: Menjaga kompatibilitas dengan versi Acrobat lama.
        -dPDFSETTINGS=...: Kunci untuk level kompresi, atau bisa diganti dengan parameter kustom.
        -dNOPAUSE -dQUIET -dBATCH: Opsi standar untuk menjalankan GS dalam skrip.
        -sOutputFile=...: Menentukan file output.
        """
        base_command = [
            self.ghostscript_path,
            "-sDEVICE=pdfwrite",
            "-dCompatibilityLevel=1.4",
            "-dNOPAUSE",
            "-dQUIET",
            "-dBATCH",
        ]

        # Cek apakah quality_setting adalah preset (string) atau kustom (list)
        if isinstance(quality_setting, str):
            # Ini adalah preset standar seperti /screen
            quality_command = [f"-dPDFSETTINGS={quality_setting}"]
        else:
            # Ini adalah list parameter kustom untuk kompresi ekstrem
            quality_command = quality_setting

        # Gabungkan semua perintah
        command = base_command + quality_command + [f"-sOutputFile={output_path}", input_path]

        # Menggunakan CREATE_NO_WINDOW agar tidak muncul jendela hitam command prompt di Windows
        startupinfo = None
        if os.name == 'nt':
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        
        process = subprocess.run(command, check=True, capture_output=True, text=True, startupinfo=startupinfo)
        if process.returncode != 0:
            raise RuntimeError(f"Ghostscript error:\n{process.stderr}")

    def toggle_widgets_state(self, state="disabled"):
        """Mengaktifkan atau menonaktifkan semua widget interaktif."""
        self.browse_button.configure(state=state)
        self.clear_button.configure(state=state)
        self.output_button.configure(state=state)
        self.quality_menu.configure(state=state)
        self.compress_button.configure(state=state)


if __name__ == "__main__":
    app = PDFCompressorApp()
    app.mainloop()