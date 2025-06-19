import os
import sqlite3
import customtkinter as ctk
from tkinter import filedialog, messagebox
from PIL import Image
from datetime import datetime

class AdminWindow:
    def __init__(self, master):
        ctk.set_appearance_mode("system")
        ctk.set_default_color_theme("blue")

        self.master = master
        self.master.title("Photo Competition Admin")
        self.master.geometry("650x600")
        self.master.resizable(True, True)

        # === DATABASE SETUP ===
        self.db = sqlite3.connect("competition.db")
        self.ensure_tables()

        # === CATEGORY SECTION ===
        self.category_frame = ctk.CTkFrame(master)
        self.category_frame.pack(fill="x", padx=10, pady=(10, 5))

        self.category_label = ctk.CTkLabel(self.category_frame, text="Category Level:")
        self.category_label.pack(anchor="w", padx=5, pady=(0, 2))

        self.selected_category_level = ctk.StringVar(value="Beginner")
        self.category_combobox = ctk.CTkOptionMenu(
            self.category_frame,
            variable=self.selected_category_level,
            values=["Beginner", "Intermediate", "Advanced"],
            command=lambda e: self.refresh_photo_list()
        )
        self.category_combobox.pack(fill="x", padx=5)

        # === PHOTO LIST SECTION ===
        self.photo_frame = ctk.CTkFrame(master)
        self.photo_frame.pack(fill="both", expand=True, padx=10, pady=(5, 10))

        self.photo_listbox = ctk.CTkTextbox(self.photo_frame, height=18)
        self.photo_listbox.pack(side="left", fill="both", expand=True, padx=(0, 5), pady=5)
        self.photo_listbox.configure(state="disabled")

        # For mapping indices to DB IDs
        self.photo_index_map = {}

        self.photo_listbox.bind("<Double-1>", self.on_listbox_double_click)
        self.photo_listbox.bind("<ButtonRelease-1>", self.on_listbox_click)

        # === BUTTON BAR (ADD / REMOVE / RESET) ===
        self.button_bar = ctk.CTkFrame(master)
        self.button_bar.pack(fill="x", padx=10, pady=(0, 10))

        self.add_photo_btn = ctk.CTkButton(
            self.button_bar,
            text="Add Photo",
            width=120,
            command=self.open_add_photo_dialog
        )
        self.add_photo_btn.pack(side="left", padx=(0, 5))

        self.remove_photo_btn = ctk.CTkButton(
            self.button_bar,
            text="Remove Selected",
            width=150,
            command=self.remove_selected_photo
        )
        self.remove_photo_btn.pack(side="left", padx=(0, 5))

        self.reset_data_btn = ctk.CTkButton(
            self.button_bar,
            text="Reset All Photos",
            width=150,
            command=self.reset_all_data
        )
        self.reset_data_btn.pack(side="left", padx=(0, 5))

        self.current_selection = None

        # Populate the listbox initially
        self.refresh_photo_list()

    def ensure_tables(self):
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
        self.photo_listbox.configure(state="normal")
        self.photo_listbox.delete("1.0", "end")
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
            display_text = f"#{idx}: {photo_name} by {photographer} [{category}]\n"
            self.photo_listbox.insert("end", display_text)
            self.photo_index_map[idx - 1] = photo_id

        self.photo_listbox.configure(state="disabled")
        self.current_selection = None

    def get_selected_index(self):
        try:
            index = int(float(self.photo_listbox.index("insert"))) - 1
            if index < 0 or index >= len(self.photo_index_map):
                return None
            return index
        except Exception:
            return None

    def on_listbox_click(self, event):
        # Simulate selection (highlight the line)
        self.photo_listbox.configure(state="normal")
        self.photo_listbox.tag_remove("sel", "1.0", "end")
        index = self.get_selected_index()
        if index is not None:
            line_start = f"{index + 1}.0"
            line_end = f"{index + 1}.end"
            self.photo_listbox.tag_add("sel", line_start, line_end)
            self.photo_listbox.tag_config("sel", background="#2257b6")
            self.current_selection = index
        self.photo_listbox.configure(state="disabled")

    def on_listbox_double_click(self, event):
        index = self.get_selected_index()
        if index is None:
            return
        photo_id = self.photo_index_map.get(index)
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

        win = ctk.CTkToplevel(self.master)
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
            new_size = (int(img_w * ratio), int(img_h * ratio))
            pil_img = pil_img.resize(new_size, Image.LANCZOS)
        else:
            new_size = pil_img.size

        ctk_img = ctk.CTkImage(light_image=pil_img, dark_image=pil_img, size=new_size)
        img_label = ctk.CTkLabel(win, image=ctk_img, text="")
        img_label.image = ctk_img
        img_label.pack(padx=10, pady=10, expand=True)

        info = f"Name: {photo_name}\nPhotographer: {photographer}\nCategory: {category}\nPath: {filepath}"
        ctk.CTkLabel(win, text=info, anchor="w", justify="left").pack(padx=10, pady=(0, 10), fill="x")

        ctk.CTkButton(win, text="Close", command=win.destroy).pack(pady=(0, 15))

    def open_add_photo_dialog(self):
        dialog = ctk.CTkToplevel(self.master)
        dialog.title("Add New Photo")
        dialog.geometry("500x700")
        dialog.resizable(True, True)
        dialog.transient(self.master)
        dialog.grab_set()

        ctk.CTkLabel(dialog, text="Photo Name:").pack(anchor="w", padx=10, pady=(15, 2))
        photo_name_var = ctk.StringVar()
        photo_name_entry = ctk.CTkEntry(dialog, textvariable=photo_name_var, width=400)
        photo_name_entry.pack(padx=10, pady=(0, 10))

        ctk.CTkLabel(dialog, text="Photographer Name:").pack(anchor="w", padx=10, pady=(0, 2))
        photographer_var = ctk.StringVar()
        photographer_entry = ctk.CTkEntry(dialog, textvariable=photographer_var, width=400)
        photographer_entry.pack(padx=10, pady=(0, 10))

        ctk.CTkLabel(dialog, text="Select Photo File:").pack(anchor="w", padx=10, pady=(0, 2))
        file_frame = ctk.CTkFrame(dialog)
        file_frame.pack(fill="x", padx=10, pady=(0, 10))

        selected_filepath_var = ctk.StringVar()
        file_entry = ctk.CTkEntry(
            file_frame,
            textvariable=selected_filepath_var,
            width=300,
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

        browse_btn = ctk.CTkButton(file_frame, text="Browse...", command=browse_file, width=90)
        browse_btn.pack(side="left", padx=(5, 0))

        preview_frame = ctk.CTkFrame(dialog, height=350)
        preview_frame.pack(fill="x", padx=10, pady=(5, 10))
        preview_frame.pack_propagate(False)

        preview_label = ctk.CTkLabel(preview_frame, text="")
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
            rotate_btn.configure(state="normal")

        def display_resized_image(pil_img):
            img_copy = pil_img.copy()
            img_copy.thumbnail((300, 300), Image.LANCZOS)
            ctk_img = ctk.CTkImage(light_image=img_copy, dark_image=img_copy, size=img_copy.size)
            preview_label.configure(image=ctk_img, text="")
            preview_label.image = ctk_img

        def rotate_image():
            if current_pil_image["img"] is None:
                return
            pil_img = current_pil_image["img"].rotate(-90, expand=True)
            current_pil_image["img"] = pil_img
            display_resized_image(pil_img)

        rotate_btn = ctk.CTkButton(dialog, text="Rotate 90°", state="disabled", command=rotate_image)
        rotate_btn.pack(pady=(0, 10))

        button_frame = ctk.CTkFrame(dialog)
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

        add_btn = ctk.CTkButton(button_frame, text="Add Photo", width=120, command=on_add)
        add_btn.pack(side="right", padx=(0, 10))

        cancel_btn = ctk.CTkButton(button_frame, text="Cancel", width=120, command=dialog.destroy)
        cancel_btn.pack(side="right", padx=(10, 0))

        photo_name_entry.focus_set()

    def remove_selected_photo(self):
        index = self.current_selection
        if index is None:
            messagebox.showinfo("No Selection", "Please select a photo to remove.")
            return

        photo_id = self.photo_index_map.get(index)
        if photo_id is None:
            messagebox.showerror("Internal Error", "Unable to map selection to a photo.")
            return

        confirm = messagebox.askyesno("Confirm Deletion", "Are you sure you want to remove the selected photo?")
        if not confirm:
            return

        try:
            cursor = self.db.cursor()
            cursor.execute("SELECT filepath FROM Photos WHERE id = ?", (photo_id,))
            row = cursor.fetchone()
            if row:
                file_path = row[0]
                if os.path.isfile(file_path):
                    try:
                        os.remove(file_path)
                    except Exception as e:
                        messagebox.showwarning("File Delete Error", f"Could not remove file:\n{file_path}\n{e}")

            cursor.execute("DELETE FROM Photos WHERE id = ?", (photo_id,))
            self.db.commit()
            self.refresh_photo_list()
        except sqlite3.Error as e:
            messagebox.showerror("Database Error", f"Failed to remove photo:\n{e}")

    def reset_all_data(self):
        confirm = messagebox.askyesno(
            "Confirm Reset",
            "This will delete ALL photos from the competition. Are you sure?"
        )
        if not confirm:
            return

        try:
            cursor = self.db.cursor()
            cursor.execute("SELECT filepath FROM Photos")
            rows = cursor.fetchall()
            for (file_path,) in rows:
                if os.path.isfile(file_path):
                    try:
                        os.remove(file_path)
                    except Exception as e:
                        print(f"Warning: Could not remove file {file_path}: {e}")

            cursor.execute("DELETE FROM Photos")
            self.db.commit()
            self.refresh_photo_list()
        except sqlite3.Error as e:
            messagebox.showerror("Database Error", f"Failed to reset data:\n{e}")

if __name__ == "__main__":
    ctk.set_appearance_mode("system")
    ctk.set_default_color_theme("blue")
    root = ctk.CTk()
    app = AdminWindow(root)
    root.mainloop()
