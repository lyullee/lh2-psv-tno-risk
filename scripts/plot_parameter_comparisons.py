"""Journal-sized comparative plots for LH2 tank, PSV and TNO sensitivity.

Every plotted quantity is read from the saved simulation ledgers.  Failed
cases are masked; no-release within 6 h and still-open-at-6 h cases carry
distinct symbols.  Run with the bundled Python runtime and matplotlib.
"""
from __future__ import annotations

import csv
import json
from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
import numpy as np


ROOT=Path(__file__).resolve().parent.parent
OUT=ROOT/'paper'/'data'
PLOTS=ROOT/'paper'/'figures'
PLOTS.mkdir(exist_ok=True)

plt.rcParams.update({
    'font.family':'DejaVu Sans','font.size':9,'axes.labelsize':9,
    'axes.titlesize':9,'axes.linewidth':.8,'xtick.labelsize':8,
    'ytick.labelsize':8,'legend.fontsize':7.5,'savefig.dpi':300,
    'pdf.fonttype':42,'svg.fonttype':'none'})
NAVY='#24394C'
TEAL='#327A75'
RUST='#B6613C'
PURPLE='#716387'
GRAY='#687781'
PALE='#E7EBED'
COLORS={.6:NAVY,2.:TEAL,6.:RUST}


def saved(name):
    return json.loads((OUT/name).read_text(encoding='utf-8'))


MAIN=saved('sweep_results.json')
SECOND=saved('secondary_results.json')
RISK={r['case']:r for r in saved('vent_fire_risk_results.json')}


def pick(source,**conditions):
    hits=[r for r in source if all(r.get(k)==v for k,v in conditions.items())]
    if len(hits)!=1:
        raise ValueError(f'expected one case for {conditions}, got {len(hits)}')
    return hits[0]


def save(fig,stem):
    for ext in ('png','pdf','svg'):
        fig.savefig(PLOTS/f'{stem}.{ext}',bbox_inches='tight',pad_inches=.06)
    plt.close(fig)


def panel(ax,title,xlabel=None,ylabel=None):
    ax.set_title(title,loc='left',fontweight='bold',pad=6)
    if xlabel:ax.set_xlabel(xlabel)
    if ylabel:ax.set_ylabel(ylabel)
    ax.spines[['top','right']].set_visible(False)
    ax.grid(axis='y',color=PALE,lw=.55,zorder=0)


def thermal_bore_matrix():
    """Show cumulative release and peak source over the valid thermal range."""
    uas=(.4,.6,.8,2.,6.)
    bores=(4.,6.,10.,18.)
    mass=np.full((len(uas),len(bores)),np.nan)
    peak=mass.copy()
    censored=np.zeros_like(mass,dtype=bool)
    for i,ua in enumerate(uas):
        for j,bore in enumerate(bores):
            c=pick(MAIN,ua_total_W_K=ua,bore_mm=bore)
            if c['status']!='COMPLETED_HORIZON':
                raise ValueError(f'incomplete manuscript case: UA={ua}, bore={bore}')
            mass[i,j]=c['released_kg']
            peak[i,j]=c['peak_rate_kg_s']
            censored[i,j]=c['last_episode_censored']
    fig,axs=plt.subplots(1,2,figsize=(7.05,4.25),layout='constrained')
    for ax,values,cmap,vmax,label in (
        (axs[0],mass,'Blues',70.,'Released by 6 h (kg)'),
        (axs[1],peak,'YlOrBr',.20,'Peak flow (kg s$^{-1}$)')):
        masked=np.ma.masked_invalid(values)
        image=ax.imshow(masked,cmap=cmap,vmin=0,vmax=vmax,aspect='auto')
        ax.set_facecolor('#F1F2F2')
        ax.set_xticks(range(4),[f'{x:g}' for x in bores])
        ax.set_yticks(range(len(uas)),[f'{x:g}' for x in uas])
        ax.set_xlabel('PSV bore (mm)')
        ax.set_ylabel('Tank UA (W K$^{-1}$)')
        ax.set_title(label,loc='left',fontweight='bold',pad=7)
        for i in range(len(uas)):
            for j in range(len(bores)):
                value=values[i,j]
                label_text=(f'{value:.1f}' if values is mass else f'{value:.3f}')
                if censored[i,j] and values is mass: label_text+='†'
                color='white' if value>vmax*.55 else NAVY
                ax.text(j,i,label_text,ha='center',va='center',fontsize=7.5,
                        color=color,fontweight='bold')
        ax.set_xticks(np.arange(-.5,4,1),minor=True)
        ax.set_yticks(np.arange(-.5,len(uas),1),minor=True)
        ax.grid(which='minor',color='white',lw=1.5)
        ax.tick_params(which='minor',bottom=False,left=False)
    fig.text(.5,-.015,'0 = no PSV lift within 6 h; † = still releasing at 6 h.',
             ha='center',fontsize=7.5,color=GRAY)
    save(fig,'thermal_bore_matrix')


