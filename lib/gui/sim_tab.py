import PySimpleGUI as sg
import numpy as np

import lib.conf.dtype_dicts as dtypes

from lib.aux.collecting import output_keys
from lib.gui.gui_lib import CollapsibleDict, Collapsible, \
    named_bool_button, save_gui_conf, delete_gui_conf, GraphList, graphic_button, t10_kws, col_kws, col_size, t24_kws, \
    t8_kws, \
    t16_kws, t11_kws, t6_kws, t12_kws
from lib.gui.tab import GuiTab, SelectionList
from lib.gui.life_conf import life_conf
from lib.sim.single_run import run_sim
from lib.sim.analysis import sim_analysis
from lib.conf.conf import loadConfDict, loadConf, next_idx


class SimTab(GuiTab):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def build(self):
        l_env = SelectionList(tab=self, conftype='Env', idx=1)
        l_sim = SelectionList(tab=self, conftype='Exp', actions=['load', 'save', 'delete', 'run'], progress=True,
                              sublists={'env_params': l_env})
        self.selectionlists = [l_sim, l_env]
        sim_conf = [[sg.Text('Sim id :', **t8_kws), sg.In('unnamed_sim', key='sim_id', **t16_kws)],
                    [sg.Text('Path :', **t8_kws), sg.In('single_runs', key='path', **t16_kws)],
                    [sg.Text('Duration :', **t8_kws),
                     sg.Spin(values=np.round(np.arange(0.0, 100.1, 0.1), 1).tolist(), initial_value=3.0, key='sim_dur',
                             **t6_kws), sg.Text('minutes', **t8_kws, justification='center')],
                    [sg.Text('Timestep :', **t8_kws),
                     sg.Spin(values=np.round(np.arange(0.01, 1.01, 0.01), 2).tolist(), initial_value=0.1, key='dt',
                             **t6_kws), sg.Text('seconds', **t8_kws, justification='center')],
                    [sg.Text('Sample :', **t11_kws),
                     sg.Combo(list(loadConfDict('Ref').keys()), default_value='reference', key='sample_dataset',
                              enable_events=True, readonly=True,
                              tooltip='The reference dataset to sample parameters from.', **t12_kws)
                     ],
                    named_bool_button('Box2D', False)]
        s1 = Collapsible('Configuration', True, sim_conf)
        output_dict = dict(zip(output_keys, [False] * len(output_keys)))
        s2 = CollapsibleDict('Output', False, dict=output_dict, auto_open=False)
        s3 = CollapsibleDict('Life', False, dict=dtypes.get_dict('life'), type_dict=dtypes.get_dict_dtypes('life'),
                             next_to_header=[graphic_button('edit', 'CONF_LIFE',
                                                            tooltip='Configure the life history of the simulated larvae.')])

        g1 = GraphList(self.name)
        l_conf = [[sg.Col([
            l_sim.l,
            l_env.l,
            *[i.get_section() for i in [s1, s2, s3]],
            [g1.get_layout()]
        ])]]
        l = [[sg.Col(l_conf, **col_kws, size=col_size(0.25)), g1.canvas]]

        c = {}
        for i in [s1, s2, s3]:
            c.update(i.get_subdicts())
        g = {g1.name: g1}
        # print(l)
        d={}
        d['sim_results']={'datasets' : [], 'fig_dict' : None}
        return l, c, g, d

    def run(self, v, w,c,d,g, conf,id):
        for k, v in conf['env_params']['larva_groups'].items():
            if type(v['model']) == str:
                v['model'] = loadConf(v['model'], 'Model')

        N=conf['sim_params']['sim_dur'] * 60 / conf['sim_params']['dt']
        p=self.selectionlists[0].progressbar
        p.run(w, max=N)
        conf['enrich'] = True
        conf['experiment'] = id
        # default_vis = dtypes.get_dict('visualization', mode='video', video_speed=60)
        default_vis=dtypes.get_dict('visualization')
        vis_kwargs = c['Visualization'].get_dict(v, w) if 'Visualization' in list(
            c.keys()) else default_vis
        dd = run_sim(**conf, vis_kwargs=vis_kwargs, progress_bar=w[p.k])
        if dd is not None:
            w[p.k_complete].update(visible=True)
            if 'analysis_data' in d.keys() :
                d['analysis_data'][dd.id] = dd
            if 'DATASET_IDS' in w.AllKeysDict.keys():
                w.Element('DATASET_IDS').Update(values=list(d['analysis_data'].keys()))
            d['sim_results']['datasets'].append(dd)
            fig_dict, results = sim_analysis(dd, conf['experiment'])
            d['sim_results']['fig_dict'] = fig_dict
            g[self.name].update(w, fig_dict)
        else:
            p.reset(w)
        return d,g


    def eval(self, e, v, w, c, d, g):
        if e == 'CONF_LIFE':
            c['Life'].update(w, life_conf())

    def update(self, w,  c, conf, id):
        sim = conf['sim_params']
        output_dict = dict(zip(output_keys, [True if k in conf['collections'] else False for k in output_keys]))
        c['Output'].update(w, output_dict)
        life = conf['life_params'] if 'life_params' in list(conf.keys()) else dtypes.get_dict('life')
        c['Life'].update(w, life)
        w.Element('sim_id').Update(value=f'{id}_{next_idx(id)}')
        w.Element('path').Update(value=f'single_runs/{id}')
        for n in ['sim_dur', 'dt', 'sample_dataset']:
            w.Element(n).Update(value=sim[n])
        w['TOGGLE_Box2D'].set_state(sim['Box2D'])




    def get(self, w, v, c, as_entry=True):
        sim = {
            'sim_id': str(v['sim_id']),
            'sim_dur': float(v['sim_dur']),
            'dt': float(v['dt']),
            'path': str(v['path']),
            'sample_dataset': str(v['sample_dataset']),
            'Box2D': w['TOGGLE_Box2D'].get_state(),
        }
        conf = {
                'sim_params': sim,
                'collections': [k for k in output_keys if c['Output'].get_dict(v, w)[k]],
                'life_params': c['Life'].get_dict(v, w),
                }
        return conf


if __name__ == "__main__":
    from lib.gui.gui import LarvaworldGui

    larvaworld_gui = LarvaworldGui(tabs=['simulation'])
    larvaworld_gui.run()