import argparse
import os
import jinja2
import yaml
from yml_to_xml import eigs_xml, perams_xml, meson_xml, chroma_sh_xml, disco_xml
from pydantic import BaseModel
from typing import Dict, Any, List, Optional
import re

PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
FDIR = os.path.dirname(os.path.realpath(__file__))
TEMPLATE = os.path.join(FDIR, 'templates')
RESULTPATH = os.path.join(FDIR, 'res')
OUTPATH = os.path.join(RESULTPATH, 'out')
LOGPATH = os.path.join(RESULTPATH, 'log')

def parse_ensemble(short_tag: str) -> Dict[str, Any]:
    """Parse ensemble short tag to extract parameters.
/p/data1/slnpp/GREGORY/CONFIGS/NF3P1/B3.6/B3.6_M-0.013M0.25_L32T64/NS8_LS1_G2
/p/data1/slnpp/GREGORY/CONFIGS/NF3P1/B3.6/B3.6_M-0.013M0.25_L40T64/NS8_LS1_G2
/p/data1/slnpp/GREGORY/CONFIGS/NF3P1/B3.6/B3.6_M-0.013M0.25_L48T64/NS8_LS1_G2
/p/data1/slnpp/GREGORY/CONFIGS/NF3P1/B3.6/B3.6_M-0.013M0.25_L64T64/NS8_LS1_G2

for beta=3.4
/p/data1/slnpp/GREGORY/CONFIGS/NF3P1/B3.4/B3.4_M-0.040M0.33_L24T64/NS8_LS1_G2/
/p/data1/slnpp/GREGORY/CONFIGS/NF3P1/B3.4/B3.4_M-0.040M0.33_L32T64/NS8_LS1_G2/
/p/data1/slnpp/GREGORY/CONFIGS/NF3P1/B3.4/B3.4_M-0.040M0.33_L36T64/NS8_LS1_G2/
/p/data1/slnpp/GREGORY/CONFIGS/NF3P1/B3.4/B3.4_M-0.040M0.33_L48T64/NS8_LS1_G2/
    
    """
    long_tag = {
        "a065m420": "b3.70_ms-0.000_mud-0.020_s32t96-000",
        "a065m300": "b3.70_ms-0.000_mud-0.025_s40t96-000",
        "a085m420": "b3.57_ms-0.007_mud-0.038_s24t64-000",
        "a085m300": "b3.57_ms-0.007_mud-0.044_s32t64-000",
        "a085m200": "b3.57_ms-0.007_mud-0.048_s48t64-000",
        "a125m400": "b3.30_ms-0.057_mud-0.1200_s16t64-000",
        "a125m330": "b3.30_ms-0.057_mud-0.1233_s24t64-000",
        "a125m280": "b3.30_ms-0.057_mud-0.1265_s24t64-000",
        "b3.6_s32t64": "b3.6_mc0.25_mud-0.013_s32t64",
        "b3.6_s40t64": "b3.6_mc0.25_mud-0.013_s40t64",
        "b3.6_s48t64": "b3.6_mc0.25_mud-0.013_s48t64",
        "b3.6_s64t64": "b3.6_mc0.25_mud-0.013_s64t64",
        "b3.4_s24t64": "b3.4_mc0.33_mud-0.040_s24t64",
        "b3.4_s32t64": "b3.4_mc0.33_mud-0.040_s32t64",
        "b3.4_s36t64": "b3.4_mc0.33_mud-0.040_s36t64",
        "b3.4_s48t64": "b3.4_mc0.33_mud-0.040_s48t64",
    }
    
    if short_tag not in long_tag:
        raise ValueError(f"Unknown ensemble short tag: {short_tag}")

    key = long_tag[short_tag]
    patterns = [
    r"b(?P<beta>[0-9]+\.[0-9]+)_ms(?P<ms>-?[0-9]+\.[0-9]+)_mud-(?P<mud>[0-9]+\.[0-9]+)_s(?P<NL>[0-9]+)t(?P<NT>[0-9]+)-(?P<P>[0-9]{3})",

    r"b(?P<beta>[0-9]+\.[0-9]+)"
        r"_mc(?P<mc>[0-9]+\.[0-9]{2})"
        r"_mud-(?P<mud>[0-9]+\.[0-9]{3})"
        r"_s(?P<NL>[0-9]{2})"
        r"t(?P<NT>[0-9]{2})",
    ]
    
    type_map = {
        "beta": str,
        "ms": str,
        "mud": str,
        "mc": str,
        "NL": int,
        "NT": int,
        "P": str,
    }

    info = {}
    for pattern in patterns:
        match = re.match(pattern, key)
        if match:
            groups = match.groupdict()
            info = {
                key: type_map[key](val)
                for key, val in groups.items()
                if key in type_map and val is not None
            }
            break
    
    # Derive cfg_path, cfg_name, and run_path
    if info['mc'] is not None:
        info["cfg_path"] = f"/p/data1/slnpp/GREGORY/CONFIGS/NF3P1/B{info['beta']}/B{info['beta']}_M-{info['mud']}M{info['mc']}_L{info['NL']}T{info['NT']}/NS8_LS1_G2"
        info["cfg_name"] = f"test_b{info['beta']}_m{info['mud']}m{info['mc']}_l{info['NL']}t{info['NT']}_nf3p1_cfg_"
        #info["run_path"] = f"/p/scratch/exflash/su3-distillation-juwels/{short_tag}"
    else:

        info["cfg_path"] = f"/p/project1/exotichadrons/pederiva/6stout/beta_{info['beta']}/ms_{info['ms']}/mud_-{info['mud']}/s{info['NL']}t{info['NT']}/cnfg/"
        info["cfg_name"] = f"b{info['beta']}_ms{info['ms']}_mud-{info['mud']}_s{info['NL']}t{info['NT']}-{info['P']}-n_cfg_"
        #info["run_path"] = f"/p/scratch/exotichadrons/exolaunch/{short_tag}"
    
    return info

