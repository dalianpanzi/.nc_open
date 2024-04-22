import xarray as xr
import json
from datetime import datetime as DT
import sys
import numpy as np
import datetime

haifeng=xr.open_dataset(r"D:/DeepLearning/ZJHF/GFS_Forecast.nc")
nc_n=haifeng[['Precipation_surface_6_hour_accumulation','Pressure_at_mean_sea-level',
           'Wind_speed_u_direction','Wind_speed_v_direction',
           'Visibility_at_surface','Temperature_above_ground']]

def gen_data_dict(parameterNumber, parameterNumberName,paraunit):
    numberPoints = 10000
    nx, ny = 100,100
    lo1 = 105.0
    la1 = 41.0
    lo2 = 129.75
    la2 = 16.25
    dx = 0.25
    dy = 0.25
    header_dict = {
        'parameterCategory': 1,
        'parameterCategoryName': 'GFS',
        'parameterNumber': parameterNumber,
        'parameterNumberName': parameterNumberName,
        'parameterUnit': paraunit,
        'numberPoints': numberPoints,
        'nx': nx,
        'ny': ny,
        'lo1': float(lo1),
        'la1': float(la1),
        'lo2': float(lo2),
        'la2': float(la2),
        'dx': dx,
        'dy': dy
    }
    d={}
    for i in range(len(nc_n['time'])):
        matlab_datenum=nc_n['time'].values[i]
        reftime = pd.to_datetime(str(matlab_datenum)[:-10]).strftime('%Y-%m-%dT%H:%M:%SZ')
        u=np.squeeze(nc_n[parameterNumberName][i])
        ###nan_to_none = np.fliplr(np.where(np.isnan(u), None, u))  np.fliplr()数据左右翻转
        nan_to_none=np.where(np.isnan(u), None, u)
        data_list = list(nan_to_none.ravel('F'))
        d[reftime]=data_list
    return {'header':header_dict,'data':d}

para_name_list=['Precipation_surface_6_hour_accumulation','Pressure_at_mean_sea-level',
           'Wind_speed_u_direction','Wind_speed_v_direction',
           'Visibility_at_surface','Temperature_above_ground']

result=[]
for j in range(len(para_name_list)):
    paraunit=nc_n[para_name_list[j]].units
    re=gen_data_dict(j, para_name_list[j], paraunit)
    result.append(re)

filename=r"D:/DeepLearning/ZJHF/GFS_Forecast.json"
with open(filename,'w') as f:
    json.dump(result, f)

#写成json数据key只能是 str, int, float, bool or None, not tuple

