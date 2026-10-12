"""Complete event and observer workspace; JSON is an optional saved project."""
from datetime import datetime, timezone
from pathlib import Path
import json
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from .desktop_controls import JobControls
from .desktop_job import start_job
from .gui_config import build_config, TIMING_NOTE
from .gui_observer import ObserverDialog, DEFAULTS, path_entry
from .gui_timeline import timeline_controls


class App(JobControls):
    """Shared event fields and independently editable observer inputs."""
    def __init__(self,root):
        self.root=root;self.process=None;self.output=None;self.observers=[]
        self.ui_language=tk.StringVar(value='中文');self.status_key='idle'
        self.labels=[];self.combos=[];self.fields={}
        root.title('OccultationVisualiser');root.geometry('1100x1000');root.minsize(900,920)
        body=ttk.Frame(root,padding=16);body.pack(fill='both',expand=True)
        ttk.Label(body,text='OccultationVisualiser',font=('',22,'bold')).pack(anchor='w')
        ttk.Label(body,text='共同事件 Shared event → 添加观测者 Add observers → 核验 / 生成 Verify / Generate').pack(anchor='w',pady=6)
        event=ttk.LabelFrame(body,text='事件信息 · 所有 observer 共用',padding=10);event.pack(fill='x')
        fields=[('event','小行星 / Event',''),('target','目标星 / Target',''),
                ('date_utc','UTC 日期',datetime.now(timezone.utc).strftime('%Y-%m-%d')),
                ('start_utc','手动开始 / Manual start UTC',''),('end_utc','手动结束 / Manual end UTC',''),
                ('step_s','显示间隔 / Step (s)','0.1')]
        for i,(key,label,default) in enumerate(fields):
            row,col=divmod(i,2);self.fields[key]=tk.StringVar(value=default)
            ttk.Label(event,text=label).grid(row=row,column=col*2,sticky='w',padx=4,pady=4)
            ttk.Entry(event,textvariable=self.fields[key]).grid(row=row,column=col*2+1,sticky='ew',padx=4)
        for c in (1,3):event.columnconfigure(c,weight=1)
        self.fields['language']=tk.StringVar(value='both')
        ttk.Label(event,text='输出语言 / Language').grid(row=3,column=0,sticky='w')
        ttk.Combobox(event,textvariable=self.fields['language'],values=('both','en','zh'),state='readonly').grid(row=3,column=1,sticky='ew')
        timeline_controls(body,self.fields)
        output=ttk.Frame(body);output.pack(fill='x',pady=8);output.columnconfigure(1,weight=1)
        self.fields['output_root']=tk.StringVar()
        path_entry(output,self.fields['output_root'],0,'输出文件夹 / Output',True)
        observers=ttk.LabelFrame(body,text='Observers · 每站独立文件、曝光与 expected time',padding=10);observers.pack(fill='both',expand=True)
        self.tree=ttk.Treeview(observers,columns=('mode','curve','coordinates','expected'),show='tree headings',height=5,selectmode='browse')
        for key,label,width in [('#0','Observer',140),('mode','来源 / Mode',120),('curve','曲线 / Curve',270),('coordinates','Latitude, Longitude (°)',240),('expected','Expected UTC',150)]:
            self.tree.heading(key,text=label);self.tree.column(key,width=width)
        self.tree.pack(fill='both',expand=True);self.tree.bind('<Double-1>',lambda _:self.edit_observer())
        row=ttk.Frame(observers);row.pack(fill='x',pady=6)
        for label,action in [('添加 Add',self.add_observer),('编辑 Edit',self.edit_observer),('删除 Delete',self.delete_observer)]:
            ttk.Button(row,text=label,command=action).pack(side='left',padx=3)
        ttk.Label(body,text=TIMING_NOTE,wraplength=1030).pack(anchor='w',pady=8)
        actions=ttk.Frame(body);actions.pack(fill='x',pady=5)
        self.generate=ttk.Button(actions,text='生成 Generate',command=self.start);self.generate.pack(side='left')
        self.config_generate=ttk.Button(actions,text='仅核验 Verify',command=lambda:self.start(True));self.config_generate.pack(side='left',padx=5)
        ttk.Button(actions,text='保存项目 Save',command=self.save_project).pack(side='left',padx=5)
        ttk.Button(actions,text='打开项目 Open',command=self.open_project).pack(side='left',padx=5)
        self.cancel=ttk.Button(actions,text='取消 Cancel',command=self.stop,state='disabled');self.cancel.pack(side='left')
        from .desktop_job import open_folder
        self.reveal=ttk.Button(actions,text='打开输出 Open output',command=lambda:open_folder(self.output),state='disabled');self.reveal.pack(side='left',padx=5)
        self.status=tk.StringVar(value='添加 observer；可选择或拖入文件。 Add an observer to begin.')
        ttk.Label(body,textvariable=self.status).pack(anchor='w')
        self.progress=ttk.Progressbar(body,mode='indeterminate');self.progress.pack(fill='x',pady=5)
        self.log=tk.Text(body,height=5,wrap='word',state='disabled');self.log.pack(fill='x')
        root.protocol('WM_DELETE_WINDOW',self.close)

    def refresh(self):
        self.tree.delete(*self.tree.get_children())
        for i,o in enumerate(self.observers):
            coordinates=', '.join(o.get(k,'') for k in ('latitude_deg','longitude_deg'))
            self.tree.insert('', 'end',iid=str(i),text=o['name'],values=(o['mode'],Path(o['curve']).name,coordinates,o['predicted_utc']))

    def add_observer(self):
        if len(self.observers)>=8:
            messagebox.showerror('Observers','最多 8 位 / Maximum 8');return
        def save(values):self.observers.append(values);self.refresh()
        ObserverDialog(self.root,{**DEFAULTS,'name':f'Observer {len(self.observers)+1}'},save)

    def edit_observer(self):
        selected=self.tree.selection()
        if not selected:return
        index=int(selected[0])
        def save(values):self.observers[index]=values;self.refresh()
        ObserverDialog(self.root,self.observers[index],save)

    def delete_observer(self):
        selected=self.tree.selection()
        if selected:self.observers.pop(int(selected[0]));self.refresh()

    def save_project(self):
        path=filedialog.asksaveasfilename(defaultextension='.json',filetypes=[('Project JSON','*.json')])
        if path:
            data=dict(gui_version=1,event={k:v.get() for k,v in self.fields.items()},observers=self.observers)
            Path(path).write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf-8')

    def open_project(self):
        path=filedialog.askopenfilename(filetypes=[('Project JSON','*.json')])
        if not path:return
        try:
            data=json.loads(Path(path).read_text(encoding='utf-8'))
            if data.get('gui_version')!=1 or not isinstance(data['observers'],list) or len(data['observers'])>8:
                raise ValueError('Choose a saved GUI project / 请选择 GUI 保存的项目')
            fallback=dict(window_mode='手动 UTC',event_padding_s='10',skip_gaps='保留',
                          playback_mode='真实时间',video_duration_s='60',station_order='输入顺序')
            values={k:str(data['event'].get(k,fallback.get(k,v.get()))) for k,v in self.fields.items()}
            observers=[{k:str(o.get(k,v)) for k,v in DEFAULTS.items()} for o in data['observers']]
            for k,v in values.items():self.fields[k].set(v)
            self.observers=observers;self.refresh()
        except Exception as e:messagebox.showerror('Open project',str(e))

    def start(self,verify_only=False):
        try:
            self.verify_only=verify_only
            cfg=build_config({k:v.get() for k,v in self.fields.items()},self.observers)
            self.output=Path(cfg['output_root'])/datetime.now(timezone.utc).strftime('occultation_%Y%m%d_%H%M%S_%f')
            self.output.mkdir(parents=True)
            config=self.output/'config.json';config.write_text(json.dumps(cfg,ensure_ascii=False,indent=2),encoding='utf-8')
            argv=['--media-config',str(config),'--output-dir',str(self.output/'media')]
            if verify_only:argv.append('--verify-only')
            self.process=start_job(argv,self.output)
        except Exception as e:messagebox.showerror('检查输入 / Check inputs',str(e));return
        self.begin_poll()


def run(smoke=False):
    from tkinterdnd2 import TkinterDnD
    root=TkinterDnD.Tk();App(root)
    if smoke:root.after(1500,root.destroy)
    root.mainloop()
