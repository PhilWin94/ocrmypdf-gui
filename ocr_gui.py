import tkinter as tk
from tkinter import ttk
from tkinter import filedialog, messagebox
import subprocess
import os
import time # Optional: for slight delay in status updates

# --- Global variables ---
# Changed from input_pdf_path to input_folder_path
input_folder_path = ""
output_folder_path = ""

# --- GUI Functions ---

# Changed function name and logic
def select_input_folder():
    global input_folder_path
    # Use the last selected input folder as initialdir
    initial_dir = input_folder_path if input_folder_path else "/"
    path = filedialog.askdirectory(
        title="Select Input Folder Containing PDFs",
        initialdir=initial_dir
    )
    if path: # Only update if a folder was selected
        input_folder_path = path
        # Update the corresponding entry widget (renamed below)
        input_folder_entry.delete(0, tk.END)
        input_folder_entry.insert(0, input_folder_path)

def select_output_folder():
    global output_folder_path
    initial_dir = output_folder_path if output_folder_path else "/"
    path = filedialog.askdirectory(
        title="Select Output Folder",
        initialdir=initial_dir
    )
    if path:
        output_folder_path = path
        output_path_entry.delete(0, tk.END)
        output_path_entry.insert(0, output_folder_path)

# --- Heavily Modified run_ocr Function ---
def run_ocr():
    # --- Input Validation ---
    # Get paths from entry widgets
    current_input_folder = input_folder_entry.get()
    current_output_folder = output_path_entry.get()
    lang_str = language_var.get().strip()

    # Validate paths are directories
    if not current_input_folder or not os.path.isdir(current_input_folder):
        messagebox.showerror("Error", "Please select a valid input folder.")
        return
    if not current_output_folder or not os.path.isdir(current_output_folder):
        messagebox.showerror("Error", "Please select a valid output folder.")
        return
    if not lang_str:
         messagebox.showerror("Error", "Please enter language code(s) (e.g., 'eng', 'deu', 'eng+fra').")
         return

    # Ensure global paths are updated
    global input_folder_path, output_folder_path
    input_folder_path = current_input_folder
    output_folder_path = current_output_folder

    # --- Prepare for Batch Processing ---
    try:
        pdf_files = [
            f for f in os.listdir(input_folder_path)
            if os.path.isfile(os.path.join(input_folder_path, f)) and f.lower().endswith(".pdf")
        ]
    except OSError as e:
        messagebox.showerror("Error", f"Could not read input folder:\n{e}")
        return

    if not pdf_files:
        messagebox.showinfo("Info", "No PDF files found in the selected input folder.")
        return

    # Disable run button during processing
    run_button.config(state=tk.DISABLED)
    status_label.config(text="Status: Starting batch...")
    root.update_idletasks()

    # --- Build Base ocrmypdf Command (options only) ---
    base_command = ["ocrmypdf"]
    base_command.extend(["--language", lang_str])
    if force_ocr_var.get(): base_command.append("--force-ocr")
    if deskew_var.get(): base_command.append("--deskew")
    if clean_var.get(): base_command.append("--clean")
    optimize_level = optimize_var.get()
    if optimize_level > 0: base_command.extend(["--optimize", str(optimize_level)])
    # Consider adding --skip-text or other relevant flags here if needed

    # --- Process Each PDF File ---
    success_count = 0
    error_count = 0
    skipped_count = 0
    error_details = []
    total_files = len(pdf_files)

    for i, input_filename in enumerate(pdf_files):
        current_input_filepath = os.path.join(input_folder_path, input_filename)
        name_without_ext = os.path.splitext(input_filename)[0]
        output_filename = f"{name_without_ext}_ocr.pdf" # Or choose a different naming scheme
        output_filepath = os.path.join(output_folder_path, output_filename)

        status_text = f"Status: Processing {i+1}/{total_files}: {input_filename}..."
        status_label.config(text=status_text)
        root.update_idletasks()

        # Optional: Skip if output file already exists
        # if os.path.exists(output_filepath):
        #     print(f"Skipping '{input_filename}', output file already exists.")
        #     skipped_count += 1
        #     continue # Skip to the next file

        # Add input and output files to the command for this specific file
        command = base_command + [current_input_filepath, output_filepath]
        print(f"Running: {' '.join(command)}") # For debugging

        try:
            # Run OCR for the current file
            result = subprocess.run(command, check=True, capture_output=True, text=True, encoding='utf-8')
            print(f"Successfully processed: {input_filename}")
            # print(f"Output for {input_filename}:\n{result.stdout}\n---") # Optional: log stdout
            success_count += 1

        except subprocess.CalledProcessError as e:
            error_count += 1
            error_msg = f"Failed file: {input_filename}\nError: {e.stderr}\n---"
            print(error_msg) # Log error to console
            error_details.append(error_msg)
            # Decide if you want to stop on first error or continue
            # continue # Continue with the next file even if one fails

        except FileNotFoundError:
            # This error should only happen once if ocrmypdf is not found
            status_label.config(text="Status: Error")
            messagebox.showerror("Fatal Error", "OCRmyPDF command not found. Make sure it's installed and in your system's PATH.")
            run_button.config(state=tk.NORMAL) # Re-enable button
            return # Stop processing
        except Exception as e:
            error_count += 1
            error_msg = f"Failed file: {input_filename}\nUnexpected Error: {e}\n---"
            print(error_msg)
            error_details.append(error_msg)
            # continue

    # --- Batch Processing Finished ---
    status_label.config(text="Status: Batch complete!")
    run_button.config(state=tk.NORMAL) # Re-enable button

    summary_message = f"Batch processing finished.\n\n" \
                      f"Successfully processed: {success_count}\n" \
                      f"Errors: {error_count}\n" \
                      f"Skipped (e.g., output exists): {skipped_count}" # Update if skip logic is added

    if error_details:
         # If many errors, maybe just show the count and log details to console/file
         summary_message += "\n\nErrors occurred on some files (see console output for details)."
         # Optional: Show first few errors in messagebox if not too long
         # summary_message += "\n\nFirst few errors:\n" + "\n".join(error_details[:3])

    messagebox.showinfo("Batch Complete", summary_message)


