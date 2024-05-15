# -*- coding: utf-8 -*-
"""
Created on Mon Apr 22 10:19:56 2024

@author: chen
"""

import xarray as xr
import json
import pandas as pd
import os
import datetime
import numpy as np


folder_path=r"D:\Dredging_forecasting_system_Near_China_sea\FEWS-NCS\trunk\Archive"
date=datetime.date.today()
year=date.year
month=date.month
day=date.day
if len(str(month))<2:
    month="0"+str(month)

folder_path=folder_path+"\\"+str(year)+'\\'+month+"\\GoG"

def fp_1(folder_path):
    lists=os.listdir(folder_path)
    lists.sort(key=lambda fn:os.path.getmtime(folder_path+"\\"+fn))
    file_n=os.path.join(folder_path,lists[-1])
    return file_n
    
folder_path=fp_1(folder_path)
folder_path=folder_path+"\\external_forecasts"

def fp_2(folder_path):
    lists=os.listdir(folder_path)
    lists.sort(key=lambda fn:os.path.getmtime(folder_path+"\\"+fn))
    list_2=lists[-2:]
    for x in list_2:
        if "Wave" in x:
            folder_w=os.path.join(folder_path,x)
        else:
            folder_g=os.path.join(folder_path,x)
    return folder_w,folder_g
    
folder_w,folder_g=fp_2(folder_path)  
        
'''
ttt=datetime.datetime(2024,5,13,2,55,14,56565)
ttt=ttt-datetime.timedelta(hours=8)
t14=datetime.datetime(2024,5,13,8,55,51,45)
t14=t14-datetime.timedelta(hours=8)
d=datetime.datetime.today()
d=d-datetime.timedelta(hours=8)
t=time.localtime()
if t.tm_hour<6:
    day=day-1
    nu='180000'
elif 8<t.tm_hour<13:
    nu='000000'
elif 14<t.tm_hour<19:
    nu='060000'
else:
    nu='120000'
folder_path=folder_path+'\\'+year+'\\'+month+'\\GoG'+day+'\\external_forecasts'
'''

gfs=xr.open_dataset(folder_g+'\\GFS_Forecast.nc')
wave=xr.open_dataset(folder_w+'\\GFS-Wave_Forecast.nc')

point_y1,point_x1=32.75,121.75
point_y2,point_x2=22.5,116.25


'''
look=xr.open_dataset(r"D:\DeepLearning\ZJHF\test_data\0507\GFS_Forecast.nc")
no=look.sel(y=32.75,x=121.75)
no=no[column_name]
wave=xr.open_dataset(r"D:\DeepLearning\ZJHF\test_data\0421\GFS-Wave_Forecast.nc")
wa=wave.variables
'''

gfs1=gfs.sel(y=point_y1,x=point_x1)
gfs2=gfs.sel(y=point_y2,x=point_x2)
gfs_column_name=['Precipation_surface_6_hour_accumulation','Pressure_at_mean_sea-level',
           'Wind_speed_u_direction','Wind_speed_v_direction',
           'Visibility_at_surface','Temperature_above_ground','Humidity_at_2m_above_ground',
           'Wind100_speed_u_direction','Wind100_speed_v_direction']

gfs1=gfs1[gfs_column_name]
gfs2=gfs2[gfs_column_name]

wave1=wave.sel(y=point_y1,x=point_x1)
wave2=wave.sel(y=point_y2,x=point_x2)
wave_col_name=['sea_surface_wave_significant_height','sea_surface_wave_to_direction','sea_surface_wind_wave_period']
wave1=wave1[wave_col_name]
wave2=wave2[wave_col_name]

col_list=gfs_column_name+wave_col_name

all1=xr.merge([gfs1,wave1])
all2=xr.merge([gfs2,wave2])

nc=[all1,all2]
#nc=xr.concat([all1,all2],dim='y')

aim_X=[121.82877,116.15948]
aim_Y=[32.67983,22.624033]

 #str(aim_X[0])+","+str(aim_X[0])


def gen_data_dict(nc,parameterNumber, parameterNumberName,paraunit,X,Y):
    numberPoints = 2
    nx, ny = 2,2
    header_dict = {
        'parameterCategory': 1,
        'parameterCategoryName': 'GFS',
        'parameterNumber': parameterNumber,
        'parameterNumberName': parameterNumberName,
        'parameterUnit': paraunit,
        'numberPoints': numberPoints,
        'nx':nx,
        'ny':ny
    }
    d={}
    for i in range(len(nc[0]['time'])):
        matlab_datenum=nc[0]['time'].values[i]
        reftime = pd.to_datetime(str(matlab_datenum)[:-10]).strftime('%Y-%m-%dT%H:%M:%SZ')
        data2={}
        for n in range(len(nc)):
            u=np.squeeze(nc[n][parameterNumberName][i])
            nan_to_none=np.where(np.isnan(u), None, u)
            data_list = list(nan_to_none.ravel('F'))
            ###nan_to_none = np.fliplr(np.where(np.isnan(u), None, u))  np.fliplr()数据左右翻转
            data2[str(X[n])+","+str(Y[n])]=data_list
        d[reftime]=data2
    return {'header':header_dict,'data':d}

result=[]

for j in range(len(col_list)):
    paraunit=nc[0][col_list[j]].units
    re=gen_data_dict(nc,j, col_list[j], paraunit,aim_X,aim_Y)
    result.append(re)

#filename=r"D:/DeepLearning/ZJHF/nc2json/0421/GFS_Forecast_test.json"

filename=r"D:\DeepLearning\ZJHF\nc2json"+"\\"+str(year)+"\\"+str(month)+str(day)
if not os.path.exists(filename):
    os.makedirs(filename)    
filename=filename+"\\"+folder_w[-6:-4]+"GFS_Forecast.json"
with open(filename,'w') as f:
    json.dump(result, f)
