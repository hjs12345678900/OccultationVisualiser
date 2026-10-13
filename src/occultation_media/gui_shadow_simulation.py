"""Optional desktop controls for a synchronized nominal-shadow map in exports."""
import tkinter as tk
from .gui_error_text import error_text
from .gui_hover_help import attach_help
from tkinter import ttk, filedialog, messagebox
from .import_prediction_event import prediction_event_fields


def simulation_controls(parent, fields, ui):
    """Add a compact opt-in panel; settings persist with the existing project."""
    fields['shadow_enabled']=tk.StringVar(value='0')
    fields['shadow_prediction_file']=tk.StringVar()
    fields['shadow_xml']=tk.StringVar()
    fields['shadow_view_mode']=tk.StringVar(value='full_path')
    panel=ui.bind(ttk.LabelFrame(parent,padding=7),'shadow_title');panel.pack(fill='x',pady=5)
    row=ttk.Frame(panel);row.pack(fill='x')
    check=ttk.Checkbutton(row,variable=fields['shadow_enabled'],onvalue='1',offvalue='0')
    ui.bind(check,'shadow_enable');check.pack(side='left')
    ui.button(row,'shadow_configure',command=lambda:PredictionDialog(parent,fields,ui)).pack(side='right')
    view=ttk.Frame(panel);view.pack(fill='x',pady=(5,0))
    ui.label(view,'shadow_view').pack(side='left',padx=(0,8))
    attach_help(ui.combo(view,fields['shadow_view_mode'],[('full_path','shadow_view_full'),('follow_shadow','shadow_view_follow')],width=26),ui,'shadow_view').pack(side='left')
    summary=ttk.Label(panel,wraplength=1020);summary.pack(anchor='w',pady=(4,0))
    def refresh(*_):
        file=fields['shadow_prediction_file'].get()
        suffix=file if file else ui.text('shadow_pasted') if fields['shadow_xml'].get().strip() else ui.text('shadow_no_prediction')
        summary.configure(text=ui.text('shadow_help')+' · '+suffix)
    for key in ('shadow_enabled','shadow_prediction_file','shadow_xml'):fields[key].trace_add('write',refresh)
    ui.callbacks.append(refresh);refresh()
    return panel


class PredictionDialog:
    """Import validated event identity and elements, preserving map preference."""
    def __init__(self,parent,fields,ui):
        self.fields,self.ui=fields,ui
        self.window=tk.Toplevel(parent);self.window.title(ui.text('shadow_configure'))
        self.window.transient(parent.winfo_toplevel());self.window.grab_set()
        self.window.geometry('900x540')
        body=ttk.Frame(self.window,padding=12);body.pack(fill='both',expand=True)
        self.file=tk.StringVar(value=fields['shadow_prediction_file'].get())
        ttk.Label(body,text=ui.text('shadow_file')).pack(anchor='w')
        row=ttk.Frame(body);row.pack(fill='x',pady=5)
        attach_help(ttk.Entry(row,textvariable=self.file),ui,'shadow_file').pack(side='left',fill='x',expand=True)
        ttk.Button(row,text=ui.text('browse'),command=self.choose_file).pack(side='left',padx=6)
        ttk.Label(body,text=ui.text('shadow_xml_label')).pack(anchor='w',pady=(6,3))
        self.xml=tk.Text(body,height=14,wrap='word');self.xml.pack(fill='both',expand=True)
        attach_help(self.xml,ui,'shadow_xml_label')
        self.xml.insert('1.0',fields['shadow_xml'].get())
        ttk.Label(body,text=ui.text('shadow_model_help'),wraplength=870).pack(anchor='w',pady=6)
        ttk.Label(body,text=ui.text('prediction_import_help'),wraplength=870).pack(anchor='w',pady=3)
        actions=ttk.Frame(body);actions.pack(fill='x')
        ttk.Button(actions,text=ui.text('cancel'),command=self.window.destroy).pack(side='right')
        ttk.Button(actions,text=ui.text('shadow_save'),command=self.save).pack(side='right',padx=6)

    def choose_file(self):
        file=filedialog.askopenfilename(parent=self.window,filetypes=[('Occult prediction','*.occelmnt *.xml'),('All files','*')])
        if file:
            self.file.set(file);self.xml.delete('1.0','end')

    def save(self):
        values={k:v.get() for k,v in self.fields.items()}
        values.update(shadow_prediction_file=self.file.get().strip(),shadow_xml=self.xml.get('1.0','end').strip())
        try:values.update(prediction_event_fields(values))
        except Exception as exc:
            messagebox.showerror(self.ui.text('shadow_title'),error_text(exc,self.ui.language.get()),parent=self.window);return
        for key in ('event','target','date_utc','shadow_prediction_file','shadow_xml'):self.fields[key].set(values[key])
        self.window.destroy()