class ChromaOptions(BaseModel):
    """Chroma run options for launching jobs."""
    # Slurm job options
    code_dir: str
    account: str 
    num_gpu: int
    max_moms_per_job: int
    facility: str 
    eigs_path: str 
    partition: str 
    
    # Ensemble properties
    cfg_i: int
    cfg_f: int
    cfg_d: int  # cfg step size
    
    # Eigs options
    num_iter: int
    num_orthog: int
    eigs_tasks_node: int 
    eigs_slurm_nodes: int
    eigs_chroma_geometry: List[int]
    eigs_chroma_minutes: int
    
    # Peram options
    prop_slurm_nodes: int
    prop_num_gpu: int
    prop_chroma_geometry: List[int]
    prop_chroma_minutes: int
    prop_mass_charm_label: str
    prop_t_sources: str
    num_tsrcs: int
    prop_t_back: int
    prop_nvec: int
    prop_zphases: str
    prop_clov_coeff: float
    rho: float
    precision: str
    max_iter: int
    
    # Meson options
    meson_slurm_nodes: int
    meson_chroma_max_tslices_in_contraction: int
    meson_nvec: int
    meson_chroma_geometry: List[int]
    meson_chroma_minutes: int
    meson_chroma_parts: int
    meson_zphases: str
    meson_t_back: int
    
    # Distillation basis
    Frequency: int
    max_nvec: int
    num_vecs: int
    num_vecs_perams: int
    decay_dir: int
    t_start: int
    Nt_backward: int
    num_tries: int
    max_rhs: int
    phase: List[int]
    write_fingerprint: bool
    LinkSmearingType: str
    link_smear_fact: float
    link_smear_num: int
    no_smear_dir: int
    gauge_id: str
    colorvec_out: str

class TaskHandler:
    def __init__(self, env):
        self.templates = {
            'eigs': env.get_template('eigs_eric.jinja.xml'),
            'peram_clover': env.get_template('peram_clover.jinja.xml'),
            'peram_charm_clover': env.get_template('peram_charm_clover.jinja.xml'),
            'peram_mg': env.get_template('peram_multigrid_eric.jinja.xml'),
            'peram_strange_mg': env.get_template('peram_strange_multigrid.jinja.xml'),
            'peram_charm_mg': env.get_template('peram_charm_multigrid_eric.jinja.xml'),
            'peram': env.get_template('peram_multigrid.jinja.xml'),
            'meson': env.get_template('meson_eric.jinja.xml'),
            'disco': env.get_template('disco.jinja.xml'),
            'chroma_eigs': env.get_template('eigs.sh.j2'),
            'chroma_peram': env.get_template('peram_jureca.sh.j2'),
            'chroma_peram_mg': env.get_template('peram_juwels.sh.j2'),
            'chroma_peram_charm_mg': env.get_template('peram_charm_juwels.sh.j2'),
            'chroma_peram_clover': env.get_template('peram_clover.sh.j2'),
            'chroma_peram_charm_clover': env.get_template('peram_charm_clover.sh.j2'),
            'chroma_meson': env.get_template('meson_juwels.sh.j2'),
            'chroma_meson_jureca': env.get_template('meson_jureca.sh.j2'),

            'chroma_disco': env.get_template('disco.sh.j2')
        }
        self.xml_classes = {
            'eigs': eigs_xml.Eigs,
            'peram': perams_xml.Perams,
            'peram_mg': perams_xml.Perams,
            'peram_strange_mg': perams_xml.Perams,
            'peram_charm_mg': perams_xml.Perams,
            'peram_charm_mg_eric': perams_xml.Perams,
            'peram_clover': perams_xml.Perams,
            'peram_charm_clover': perams_xml.Perams,
            'meson': meson_xml.Meson,
            'disco': disco_xml.Disco,
            'chroma_eigs': ChromaOptions,
            'chroma_meson': ChromaOptions,
            'chroma_meson_jureca': ChromaOptions,

            'chroma_peram': ChromaOptions,
            'chroma_peram_mg': ChromaOptions,
            'chroma_peram_charm_mg': ChromaOptions,
            'chroma_peram_clover': ChromaOptions,
            'chroma_peram_charm_clover': ChromaOptions,
            'chroma_disco': ChromaOptions,
        }

