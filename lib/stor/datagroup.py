import json
import sys
import shutil
import os
from lib.conf.data_modes import *
import lib.conf.env_modes as env
import lib.stor.paths as paths

sys.path.insert(0, paths.get_parent_dir())


def get_input(message, itype, default='', accepted=None, range=None):
    while True:
        t = input(f'{message} (default : {default}) :')
        if t == '':
            if default != '':
                v = default
                break
            else:
                print(f"Input not given and default not set! Try again.")
                continue
        if itype == type:
            if t == 'str':
                v = str
                break
            if t == 'int':
                v = int
                break
            if t == 'float':
                v = float
                break
            if t == 'bool':
                v = bool
                break
            else:
                print("Data type must be one of ['str','int','float','bool']")
        if itype == bool:
            if t in ['n', 'N', 'False', False]:
                v = False
                break
            elif t in ['y', 'Y', 'True', True]:
                v = True
                break
            else:
                print(f"Input must be converted to boolean! Type 'n'/'N' or 'y'/'Y'.")
                continue
        try:
            t = itype(t)
        except:
            print(f"Input must be of type {itype}! Try again.")
            continue
        if accepted is None and range is None:
            v = t
            break
        elif accepted is not None:
            if t in accepted:
                v = t
                break
            else:
                print(f"Input must be one of {accepted}")
                continue
        elif range is not None:
            if range[0] <= t <= range[1]:
                v = t
                break
            else:
                print(f"Input must be within {range}")
                continue
    print(f'Input stored : {v}')
    return v


def setDataConf():
    Npoints = get_input("Enter the number of midline points tracked per larva", itype=int, range=[0, +np.inf],
                        default=12)
    Ncontour = get_input("Enter the number of contour points tracked per larva", itype=int, range=[0, +np.inf],
                         default=22)
    fr = get_input("Enter the framerate of the tracking", itype=float, range=[0, +np.inf], default=16.0)


    data_conf = {'fr': fr,
                 'Npoints': Npoints,
                 'Ncontour': Ncontour}
    return data_conf


def setParConf(N):
    bend_mode = get_input("How is the body bend computed? Enter 1 if computed from angles, 2 if computed from vectors",
                          itype=int, accepted=[1, 2], default=1)
    if bend_mode == 1:
        bend = 'from_angles'
    elif bend_mode == 2:
        bend = 'from_vectors'
    f0 = get_input("Enter midline point where front vector starts", itype=int, range=[1, N - 3], default=1)
    f1 = get_input("Enter midline point where front vector ends", itype=int, range=[f0 + 1, N - 2], default=2)
    r0 = get_input("Enter midline point where rear vector starts", itype=int, range=[f1, N - 1], default=7)
    r1 = get_input("Enter midline point where rear vector ends", itype=int, range=[r0 + 1, N], default=11)
    fr_ratio = get_input("Enter ratio between front and rear vectors", itype=float, range=[0, 1], default=0.5)
    point_idx = get_input("Enter midline point used for linear velocity computation (nan defines centroid)", itype=int,
                          range=[1, +np.inf], default=np.nan)
    use_component_vel = get_input("Use component linear velocity?", itype=bool, default=False)
    scaled_vel_threshold = get_input("Enter scal linear velocity threshold for stride detection", itype=float,
                                     range=[0, +np.inf], default=0.2)
    par_conf = {'bend': bend,
                'front_vector_start': f0,
                'front_vector_stop': f1,
                'rear_vector_start': r0,
                'rear_vector_stop': r1,
                'front_body_ratio': fr_ratio,
                'point_idx': point_idx,
                'use_component_vel': use_component_vel,
                'scaled_vel_threshold': scaled_vel_threshold}
    return par_conf