# --- Initialize the main window ---
root = tk.Tk()
root.title("OCRmyPDF GUI - Batch Mode") # Updated title

# --- GUI Widgets ---

# Frame for file paths
path_frame = tk.Frame(root, padx=5, pady=5)
path_frame.grid(row=0, column=0, sticky="ew")
path_frame.grid_columnconfigure(1, weight=1)

# --- Input Folder Path (Modified) ---
input_folder_label = tk.Label(path_frame, text="Input Folder:") # Renamed Label
input_folder_label.grid(row=0, column=0, padx=5, pady=5, sticky="w")
input_folder_entry = tk.Entry(path_frame, width=50) # Renamed Entry
input_folder_entry.grid(row=0, column=1, padx=5, pady=5, sticky="ew")
# Changed button command
input_folder_button = tk.Button(path_frame, text="Browse...", command=select_input_folder)
input_folder_button.grid(row=0, column=2, padx=5, pady=5)

# Output Folder Path (Unchanged)
output_path_label = tk.Label(path_frame, text="Output Folder:")
output_path_label.grid(row=1, column=0, padx=5, pady=5, sticky="w")
output_path_entry = tk.Entry(path_frame, width=50)
output_path_entry.grid(row=1, column=1, padx=5, pady=5, sticky="ew")
output_path_button = tk.Button(path_frame, text="Browse...", command=select_output_folder)
output_path_button.grid(row=1, column=2, padx=5, pady=5)


# Frame for OCR Options (Unchanged)
options_frame = tk.LabelFrame(root, text="OCR Options", padx=10, pady=10)
options_frame.grid(row=1, column=0, padx=10, pady=5, sticky="ew")
options_frame.grid_columnconfigure(1, weight=1)

# Language (Unchanged)
language_label = tk.Label(options_frame, text="Language(s):")
language_label.grid(row=0, column=0, padx=5, pady=2, sticky="w")
language_var = tk.StringVar(root, value='deu')
language_entry = tk.Entry(options_frame, textvariable=language_var, width=20)
language_entry.grid(row=0, column=1, padx=5, pady=2, sticky="ew")
language_help = tk.Label(options_frame, text="(e.g., 'eng', 'deu', 'eng+fra')")
language_help.grid(row=0, column=2, padx=5, pady=2, sticky="w")

# Checkbox Options Frame (Unchanged)
checkbox_frame = tk.Frame(options_frame)
checkbox_frame.grid(row=1, column=0, columnspan=3, pady=5, sticky="w")

force_ocr_var = tk.BooleanVar(root, value=False)
force_ocr_check = tk.Checkbutton(checkbox_frame, text="Force OCR", variable=force_ocr_var)
force_ocr_check.pack(side=tk.LEFT, padx=5)

deskew_var = tk.BooleanVar(root, value=False)
deskew_check = tk.Checkbutton(checkbox_frame, text="Deskew", variable=deskew_var)
deskew_check.pack(side=tk.LEFT, padx=5)

clean_var = tk.BooleanVar(root, value=False)
clean_check = tk.Checkbutton(checkbox_frame, text="Clean", variable=clean_var)
clean_check.pack(side=tk.LEFT, padx=5)

# Optimization Options (Unchanged)
optimize_frame = tk.Frame(options_frame)
optimize_frame.grid(row=2, column=0, columnspan=3, pady=5, sticky="w")

optimize_label = tk.Label(optimize_frame, text="Optimization:")
optimize_label.pack(side=tk.LEFT, padx=5)

optimize_var = tk.IntVar(root, value=1)
opt0 = tk.Radiobutton(optimize_frame, text="None (0)", variable=optimize_var, value=0)
opt1 = tk.Radiobutton(optimize_frame, text="Fast (1)", variable=optimize_var, value=1)
opt3 = tk.Radiobutton(optimize_frame, text="Max (3)", variable=optimize_var, value=3)
opt0.pack(side=tk.LEFT)
opt1.pack(side=tk.LEFT)
opt3.pack(side=tk.LEFT)

# Run Button & Status (Added disabling/enabling of button)
action_frame = tk.Frame(root, padx=5, pady=5)
action_frame.grid(row=2, column=0, sticky="ew")
action_frame.grid_columnconfigure(0, weight=1)

run_button = tk.Button(action_frame, text="Run OCR Batch", command=run_ocr, width=15) # Updated button text
run_button.pack(side=tk.RIGHT, padx=5, pady=5)

status_label = tk.Label(action_frame, text="Status: Idle", anchor="w", relief=tk.SUNKEN, bd=1)
status_label.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5, pady=5)

# Configure main window resizing behavior
root.grid_columnconfigure(0, weight=1)

# Start the Tkinter event loop
root.mainloop()