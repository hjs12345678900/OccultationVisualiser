"""Choose or drop paths, using the active interface language."""
from tkinter import ttk,filedialog,messagebox


def path_entry(parent,variable,row,label,directory=False,ui=None,source=False):
    """Attach one path entry; source inputs additionally accept FITS folders."""
    caption=ui.label(parent,label) if ui else ttk.Label(parent,text=label)
    caption.grid(row=row,column=0,sticky='w',pady=3)
    entry=ttk.Entry(parent,textvariable=variable,width=45);entry.grid(row=row,column=1,sticky='ew',pady=3)
    def choose(folder=directory):
        value=filedialog.askdirectory(parent=parent) if folder else filedialog.askopenfilename(parent=parent)
        if value:variable.set(value)
    button=ui.button(parent,'browse',command=choose) if ui else ttk.Button(parent,text='Browse',command=choose)
    button.grid(row=row,column=2,padx=4)
    if source:
        button=ui.button(parent,'fits_folder',command=lambda:choose(True)) if ui else ttk.Button(parent,text='FITS folder',command=lambda:choose(True))
        button.grid(row=row,column=3)
    if hasattr(entry,'drop_target_register'):
        entry.drop_target_register('DND_Files')
        def drop(event):
            paths=parent.tk.splitlist(event.data)
            if len(paths)==1:variable.set(paths[0])
            else:messagebox.showerror('Input','Choose one file or folder',parent=parent)
        entry.dnd_bind('<<Drop>>',drop)
    return entry