def fill_fraction_sensitivity():
    """Compare thermal demand and fill without dropping failed states."""
    fills=(.4,.6,.8)
    uas=(.6,2.,6.)
    fig,axs=plt.subplots(1,3,figsize=(7.05,2.95),layout='constrained')
    for ua in uas:
        lifts=[]
        for fill in fills:
            case=(pick(MAIN,ua_total_W_K=ua,bore_mm=6.) if fill==.6
                  else pick(SECOND,ua_total_W_K=ua,bore_mm=6.,fill_fraction=fill,
                            p_initial_kPa_abs=380.,p_set_kPa_abs=390.,
                            p_reseat_kPa_abs=360.))
            lifts.append(case.get('first_open_s')/3600 if case.get('first_open_s') is not None else np.nan)
        axs[0].plot(fills,lifts,color=COLORS[ua],lw=1.35,marker='o',ms=4,
                    label=f'UA {ua:g}')
    panel(axs[0],'(a) Time to first lift','Fill fraction','First lift (h)')
    axs[0].set_ylim(0,6.5)
    handles,labels=axs[0].get_legend_handles_labels()
    for ax,bore,title in ((axs[1],6.,'(b) 6 mm PSV'),
                          (axs[2],18.,'(c) 18 mm PSV')):
        for ua in uas:
            points=[]
            for fill in fills:
                c=(pick(MAIN,ua_total_W_K=ua,bore_mm=bore) if fill==.6
                   else pick(SECOND,ua_total_W_K=ua,bore_mm=bore,
                             fill_fraction=fill,p_initial_kPa_abs=380.,
                             p_set_kPa_abs=390.,p_reseat_kPa_abs=360.))
                points.append(c)
            xx=[fills[i] for i,c in enumerate(points) if c['status']=='COMPLETED_HORIZON']
            yy=[c['released_kg'] for c in points if c['status']=='COMPLETED_HORIZON']
            ax.plot(xx,yy,color=COLORS[ua],lw=1.35,marker='o',ms=4)
            for fill,c in zip(fills,points):
                if c['status']!='COMPLETED_HORIZON':
                    ax.text(fill,70,'FAIL',ha='center',va='center',
                            color=COLORS[ua],fontsize=7,fontweight='bold')
                elif c['last_episode_censored']:
                    ax.scatter(fill,c['released_kg'],s=48,facecolor='white',
                               edgecolor=COLORS[ua],lw=1.3,zorder=5)
        panel(ax,title,'Fill fraction','Released by 6 h (kg)')
        ax.set_ylim(0,80)
    for ax in axs:ax.set_xticks(fills,['0.4','0.6','0.8'])
    axs[1].legend(handles,labels,frameon=False,loc='upper left')
    fig.text(.5,-.02,'Open circle: release still active at 6 h. FAIL: solver '
             'failure for UA 6, fill 0.8; no mass value is implied.',
             ha='center',fontsize=7,color=GRAY)
    save(fig,'fill_fraction_sensitivity')


