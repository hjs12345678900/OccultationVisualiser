"""Inspect immutable noise reports in the active desktop interface language."""
import json
from pathlib import Path
import tkinter as tk
from tkinter import ttk
from .gui_localization import Localizer
from .render_noise_canvas import draw_pair


def fmt(value,digits=2):
    """Display absent evidence as an em dash, rather than zero."""
    return '—' if value is None else f'{value:.{digits}f}'


def station_details(s,language='en'):
    """Describe separate count statistics and the approximate spatial-noise budget."""
    zh=language in ('zh','中文');p,c,b=s['baseline'],s['context'],s['pixel_budget']
    def word(chinese,english):return chinese if zh else english
    unknown=word('未知','unknown')
    lines=[s['name'],
        f"{word('相机','Camera')}: {c.get('camera',unknown)}    {word('像素合并','Binning')}: {c.get('binning',unknown)}",
        f"{word('记录增益','Recorded gain')}: {c.get('recorded_gain',unknown)} — "+word('不同相机的单位不可直接比较','cross-camera units may differ'),
        f"{word('曝光','Exposure')}: {s['exposure_s']*1000:.3f} ms; {word('孔径半径','Aperture radius')}: {c.get('aperture_radius_pixels',unknown)} px",
        f"{word('保存 SNR','Saved SNR')}: {fmt(s['saved_snr'].get('snr'))}; {word('保护区基线 SNR','Guarded baseline SNR')}: {fmt(p.get('snr'))}",
        f"{word('基线样本','Baseline samples')} n={p['samples']}; B={fmt(p.get('B'))}; σB={fmt(p.get('sigmaB'))} — "+word('保存计数的单位','saved count units'),
        f"{word('线性残差','Linear-residual')} σ={fmt(p.get('linear_residual_sigma'))}; {word('相邻差分','Adjacent-difference')} σ={fmt(p.get('adjacent_difference_sigma'))}",
        word('后两项仅供诊断；相邻差分假设噪声不相关。原始曲线和保存 SNR 不去趋势。','Residuals are separate diagnostics; adjacent differences assume uncorrelated noise. Original curves and saved SNR are not detrended.')]
    if b['available']:
        lines += [f"{word('背景预算','Background estimate')}: σpixel={fmt(b['pixel_sigma_median'])}, N={fmt(b['mask_pixels_median'],0)}, σap≈{fmt(b['aperture_sigma_estimate'])}",
            word('σap = median(σpixel × √N)，假设背景像素独立且有代表性。','σap = median(σpixel × √N); assumes independent representative background pixels.'),
            word('包含天空和探测器噪声；未分离读出噪声，未计源泊松噪声和背景估计误差。','Sky and detector noise are combined; read noise is not isolated. Source shot noise and background-estimator uncertainty are omitted.')]
    else:
        reason=word('没有兼容的原始像素背景/掩膜记录','No compatible raw-pixel background/mask records')
        lines += [word('背景预算不可用：','Background budget unavailable: ')+reason]
    if b['default_mask_samples'] or b['other_mask_samples']:
        default=b.get('default_mask_profile') or {}
        lines += [f"{word('默认掩膜样本','Default-mask samples')}: {b['default_mask_samples']}; {word('其他掩膜','other masks')}: {b['other_mask_samples']}; {word('仅默认掩膜 SNR','default-only SNR')}={fmt(default.get('snr'))}"]
    if s.get('separately_reported_snr'):
        lines += [word('独立报告指标：','Separately reported metric: ')+json.dumps(s['separately_reported_snr'],ensure_ascii=False)]
    return '\n'.join(lines)


