import sys
sys.path.append('../')
sys.path.append('../../')
import h5py
import numpy as np
import matplotlib.pyplot as plt

file = 'pi_cfg1750_2pt_nvec_64_tsrc_16_test.h5'


# with h5py.File(file) as f:
#     tsrcs = list(f.keys())
#     print(tsrcs)
#     #data = f['/total_0/mom_0_0_0_mom_0_0_0/Dpi/direct/tsrc_5/cfg_1750'][:]
#     for keys in f['/pi_000/meson1_light_light'].keys(): 
#         Lt = 64
#         for t in range(Lt):
#             print(keys.split(('_')[-1]))
#             delta_t = t - int(keys.split(('_')[-1]))
#             if delta_t < 0:
#                 _delta_t = delta_t+ Lt
#                 print(_delta_t)


def load_data_tsrc(tsrc_avg: bool):
    """
    Load data for all operators and optionally average over 16 tsrc locations.
    
    Args:
        tsrc_avg (bool): If True, averages data over 16 tsrc locations.

    Returns:
        dict: keys are operator names and values are data arrays shape (num_cfgs, Lt, num_tsrcs) or (num_cfgs, Lt) if tsrc_avg=True.
    """
    data = {}
    
    with h5py.File(file,'r') as f:
        ops_list = list(f.keys())
        print(ops_list)

        for ops in ops_list:
            tsrc_groups = sorted([tsrc for tsrc in f[f'{ops}/meson1_light_light'].keys()], key=lambda x: int(x.split('_')[-1]))  
            print(tsrc_groups)
            
            for tsrc in tsrc_groups:
                cfg_groups = f[f'{ops}/meson1_light_light/{tsrc}'].keys()
                print(cfg_groups)
                
                # for cfg in cfg_groups:
                #     dataset_names = list(f[f'{ops}/meson1_light_light/{tsrc}/{cfg}'].keys())
                    
                for dataset in cfg_groups:
                    dataset_path = f'{ops}/meson1_light_light/{tsrc}/{dataset}'
                    try:
                        data_array = np.array(f[dataset_path], dtype=np.float64)
                        if (ops, int(tsrc.split('_')[-1])) not in data:
                            data[(ops, int(tsrc.split('_')[-1]))] = []
                        data[(ops, int(tsrc.split('_')[-1]))].append(data_array)
                    except ValueError:
                        print(f"Skipping dataset {dataset_path} due to conversion error")
            
            if (ops, int(tsrc.split('_')[-1])) in data:
                data[(ops, int(tsrc.split('_')[-1]))] = np.stack(data[(ops, int(tsrc.split('_')[-1]))])
                data[(ops, int(tsrc.split('_')[-1]))] = np.roll(data[(ops, int(tsrc.split('_')[-1]))], -int(tsrc.split('_')[-1]) * 4, axis=1)
    
    if tsrc_avg:
        avg_data = {}
        for ops in ops_list:
            valid_tsrcs = [t for _, t in data.keys() if ops in _]
            if valid_tsrcs:
                stacked_data = np.stack([data[(ops, t)] for t in valid_tsrcs], axis=2)  # shape: (ncfg, Lt, num_tsrcs)
                avg_data[ops] = stacked_data.mean(axis=2)  # shape: (ncfg, Lt)
        return avg_data
    
    return data


new_data = load_data_tsrc(tsrc_avg=True)
print(new_data['pi_000'])
def time_reverse(corr, reverse=True, phase=1, time_axis=0):
    if reverse:
        if len(corr.shape) > 1:
            cr = phase * np.roll(corr[:, ::-1], 1, axis=time_axis)
            cr[:, 0] = phase * cr[:, 0]
        else:
            cr = phase * np.roll(corr[::-1], 1)
            cr[0] = phase * cr[0]
    else:
        cr = phase * corr
    return cr
# tr = time_reverse(corr=data)

new_data = load_data_tsrc(tsrc_avg=True)
_new_data = np.array(new_data['pi_000'][0])
print(_new_data)

# print("tr",tr)
# print(data.shape)
    
# data_fold = 0.5*(data + np.roll(tr,0))
# #print(data)
import matplotlib.pyplot
plt.plot(np.arange(64), _new_data, '.', )
plt.yscale('log')
#plt.legend()
plt.savefig('pi.jpg')