def initial_pressure_sensitivity():
    """Initial pressure controls demand timing much more than PSV bore."""
    pressures=(300.,350.,380.)
    fig,axs=plt.subplots(1,3,figsize=(7.05,2.9),layout='constrained')
    for ua in (2.,6.):
        cases=[]
        for p0 in pressures:
            c=(pick(MAIN,ua_total_W_K=ua,bore_mm=6.) if p0==380.
               else pick(SECOND,ua_total_W_K=ua,bore_mm=6.,
                         p_initial_kPa_abs=p0,fill_fraction=.6,
                         p_set_kPa_abs=390.,p_reseat_kPa_abs=360.))
            cases.append(c)
        lift=[c['first_open_s']/3600 if c['first_open_s'] is not None else np.nan
              for c in cases]
        axs[0].plot(pressures,lift,color=COLORS[ua],marker='o',ms=4,
                    lw=1.35,label=f'UA {ua:g}')
        for p0,c in zip(pressures,cases):
            if c['first_open_s'] is None:
                axs[0].scatter(p0,6.2,marker='v',facecolor='white',
                               edgecolor=COLORS[ua],s=45,zorder=5)
        axs[1].plot(pressures,[c['max_pressure_kPa_abs'] for c in cases],
                    color=COLORS[ua],marker='o',ms=4,lw=1.35)
        axs[2].plot(pressures,[c['released_kg'] for c in cases],
                    color=COLORS[ua],marker='o',ms=4,lw=1.35)
    panel(axs[0],'(a) PSV demand','Initial pressure (kPa abs)','First lift (h)')
    axs[0].set_ylim(0,6.7)
    axs[0].legend(frameon=False,loc='upper right')
    panel(axs[1],'(b) Tank pressure','Initial pressure (kPa abs)','Maximum (kPa abs)')
    axs[1].axhline(390,color=GRAY,lw=.8,ls='--')
    panel(axs[2],'(c) Vent burden','Initial pressure (kPa abs)','Released by 6 h (kg)')
    axs[2].set_ylim(0,65)
    for ax in axs:ax.set_xticks(pressures,['300','350','380'])
    fig.text(.5,-.02,'6 mm PSV. Open triangle at 6.2 h denotes no lift within the 6 h horizon.',
             ha='center',fontsize=7,color=GRAY)
    save(fig,'initial_pressure_sensitivity')


def setpoint_time_step_sensitivity():
    """Make the set-pressure tradeoff and short-pulse resolution visible."""
    base20=pick(MAIN,ua_total_W_K=6.,bore_mm=18.)
    base10=saved('ua6_d18_dt10.json')
    checked={int(c['p_set_kPa_abs']):c for c in saved('setpoint_time_step_checks.json')}
    values20=[base20]
    for pset in (430.,470.):
        values20.append(pick(SECOND,ua_total_W_K=6.,bore_mm=18.,
            p_set_kPa_abs=pset,p_reseat_kPa_abs=pset-30.,
            p_initial_kPa_abs=380.,fill_fraction=.6))
    values10=[base10,checked[430],checked[470]]
    x=np.array([390.,430.,470.])
    fig,axs=plt.subplots(1,3,figsize=(7.05,3.0),layout='constrained')
    axs[0].plot(x,[c['max_pressure_kPa_abs'] for c in values20],
                color=NAVY,marker='o',ms=4,lw=1.35)
    panel(axs[0],'(a) Pressure retained','PSV set (kPa abs)','Maximum tank pressure\n(kPa abs)')
    axs[0].set_ylim(380,490)
    for ax,key,ylabel,title in (
        (axs[1],'released_kg','Released by 6 h (kg)','(b) Vent burden'),
        (axs[2],'peak_rate_kg_s','Peak flow (kg s$^{-1}$)','(c) Source intensity')):
        ax.plot(x,[c[key] for c in values20],color=RUST,marker='o',ms=4,
                lw=1.35,label='20 s')
        ax.plot(x,[c[key] for c in values10],color=NAVY,marker='s',ms=4,
                lw=1.1,ls='--',label='10 s')
        panel(ax,title,'PSV set (kPa abs)',ylabel)
    axs[1].legend(frameon=False,loc='upper right')
    for ax in axs:ax.set_xticks(x,['390','430','470'])
    fig.text(.5,-.02,'UA 6 W/K, 18 mm PSV; reseat follows set pressure −30 kPa. '
             'The 430/470 kPa pulse metrics depend on the time step.',
             ha='center',fontsize=7,color=GRAY)
    save(fig,'setpoint_time_step_sensitivity')


