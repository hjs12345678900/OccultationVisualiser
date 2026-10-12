"""Native desktop noise inspection, with explicit units and UTC comparisons."""
import json
from pathlib import Path
import tkinter as tk
from tkinter import ttk
from .render_noise_canvas import draw_pair


def fmt(value,digits=2):
    """Display absent numerical evidence as an em dash, rather than zero."""
    return '—' if value is None else f'{value:.{digits}f}'


def station_details(s):
    """Explain separately measured statistics and the approximate pixel budget."""
    p,c,b=s['baseline'],s['context'],s['pixel_budget']
    lines=[s['name'],f"Camera: {c.get('camera','unknown')}    Binning: {c.get('binning','unknown')}",
           f"Recorded gain: {c.get('recorded_gain','unknown')} (相机间单位不能直接比较 / camera units may differ)",
           f"Exposure: {s['exposure_s']*1000:.3f} ms    Aperture radius: {c.get('aperture_radius_pixels','unknown')} px",
           f"保存 SNR / Saved: {fmt(s['saved_snr'].get('snr'))}    保护区基线 SNR / Guarded: {fmt(p.get('snr'))}",
           f"Baseline n={p['samples']}; B={fmt(p.get('B'))}; σB={fmt(p.get('sigmaB'))} (saved count units)",
           f"Linear-residual σ={fmt(p.get('linear_residual_sigma'))}; adjacent-difference σ={fmt(p.get('adjacent_difference_sigma'))}",
           '后两项仅用于诊断；相邻差分假设噪声不相关。原始曲线与 SNR 未去趋势。',
           'Residuals are separate diagnostics; adjacent differences assume uncorrelated noise.']
    if b['available']:
        lines += [f"背景预算 / Background estimate: σpixel={fmt(b['pixel_sigma_median'])}, N={fmt(b['mask_pixels_median'],0)}, σap≈{fmt(b['aperture_sigma_estimate'])}",
                  'σap = median(σpixel × √N); assumes independent representative background pixels.',
                  '含天空与探测器噪声；未分离读出噪声，未计源泊松噪声和背景估计误差。']
    else: lines += ['Background budget: '+b['reason']]
    if b['default_mask_samples'] or b['other_mask_samples']:
        default=b.get('default_mask_profile') or {}
        lines += [f"默认掩膜 / Default: {b['default_mask_samples']}; other: {b['other_mask_samples']}; default-only SNR={fmt(default.get('snr'))}"]
    if s.get('separately_reported_snr'):
        lines += ['独立报告指标 / Separately reported metric: '+json.dumps(s['separately_reported_snr'],ensure_ascii=False)]
    return '\n'.join(lines)


class QualityDialog:
    """Inspect one immutable report; selecting a pair never re-fits the curve."""
    def __init__(self,root,path):
        self.report=json.loads(Path(path).read_text(encoding='utf-8'))
        self.window=tk.Toplevel(root);self.window.title('噪声诊断 · Noise diagnostics')
        self.window.geometry('1080x760');self.window.minsize(860,620)
        body=ttk.Frame(self.window,padding=12);body.pack(fill='both',expand=True)
        ttk.Label(body,text='SNR = B / σB · 每曝光散布；不是平均值误差 / Per-exposure baseline scatter').pack(anchor='w')
        ttk.Label(body,text=f"诊断排除 D−{self.report['diagnostic_margin_s']:g}s 至 R+{self.report['diagnostic_margin_s']:g}s；完整曝光须在区间外。曲线与 D/R 保持原值。",wraplength=1020).pack(anchor='w',pady=4)
        self.tree=ttk.Treeview(body,columns=('saved','direct','scatter','exposure','binning','camera'),show='tree headings',height=4)
        for key,label,width in [('#0','Station',145),('saved','Saved SNR',100),('direct','Guarded SNR',110),('scatter','Scatter %',100),('exposure','Exposure ms',105),('binning','Binning',80),('camera','Camera',150)]:
            self.tree.heading(key,text=label);self.tree.column(key,width=width)
        for i,s in enumerate(self.report['stations']):
            p=s['baseline'];c=s['context']
            self.tree.insert('','end',iid=str(i),text=s['name'],values=(fmt(s['saved_snr'].get('snr')),fmt(p.get('snr')),fmt(p.get('scatter_percent')),fmt(s['exposure_s']*1000,3),c.get('binning','—'),c.get('camera','—')))
        self.tree.pack(fill='x',pady=5)
        self.details=tk.Text(body,height=11,wrap='word');self.details.pack(fill='both',expand=True)
        self.tree.bind('<<TreeviewSelect>>',self.select_station)
        pairrow=ttk.Frame(body);pairrow.pack(fill='x',pady=6)
        ttk.Label(pairrow,text='共同 UTC 比较 / Pair').pack(side='left')
        self.pair_choice=ttk.Combobox(pairrow,state='readonly',width=60,values=[' ↔ '.join(p['names']) for p in self.report['pairs']]);self.pair_choice.pack(side='left',padx=8)
        self.pair_choice.bind('<<ComboboxSelected>>',self.select_pair)
        self.pair_text=tk.StringVar();ttk.Label(body,textvariable=self.pair_text,wraplength=1020).pack(anchor='w')
        self.canvas=tk.Canvas(body,height=190,background='white',highlightthickness=1);self.canvas.pack(fill='both',expand=True,pady=6)
        self.canvas.bind('<Configure>',self.select_pair)
        ttk.Label(body,text='观测与测光质量比较。相机性能需匹配条件及电子标定。 / Camera performance needs matched conditions and electron calibration.',wraplength=1020).pack(anchor='w')
        ttk.Label(body,text=str(path),wraplength=1020).pack(anchor='w',pady=4)
        self.tree.selection_set('0');self.select_station()
        if self.report['pairs']:self.pair_choice.current(0)
        self.select_pair()

    def select_station(self,event=None):
        selected=self.tree.selection()
        if not selected:return
        self.details.configure(state='normal');self.details.delete('1.0','end')
        self.details.insert('end',station_details(self.report['stations'][int(selected[0])]))
        self.details.configure(state='disabled')

    def select_pair(self,event=None):
        index=self.pair_choice.current()
        if index<0:self.pair_text.set('需要至少两站 / At least two stations needed');return
        p=self.report['pairs'][index]
        if not p['available']:self.pair_text.set('无法比较 / Unavailable: '+p['reason'])
        else:
            stats=' | '.join(f"{n}: n={s['samples']}, SNR={s['snr']:.2f}, σ/B={s['scatter_percent']:.2f}%" for n,s in zip(p['names'],p['profiles']))
            self.pair_text.set(stats+f"\nSNR ratio={p['snr_ratio']:.2f}; exposure-only √(t1/t2)={p['exposure_only_photon_noise_ratio']:.2f} (equal photon rates, photon noise dominant)")
        draw_pair(self.canvas,p)
