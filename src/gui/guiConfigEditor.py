import json
import tkinter as tk
import subprocess

from tkinter import filedialog, messagebox


CONFIG_PATH = "config.json"


class ConfigEditor:
    def __init__(self, root):
        self.root = root
        root.title("Config Editor")
        
        with open(CONFIG_PATH, "r") as f:
            self.config = json.load(f)
        
        self.entries = {}
        
        row = 0
        
        for key, value in self.config.items():
            tk.Label(root, text=key).grid(row=row, column=0, sticky="w")
            
            if isinstance(value, bool):
                var = tk.BooleanVar(value=value)
                
                cb = tk.Checkbutton(root, variable=var)
                cb.grid(row=row, column=1, sticky="w")
                
                self.entries[key] = var
            
            elif "path" in key:
                entry = tk.Entry(root, width=40)
                entry.insert(0, value)
                entry.grid(row=row, column=1, sticky="w")
                
                btn = tk.Button(root, text="📁", command=lambda k=key, e=entry: self.browse_path(k, e))
                btn.grid(row=row, column=2)
                
                self.entries[key] = entry
            
            else:
                entry = tk.Entry(root)
                entry.insert(0, str(value))
                entry.grid(row=row, column=1, sticky="w")
                
                self.entries[key] = entry
            
            row += 1
        
        tk.Button(root, text="Save and Run", command=self.save_and_run).grid(row=row, column=0, columnspan=2, pady=10)

    def browse_path(self, key, entry : tk.Entry):
        path = filedialog.askdirectory(title=f"Select folder for {key}")
        
        if path:
            entry.delete(0, tk.END)
            entry.insert(0, path)
    
    def save_and_run(self):
        for key, widget in self.entries.items():
            if isinstance(widget, tk.BooleanVar):
                self.config[key] = widget.get()
            else:
                val = widget.get()
                
                if val.isdigit():
                    self.config[key] = int(val)
                elif val.replace('.', '', 1).isdigit():
                    self.config[key] = float(val)
                else:
                    self.config[key] = val
        
        with open(CONFIG_PATH, "w") as f:
            json.dump(self.config, f, indent=4)
            
        try:
            subprocess.run(["python", "runPipeline.py"], check=True)
        except Exception as e:
            messagebox.showerror("Run Error", f"Error running pipeline:\n{e}")


if __name__ == "__main__":
    root = tk.Tk()
    app = ConfigEditor(root=root)
    root.mainloop()