def reseat_pressure_sensitivity():
    """Hysteresis controls cumulative venting separately from peak intensity."""
    reseats=(330.,360.,375.)
    fig,axs=plt.subplots(1,3,figsize=(7.05,2.95),layout='constrained')
    for bore,color in ((6.,NAVY),(18.,RUST)):
        cases=[]
        for reseat in reseats:
            c=(pick(MAIN,ua_total_W_K=2.,bore_mm=bore) if reseat==360.
               else pick(SECOND,ua_total_W_K=2.,bore_mm=bore,
                         p_reseat_kPa_abs=reseat,p_set_kPa_abs=390.,
                         fill_fraction=.6,p_initial_kPa_abs=380.))
            cases.append(c)
        for ax,key in zip(axs,('released_kg','total_active_s','peak_rate_kg_s')):
            yy=[c[key]/60 if key=='total_active_s' else c[key] for c in cases]
            ax.plot(reseats,yy,color=color,marker='o',ms=4,lw=1.35,
                    label=f'{bore:g} mm')
        for x,c in zip(reseats,cases):
            if c['episode_count']>1:
                axs[0].annotate(f"{c['episode_count']} lifts",
                    (x,c['released_kg']),xytext=(0,7),textcoords='offset points',
                    ha='center',fontsize=7,color=color)
    panel(axs[0],'(a) Released mass','Reseat (kPa abs)','By 6 h (kg)')
    axs[0].set_ylim(0,78)
    axs[0].legend(frameon=False,loc='upper right')
    panel(axs[1],'(b) PSV open time','Reseat (kPa abs)','Active time (min)')
    panel(axs[2],'(c) Peak release','Reseat (kPa abs)','kg s$^{-1}$')
    for ax in axs:ax.set_xticks(reseats,['330','360','375'])
    fig.text(.5,-.02,'UA 2 W/K; set pressure 390 kPa(abs). Binary PSV model; '
             'these lifts are not mechanical chatter. 20 s time step.',
             ha='center',fontsize=7,color=GRAY)
    save(fig,'reseat_pressure_sensitivity')


def risk_model_sensitivity():
    rows=saved('risk_model_matrix.json')
    fig,axs=plt.subplots(1,2,figsize=(7.05,3.0),layout='constrained')
    bores=[4.,6.,10.,18.]
    for flame,color in (('delichatsios',NAVY),('molkov-conservative',RUST)):
        group=[next(r for r in rows if r['bore_mm']==b and
                    r['flame_model']==flame and r['ignition_scheme']=='HYRAM')
               for b in bores]
        axs[0].plot(bores,[r['fatality_area_given_fire_m2'] for r in group],
                    color=color,marker='o',ms=4,lw=1.35,label=flame.title())
    panel(axs[0],'(a) Consequence model','PSV bore (mm)',
          'Area given jet fire (m$^2$)')
    axs[0].legend(frameon=False,loc='upper left')
    for scheme,color in (('HYRAM',NAVY),('PURPLE',RUST)):
        for flame,style,marker in (('delichatsios','-','o'),
                                    ('molkov-conservative','--','s')):
            group=[next(r for r in rows if r['bore_mm']==b and
                        r['flame_model']==flame and r['ignition_scheme']==scheme)
                   for b in bores]
            axs[1].plot(bores,[r['one_demand_risk_area_m2'] for r in group],
                        color=color,ls=style,marker=marker,ms=3.5,lw=1.25,
                        label=f'{scheme} / {"Delich." if style=="-" else "Molkov"}')
    panel(axs[1],'(b) Ignition × flame model','PSV bore (mm)',
          'One-demand risk-area proxy (m$^2$)')
    axs[1].set_yscale('log')
    handles,labels=axs[1].get_legend_handles_labels()
    fig.legend(handles,labels,frameon=False,loc='lower center',ncol=4,
               bbox_to_anchor=(.5,-.075),columnspacing=1.1,
               handlelength=1.5,fontsize=7)
    for ax in axs:ax.set_xticks(bores,['4','6','10','18'])
    fig.text(.5,-.14,'UA 0.6 W/K; 150 K vent outlet, receptor at 5 m elevation, '
             '20 s exposure. Relative conditional measure, not annual IR.',
             ha='center',fontsize=7,color=GRAY)
    save(fig,'risk_model_sensitivity')