def process_yaml_file(yaml_file, options, env, handler):
    """Process a single YAML file to generate XML and shell scripts."""
    ens_short = os.path.splitext(os.path.basename(yaml_file))[0]
    print(f"Processing ensemble: {ens_short}")
    
    with open(yaml_file) as f:
        dataMap = yaml.safe_load(f)
    
    # Derive ensemble parameters
    try:
        ens_props = parse_ensemble(ens_short)
    except ValueError as e:
        print(f"Error parsing ensemble {ens_short}: {e}")
        raise
    
    dataMap.update(ens_props)  # Add derived parameters (beta, ms, mud, cfg_path, cfg_name, run_path, etc.)
    dataMap['ens_short'] = ens_short
    dataMap['Nt_forward'] = ens_props['NT']
    dataMap['prop_t_fwd'] = ens_props['NT']
    dataMap['meson_t_fwd'] = ens_props['NT']
    dataMap['NL'] = ens_props['NL']
    dataMap['num_vecs_perams'] = ens_props['NT']
    dataMap['meson_nvec'] = ens_props['NT']
    
    # Define additional directories to create in run_path
    additional_dirs = ['eigs_sdb', 'perams_sdb', 'meson_sdb', 'chroma_out','perams_charm_sdb']
    
    # Create run_path and additional directories
    # if dataMap['facility']== 'juwels': 
    #     run_path = f'/p/scratch/exflash/{ens_short}'
    # else:
    #     run_path = dataMap['run_path']
    # print(f"Attempting to create directories in run_path: {run_path}")
    
    # Ensure run_path exists
    run_path = dataMap['run_path']
    try:
        os.makedirs(run_path, exist_ok=True)
        print(f"Ensured base run_path exists: {run_path}")
    except Exception as e:
        print(f"Error creating run_path {run_path}: {e}")
        raise
    
    # Create additional directories
    for dir_name in additional_dirs:
        dir_path = os.path.join(run_path, dir_name)
        try:
            os.makedirs(dir_path, exist_ok=True)
            if os.path.exists(dir_path):
                print(f"Directory exists or was created: {dir_path}")
            else:
                print(f"Failed to create directory: {dir_path}")
        except Exception as e:
            print(f"Error creating directory {dir_path}: {e}")
            raise

    run_objects = []
    for task in options.list_tasks:
        if 'eigs' == task:
            run_objects.extend(['eigs', 'chroma_eigs'])
        elif 'peram_mg' == task:
            run_objects.extend(['peram_mg', 'chroma_peram_mg'])
        elif 'peram_charm_mg' == task:
            run_objects.extend(['peram_charm_mg', 'chroma_peram_charm_mg'])
        elif 'peram_charm_mg_eric' == task:
            run_objects.extend(['peram_charm_mg_eric', 'chroma_peram_charm_mg'])
        elif 'peram_clover' == task:
            run_objects.extend(['peram_clover', 'chroma_peram_clover'])
        elif 'peram_charm_clover' == task:
            run_objects.extend(['peram_charm_clover', 'chroma_peram_charm_clover'])
        elif 'peram' == task:
            run_objects.extend(['peram', 'chroma_peram'])
        elif 'meson' == task:
            run_objects.extend(['meson', 'chroma_meson'])
        elif 'disco' == task:
            run_objects.extend(['disco', 'chroma_disco'])

    # Remove duplicates while preserving order
    run_objects = list(dict.fromkeys(run_objects))
    cfg_i = dataMap['cfg_i']
    cfg_f = dataMap['cfg_f']
    cfg_step = dataMap['cfg_d']


    for cfg_id in range(cfg_i, cfg_f, cfg_step):
        print(f'Creating scripts for configuration {cfg_id} from {yaml_file}')
        
        for obj in run_objects:
            # Determine task-specific subdirectory
            if obj in ['eigs', 'chroma_eigs']:
                task_dir = 'ini-eigs'
            elif obj in ['peram_mg','chroma_peram_mg']:
                task_dir = 'ini-perams'
            elif obj in ['peram_charm_mg','chroma_peram_charm_mg']:
                task_dir = 'ini-perams-charm'
            elif obj in ['meson', 'chroma_meson']:
                task_dir = 'ini-meson'
            elif obj in ['disco', 'chroma_disco']:
                task_dir = 'ini-disco'
            else:
                task_dir = 'ini-other'

            # Create directory structure: run_path/task_dir/cnfg{cfg_id}
            obj_dir = os.path.join(dataMap['run_path'], task_dir, f'cnfg{cfg_id:02d}')
            try:
                os.makedirs(obj_dir, exist_ok=True)
                print(f"Ensured task directory exists: {obj_dir}")
            except Exception as e:
                print(f"Error creating task directory {obj_dir}: {e}")
                raise

            # Determine output file name
            if obj in ['chroma_eigs', 'chroma_disco']:
                ini_out = f'{obj.split("_")[1]}_cfg{cfg_id:02d}.sh'
            elif obj != 'chroma_eigs' and obj.startswith('chroma'):
                ini_out = f'{obj.split("_")[1]}_cfg{cfg_id:02d}.sh'
            elif obj == 'peram_charm_mg':
                ini_out = f'peram_charm_mg_cfg{cfg_id:02d}.ini.xml'
            elif obj in ['disco', 'eigs']:
                ini_out = f'{obj}_cfg{cfg_id:02d}.ini.xml'
            else:
                ini_out = f'{obj}_cfg{cfg_id:02d}.ini.xml'

            ini_out_path = os.path.join(obj_dir, ini_out)

            if os.path.exists(ini_out_path) and not options.overwrite:
                print(f"Skipping {ini_out_path} (already exists, overwrite=False)")
                continue

            # Prepare data for rendering
            filtered_data = dataMap.copy()  # Use all dataMap entries
            filtered_data['cfg_id'] = f'{cfg_id:02d}'
            filtered_data['momentum_list'] = meson_xml._gen_mom_list()
            filtered_data['displacement_list'] = meson_xml._displacement_list()
            filtered_data['disco_displacement_list'] = disco_xml._displacement_list()
            filtered_data['disco_t_sources'] = disco_xml._displacement_list()
            #filtered_data['tsrc'] = 24
            #filtered_data['t_sources'] = dataMap.get('prop_t_sources', " ".join(str(i) for i in range(0, dataMap.get('prop_t_fwd', ens_props['NT']), round(dataMap.get('prop_t_fwd', ens_props['NT']) / dataMap.get('num_tsrc')))))
            #print(filtered_data['t_sources'])
            output_xml = handler.templates[obj].render(filtered_data)
            print(f"Writing file {ini_out_path} for object {obj}")
            with open(ini_out_path, 'w') as f:
                f.write(output_xml)
