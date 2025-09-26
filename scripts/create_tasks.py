import argparse
import os
import jinja2
import yaml
from yml_to_xml import eigs_xml, perams_xml, meson_xml, chroma_sh_xml, disco_xml

PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
FDIR = os.path.dirname(os.path.realpath(__file__))
TEMPLATE = os.path.join(FDIR, 'templates')
RESULTPATH = os.path.join(FDIR, 'res')
OUTPATH = os.path.join(RESULTPATH, 'out')
LOGPATH = os.path.join(RESULTPATH, 'log')

class TaskHandler:
    def __init__(self, env):
        self.templates = {
            'eigs': env.get_template('eigs.jinja.xml'),
            'peram_clover': env.get_template('peram_clover.jinja.xml'),
            'peram_charm_clover': env.get_template('peram_charm_clover.jinja.xml'),
            'peram_mg': env.get_template('peram_multigrid.jinja.xml'),
            'peram_strange_mg': env.get_template('peram_strange_multigrid.jinja.xml'),
            'peram_charm_mg': env.get_template('peram_charm_multigrid.jinja.xml'),
            'peram_charm_mg_eric': env.get_template('peram_charm_multigrid_eric.jinja.xml'),
            'peram': env.get_template('peram_multigrid.jinja.xml'),
            'meson': env.get_template('meson.jinja.xml'),
            'disco': env.get_template('disco.jinja.xml'),
            'chroma_eigs': env.get_template('eigs.sh.j2'),
            'chroma_peram': env.get_template('peram_jureca.sh.j2'),
            'chroma_peram_mg': env.get_template('peram_jureca.sh.j2'),
            'chroma_peram_charm_mg': env.get_template('peram_charm_mg.sh.j2'),
            'chroma_peram_clover': env.get_template('peram_clover.sh.j2'),
            'chroma_peram_charm_clover': env.get_template('peram_charm_clover.sh.j2'),
            'chroma_meson': env.get_template('meson_jureca.sh.j2'),
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
            'chroma_eigs': chroma_sh_xml.ChromaOptions,
            'chroma_meson': chroma_sh_xml.ChromaOptions,
            'chroma_peram': chroma_sh_xml.ChromaOptions,
            'chroma_peram_mg': chroma_sh_xml.ChromaOptions,
            'chroma_peram_charm_mg': chroma_sh_xml.ChromaOptions,
            'chroma_peram_clover': chroma_sh_xml.ChromaOptions,
            'chroma_peram_charm_clover': chroma_sh_xml.ChromaOptions,
            'chroma_disco': chroma_sh_xml.ChromaOptions,
        }