def vent_route_curves():
    with (OUT/'vent_route_curves.csv').open(encoding='utf-8-sig',newline='') as f:
        rows=list(csv.DictReader(f))
    fig,axs=plt.subplots(1,2,figsize=(7.05,3.15),layout='constrained')
    colors={4.:NAVY,6.:TEAL,10.:RUST,18.:PURPLE}
    for bore,color in colors.items():
        group=sorted((r for r in rows if float(r['bore_mm'])==bore and
                      float(r['stack_UA_W_K'])>0),
                     key=lambda r:float(r['stack_UA_W_K']))
        ua=[float(r['stack_UA_W_K']) for r in group]
        axs[0].plot(ua,[float(r['outlet_temperature_K']) for r in group],
                    color=color,lw=1.5,label=f'{bore:g} mm')
        axs[1].plot(ua,[float(r['density_ratio']) for r in group],
                    color=color,lw=1.5)
    panel(axs[0],'(a) Outlet thermalization','Vent-stack UA (W K$^{-1}$)',
          'Outlet temperature (K)')
    axs[0].legend(frameon=False,loc='upper left')
    axs[1].axhspan(0,0.6,color='#DCE9E4',alpha=.55,zorder=-1)
    axs[1].axhspan(.6,1,color='#F6E2D0',alpha=.65,zorder=-1)
    axs[1].axhspan(1,1.08,color='#E4E9EB',alpha=.8,zorder=-1)
    axs[1].axhline(.6,color=GRAY,lw=.75,ls='--')
    axs[1].axhline(1.,color=GRAY,lw=.75,ls='--')
    axs[1].text(.97,.12,'Jet route',transform=axs[1].transAxes,
                ha='right',fontsize=7,color=TEAL)
    axs[1].text(.97,.66,'Uncovered',transform=axs[1].transAxes,
                ha='right',fontsize=7,color=RUST)
    axs[1].text(.97,.94,'Dense route',transform=axs[1].transAxes,
                ha='right',fontsize=7,color=GRAY)
    panel(axs[1],'(b) TNO model boundary','Vent-stack UA (W K$^{-1}$)',
          'H$_2$/air density ratio')
    axs[1].set_ylim(.05,1.08)
    for ax in axs:
        ax.set_xscale('log')
        ax.set_xlim(.05,150)
    fig.text(.5,-.02,'At peak flow from the UA 0.6 W/K tank sweep; '
             'saturated-vapor inlet proxy, thermal-only stack closure.',
             ha='center',fontsize=7,color=GRAY)
    save(fig,'vent_route_curves')