def main(options):
    os.makedirs(LOGPATH, exist_ok=True)
    os.makedirs(OUTPATH, exist_ok=True)
    env = jinja2.Environment(loader=jinja2.FileSystemLoader(TEMPLATE), undefined=jinja2.StrictUndefined)
    handler = TaskHandler(env)

    if options.ini_dir and os.path.isdir(options.ini_dir):
        for root, _, files in os.walk(options.ini_dir):
            for file in files:
                if file.endswith('.yml') or file.endswith('.yaml'):
                    yaml_file = os.path.join(root, file)
                    print(f"Processing YAML file: {yaml_file}")
                    process_yaml_file(yaml_file, options, env, handler)
    elif options.in_file and os.path.isfile(options.in_file):
        print(f"Processing single YAML file: {options.in_file}")
        process_yaml_file(options.in_file, options, env, handler)
    else:
        raise ValueError("Please provide a valid --in_file or --ini_dir")

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--in_file', type=str, required=False, help='Path to a single YAML input file')
    parser.add_argument('--ini_dir', type=str, required=False, help='Directory containing YAML files for ensembles')
    parser.add_argument('-l', '--list_tasks', nargs='+', required=True, help='List of tasks to generate (e.g., eigs, peram, meson, disco)')
    parser.add_argument('--overwrite', action='store_true', help='Overwrite existing XML and shell scripts')
    parser.add_argument('--test', action='store_true', help='Run in test mode')

    options = parser.parse_args()
    if not (options.in_file or options.ini_dir):
        parser.error("At least one of --in_file or --ini_dir must be provided")
    main(options)