import tkinter as tk
from tkinter import ttk, filedialog, simpledialog, messagebox
from PIL import Image, ImageTk
import random

# Store photo entries
photo_entries = []
photo_scores = {}
current_photo = {}

# Create main window
root = tk.Tk()
root.title("Photography Competition Manager")
root.geometry("800x600")

# Image display
img_label = tk.Label(root)
img_label.pack(pady=10)

# Photographer info
info_label = tk.Label(root, text="", font=("Helvetica", 14))
info_label.pack()

# Functions
def add_photo():
    file_path = filedialog.askopenfilename(filetypes=[("Image Files", "*.jpg *.jpeg *.png *.gif")])
    if file_path:
        photographer = simpledialog.askstring("Photographer Name", "Enter photographer's name:")
        if photographer:
            photo_entries.append({"file": file_path, "photographer": photographer})
            messagebox.showinfo("Photo Added", f"Photo added for {photographer}")

def show_random_photo():
    if not photo_entries:
        messagebox.showwarning("No Entries", "No photos available. Please add some.")
        return
    photo = random.choice(photo_entries)
    img = Image.open(photo["file"])
    img = img.resize((500, 400), Image.ANTIALIAS)

    img_tk = ImageTk.PhotoImage(img)
    img_label.configure(image=img_tk)
    img_label.image = img_tk
    info_label.config(text=f"Photographer: {photo['photographer']}")

    current_photo["data"] = photo
    current_photo["image"] = img  # Save PIL image

def rotate_image():
    if "image" not in current_photo or "data" not in current_photo:
        messagebox.showwarning("No Image", "No photo is currently displayed.")
        return

    # Rotate the image
    img = current_photo["image"].rotate(-90, expand=True)
    current_photo["image"] = img

    # Resize and display updated image
    img_resized = img.resize((500, 400), Image.ANTIALIAS)
    img_tk = ImageTk.PhotoImage(img_resized)
    img_label.configure(image=img_tk)
    img_label.image = img_tk

    # Save rotated image back to file (overwrite original)
    try:
        img.save(current_photo["data"]["file"])
        messagebox.showinfo("Saved", "Image rotated and saved.")
    except Exception as e:
        messagebox.showerror("Save Failed", f"Failed to save image:\n{e}")

def submit_score():
    if "data" not in current_photo:
        messagebox.showwarning("No Photo", "Please show a photo first.")
        return
    score = simpledialog.askinteger("Judge Score", "Enter score (0–10):", minvalue=0, maxvalue=10)
    if score is not None:
        file_path = current_photo["data"]["file"]
        photo_scores[file_path] = score
        messagebox.showinfo("Score Recorded", f"Score of {score} recorded.")

def show_all_scores():
    if not photo_scores:
        messagebox.showinfo("Scores", "No scores recorded yet.")
        return
    result = "\n".join(
        f"{entry['photographer']} - Score: {photo_scores.get(entry['file'], 'Not scored')}"
        for entry in photo_entries
    )
    messagebox.showinfo("All Scores", result)

def clear_photo():
    img_label.config(image='')
    img_label.image = None
    info_label.config(text="")
    current_photo.clear()

# Bottom button frame
btn_frame = tk.Frame(root)
btn_frame.pack(side="bottom", pady=20)

# Buttons
tk.Button(btn_frame, text="Add Photo", command=add_photo, width=15).grid(row=0, column=0, padx=10)
tk.Button(btn_frame, text="Show Random Photo", command=show_random_photo, width=15).grid(row=0, column=1, padx=10)
tk.Button(btn_frame, text="Submit Score", command=submit_score, width=15).grid(row=0, column=2, padx=10)
tk.Button(btn_frame, text="Show All Scores", command=show_all_scores, width=15).grid(row=0, column=3, padx=10)
tk.Button(btn_frame, text="Clear Photo", command=clear_photo, width=15).grid(row=0, column=4, padx=10)
tk.Button(btn_frame, text="Rotate Image 90°", command=rotate_image, width=15).grid(row=0, column=5, padx=10)

# Run the application
root.mainloop()
