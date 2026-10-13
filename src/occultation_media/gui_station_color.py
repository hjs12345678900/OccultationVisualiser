"""Optional station color entry, native picker and reset-to-automatic button."""
import tkinter as tk
from tkinter import ttk, colorchooser
from .resolve_station_colors import normalize_color, PALETTE


def color_controls(parent, row, variable, ui):
    """Bind a blank-or-hex field; cancelled picker leaves the value unchanged."""
    ui.label(parent,'station_color').grid(row=row,column=0,sticky='w',pady=3)
    frame=ttk.Frame(parent)
    frame.grid(row=row,column=1,columnspan=3,sticky='ew',pady=3)
    entry=ttk.Entry(frame,textvariable=variable,width=14)
    entry.pack(side='left')
    swatch=tk.Canvas(frame,width=28,height=20,highlightthickness=0)
    swatch.pack(side='left',padx=6)
    status=ttk.Label(frame)

    def choose():
        try:initial=normalize_color(variable.get()) or PALETTE[0]
        except ValueError:initial=PALETTE[0]
        _, selected=colorchooser.askcolor(color=initial,parent=parent.winfo_toplevel(),title=ui.text('choose_color'))
        if selected:variable.set(normalize_color(selected))

    ui.button(frame,'choose_color',command=choose).pack(side='left',padx=3)
    ui.button(frame,'automatic_color',command=lambda:variable.set('')).pack(side='left',padx=3)
    status.pack(side='left',padx=5)

    def refresh(*_):
        try:
            color=normalize_color(variable.get())
            label=ui.text('automatic_color') if not color else color
        except ValueError:
            color='';label=ui.text('invalid_color')
        swatch.delete('all')
        swatch.create_rectangle(1,1,27,19,fill=color or '#D9D9D9',outline='#777777')
        status.configure(text=label)

    trace=variable.trace_add('write',refresh)
    ui.traces.append((variable,trace));ui.callbacks.append(refresh)
    refresh()
    return entry