def thermal_risk_separation():
    """Separate risk per opening from the optional repeat-opening assumption."""
    uas=(.6,.8,2.,6.)
    bores=(4.,6.,10.,18.)
    colors={4.:GRAY,6.:NAVY,10.:TEAL,18.:RUST}
    fig,axs=plt.subplots(1,2,figsize=(7.05,3.2),sharey=True,layout='constrained')
    for bore in bores:
        cases=[pick(MAIN,ua_total_W_K=ua,bore_mm=bore) for ua in uas]
        single=[RISK[c['case']]['hyram_single_opportunity_area_m2'] for c in cases]
        multi=[RISK[c['case']]['hyram_independent_openings_area_m2'] for c in cases]
        axs[0].plot(range(len(uas)),single,color=colors[bore],marker='o',
                    ms=4,lw=1.3,label=f'{bore:g} mm')
        axs[1].plot(range(len(uas)),multi,color=colors[bore],marker='o',
                    ms=4,lw=1.3)
        for ax,ys in ((axs[0],single),(axs[1],multi)):
            for i,c in enumerate(cases):
                if c['last_episode_censored']:
                    ax.scatter(i,ys[i],s=55,facecolor='white',edgecolor=colors[bore],
                               lw=1.2,zorder=5)
    panel(axs[0],'(a) One ignition opportunity','Tank UA (W K$^{-1}$)',
          'Conditional risk-area proxy (m$^2$)')
    panel(axs[1],'(b) Independent PSV openings','Tank UA (W K$^{-1}$)')
    axs[0].legend(frameon=False,loc='upper left',ncol=2)
    for ax in axs:
        ax.set_yscale('log')
        ax.set_xticks(range(len(uas)),[f'{x:g}' for x in uas])
        ax.set_ylim(5e-4,.5)
    fig.text(.5,-.02,'150 K outlet and HyRAM direct ignition. Open marker: '
             'still releasing at 6 h. Right panel assumes each lift has a '
             'separate ignition opportunity.',ha='center',fontsize=7,color=GRAY)
    save(fig,'thermal_risk_separation')


def ua_trace_small_multiples():
    """Reveal timing and recurrence instead of compressing traces to maxima."""
    uas=(.4,.6,.8,2.,6.)
    fig,axs=plt.subplots(5,2,figsize=(7.05,5.9),sharex=True,
                         layout='constrained')
    for i,ua in enumerate(uas):
        if ua==.4:
            case=next(c for c in saved('extended_horizon.json') if
                      c['ua_total_W_K']==.4 and c['bore_mm']==6.)
        else:
            case=pick(MAIN,ua_total_W_K=ua,bore_mm=6.)
        with (OUT/f"{case['case']}.csv").open(encoding='utf-8-sig',newline='') as f:
            rows=list(csv.DictReader(f))
        t=np.array([float(r['time_s'])/3600 for r in rows])
        p=np.array([float(r['pressure_kPa_abs']) for r in rows])
        q=np.array([float(r['rate_kg_s']) for r in rows])
        axs[i,0].plot(t,p,color=NAVY,lw=1.1)
        axs[i,1].plot(t,q,color=RUST,lw=1.1)
        axs[i,0].axhline(390,color=GRAY,ls='--',lw=.65)
        axs[i,0].axhline(360,color=GRAY,ls=':',lw=.65)
        axs[i,0].text(.83,.78,f'UA {ua:g}',transform=axs[i,0].transAxes,
                      ha='center',color=NAVY,fontsize=8,fontweight='bold')
        axs[i,0].set_ylim(355,396)
        axs[i,1].set_ylim(-.001,.024)
        for ax in axs[i]:
            ax.set_xlim(0,12)
            ax.spines[['top','right']].set_visible(False)
            ax.grid(axis='y',color=PALE,lw=.45)
            ax.tick_params(labelsize=7)
    axs[0,0].set_title('Tank pressure (kPa abs)',loc='left',fontweight='bold')
    axs[0,1].set_title('PSV rate (kg s$^{-1}$)',loc='left',fontweight='bold')
    axs[-1,0].set_xlabel('Elapsed time (h)')
    axs[-1,1].set_xlabel('Elapsed time (h)')
    fig.text(.5,-.015,'6 mm PSV. UA 0.4 was followed for 12 h; all other rows '
             'end at 6 h. Blank tails are not zero-release predictions.',
             ha='center',fontsize=7,color=GRAY)
    save(fig,'tank_UA_trace_comparison')


if __name__=='__main__':
    thermal_bore_matrix()
    fill_fraction_sensitivity()
    initial_pressure_sensitivity()
    setpoint_time_step_sensitivity()
    reseat_pressure_sensitivity()
    risk_model_sensitivity()
    vent_route_curves()
    thermal_risk_separation()
    ua_trace_small_multiples()
    print('saved 9 comparison figures in',PLOTS)
