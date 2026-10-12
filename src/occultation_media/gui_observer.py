"""Observer editor with native file selection and drag-and-drop targets."""
from pathlib import Path
import tkinter as tk
from tkinter import ttk, filedialog, messagebox


def path_entry(parent, variable, row, label, directory=False):
    """Attach a path entry accepting one native dropped path, including spaces."""
    ttk.Label(parent,text=label).grid(row=row,column=0,sticky='w',pady=3)
    entry=ttk.Entry(parent,textvariable=variable,width=48)
    entry.grid(row=row,column=1,sticky='ew',pady=3)
    def choose(folder=directory):
        value=filedialog.askdirectory(parent=parent) if folder else filedialog.askopenfilename(parent=parent)
        if value: variable.set(value)
    ttk.Button(parent,text='选择 Browse',command=choose).grid(row=row,column=2,padx=4)
    if label.startswith('影像'):
        ttk.Button(parent,text='FITS 文件夹',command=lambda:choose(True)).grid(row=row,column=3)
    if hasattr(entry,'drop_target_register'):
        entry.drop_target_register('DND_Files')
        def drop(event):
            paths=parent.tk.splitlist(event.data)
            if len(paths)==1: variable.set(paths[0])
            else: messagebox.showerror('选择一个文件', 'Drop one file or one FITS folder at a time.',parent=parent)
        entry.dnd_bind('<<Drop>>',drop)
    return entry


DEFAULTS=dict(name='Observer',mode='PyMovie / PyOTE',curve='',source='',pyote_result='',
              tracking_csv='',exposure_ms='',target_column='signal-target',source_first_frame='0',
              predicted_utc='',native_mode='raw',mapping_tolerance_s='0.001',source_minus_curve_s='0',
              ser_byte_order='header',D_utc='',R_utc='',target_xy='',fits_hdu='',timing_source_file='',adv_python='',
              latitude_deg='',longitude_deg='',altitude_m='',camera_settings_file='')


class ObserverDialog:
    """Edit a copy; cancelling never changes the saved observer."""
    def __init__(self,root,values,on_save):
        self.window=tk.Toplevel(root);self.window.title('编辑 Observer')
        self.window.transient(root);self.window.grab_set()
        self.values={k:tk.StringVar(value=str(values.get(k,v))) for k,v in DEFAULTS.items()}
        self.on_save=on_save
        book=ttk.Notebook(self.window);book.pack(fill='both',expand=True,padx=12,pady=12)
        main=ttk.Frame(book,padding=12);advanced=ttk.Frame(book,padding=12)
        book.add(main,text='文件与观测 Files');book.add(advanced,text='高级 Advanced')
        for panel in (main,advanced): panel.columnconfigure(1,weight=1)
        self.field(main,0,'name','观测者 Observer')
        self.field(main,1,'mode','测光来源',('Tangra','PyMovie / PyOTE'))
        for row,key,label in [(2,'curve','光变曲线 CSV / Tangra LC'),(3,'source','影像 ADV / SER / FITS / RAVF / LC'),
                              (4,'pyote_result','PyOTE 结果 JSON（可选）'),(5,'tracking_csv','原始跟踪 CSV（可选）')]:
            path_entry(main,self.values[key],row,label)
        self.field(main,6,'target_column','PyMovie 目标列 Target column')
        self.field(main,7,'exposure_ms','曝光 Exposure (ms)')
        self.field(main,8,'source_first_frame','源第 0 帧对应帧号 First frame ID')
        self.field(main,9,'predicted_utc','Expected UTC（可选，每站独立）')
        self.field(main,10,'native_mode','PyOTE mode',('raw','C3','C4'))
        self.field(main,11,'latitude_deg','纬度 Latitude (°，北正 / 南负)')
        self.field(main,12,'longitude_deg','经度 Longitude (°，东正 / 西负)')
        self.field(main,13,'altitude_m','海拔 Altitude (m，可选)')
        self.note=ttk.Label(main,wraplength=630);self.note.grid(row=14,column=0,columnspan=4,sticky='w',pady=8)
        for row,(key,label) in enumerate([('mapping_tolerance_s','UTC 核验容差 (s)'),('source_minus_curve_s','已知源减曲线时差 (s)'),
                  ('D_utc','报告 D UTC（可选）'),('R_utc','报告 R UTC（可选）'),('target_xy','目标 X Y（从 0 起，可选）'),('fits_hdu','FITS HDU（可选）')]):
            self.field(advanced,row,key,label)
        self.field(advanced,6,'ser_byte_order','SER 字节序',('header','little','big'))
        path_entry(advanced,self.values['timing_source_file'],7,'定时来源报告（可选）')
        path_entry(advanced,self.values['adv_python'],8,'ADV 解码 Python（可选）')
        path_entry(advanced,self.values['camera_settings_file'],9,'CameraSettings（可选）')
        ttk.Label(advanced,text='容差用于导出舍入精度；请勿用它掩盖未知时间偏移。',wraplength=600).grid(row=10,column=0,columnspan=4,pady=8)
        buttons=ttk.Frame(self.window);buttons.pack(fill='x',padx=12,pady=10)
        ttk.Button(buttons,text='取消 Cancel',command=self.window.destroy).pack(side='right')
        ttk.Button(buttons,text='保存 Observer',command=self.save).pack(side='right',padx=8)
        self.values['mode'].trace_add('write',self.mode_changed);self.mode_changed()
        self.values['curve'].trace_add('write',self.inspect_curve)

    def field(self,parent,row,key,label,choices=None):
        ttk.Label(parent,text=label).grid(row=row,column=0,sticky='w',pady=4)
        widget=ttk.Combobox(parent,textvariable=self.values[key],values=choices,state='readonly') if choices else ttk.Entry(parent,textvariable=self.values[key])
        widget.grid(row=row,column=1,sticky='ew',pady=4)

    def mode_changed(self,*_):
        tangra=self.values['mode'].get()=='Tangra'
        self.note.config(text=('Tangra：选择导出 CSV 或 LC；CSV 使用导出的曝光中点 UTC。LC 影像仅含目标小图。' if tangra else
            'PyMovie：选择原始 CSV；PyOTE 结果为可选，不重新拟合。时标跟随影像源。')+'\n可拖入文件；SER / DATE-OBS 按 SharpCap 曝光开始处理，显示时加半曝光。')

    def inspect_curve(self,*_):
        """Suggest native signal column and first frame without changing a source mapping."""
        try:
            import csv
            path=Path(self.values['curve'].get())
            if path.suffix.lower()!='.csv': return
            with path.open(encoding='utf-8-sig') as stream:
                for line in stream:
                    if line.startswith('FrameNum,'):
                        columns=next(csv.reader([line]))
                        signal=next((c for c in columns if c.startswith('signal-')),None)
                        if signal: self.values['target_column'].set(signal)
                        break
        except (OSError,UnicodeError): pass

    def save(self):
        values={k:v.get().strip() for k,v in self.values.items()}
        if not values['name']:
            messagebox.showerror('Observer','请输入观测者姓名 / Enter a name',parent=self.window);return
        self.on_save(values);self.window.destroy()
