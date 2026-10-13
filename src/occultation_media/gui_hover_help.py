"""Non-modal, keyboard-accessible help cards with window-scoped cleanup."""
import tkinter as tk
from tkinter import ttk
from .gui_input_help import HELP, ALIASES


class HoverHelp:
    """Show translated guidance after a short dwell without taking focus/grabs."""
    def __init__(self, widget, ui, key):
        self.widget, self.ui, self.key = widget, ui, key
        self.pending = None
        self.popup = None
        for event in ('<Enter>', '<FocusIn>'):
            widget.bind(event, self.schedule, add='+')
        for event in ('<Leave>', '<FocusOut>', '<ButtonPress>', '<KeyPress>', '<Escape>', '<Unmap>'):
            widget.bind(event, self.hide, add='+')
        widget.bind('<Destroy>', self.destroy, add='+')
        ui.callbacks.append(self.hide)

    def schedule(self, event=None):
        self.hide()
        self.pending = self.widget.after(550, self.show)

    def show(self):
        self.pending = None
        if not self.widget.winfo_viewable():
            return
        # At most one help card per window, including keyboard focus changes.
        previous = getattr(self.ui, '_active_help', None)
        if previous is not None:
            previous.hide()
        self.ui._active_help = self
        language = self.ui.language.get()
        text = HELP[self.key][0 if language in ('zh', '中文') else 1] if self.key in HELP else self.ui.text(ALIASES[self.key])
        popup = self.popup = tk.Toplevel(self.widget)
        popup.withdraw()
        popup.overrideredirect(True)
        popup.transient(self.widget.winfo_toplevel())
        frame = ttk.Frame(popup, padding=12, relief='solid', borderwidth=1)
        frame.pack(fill='both', expand=True)
        ttk.Label(frame, text=text, wraplength=440, justify='left').pack()
        popup.update_idletasks()
        w, h = popup.winfo_reqwidth(), popup.winfo_reqheight()
        x = self.widget.winfo_rootx()
        y = self.widget.winfo_rooty() + self.widget.winfo_height() + 6
        sw, sh = popup.winfo_screenwidth(), popup.winfo_screenheight()
        if y + h > sh:
            y = self.widget.winfo_rooty() - h - 6
        popup.geometry(f'+{max(0, min(x, sw-w))}+{max(0, min(y, sh-h))}')
        popup.deiconify()
        popup.lift()

    def hide(self, event=None):
        if self.pending is not None:
            self.widget.after_cancel(self.pending)
            self.pending = None
        if self.popup is not None:
            self.popup.destroy()
            self.popup = None

    def destroy(self, event):
        if event.widget is self.widget:
            self.hide()
            if self.hide in self.ui.callbacks:
                self.ui.callbacks.remove(self.hide)
            if getattr(self.ui, '_active_help', None) is self:
                self.ui._active_help = None


def attach_help(widget, ui, key):
    """Attach known guidance once; return the unchanged widget for layout calls."""
    if ui is not None and key in (HELP.keys() | ALIASES.keys()) and not hasattr(widget, '_input_help'):
        widget._input_help = HoverHelp(widget, ui, key)
    return widget
