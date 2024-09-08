from tkinter import *
from PIL import ImageGrab, Image
import os
from tkinter import messagebox
import pyperclip
import threading
import time
import hashlib
import json
from fpdf import FPDF


class MyPDF(FPDF):
    def __init__(self, config, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.config = config

    def header(self):
        """ Header """
        header_config = self.config['header']
        self.set_font(header_config['font'], header_config['style'], header_config['size'])
        self.cell(0, 10, header_config['text'], 0, 1, header_config['align'])

    def footer(self):
        """ Footer """
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.cell(0, 10, f'Page {self.page_no()}', 0, 0, 'C')


class ClipboardApp:
    def __init__(self, root):
        self.root = root
        self.root.geometry("550x450+550+280")
        self.root.configure(background='ivory4')
        self.root.title("Clipboard")
        self.root.resizable(False, False)

        # Load configuration settings from JSON
        self.config = self.load_config()

        # Load icons
        self.clipboard_icon = PhotoImage(file="./asset/clipboard.png")
        self.ClearIcon = PhotoImage(file="./asset/clear.png")
        self.SavePDF = PhotoImage(file="./asset/pdf.png")

        # Create Listbox and scrollbar
        self.listbox = Listbox(self.root, background='ivory4', height=10, width=56)
        self.listbox.grid(row=3, column=0, columnspan=3, padx=5, pady=10, sticky="w")
        self.scrollbar = Scrollbar(self.root)
        self.listbox.config(yscrollcommand=self.scrollbar.set)

        # Logo label using configuration settings
        logo_config = self.config['logo']
        self.logo = Label(
            self.root,
            text=logo_config['text'],
            font=(logo_config['font'], logo_config['size']),
            fg=logo_config['color'],
            background='ivory4'
        )
        self.logo.grid(row=1, column=0, columnspan=2, padx=2, pady=10, sticky="W")

        # Variable for storing selected listbox item
        self.name_var = StringVar()

        # Current Value Label
        self.current_value_label = Label(self.root, text="Current Value:", font=('Papyrus', 17), fg="White",
                                         background='ivory4')
        self.current_value_label.grid(row=2, column=0, padx=5, pady=10, sticky="w")

        # Entry to display the current value
        self.current_value_entry = Entry(self.root, font=('Papyrus', 17), fg="White", background='ivory4',
                                         textvariable=self.name_var)
        self.current_value_entry.grid(row=2, column=1, padx=0, pady=10, sticky="w")

        # Clipboard icon that triggers the copy action
        self.clipboard_label = Label(self.root, image=self.clipboard_icon, background='ivory4')
        self.clipboard_label.grid(row=2, column=1, padx=260, pady=10, sticky="w")
        self.clipboard_label.bind("<Button-1>", self.copy_to_clipboard)

        # List Box Clear
        self.ClearListbox = Label(self.root, image=self.ClearIcon, background='ivory4')
        self.ClearListbox.grid(row=2, column=1, padx=300, pady=10, sticky="w")
        self.ClearListbox.bind("<Button-1>", self.clear)

        # Save in PDF
        self.SavePDfLable = Label(self.root, image=self.SavePDF, background='ivory4')
        self.SavePDfLable.grid(row=2, column=1, padx=340, pady=10, sticky="w")
        self.SavePDfLable.bind("<Button-1>", self.SavePdf)

        # Start clipboard monitoring in a separate thread
        self.stop_event = threading.Event()
        self.thread = threading.Thread(target=self.monitor_clipboard)
        self.thread.daemon = True
        self.thread.start()

        # Initialize the last image hash
        self.last_image_hash = None

    def load_config(self):
        """Load settings from the config.json file."""
        with open('./asset/config.json', 'r', encoding='utf-8') as config_file:
            return json.load(config_file)

    def copy_to_clipboard(self, event):
        """Copy selected listbox item to clipboard."""
        try:
            selected_value = self.listbox.get(self.listbox.curselection()[0])
            self.name_var.set(selected_value)
            self.root.clipboard_clear()
            self.root.clipboard_append(selected_value)
        except IndexError:
            pass

    def SavePdf(self, event=None):
        """Save the current clipboard image or text as a PDF."""
        timestamp = int(time.time() * 1000)  # Ensure timestamp is defined here
        try:
            im = ImageGrab.grabclipboard()
            pdf_config = self.config['pdf_settings']

            # Create the PDF
            pdf = MyPDF(config=self.config, unit='mm', format=pdf_config['page_format'])
            pdf.add_page()

            # PDF text settings
            pdf.set_font(pdf_config['font'], size=pdf_config['font_size'])

            if im is None:
                # Save text from the clipboard if no image is found
                clipboard_text = pyperclip.paste()
                pdf_width = pdf.w - 2 * pdf_config['margin']
                pdf.set_x(pdf_config['margin'])
                pdf.multi_cell(pdf_width, 10, txt=clipboard_text.encode('latin-1', 'replace').decode('latin-1'), align='L', border=0)
            else:
                # Save the image temporarily to include in the PDF
                temp_image_path = f'./Image/temp_image_{timestamp}.png'
                im.save(temp_image_path, 'PNG')

                # Get page dimensions
                page_width = pdf.w - 2 * pdf_config['margin']
                page_height = pdf.h - 2 * pdf_config['margin']

                # Load the image and calculate new dimensions
                with Image.open(temp_image_path) as image:
                    img_width, img_height = image.size
                    scale_factor = min(page_width / img_width, page_height / img_height)
                    new_width = img_width * scale_factor
                    new_height = img_height * scale_factor
                    x_offset = (page_width - new_width) / 2 + pdf_config['margin']
                    y_offset = (page_height - new_height) / 2 + pdf_config['margin']

                    # Add the image to the PDF
                    pdf.image(temp_image_path, x=x_offset, y=y_offset, w=new_width, h=new_height)

                # Remove the temporary image
                if os.path.exists(temp_image_path):
                    os.remove(temp_image_path)

            # Save the PDF
            pdf_filename = f'./PDF/sample_{timestamp}.pdf'
            pdf.output(pdf_filename)
            messagebox.showinfo(title="Success", message=f"PDF saved successfully as {pdf_filename}")

        except Exception as e:
            messagebox.showerror(title="Error", message=f"An error occurred: {str(e)}")

    def clear(self, event=None):
        """Clear all items in the listbox."""
        self.listbox.delete(0, END)
        self.name_var.set(None)

    def add_clipboard(self):
        """Add clipboard content to the listbox if it's not already present."""
        current_clipboard = pyperclip.paste()
        if current_clipboard not in self.listbox.get(0, END):
            self.listbox.insert(END, current_clipboard)

    def monitor_clipboard(self):
        """Continuously monitor the clipboard in a separate thread."""
        previous_clipboard = None
        while not self.stop_event.is_set():
            im = ImageGrab.grabclipboard()
            if im is None:
                current_clipboard = pyperclip.paste()
                if current_clipboard != previous_clipboard:
                    previous_clipboard = current_clipboard
                    self.root.after(0, self.add_clipboard)
            else:
                image_data = im.tobytes()
                current_image_hash = hashlib.md5(image_data).hexdigest()

                # Compare with the last image hash
                if current_image_hash != self.last_image_hash:
                    self.last_image_hash = current_image_hash

            # Check every 0.5 seconds for quick shutdown response
            time.sleep(0.5)

    def on_closing(self):
        """Clean up when closing the application."""
        self.stop_event.set()  # Set the stop event to signal the thread to exit
        self.root.destroy()


if __name__ == "__main__":
    root = Tk()
    app = ClipboardApp(root)
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    root.mainloop()