"""Lay out the shared event form and its visible language selector."""
from datetime import datetime,timezone
import tkinter as tk
from tkinter import ttk
from .gui_path_entry import path_entry
from .gui_timeline import timeline_controls
from .desktop_job import open_folder
from .record_media_run import version


def build_workspace(app):
    """Bind localized captions to stable application fields and actions."""
    root,ui=app.root,app.i18n
    root.title('OccultationVisualiser '+version());root.geometry('1100x950');root.minsize(920,850)
    body=ttk.Frame(root,padding=14);body.pack(fill='both',expand=True)
    header=ttk.Frame(body);header.pack(fill='x')
    ttk.Label(header,text='OccultationVisualiser',font=('',22,'bold')).pack(side='left')
    switch=ttk.LabelFrame(header,text='界面语言 / UI language',padding=7);switch.pack(side='right')
    app.language_picker=ttk.Combobox(switch,textvariable=app.ui_language,values=('中文','English'),state='readonly',width=12,font=('',13,'bold'))
    app.language_picker.pack();app.language_picker.bind('<<ComboboxSelected>>',app.change_language)
    ui.label(body,'workflow').pack(anchor='w',pady=5)
    event=ui.bind(ttk.LabelFrame(body,padding=8),'event_title');event.pack(fill='x')
    for i,(key,label,default) in enumerate([('event','event_name',''),('target','target_name',''),('date_utc','utc_date',datetime.now(timezone.utc).strftime('%Y-%m-%d')),('step_s','display_step','0.2')]):
        row,col=divmod(i,2);app.fields[key]=tk.StringVar(value=default)
        ui.label(event,label).grid(row=row,column=col*2,sticky='w',padx=4,pady=3)
        ttk.Entry(event,textvariable=app.fields[key]).grid(row=row,column=col*2+1,sticky='ew',padx=4)
    app.fields['language']=tk.StringVar(value='both')
    ui.label(event,'export_language').grid(row=2,column=0,sticky='w',padx=4)
    ui.combo(event,app.fields['language'],[(k,k) for k in ('both','zh','en')]).grid(row=2,column=1,sticky='ew')
    for c in (1,3):event.columnconfigure(c,weight=1)
    ui.label(event,'event_help',wraplength=1000).grid(row=3,column=0,columnspan=4,sticky='w',pady=4)
    app.timeline_widgets=timeline_controls(body,app.fields,ui)
    output=ttk.Frame(body);output.pack(fill='x',pady=6);output.columnconfigure(1,weight=1)
    app.fields['output_root']=tk.StringVar();path_entry(output,app.fields['output_root'],0,'output',True,ui)
    stations=ui.bind(ttk.LabelFrame(body,padding=8),'stations_title');stations.pack(fill='both',expand=True)
    app.tree=ttk.Treeview(stations,columns=('mode','curve','coordinates','expected'),show='tree headings',height=4,selectmode='browse')
    headings=[('#0','station',130),('mode','curve_kind',130),('curve','curve_file',250),('coordinates','coordinates',220),('expected','predicted_col',160)]
    def translated_tree():
        for key,label,width in headings:app.tree.heading(key,text=ui.text(label));app.tree.column(key,width=width)
    ui.callbacks.append(translated_tree);translated_tree()
    app.tree.pack(fill='both',expand=True);app.tree.bind('<Double-1>',lambda _:app.edit_observer())
    row=ttk.Frame(stations);row.pack(fill='x',pady=5)
    for label,action in [('add',app.add_observer),('edit',app.edit_observer),('delete',app.delete_observer)]:ui.button(row,label,command=action).pack(side='left',padx=3)
    app.quality=ui.button(row,'quality',command=lambda:app.start(quality_only=True));app.quality.pack(side='left',padx=8)
    ui.button(row,'view_quality',command=app.show_quality).pack(side='left')
    ui.label(body,'timestamp_note',wraplength=1000).pack(anchor='w',pady=5)
    actions=ttk.Frame(body);actions.pack(fill='x',pady=4)
    app.generate=ui.button(actions,'generate',command=app.start);app.generate.pack(side='left')
    app.config_generate=ui.button(actions,'verify',command=lambda:app.start(True));app.config_generate.pack(side='left',padx=5)
    for key,action in [('save_project',app.save_project),('open_project',app.open_project)]:ui.button(actions,key,command=action).pack(side='left',padx=5)
    app.cancel=ui.button(actions,'cancel',command=app.stop,state='disabled');app.cancel.pack(side='left')
    app.reveal=ui.button(actions,'reveal',command=lambda:open_folder(app.output),state='disabled');app.reveal.pack(side='left',padx=5)
    app.status=tk.StringVar(value=app.tr('idle'));ttk.Label(body,textvariable=app.status).pack(anchor='w')
    ui.callbacks.append(lambda:app.status.set(app.tr(app.status_key)))
    app.progress=ttk.Progressbar(body,mode='indeterminate');app.progress.pack(fill='x',pady=4)
    app.log=tk.Text(body,height=4,wrap='word',state='disabled');app.log.pack(fill='x')
    root.protocol('WM_DELETE_WINDOW',app.close)