def setEnrichConf():
    rescale_by = get_input("Rescale xy coordinates by a scalar :", itype=float, default=None)
    drop_collisions = get_input("Drop timesteps where collisions are detected?", itype=bool, default=True)
    filter_f = get_input("Enter cut-off frequency for xy filtering", itype=float, default=2.0)
    interpolate_nans = get_input("Interpolate missing track xy coordinates?", itype=bool, default=False)
    length_and_centroid = get_input("Compute length and centroid?", itype=bool, default=True)
    drop_contour = get_input("Drop contour xy coordinates?", itype=bool, default=False)
    drop_non_simulated_parameters = get_input("Drop parameters not used in simulation?", itype=bool, default=False)
    drop_immobile = get_input("Drop larvae that are immobile during tracking?", itype=bool, default=False)
    ang_analysis = get_input("Perform angular analysis?", itype=bool, default=True)
    lin_analysis = get_input("Perform linear analysis?", itype=bool, default=True)
    N_dispersion_starts = get_input("Enter number of starting timepoints for dispersion computation", itype=int,
                                    range=[1, 10], default=1)
    dispersion_starts = []
    for i in range(N_dispersion_starts):
        dispersion_starts.append(
            get_input(f"Enter starting timepoints for dispersion computation {i} of {N_dispersion_starts}", itype=float,
                      range=[0.0, +np.inf], default=0.0))
    dispersion_starts = list(set(dispersion_starts))
    bout_annotation = []
    for ep in ['turn', 'stride', 'pause']:
        if get_input(f"Detect epochs of {ep}?", itype=bool, default=True):
            bout_annotation.append(ep)
    mode = get_input("Perform minimal or full enrichment?", itype=str, accepted=['full', 'minimal'], default='minimal')

    enrich_config = {'rescale_by': rescale_by,
                     'drop_collisions': drop_collisions,
                     'interpolate_nans': interpolate_nans,
                     'filter_f': filter_f,
                     'length_and_centroid': length_and_centroid,
                     'drop_contour': drop_contour,
                     'drop_unused_pars': drop_non_simulated_parameters,
                     'drop_immobile': drop_immobile,
                     'ang_analysis': ang_analysis,
                     'lin_analysis': lin_analysis,
                     'dispersion_starts': dispersion_starts,
                     'bout_annotation': bout_annotation,
                     'mode': mode}
    return enrich_config


def setConf(id):
    print(f' --- Definition of Configuration : {id} --- ')
    print(f' - Step 1 : Data configuration')
    data_conf = setDataConf()

    print(f' - Step 2 : Raw data configuration')
    Ncols = get_input("Enter sequence of columns in raw data", itype=int, range=[0, +np.inf],
                      default=len(Schleyer_raw_cols))
    read_sequence = []
    for i in range(Ncols):
        read_sequence.append(
            get_input(f"Enter raw column name {i} of {Ncols}", itype=str, default=Schleyer_raw_cols[i]))
    read_metadata = get_input("Read dataset metadata?", itype=bool, default=True)

    print(f' - Step 3 : Enrichment configuration')
    enrich_conf = setEnrichConf()

    print(f' - Step 4 : Parameter configuration')
    if get_input("Use an existing parameter configuration?", itype=bool, default=False):
        par_conf_id = get_input("Enter the id of the parameter configuration to use", itype=str,
                            accepted=list(loadParConfDict().keys()))
    else:
        par_conf_id = get_input("Enter the id of the new parameter configuration", itype=str, default=f'{id}Par')
        par_conf = setParConf(data_conf['Npoints'])
        saveParConf(par_conf, par_conf_id)


    conf = {'id': id,
            'data': data_conf,
            'par': par_conf_id,
            'build': {'read_sequence': read_sequence,
                      'read_metadata': read_metadata},
            'enrich': enrich_conf}
    saveConf(conf)
    return conf


