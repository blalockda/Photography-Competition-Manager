import os
import sqlite3
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from PIL import Image, ImageTk
from datetime import datetime

class AdminWindow:
    def __init__(self, master):
        self.master = master
        master.title("Photo Competition Admin")
        master.geometry("650x600")
        master.resizable(True, True)

        # === DATABASE SETUP ===
        self.db = sqlite3.connect("competition.db")
        self.ensure_tables()

        # === CATEGORY SECTION ===
        self.category_frame = tk.LabelFrame(master, text="Select Category Level", padx=10, pady=10)
        self.category_frame.pack(fill="x", padx=10, pady=(10, 5))

        self.selected_category_level = tk.StringVar(value="Beginner")
        self.category_label = tk.Label(self.category_frame, text="Category Level:")
        self.category_label.pack(anchor="w", padx=5, pady=(0, 2))

        self.category_combobox = ttk.Combobox(
            self.category_frame,
            textvariable=self.selected_category_level,
            state="readonly",
            values=["Beginner", "Intermediate", "Advanced"]
        )
        self.category_combobox.pack(fill="x", padx=5)
        self.category_combobox.bind("<<ComboboxSelected>>", lambda e: self.refresh_photo_list())

        # === PHOTO LIST SECTION ===
        self.photo_frame = tk.LabelFrame(master, text="Photos in Competition", padx=10, pady=10)
        self.photo_frame.pack(fill="both", expand=True, padx=10, pady=(5, 10))

        self.photo_listbox = tk.Listbox(self.photo_frame, height=18, activestyle="none")
        self.photo_listbox.pack(side="left", fill="both", expand=True, padx=(0, 5), pady=5)

        self.scrollbar = tk.Scrollbar(self.photo_frame, orient="vertical", command=self.photo_listbox.yview)
        self.scrollbar.pack(side="left", fill="y", pady=5)
        self.photo_listbox.config(yscrollcommand=self.scrollbar.set)

        self.photo_index_map = {}

        # Double-click to open photo
        self.photo_listbox.bind("<Double-1>", self.on_listbox_double_click)

        # === BUTTON BAR (ADD / REMOVE / RESET) ===
        self.button_bar = tk.Frame(master)
        self.button_bar.pack(fill="x", padx=10, pady=(0, 10))

        self.add_photo_btn = tk.Button(
            self.button_bar,
            text="Add Photo",
            width=12,
            command=self.open_add_photo_dialog
        )
        self.add_photo_btn.pack(side="left", padx=(0, 5))

        self.remove_photo_btn = tk.Button(
            self.button_bar,
            text="Remove Selected",
            width=15,
            command=self.remove_selected_photo
        )
        self.remove_photo_btn.pack(side="left", padx=(0, 5))

        self.reset_data_btn = tk.Button(
            self.button_bar,
            text="Reset All Photos",
            width=15,
            command=self.reset_all_data
        )
        self.reset_data_btn.pack(side="left", padx=(0, 5))

        # Populate the listbox initially according to the default category
        self.refresh_photo_list()

    def ensure_tables(self):
        """
        Ensure that the Photos table exists with columns:
          id, filepath, category, photo_name, photographer.
        If the table already exists but lacks the new columns, ALTER to add them.
        """
        cursor = self.db.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='Photos'")
        exists = cursor.fetchone()
        if not exists:
            cursor.execute("""
                CREATE TABLE Photos (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    filepath TEXT NOT NULL,
                    category TEXT NOT NULL,
                    photo_name TEXT NOT NULL,
                    photographer TEXT NOT NULL
                )
            """)
            self.db.commit()
        else:
            cursor.execute("PRAGMA table_info(Photos)")
            columns = [row[1] for row in cursor.fetchall()]
            if "photo_name" not in columns:
                cursor.execute("ALTER TABLE Photos ADD COLUMN photo_name TEXT NOT NULL DEFAULT ''")
            if "photographer" not in columns:
                cursor.execute("ALTER TABLE Photos ADD COLUMN photographer TEXT NOT NULL DEFAULT ''")
            self.db.commit()

    def refresh_photo_list(self):
        """
        Clear and rebuild the Listbox from the Photos table,
        filtering by the currently selected category. Numbering (#1, #2, …)
        resets per-category.
        """
        self.photo_listbox.delete(0, tk.END)
        self.photo_index_map.clear()

        category = self.selected_category_level.get()
        cursor = self.db.cursor()
        cursor.execute("""
            SELECT id, photo_name, photographer
            FROM Photos
            WHERE category = ?
            ORDER BY id ASC
        """, (category,))
        rows = cursor.fetchall()

        for idx, (photo_id, photo_name, photographer) in enumerate(rows, start=1):
            display_text = f"#{idx}: {photo_name} by {photographer} [{category}]"
            self.photo_listbox.insert(tk.END, display_text)
            self.photo_index_map[idx - 1] = photo_id

    def open_add_photo_dialog(self):
        """
        Modal dialog to collect:
          - Photo Name
          - Photographer Name
          - Filepath (via file dialog)
          - Preview + Rotate
        Uses the currently selected category to tag the new photo.
        """
        dialog = tk.Toplevel(self.master)
        dialog.title("Add New Photo")
        dialog.geometry("500x700")
        dialog.resizable(True, True)
        dialog.transient(self.master)
        dialog.grab_set()

        tk.Label(dialog, text="Photo Name:").pack(anchor="w", padx=10, pady=(15, 2))
        photo_name_var = tk.StringVar()
        photo_name_entry = tk.Entry(dialog, textvariable=photo_name_var, width=60)
        photo_name_entry.pack(padx=10, pady=(0, 10))

        tk.Label(dialog, text="Photographer Name:").pack(anchor="w", padx=10, pady=(0, 2))
        photographer_var = tk.StringVar()
        photographer_entry = tk.Entry(dialog, textvariable=photographer_var, width=60)
        photographer_entry.pack(padx=10, pady=(0, 10))

        tk.Label(dialog, text="Select Photo File:").pack(anchor="w", padx=10, pady=(0, 2))
        file_frame = tk.Frame(dialog)
        file_frame.pack(fill="x", padx=10, pady=(0, 10))

        selected_filepath_var = tk.StringVar()
        file_entry = tk.Entry(
            file_frame,
            textvariable=selected_filepath_var,
            width=45,
            state="readonly"
        )
        file_entry.pack(side="left", fill="x", expand=True)

        def browse_file():
            filetypes = [
                ("Image Files", "*.jpg;*.jpeg;*.png;*.gif;*.bmp"),
                ("All Files", "*.*")
            ]
            path = filedialog.askopenfilename(
                title="Choose Photo File",
                filetypes=filetypes
            )
            if path:
                selected_filepath_var.set(path)
                load_image_preview(path)

        browse_btn = tk.Button(file_frame, text="Browse...", command=browse_file, width=10)
        browse_btn.pack(side="left", padx=(5, 0))

        preview_frame = tk.LabelFrame(dialog, text="Image Preview", padx=10, pady=10, height=350)
        preview_frame.pack(fill="x", padx=10, pady=(5, 10))
        preview_frame.pack_propagate(False)

        preview_label = tk.Label(preview_frame)
        preview_label.pack(expand=True)

        current_pil_image = {"img": None}

        def load_image_preview(path):
            try:
                pil_img = Image.open(path)
            except Exception as e:
                messagebox.showerror("Image Error", f"Failed to open image:\n{e}", parent=dialog)
                return
            current_pil_image["img"] = pil_img
            display_resized_image(pil_img)
            rotate_btn.config(state="normal")

        def display_resized_image(pil_img):
            img_copy = pil_img.copy()
            img_copy.thumbnail((300, 300), Image.LANCZOS)
            tk_img = ImageTk.PhotoImage(img_copy)
            preview_label.config(image=tk_img)
            preview_label.image = tk_img

        def rotate_image():
            if current_pil_image["img"] is None:
                return
            pil_img = current_pil_image["img"].rotate(-90, expand=True)
            current_pil_image["img"] = pil_img
            display_resized_image(pil_img)

        rotate_btn = tk.Button(dialog, text="Rotate 90°", state="disabled", command=rotate_image)
        rotate_btn.pack(pady=(0, 10))

        button_frame = tk.Frame(dialog)
        button_frame.pack(fill="x", side="bottom", pady=(0, 10))

        def on_add():
            name = photo_name_var.get().strip()
            photographer = photographer_var.get().strip()
            filepath = selected_filepath_var.get().strip()
            category = self.selected_category_level.get()
            pil_img = current_pil_image["img"]

            if not name:
                messagebox.showwarning("Missing Field", "Please enter a Photo Name.", parent=dialog)
                return
            if not photographer:
                messagebox.showwarning("Missing Field", "Please enter a Photographer Name.", parent=dialog)
                return
            if not filepath:
                messagebox.showwarning("Missing Field", "Please select a Photo File.", parent=dialog)
                return
            if pil_img is None:
                messagebox.showwarning("No Image", "No image has been loaded for preview.", parent=dialog)
                return

            storage_dir = "competition_images"
            os.makedirs(storage_dir, exist_ok=True)
            base_name = os.path.basename(filepath)
            timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
            new_filename = f"{timestamp}_{base_name}"
            new_path = os.path.join(storage_dir, new_filename)

            try:
                pil_img.save(new_path)
            except Exception as e:
                messagebox.showerror("Save Error", f"Failed to save rotated image:\n{e}", parent=dialog)
                return

            try:
                cursor = self.db.cursor()
                cursor.execute("""
                    INSERT INTO Photos (filepath, category, photo_name, photographer)
                    VALUES (?, ?, ?, ?)
                """, (new_path, category, name, photographer))
                self.db.commit()
            except sqlite3.Error as e:
                messagebox.showerror("Database Error", f"Failed to add photo:\n{e}", parent=dialog)
                return

            dialog.destroy()
            self.refresh_photo_list()

        add_btn = tk.Button(button_frame, text="Add Photo", width=12, command=on_add)
        add_btn.pack(side="right", padx=(0, 10))

        cancel_btn = tk.Button(button_frame, text="Cancel", width=12, command=dialog.destroy)
        cancel_btn.pack(side="right", padx=(10, 0))

        photo_name_entry.focus_set()

    def on_listbox_double_click(self, event):
        """
        Open the selected photo in a new window when double-clicked.
        """
        sel = self.photo_listbox.curselection()
        if not sel:
            return
        idx = sel[0]
        photo_id = self.photo_index_map.get(idx)
        if photo_id is None:
            return
        cursor = self.db.cursor()
        cursor.execute(
            "SELECT filepath, photo_name, photographer, category FROM Photos WHERE id = ?", (photo_id,)
        )
        row = cursor.fetchone()
        if not row:
            messagebox.showerror("Error", "Could not find photo in database.")
            return
        filepath, photo_name, photographer, category = row
        if not os.path.isfile(filepath):
            messagebox.showerror("Error", f"Image file not found:\n{filepath}")
            return

        win = tk.Toplevel(self.master)
        win.title(f"{photo_name} by {photographer} [{category}]")
        win.geometry("800x800")
        win.resizable(True, True)

        try:
            pil_img = Image.open(filepath)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to open image:\n{e}")
            win.destroy()
            return

        img_w, img_h = pil_img.size
        max_dim = 750
        if img_w > max_dim or img_h > max_dim:
            ratio = min(max_dim / img_w, max_dim / img_h)
            pil_img = pil_img.resize((int(img_w * ratio), int(img_h * ratio)), Image.LANCZOS)

        tk_img = ImageTk.PhotoImage(pil_img)
        img_label = tk.Label(win, image=tk_img)
        img_label.image = tk_img
        img_label.pack(padx=10, pady=10, expand=True)

        info = f"Name: {photo_name}\nPhotographer: {photographer}\nCategory: {category}\nPath: {filepath}"
        tk.Label(win, text=info, anchor="w", justify="left").pack(padx=10, pady=(0, 10), fill="x")

        tk.Button(win, text="Close", command=win.destroy).pack(pady=(0, 15))

    def remove_selected_photo(self):
        """
        Delete the photo currently selected in the Listbox from the DB, then refresh.
        """
        sel_indices = self.photo_listbox.curselection()
        if not sel_indices:
            messagebox.showinfo("No Selection", "Please select a photo to remove.")
            return

        idx = sel_indices[0]
        photo_id = self.photo_index_map.get(idx)
        if photo_id is None:
            messagebox.showerror("Internal Error", "Unable to map selection to a photo.")
            return

        confirm = messagebox.askyesno("Confirm Deletion", "Are you sure you want to remove the selected photo?")
        if not confirm:
            return

        try:
            cursor = self.db.cursor()
            cursor.execute("DELETE FROM Photos WHERE id = ?", (photo_id,))
            self.db.commit()
            self.refresh_photo_list()
        except sqlite3.Error as e:
            messagebox.showerror("Database Error", f"Failed to remove photo:\n{e}")

    def reset_all_data(self):
        """
        Wipe out all rows in the Photos table after confirmation, then refresh.
        """
        confirm = messagebox.askyesno(
            "Confirm Reset",
            "This will delete ALL photos from the competition. Are you sure?"
        )
        if not confirm:
            return

        try:
            cursor = self.db.cursor()
            cursor.execute("DELETE FROM Photos")
            self.db.commit()
            self.refresh_photo_list()
        except sqlite3.Error as e:
            messagebox.showerror("Database Error", f"Failed to reset data:\n{e}")


if __name__ == "__main__":
    root = tk.Tk()
    app = AdminWindow(root)
    root.mainloop()
