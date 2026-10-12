"""Desktop job lifecycle and translatable status handling."""
import json
from .ui_text import text
from .desktop_job import cancel_job


class JobControls:

    def tr(self,key):
        return text(key,'zh' if self.ui_language.get()=='中文' else 'en')

    def change_language(self,event=None):
        # Configure existing widgets: input values and running jobs survive.
        for widget,key in self.labels:widget.configure(text=self.tr(key))
        for combo,display,value,options in self.combos:
            combo.configure(values=[self.tr(o) for o in options]);display.set(self.tr(value.get()))
        self.root.title('OccultationVisualiser — '+self.tr('title') if self.ui_language.get()=='中文' else 'OccultationVisualiser')
        self.status.set(self.tr(self.status_key))

    def set_status(self,key):
        self.status_key=key;self.status.set(self.tr(key))

    def begin_poll(self):
        self.generate.config(state='disabled');self.config_generate.config(state='disabled')
        self.quality.config(state='disabled')
        self.cancel.config(state='normal');self.reveal.config(state='normal')
        self.progress.start();self.set_status('running');self.poll()

    def poll(self):
        log=self.output/'run.log'
        if log.exists():
            self.log.config(state='normal');self.log.delete('1.0','end')
            self.log.insert('end',log.read_text(encoding='utf-8',errors='replace')[-12000:]);self.log.see('end');self.log.config(state='disabled')
        if self.process.poll() is None:self.root.after(500,self.poll);return
        self.progress.stop();self.generate.config(state='normal');self.config_generate.config(state='normal');self.cancel.config(state='disabled')
        self.quality.config(state='normal')
        result=self.output/'result.json'
        if result.exists():
            data=json.loads(result.read_text(encoding='utf-8'))
            self.set_status('done' if data['ok'] else 'failed')
            if data['ok'] and getattr(self,'verify_only',False):
                self.status.set('核验完成（未生成动画） / Verification complete (no animation)')
            if data['ok'] and getattr(self,'quality_only',False):
                self.status.set('噪声诊断完成 / Noise diagnostics complete');self.show_quality()
        else:self.set_status('ended')

    def stop(self):
        if self.process:cancel_job(self.process)

    def close(self):
        if self.process and self.process.poll() is None:self.stop()
        self.root.destroy()
