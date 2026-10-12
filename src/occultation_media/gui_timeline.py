"""Expose event-window, gap, playback and geographic ordering controls."""
import tkinter as tk
from tkinter import ttk

DEFAULTS = dict(window_mode='D/R 周围', event_padding_s='10', skip_gaps='跳过',
                playback_mode='真实时间', video_duration_s='60', station_order='北 → 南')


def timeline_controls(parent, fields):
    """Add editable presentation settings; all saved values are GUI strings."""
    panel=ttk.LabelFrame(parent,text='视频设置 · Timeline / Playback',padding=8)
    panel.pack(fill='x',pady=5)
    choices=dict(window_mode=('D/R 周围','手动 UTC'),skip_gaps=('跳过','保留'),
                 playback_mode=('真实时间','指定时长'),station_order=('北 → 南','输入顺序'))
    labels=dict(window_mode='时间范围 / Window',event_padding_s='D/R 前后各 (s)',
                skip_gaps='站间空档 / Gaps',playback_mode='播放速度 / Playback',
                video_duration_s='视频总时长 / Duration (s)',station_order='站点排序 / Order')
    widgets={}
    for i,(key,default) in enumerate(DEFAULTS.items()):
        row,col=divmod(i,2);fields[key]=tk.StringVar(value=default)
        ttk.Label(panel,text=labels[key]).grid(row=row,column=col*2,sticky='w',padx=4,pady=4)
        widget=(ttk.Combobox(panel,textvariable=fields[key],values=choices[key],state='readonly')
                if key in choices else ttk.Entry(panel,textvariable=fields[key]))
        widget.grid(row=row,column=col*2+1,sticky='ew',padx=4)
        widgets[key]=widget
    for col in (1,3): panel.columnconfigure(col,weight=1)
    def changed(*_):
        widgets['video_duration_s'].config(state='normal' if fields['playback_mode'].get()=='指定时长' else 'disabled')
        widgets['event_padding_s'].config(state='normal' if fields['window_mode'].get()=='D/R 周围' else 'disabled')
    fields['playback_mode'].trace_add('write',changed)
    fields['window_mode'].trace_add('write',changed)
    changed()
    ttk.Label(panel,text='D/R 周围需每站的 PyOTE 结果或 D/R；北→南需纬度、经度。空档跳过不修改 UTC。',wraplength=1030).grid(row=3,column=0,columnspan=4,sticky='w',pady=3)
    return panel