class QualityDialog:
    """Select stations/pairs without recalculating or altering their saved reports."""
    def __init__(self,root,path,language=None):
        self.report=json.loads(Path(path).read_text(encoding='utf-8'))
        self.window=tk.Toplevel(root);self.window.geometry('1080x760');self.window.minsize(860,620)
        self.language=language if language is not None else tk.StringVar(value='中文')
        self.ui=Localizer(self.window,self.language)
        body=ttk.Frame(self.window,padding=12);body.pack(fill='both',expand=True)
        self.ui.label(body,'quality_definition').pack(anchor='w')
        self.guard=ttk.Label(body,wraplength=1020);self.guard.pack(anchor='w',pady=4)
        self.tree=ttk.Treeview(body,columns=('saved','direct','scatter','exposure','binning','camera'),show='tree headings',height=4)
        self.headings=[('#0','station',145),('saved','saved_snr',100),('direct','guarded_snr',130),('scatter','scatter',90),('exposure','exposure_ms',105),('binning','binning',80),('camera','camera',150)]
        for i,s in enumerate(self.report['stations']):
            p=s['baseline'];c=s['context']
            self.tree.insert('','end',iid=str(i),text=s['name'],values=(fmt(s['saved_snr'].get('snr')),fmt(p.get('snr')),fmt(p.get('scatter_percent')),fmt(s['exposure_s']*1000,3),c.get('binning','—'),c.get('camera','—')))
        self.tree.pack(fill='x',pady=5)
        details=ttk.Frame(body);details.pack(fill='both',expand=True)
        self.details=tk.Text(details,height=10,wrap='word');self.details.pack(side='left',fill='both',expand=True)
        scrollbar=ttk.Scrollbar(details,command=self.details.yview);scrollbar.pack(side='right',fill='y');self.details.configure(yscrollcommand=scrollbar.set)
        self.tree.bind('<<TreeviewSelect>>',self.select_station)
        row=ttk.Frame(body);row.pack(fill='x',pady=6)
        self.ui.label(row,'quality_pair').pack(side='left')
        self.pair_choice=ttk.Combobox(row,state='readonly',width=60,values=[' ↔ '.join(p['names']) for p in self.report['pairs']]);self.pair_choice.pack(side='left',padx=8)
        self.pair_choice.bind('<<ComboboxSelected>>',self.select_pair)
        self.pair_text=tk.StringVar();ttk.Label(body,textvariable=self.pair_text,wraplength=1020).pack(anchor='w')
        self.canvas=tk.Canvas(body,height=190,background='white',highlightthickness=1);self.canvas.pack(fill='both',expand=True,pady=6)
        self.canvas.bind('<Configure>',self.select_pair)
        self.ui.label(body,'quality_note',wraplength=1020).pack(anchor='w')
        ttk.Label(body,text=str(path),wraplength=1020).pack(anchor='w',pady=4)
        self.tree.selection_set('0')
        if self.report['pairs']:self.pair_choice.current(0)
        self.ui.callbacks.append(self.refresh_language);self.refresh_language()

    def refresh_language(self):
        self.window.title(self.ui.text('quality_title'))
        for key,label,width in self.headings:self.tree.heading(key,text=self.ui.text(label));self.tree.column(key,width=width)
        margin=self.report['diagnostic_margin_s'];zh=self.language.get() in ('zh','中文')
        self.guard.configure(text=(f'排除 D 前 {margin:g} 秒至 R 后 {margin:g} 秒，仅取区间外完整曝光；保留原始曲线和 D/R。' if zh else f'Exclude D−{margin:g}s to R+{margin:g}s; use complete baseline exposures. Original counts and D/R are retained.'))
        self.select_station();self.select_pair()

    def select_station(self,event=None):
        selected=self.tree.selection()
        if not selected:return
        self.details.configure(state='normal');self.details.delete('1.0','end')
        self.details.insert('end',station_details(self.report['stations'][int(selected[0])],self.language.get()));self.details.configure(state='disabled')

    def select_pair(self,event=None):
        index=self.pair_choice.current()
        if index<0:self.pair_text.set(self.ui.text('quality_no_pair'));return
        p=self.report['pairs'][index];zh=self.language.get() in ('zh','中文')
        if not p['available']:
            self.pair_text.set(self.ui.text('quality_no_overlap' if p['reason'].startswith('No shared') else 'quality_no_baseline'))
        else:
            stats=' | '.join(f"{n}: n={s['samples']}, SNR={s['snr']:.2f}, σ/B={s['scatter_percent']:.2f}%" for n,s in zip(p['names'],p['profiles']))
            label='SNR 比值' if zh else 'SNR ratio';exposure='仅曝光差异' if zh else 'Exposure-only'
            assumption='同光子率、光子噪声主导时' if zh else 'equal photon rates, photon noise dominant'
            self.pair_text.set(stats+f"\n{label}={p['snr_ratio']:.2f}; {exposure} √(t1/t2)={p['exposure_only_photon_noise_ratio']:.2f} ({assumption})")
        draw_pair(self.canvas,p,self.language.get())
