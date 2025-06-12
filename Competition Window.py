import os
import sqlite3
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from PIL import Image, ImageTk
import random

DB_PATH = 'data/competition.db'
IMAGE_DIR = 'images'

class CompetitionWindow:
    def __init__(self, root):
        self.root = root
        self.root.title("Photography Competition - Judging")
        self.root.geometry("800x600")

        self.db_conn = sqlite3.connect(DB_PATH)
        self.current_photo = None
        self.photo_sequence = []

        self.create_widgets()
        self.load_categories()

    def create_widgets(self):
        frame_top = tk.Frame(self.root)
        frame_top.pack(pady=10)

        tk.Label(frame_top, text="Select Category:").pack(side=tk.LEFT, padx=5)
        self.category_var = tk.StringVar()
        self.category_dropdown = ttk.Combobox(frame_top, textvariable=self.category_var, state="readonly")
        self.category_dropdown.pack(side=tk.LEFT, padx=5)
        tk.Button(frame_top, text="Show Random Photo", command=self.show_random_photo).pack(side=tk.LEFT, padx=5)

        # Image display
        self.image_label = tk.Label(self.root)
        self.image_label.pack(pady=10)

        # Photo number display
        self.photo_number_label = tk.Label(self.root, text="", font=("Helvetica", 16))
        self.photo_number_label.pack(pady=5)

        # Score button
        tk.Button(self.root, text="Submit Score", command=self.submit_score).pack(pady=10)

    def load_categories(self):
        cur = self.db_conn.cursor()
        cur.execute("SELECT name FROM categories")
        categories = [row[0] for row in cur.fetchall()]
        self.category_dropdown['values'] = categories

    def show_random_photo(self):
        category_name = self.category_var.get()
        if not category_name:
            messagebox.showwarning("Select Category", "Please select a category first.")
            return

        cur = self.db_conn.cursor()
        cur.execute("""
            SELECT photos.id, photos.filename 
            FROM photos 
            JOIN categories ON photos.category_id = categories.id 
            WHERE categories.name = ?
        """, (category_name,))
        photos = cur.fetchall()

        if not photos:
            messagebox.showinfo("No Photos", "No photos found in this category.")
            return

        self.photo_sequence = sorted(photos, key=lambda x: x[0])  # Sort by ID for consistent numbering
        self.current_photo = random.choice(self.photo_sequence)
        image_path = os.path.join(IMAGE_DIR, self.current_photo[1])
        image = Image.open(image_path)
        image = image.resize((500, 400), Image.ANTIALIAS)
        photo = ImageTk.PhotoImage(image)
        self.image_label.configure(image=photo)
        self.image_label.image = photo

        # Determine display number based on sequence
        index = self.photo_sequence.index(self.current_photo) + 1
        self.photo_number_label.config(text=f"Photo #{index}")

    def submit_score(self):
        if not self.current_photo:
            messagebox.showwarning("No Photo", "No photo is currently shown.")
            return
        score = simpledialog.askinteger("Judge Score", "Enter score (0-10):", minvalue=0, maxvalue=10)
        if score is None:
            return
        with self.db_conn:
            self.db_conn.execute("INSERT INTO scores (photo_id, score) VALUES (?, ?)",
                                 (self.current_photo[0], score))
        messagebox.showinfo("Score Submitted", f"Score of {score} saved.")
        self.image_label.config(image='')
        self.image_label.image = None
        self.photo_number_label.config(text="")
        self.current_photo = None

if __name__ == "__main__":
    root = tk.Tk()
    app = CompetitionWindow(root)
    root.mainloop()
