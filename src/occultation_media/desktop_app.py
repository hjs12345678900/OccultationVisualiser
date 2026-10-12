"""Event/project actions, independent of localized widget construction."""
from datetime import datetime,timezone
from pathlib import Path
import json
import tkinter as tk
from tkinter import filedialog,messagebox
from .desktop_controls import JobControls
from .desktop_job import start_job
from .gui_config import build_config
from .gui_observer import ObserverDialog,DEFAULTS
from .gui_localization import Localizer
from .gui_event_workspace import build_workspace
from .migrate_desktop_project import migrate_project


class App(JobControls):
    """Shared event fields and independently editable observer inputs."""
    def __init__(self,root):
        self.root=root;self.process=None;self.output=None;self.observers=[]
        self.ui_language=tk.StringVar(value='中文');self.status_key='idle'
        self.labels=[];self.combos=[];self.fields={}
        self.i18n=Localizer(root,self.ui_language)
        build_workspace(self)

    def refresh(self):
        self.tree.delete(*self.tree.get_children())
        for i,o in enumerate(self.observers):
            coordinates=', '.join(o.get(k,'') for k in ('latitude_deg','longitude_deg')).strip(', ')
            self.tree.insert('','end',iid=str(i),text=o['name'],values=(o['mode'],Path(o['curve']).name,coordinates or '—',o['predicted_utc'] or '—'))

    def add_observer(self):
        if len(self.observers)>=8:
            messagebox.showerror(self.tr('stations_title'),'Maximum 8',parent=self.root);return
        def save(values):self.observers.append(values);self.refresh()
        ObserverDialog(self.root,{**DEFAULTS,'name':f'Observer {len(self.observers)+1}'},save,self.ui_language)

    def edit_observer(self):
        selected=self.tree.selection()
        if not selected:return
        index=int(selected[0])
        def save(values):self.observers[index]=values;self.refresh()
        ObserverDialog(self.root,self.observers[index],save,self.ui_language)

    def delete_observer(self):
        selected=self.tree.selection()
        if selected:self.observers.pop(int(selected[0]));self.refresh()

    def save_project(self):
        path=filedialog.asksaveasfilename(parent=self.root,title=self.tr('save_project'),defaultextension='.json',filetypes=[('JSON','*.json')])
        if path:
            data=dict(gui_version=1,ui_language=self.ui_language.get(),event={k:v.get() for k,v in self.fields.items()},observers=self.observers)
            Path(path).write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf-8')

    def load_project(self,path):
        """Load supported historical choices without resetting scientific overrides."""
        data=json.loads(Path(path).read_text(encoding='utf-8'))
        event,observers=migrate_project(data,DEFAULTS)
        for k,v in self.fields.items():v.set(str(event.get(k,v.get())))
        self.observers=observers;self.refresh()
        if data.get('ui_language') in ('中文','English'):self.ui_language.set(data['ui_language'])

    def open_project(self):
        path=filedialog.askopenfilename(parent=self.root,title=self.tr('open_project'),filetypes=[('JSON','*.json')])
        if path:
            try:self.load_project(path)
            except Exception as exc:messagebox.showerror(self.tr('open_project'),str(exc),parent=self.root)

    def start(self,verify_only=False,quality_only=False):
        try:
            self.verify_only=verify_only;self.quality_only=quality_only
            cfg=build_config({k:v.get() for k,v in self.fields.items()},self.observers,quality_only)
            self.output=Path(cfg['output_root'])/datetime.now(timezone.utc).strftime('occultation_%Y%m%d_%H%M%S_%f')
            self.output.mkdir(parents=True)
            config=self.output/'config.json';config.write_text(json.dumps(cfg,ensure_ascii=False,indent=2),encoding='utf-8')
            argv=['--media-config',str(config),'--output-dir',str(self.output/'media')]
            if verify_only:argv.append('--verify-only')
            if quality_only:argv.append('--quality-only')
            self.process=start_job(argv,self.output)
        except Exception as exc:messagebox.showerror(self.tr('cannot_start'),str(exc),parent=self.root);return
        self.begin_poll()

    def show_quality(self):
        path=self.output/'media/quality_report.json' if self.output else None
        if path is None or not path.exists():
            chosen=filedialog.askopenfilename(parent=self.root,title=self.tr('choose_quality'),filetypes=[('JSON','*.json')])
            if not chosen:return
            path=Path(chosen)
        try:
            from .gui_quality import QualityDialog
            QualityDialog(self.root,path,self.ui_language)
        except Exception as exc:messagebox.showerror(self.tr('quality_title'),str(exc),parent=self.root)


def run(smoke=False):
    from tkinterdnd2 import TkinterDnD
    root=TkinterDnD.Tk();App(root)
    if smoke:root.after(1500,root.destroy)
    root.mainloop()