def process_yaml_file(yaml_file, options, env, handler):
    """Process a single YAML file to generate XML and shell scripts."""
    with open(yaml_file) as f:
        dataMap = yaml.safe_load(f)

    # Check for required keys
    missing_values = [key for key in ['run_path', 'cfg_path'] if key not in dataMap]
    if missing_values:
        for key in missing_values:
            value = input(f"Missing '{key}' in {yaml_file}. Please provide a value: ")
            dataMap[key] = value
        with open(yaml_file, 'w') as f:
            yaml.safe_dump(dataMap, f)

    run_objects = []
    for task in options.list_tasks:
        if 'eigs' in task:
            run_objects.extend(['eigs', 'chroma_eigs'])
        if 'peram_mg' in task:
            run_objects.extend(['peram_mg', 'chroma_peram_mg'])
        if 'peram_strange_mg' in task:
            run_objects.extend(['peram_strange_mg', 'chroma_peram_mg'])
        if 'peram_charm_mg' in task:
            run_objects.extend(['peram_charm_mg', 'chroma_peram_charm_mg'])
        if 'peram_charm_mg_eric' in task:
            run_objects.extend(['peram_charm_mg_eric', 'chroma_peram_charm_mg'])
        if 'peram_clover' in task:
            run_objects.extend(['peram_clover', 'chroma_peram_clover'])
        if 'peram_charm_clover' in task:
            run_objects.extend(['peram_charm_clover', 'chroma_peram_charm_clover'])
        if 'peram' in task:
            run_objects.extend(['peram', 'chroma_peram'])
        if 'meson' in task:
            run_objects.extend(['meson', 'chroma_meson'])
        if 'disco' in task:
            run_objects.extend(['disco', 'chroma_disco'])

    for cfg_id in range(options.cfg_i, options.cfg_f, options.cfg_step):
        print(f'Creating scripts for configuration {cfg_id} from {yaml_file}')
        ens_short = os.path.splitext(os.path.basename(yaml_file))[0]
        print(ini_path)
        cfg_dir = os.path.realpath(os.path.join('..', ini_path, f'cnfg{cfg_id:02d}'))
        rundir = os.path.join(options.run_dir, cfg_dir)
        os.makedirs(rundir, exist_ok=True)

        for obj in run_objects:
            obj_dir = os.path.join(rundir)
            os.makedirs(obj_dir, exist_ok=True)
            nvec_values = options.num_vecs if options.num_vecs else [None]

            for nvec in nvec_values:
                if nvec:
                    nvec_dir = os.path.join(obj_dir, f'numvec{nvec}')
                    os.makedirs(nvec_dir, exist_ok=True)
                else:
                    nvec_dir = obj_dir

                # Determine output file name
                if obj in ['chroma_eigs', 'chroma_disco']:
                    ini_out = f'{obj.split("_")[1]}_cfg{cfg_id:02d}.sh'
                elif obj != 'chroma_eigs' and obj.startswith('chroma'):
                    ini_out = f'{obj.split("_")[1]}_{nvec}_cfg{cfg_id:02d}.sh' if nvec else f'{obj.split("_")[1]}_cfg{cfg_id:02d}.sh'
                elif obj == 'peram_charm_mg_eric':
                    ini_out = f'peram_charm_mg_{nvec}_cfg{cfg_id:02d}.ini.xml' if nvec else f'peram_charm_mg_cfg{cfg_id:02d}.ini.xml'
                elif obj in ['disco', 'eigs']:
                    ini_out = f'{obj}_cfg{cfg_id:02d}.ini.xml'
                else:
                    ini_out = f'{obj}_{nvec}_cfg{cfg_id:02d}.ini.xml' if nvec else f'{obj}_cfg{cfg_id:02d}.ini.xml'

                ini_out_path = os.path.join(nvec_dir if nvec and not obj.__contains__('eigs|disco') else obj_dir, ini_out)

                if os.path.exists(ini_out_path) and not options.overwrite:
                    print(f"Skipping {ini_out_path} (already exists, overwrite=False)")
                    continue

                # Prepare data for rendering
                base = handler.xml_classes[obj]
                expected_keys = base.model_fields.keys()
                filtered_data = {k: v for k, v in dataMap.items() if k in expected_keys}
                filtered_data['cfg_id'] = f'{cfg_id:02d}'
                filtered_data['momentum_list'] = meson_xml._gen_mom_list()
                filtered_data['displacement_list'] = meson_xml._displacement_list()
                filtered_data['disco_displacement_list'] = disco_xml._displacement_list()
                filtered_data['disco_t_sources'] = disco_xml._displacement_list()
                filtered_data['tsrc'] = 24
                filtered_data['t_sources'] = " ".join(str(i) for i in range(0, dataMap.get('prop_t_fwd', 96), round(dataMap.get('prop_t_fwd', 96) / dataMap.get('num_tsrc', 4))))
                if nvec:
                    filtered_data['num_vecs_perams'] = nvec
                    filtered_data['meson_nvec'] = nvec
                ens_props = chroma_sh_xml.parse_ensemble(short_tag=filtered_data.get('ens_short', ''))
                filtered_data.update(ens_props)

                # Render and write output
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
        # Process all YAML files in the directory
        for root, _, files in os.walk(options.ini_dir):
            for file in files:
                if file.endswith('.yml') or file.endswith('.yaml'):
                    yaml_file = os.path.join(root, file)
                    print(f"Processing YAML file: {yaml_file}")
                    process_yaml_file(yaml_file, options, env, handler)
    elif options.in_file and os.path.isfile(options.in_file):
        # Process single YAML file
        print(f"Processing single YAML file: {options.in_file}")
        process_yaml_file(options.in_file, options, env, handler)
    else:
        raise ValueError("Please provide a valid --in_file or --ini_dir")

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--in_file', type=str, required=False, help='Path to a single YAML input file')
    parser.add_argument('--ini_dir', type=str, required=False, help='Directory containing YAML files for ensembles')
    parser.add_argument('--cfg_i', type=int, required=True, help='Starting configuration ID')
    parser.add_argument('--cfg_f', type=int, required=True, help='Ending configuration ID')
    parser.add_argument('--cfg_step', type=int, default=10, help='Configuration step size (default: %(default)s)')
    parser.add_argument('-l', '--list_tasks', nargs='+', required=True, help='List of tasks to generate (e.g., eigs, peram, meson, disco)')
    parser.add_argument('-nv', '--num_vecs', nargs='+', type=int, help='Number of vectors for perams and mesons')
    parser.add_argument('--overwrite', action='store_true', help='Overwrite existing XML and shell scripts')
    parser.add_argument('--cfg_path', default='/p/project1/exotichadrons/pederiva/6stout/beta_3.70/ms_0.000/mud_-0.022/s32t96/cnfg/', help='Default configuration path')
    parser.add_argument('--run_dir', default='', help='Run directory (default: %(default)s)')
    parser.add_argument('--test', action='store_true', help='Run in test mode')

    options = parser.parse_args()
    if not (options.in_file or options.ini_dir):
        parser.error("At least one of --in_file or --ini_dir must be provided")
    main(options)
