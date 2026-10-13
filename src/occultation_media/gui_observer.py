"""Edit station files and optional overrides without changing observation data."""
from pathlib import Path
import csv
import tkinter as tk
from tkinter import ttk,messagebox
from .gui_path_entry import path_entry
from .gui_localization import Localizer
from .inspect_observer_metadata import inspect_exposure,resolve_native_mode

DEFAULTS=dict(name='Station',observer='',color='',mode='PyMovie / PyOTE',curve='',source='',pyote_result='',
              tracking_csv='',exposure_ms='',exposure_mode='auto',target_column='signal-target',source_first_frame='',
              predicted_utc='',native_mode='auto',mapping_tolerance_s='0.001',source_minus_curve_s='0',
              ser_byte_order='header',D_utc='',R_utc='',target_xy='',fits_hdu='',timing_source_file='',adv_python='',
              latitude_deg='',longitude_deg='',altitude_m='',camera_settings_file='',avi_timestamp_reference='auto')


class ObserverDialog:
    """Separate required files, automatically read metadata, and optional settings."""
    def __init__(self,root,values,on_save,language=None):
        self.window=tk.Toplevel(root);self.window.transient(root);self.window.grab_set()
        self.language=language if language is not None else tk.StringVar(value='中文')
        self.ui=Localizer(self.window,self.language);self.on_save=on_save
        self.values={k:tk.StringVar(value=str(values.get(k,v))) for k,v in DEFAULTS.items()}
        self.metadata=None;self.metadata_error=None;self.pending=None;self.widgets={}
        self.window.geometry('980x760');self.window.minsize(870,700)
        self.book=ttk.Notebook(self.window);self.book.pack(fill='both',expand=True,padx=12,pady=12)
        main=ttk.Frame(self.book,padding=12);location=ttk.Frame(self.book,padding=12);advanced=ttk.Frame(self.book,padding=12)
        self.panels=[main,location,advanced]
        for panel,key in zip(self.panels,('files_tab','location_tab','advanced_tab')):
            self.book.add(panel,text=self.ui.text(key));panel.columnconfigure(1,weight=1)
        self.field(main,0,'name','station_name')
        self.field(main,1,'observer','observer_name')
        from .gui_station_color import color_controls
        self.widgets['color']=color_controls(main,2,self.values['color'],self.ui)
        self.field(main,3,'mode','curve_kind',[('Tangra','Tangra'),('PyMovie / PyOTE','PyMovie / PyOTE')],literal=True)
        for row,key,label in [(4,'curve','curve_input'),(5,'source','source_input'),(6,'pyote_result','pyote_input'),(7,'tracking_csv','tracking_input')]:
            path_entry(main,self.values[key],row,label,ui=self.ui,source=key=='source')
        self.field(main,8,'target_column','target_column')
        self.ui.label(main,'auto_exposure').grid(row=9,column=0,sticky='w',pady=6)
        self.exposure_info=ttk.Label(main,wraplength=540);self.exposure_info.grid(row=9,column=1,columnspan=3,sticky='w')
        self.ui.label(main,'data_mode').grid(row=10,column=0,sticky='w',pady=6)
        self.mode_info=ttk.Label(main,wraplength=540);self.mode_info.grid(row=10,column=1,columnspan=3,sticky='w')
        self.ui.label(main,'file_help',wraplength=875).grid(row=11,column=0,columnspan=4,sticky='w',pady=10)
        self.ui.label(main,'mode_help',wraplength=875).grid(row=12,column=0,columnspan=4,sticky='w',pady=6)
        self.field(main,13,'avi_timestamp_reference','avi_reference',[(v,'avi_'+v) for v in ('auto','start','midpoint','end')])
        for row,key,label in [(0,'latitude_deg','latitude'),(1,'longitude_deg','longitude'),(2,'altitude_m','altitude'),(3,'predicted_utc','prediction')]:self.field(location,row,key,label)
        self.ui.label(location,'location_help',wraplength=875).grid(row=4,column=0,columnspan=4,sticky='w',pady=12)
        choices=[('auto','auto'),('manual','manual_override')]
        self.field(advanced,0,'exposure_mode','exposure_mode',choices)
        self.field(advanced,1,'exposure_ms','exposure_override')
        self.field(advanced,2,'native_mode','data_mode',[(v,'mode_'+v.lower()) for v in ('auto','raw','C3','C4')])
        self.field(advanced,3,'source_first_frame','frame_override')
        self.ui.label(advanced,'frame_help',wraplength=875).grid(row=4,column=0,columnspan=4,sticky='w',pady=6)
        for row,key,label in [(5,'D_utc','d_utc'),(6,'R_utc','r_utc'),(7,'mapping_tolerance_s','tolerance'),(8,'source_minus_curve_s','clock_offset'),(9,'target_xy','target_xy'),(10,'fits_hdu','fits_hdu')]:self.field(advanced,row,key,label)
        self.field(advanced,11,'ser_byte_order','byte_order',[(k,k) for k in ('header','little','big')])
        for row,key,label in [(12,'timing_source_file','timing_report'),(13,'adv_python','adv_python'),(14,'camera_settings_file','camera_settings')]:path_entry(advanced,self.values[key],row,label,ui=self.ui)
        self.ui.label(advanced,'advanced_help',wraplength=875).grid(row=15,column=0,columnspan=4,sticky='w',pady=6)
        buttons=ttk.Frame(self.window);buttons.pack(fill='x',padx=12,pady=8)
        self.ui.button(buttons,'cancel',command=self.window.destroy).pack(side='right')
        self.ui.button(buttons,'save_station',command=self.save).pack(side='right',padx=8)
        for key in ('curve','source','pyote_result','fits_hdu','camera_settings_file','adv_python'):self.values[key].trace_add('write',self.schedule_inspection)
        for key in ('native_mode','exposure_mode','exposure_ms'):self.values[key].trace_add('write',self.refresh_metadata)
        self.ui.callbacks.append(self.translate_dynamic)
        self.window.bind('<Destroy>',self.destroy,add='+')
        self.translate_dynamic();self.schedule_inspection()

    def field(self,parent,row,key,label,choices=None,literal=False):
        self.ui.label(parent,label).grid(row=row,column=0,sticky='w',pady=3)
        if literal:
            widget=ttk.Combobox(parent,textvariable=self.values[key],values=[v for v,_ in choices],state='readonly')
        elif choices:widget=self.ui.combo(parent,self.values[key],choices,width=40)
        else:widget=ttk.Entry(parent,textvariable=self.values[key])
        widget.grid(row=row,column=1,sticky='ew',pady=3);self.widgets[key]=widget

    def schedule_inspection(self,*_):
        if self.pending:self.window.after_cancel(self.pending)
        self.pending=self.window.after(250,self.inspect_files)

    def inspect_files(self):
        """Inspect metadata only after a complete file selection/drop."""
        self.pending=None;values={k:v.get().strip() for k,v in self.values.items()}
        curve=Path(values['curve'])
        try:
            if curve.is_file():
                if curve.suffix.lower()=='.lc':self.values['mode'].set('Tangra')
                elif curve.suffix.lower()=='.csv':
                    with curve.open(encoding='utf-8-sig') as stream:
                        for line in stream:
                            if line.startswith('Tangra '):self.values['mode'].set('Tangra')
                            if line.startswith('FrameNum,'):
                                self.values['mode'].set('PyMovie / PyOTE');columns=next(csv.reader([line]))
                                if values['target_column'] not in columns:
                                    self.values['target_column'].set(next((c for c in columns if c.startswith('signal-')),'signal-target'))
                                break
                            if line.startswith('FrameNo,'):break
            self.metadata=inspect_exposure(values) if values['curve'] or values['source'] else None
            self.metadata_error=None
        except Exception as exc:self.metadata=None;self.metadata_error=str(exc)
        self.refresh_metadata()

    def refresh_metadata(self,*_):
        if self.metadata:self.exposure_info.configure(text=f"{self.metadata['exposure_s']*1000:.6g} ms · {Path(self.metadata['path']).name}")
        else:self.exposure_info.configure(text=self.metadata_error or self.ui.text('metadata_missing' if self.values['curve'].get() else 'metadata_pending'))
        if self.values['exposure_mode'].get()=='manual':
            override=self.ui.text('manual_override')+': '+self.values['exposure_ms'].get()+' ms'
            self.exposure_info.configure(text=(self.exposure_info.cget('text')+' · '+override) if self.metadata else override)
        try:
            mode=resolve_native_mode({k:v.get() for k,v in self.values.items()})
            self.mode_info.configure(text=self.ui.text('mode_'+mode.lower()))
        except Exception as exc:self.mode_info.configure(text=str(exc))
        self.widgets['exposure_ms'].configure(state='normal' if self.values['exposure_mode'].get()=='manual' else 'disabled')

    def translate_dynamic(self):
        self.window.title(self.ui.text('station_editor'))
        for panel,key in zip(self.panels,('files_tab','location_tab','advanced_tab')):self.book.tab(panel,text=self.ui.text(key))
        self.refresh_metadata()

    def destroy(self,event):
        if event.widget is self.window and self.pending:self.window.after_cancel(self.pending);self.pending=None

    def save(self):
        values={k:v.get().strip() for k,v in self.values.items()}
        if not values['name']:
            messagebox.showerror(self.ui.text('station'),self.ui.text('station_name'),parent=self.window);return
        from .resolve_station_colors import normalize_color
        try:values['color']=normalize_color(values['color'])
        except ValueError as exc:
            messagebox.showerror(self.ui.text('station_color'),str(exc),parent=self.window);return
        self.on_save(values);self.window.destroy()