def setDataGroup(id=None):
    if id is None:
        id = get_input("Enter DataGroup id", itype=str)
    print(f' ----- Registration of new DataGroup : {id} ----- ')

    print(f' -- Step 1 : DataGroup Configuration')
    if get_input("Use an existing configuration? ", itype=bool, default=False):
        conf_id = get_input("Enter the id of the DataGroup Configuration to use", itype=str,
                            accepted=list(loadConfDict().keys()))
    else:
        conf_id = get_input("Enter the id of the new DataGroup Configuration", itype=str, default=f'{id}Conf')
        conf = setConf(conf_id)

    print(f' -- Step 2 : DataGroup Path')
    path = get_input("Enter DataGroup relative path", itype=str, default=id)

    print(f' -- Step 3 : DataGroup Arena')
    shape = get_input("Enter arena shape", itype=str, accepted=['circular', 'rectangular'], default='circular')
    if shape == 'circular':
        r = get_input("Enter arena radius in m", itype=float, range=[0, +np.inf], default=0.15)
        arena_pars = env.dish(r)
    elif shape == 'rectangular':
        x = get_input("Enter arena x dimension in m", itype=float, range=[0, +np.inf], default=0.15)
        y = get_input("Enter arena y dimension in m", itype=float, range=[0, +np.inf], default=0.15)
        arena_pars = env.arena(x, y)

    print(f' -- Step 4 : DataGroup Subgroups')
    Nsubgroups = get_input("How many subgroups are there?", itype=int, default=0)
    subgroups = []
    for i in range(Nsubgroups):
        subgroups.append(get_input(f"Set id of subgroup {i} of {Nsubgroups}", itype=str, default=f'subgroup_{i}'))

    DataGroup = {
        'id': id,
        'conf': conf_id,
        'path': path,
        'arena_pars': arena_pars,
        'subgroups': subgroups
    }
    print(f' -- Step 5 : DataGroup additional parameters')
    while get_input("Add additional parameter?", itype=bool, default=False):
        key = get_input("Enter additional parameter name", itype=str)
        itype = get_input(f"Enter data type for {key}", itype=type)
        value = get_input(f"Enter value for {key}", itype=itype)
        DataGroup[key] = value
    saveDataGroup(DataGroup)
    return DataGroup


def loadDataGroup(id):
    try:
        DataGroupDict = loadDataGroupDict()
        DataGroup = DataGroupDict[id]
        return DataGroup
    except:
        raise ValueError(f'DataGroup {id} does not exist')


def loadConf(id):
    try:
        conf_dict = loadConfDict()
        conf = conf_dict[id]
        return conf
    except:
        raise ValueError(f'Configuration {id} does not exist')

def loadParConf(id):
    try:
        conf_dict = loadParConfDict()
        conf = conf_dict[id]
        return conf
    except:
        raise ValueError(f'Parameter configuration {id} does not exist')


def loadConfDict():
    with open(paths.DataConfs_path) as tfp:
        Conf_dict = json.load(tfp)
    return Conf_dict

def loadParConfDict():
    with open(paths.ParConfs_path) as tfp:
        Conf_dict = json.load(tfp)
    return Conf_dict


def loadDataGroupDict():
    with open(paths.DataGroups_path) as tfp:
        DataGroup_dict = json.load(tfp)
    return DataGroup_dict


def saveConfDict(ConfDict):
    with open(paths.DataConfs_path, "w") as fp:
        json.dump(ConfDict, fp)





def saveParConfDict(ConfDict):
    with open(paths.ParConfs_path, "w") as fp:
        json.dump(ConfDict, fp)


def saveDataGroupDict(DataGroupDict):
    with open(paths.DataGroups_path, "w") as fp:
        json.dump(DataGroupDict, fp)


def saveConf(conf):
    try:
        conf_dict = loadConfDict()
    except:
        conf_dict = {}
    id = conf['id']
    conf_dict[id] = conf
    saveConfDict(conf_dict)
    print(f'Configuration saved under the id : {id}')

def saveParConf(conf, id):
    try:
        conf_dict = loadParConfDict()
    except:
        conf_dict = {}
    conf_dict[id] = conf
    saveParConfDict(conf_dict)
    print(f'Parameter configuration saved under the id : {id}')

