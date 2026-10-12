"""Translate live widgets while stable model values and job state survive."""
import tkinter as tk
from tkinter import ttk
from .gui_strings import TEXT
from .ui_text import TEXT as LEGACY


def translate(key,language):
    """Resolve a caption key; locales are zh/en or language-picker labels."""
    return (TEXT if key in TEXT else LEGACY)[key][0 if language in ('zh','中文') else 1]


class Localizer:
    """Own one window's bindings and shared-language trace lifetime."""
    def __init__(self,window,language):
        self.window,self.language=window,language
        self.captions=[];self.combos=[];self.callbacks=[];self.traces=[]
        self.lang_trace=language.trace_add('write',self.refresh)
        window.bind('<Destroy>',self.destroy,add='+')

    def text(self,key):return translate(key,self.language.get())

    def bind(self,widget,key):
        self.captions.append((widget,key));widget.configure(text=self.text(key));return widget

    def label(self,parent,key,**kwargs):return self.bind(ttk.Label(parent,**kwargs),key)

    def button(self,parent,key,**kwargs):return self.bind(ttk.Button(parent,**kwargs),key)

    def combo(self,parent,model,options,**kwargs):
        """Map stable saved values to translated options without changing inputs."""
        display=tk.StringVar();widget=ttk.Combobox(parent,textvariable=display,state='readonly',**kwargs)
        def changed(*_):
            widget.configure(values=[self.text(k) for _,k in options])
            display.set(next((self.text(k) for v,k in options if v==model.get()),model.get()))
        def selected(event):
            index=widget.current()
            if index>=0:model.set(options[index][0])
        widget.bind('<<ComboboxSelected>>',selected)
        trace=model.trace_add('write',changed);self.traces.append((model,trace))
        self.combos.append(changed);changed();return widget

    def refresh(self,*_):
        for widget,key in self.captions:widget.configure(text=self.text(key))
        for callback in self.combos+self.callbacks:callback()

    def destroy(self,event):
        if event.widget is not self.window:return
        self.language.trace_remove('write',self.lang_trace)
        for variable,trace in self.traces:variable.trace_remove('write',trace)
