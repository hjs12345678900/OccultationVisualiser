"""Expose independent recording crops, playback, gap and location preferences."""
import tkinter as tk
from .gui_hover_help import attach_help
from tkinter import ttk

DEFAULTS=dict(window_mode='dr',event_padding_s='5',skip_gaps='accelerate',gap_speed='50',
              playback_mode='real_time',video_duration_s='20',station_order='input',start_utc='',end_utc='')


def timeline_controls(parent,fields,ui):
    """Enable start/end only for custom UTC; D/R padding is conditional."""
    panel=ui.bind(ttk.LabelFrame(parent,padding=8),'timeline_title');panel.pack(fill='x',pady=5)
    choices=dict(window_mode=[('full','window_full'),('dr','window_dr'),('manual','window_manual')],
                 skip_gaps=[('accelerate','accelerate'),('skip','skip'),('keep','keep')],playback_mode=[('real_time','real_time'),('fixed_duration','fixed_duration')],
                 station_order=[('path_north_to_south','path_north_south'),('input','input_order'),('north_to_south','north_south')])
    keys=['window_mode','event_padding_s','start_utc','end_utc','skip_gaps','playback_mode','video_duration_s','station_order','gap_speed']
    labels=['window','padding','start','end','gaps','playback','duration','order','gap_speed'];widgets={}
    for i,(key,label) in enumerate(zip(keys,labels)):
        row,col=divmod(i,2);fields[key]=tk.StringVar(value=DEFAULTS[key])
        ui.label(panel,label).grid(row=row,column=col*2,sticky='w',padx=4,pady=3)
        widget=ui.combo(panel,fields[key],choices[key],width=27) if key in choices else ttk.Entry(panel,textvariable=fields[key])
        attach_help(widget,ui,label)
        widget.grid(row=row,column=col*2+1,sticky='ew',padx=4);widgets[key]=widget
    for col in (1,3):panel.columnconfigure(col,weight=1)
    help_label=ttk.Label(panel,wraplength=1000);help_label.grid(row=5,column=0,columnspan=4,sticky='w',pady=4)
    def changed(*_):
        mode=fields['window_mode'].get()
        for key in ('start_utc','end_utc'):widgets[key].configure(state='normal' if mode=='manual' else 'disabled')
        widgets['event_padding_s'].configure(state='normal' if mode=='dr' else 'disabled')
        widgets['video_duration_s'].configure(state='normal' if fields['playback_mode'].get()=='fixed_duration' else 'disabled')
        widgets['gap_speed'].configure(state='normal' if fields['skip_gaps'].get()=='accelerate' else 'disabled')
        help_label.configure(text=ui.text('window_'+mode+'_help'))
    for key in ('window_mode','playback_mode','skip_gaps'):fields[key].trace_add('write',changed)
    ui.callbacks.append(changed);changed()
    ui.label(panel,'timeline_help',wraplength=1000).grid(row=6,column=0,columnspan=4,sticky='w')
    return widgets
