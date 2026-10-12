"""Display brand artwork; observation data and configuration are untouched."""
from pathlib import Path
import tkinter as tk
from tkinter import ttk
from PIL import Image,ImageTk
from .gui_localization import Localizer
from .record_media_run import version


def branding_asset(name):
    """Resolve a required source/frozen-package resource, failing if absent."""
    path=Path(__file__).parent/'assets/branding'/name
    if not path.is_file():raise FileNotFoundError(f'Missing branding resource: {name}')
    return path


def brand_photo(master,name,bounds):
    """Fit unmodified artwork within Tk logical pixels, preserving aspect ratio."""
    with Image.open(branding_asset(name)) as source:
        image=source.copy();image.thumbnail(bounds,Image.Resampling.LANCZOS)
    return ImageTk.PhotoImage(image,master=master)


def set_window_icon(root):
    """Keep the Tk icon alive; packaged native icons are configured separately."""
    root.brand_icon=brand_photo(root,'icon.png',(128,128))
    root.iconphoto(True,root.brand_icon)


class CoverDialog:
    """Show a dismissible cover; startup timeout never delays worker/CLI jobs."""
    def __init__(self,root,language,auto_close_ms=None):
        self.window=tk.Toplevel(root);self.window.transient(root);self.window.resizable(False,False)
        self.ui=Localizer(self.window,language);self.timer=None
        self.photo=brand_photo(self.window,'cover.png',(850,480))
        tk.Label(self.window,image=self.photo,borderwidth=0,background='#050c18').pack()
        footer=ttk.Frame(self.window,padding=10);footer.pack(fill='x')
        ttk.Label(footer,text='OccultationVisualiser '+version()).pack(side='left')
        self.ui.button(footer,'enter_workspace',command=self.close).pack(side='right')
        self.ui.callbacks.append(lambda:self.window.title(self.ui.text('cover_title')))
        self.ui.refresh();self.window.update_idletasks()
        width,height=self.window.winfo_reqwidth(),self.window.winfo_reqheight()
        x=max(0,(root.winfo_screenwidth()-width)//2);y=max(0,(root.winfo_screenheight()-height)//2)
        self.window.geometry(f'{width}x{height}+{x}+{y}')
        self.window.bind('<Escape>',lambda _:self.close())
        self.window.bind('<Button-1>',lambda _:self.close())
        self.window.bind('<Destroy>',self.destroy,add='+')
        self.window.protocol('WM_DELETE_WINDOW',self.close)
        if auto_close_ms:self.timer=self.window.after(auto_close_ms,self.close)

    def close(self):
        self.window.destroy()

    def destroy(self,event):
        if event.widget is self.window and self.timer:
            self.window.after_cancel(self.timer);self.timer=None