def saveDataGroup(DataGroup):
    try:
        DataGroup_dict = loadDataGroupDict()
    except:
        DataGroup_dict = {}
    id = DataGroup['id']
    DataGroup_dict[id] = DataGroup
    saveDataGroupDict(DataGroup_dict)
    print(f'DataGroup saved under the id : {id}')


def deleteDataGroup(id):
    DataGroup = loadDataGroup(id)
    path = DataGroup['path']
    try:
        shutil.rmtree(path)
    except:
        pass
    DataGroup_dict = loadDataGroupDict()
    try:
        DataGroup_dict.pop(id, None)
        saveDataGroupDict(DataGroup_dict)
        print(f'Deleted DataGroup under the id : {id}')
    except:
        pass


def deleteConf(id):
    conf_dict = loadConfDict()
    try:
        conf_dict.pop(id, None)
        saveConfDict(conf_dict)
        print(f'Deleted configuration under the id : {id}')
    except:
        pass


def initializeDataGroup(id):
    DataGroup = loadDataGroup(id)
    path = DataGroup['path']
    raw_path = f'{path}/raw'
    processed_path = f'{path}/processed'
    plot_path = f'{path}/plots'
    visuals_path = f'{path}/visuals'
    subgroups = DataGroup['subgroups']
    dirs = [f'{DataFolder}/{i}' for i in [path, raw_path, processed_path, plot_path, visuals_path]]
    for i in dirs:
        if not os.path.exists(i):
            os.makedirs(i)


class LarvaDataGroup:
    def __init__(self, id):
        try:
            temp = loadDataGroup(id)
        except:
            temp = setDataGroup(id)
        self.__dict__.update(temp)
        self.build_dirs()

    def delete(self):
        deleteDataGroup(self.id)

    def build_dirs(self):
        dir = self.get_path()
        self.raw_dir = f'{dir}/raw'
        self.proc_dir = f'{dir}/processed'
        self.plot_dir = f'{dir}/plots'
        self.vis_dir = f'{dir}/visuals'
        self.dirs = [self.raw_dir, self.proc_dir, self.plot_dir, self.vis_dir]
        for i in self.dirs:
            if not os.path.exists(i):
                os.makedirs(i)

    def save(self):
        saveDataGroup(self, self.id)

    def add_subgroup(self, id):
        self.subgroups += [id]
        self.save()
        # self.subgroups+=[id]
        for i in [f'{d}/{id}' for d in self.dirs]:
            if not os.path.exists(i):
                os.makedirs(i)

    def get_dirs(self, subgroup=None, raw_data=False, startswith=None, absolute=True):
        if raw_data:
            dir = self.raw_dir
        else:
            dir = self.proc_dir
        if subgroup is not None:
            dir = f'{dir}/{subgroup}'
        if startswith is None:
            dirs = os.listdir(dir)
        else:
            dirs = [f for f in os.listdir(dir) if f.startswith(startswith)]
        if absolute:
            return [os.path.join(dir, d) for d in dirs]
        else:
            return dirs

    def get_conf(self):
        return loadConf(self.conf)

    def get_par_conf(self):
        return loadParConf(loadConf(self.conf)['par'])

    def get_path(self):
        return f'{DataFolder}/{self.path}'



if __name__ == '__main__':
    saveConf(SchleyerConf)
    saveConf(JovanicConf)
    saveConf(SimConf)
    saveParConf(SchleyerParConf, 'SchleyerParConf')
    saveParConf(JovanicParConf, 'JovanicParConf')
    saveParConf(PaisiosParConf, 'PaisiosParConf')
    saveParConf(SinglepointParConf, 'SinglepointParConf')
    saveParConf(SimParConf, 'SimParConf')
    saveDataGroup(SchleyerGroup)
    saveDataGroup(JovanicGroup)
    saveDataGroup(TestGroup)
    saveDataGroup(SimGroup)

# a=loadDataGroupDict()
# print(list(a.keys()))