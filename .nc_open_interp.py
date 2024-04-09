import numpy as np
import netCDF4 as nc
import pandas as pd
import os 
import xarray as xr
import matplotlib 
import matplotlib.pyplot as plt

folder_path=r"E:\ocean1"
ff=os.listdir(folder_path)

nc_2017=[]
nc_2018=[]
nc_2019=[]
nc_2020=[]

for i in range(len(ff)):
    if "2017" in ff[i]:
        nc_2017.append(ff[i])
    if "2018" in ff[i]:
        nc_2018.append(ff[i])
    if "2019" in ff[i]:
        nc_2019.append(ff[i])
    if "2020" in ff[i]:
        nc_2020.append(ff[i])

def Hebing(lister):
    lis=[]
    for i in range(len(lister)):
        u=xr.open_dataset(folder_path+"\\"+lister[i])[['mwd','mwp','swh']]
        lis.append(u)
    lis=xr.concat(lis, dim='time')
    return lis
        
all_2017=Hebing(nc_2017)
all_2018=Hebing(nc_2018)
all_2019=Hebing(nc_2019)
all_2020=Hebing(nc_2020)

print(all_2017)#确定经纬度、时间范围

all_2017.variables.keys() #查看变量

‘’‘
如果time是从X年X月X日 X：X：X的天数累计存储的，可以用.data直接把masked_array中的data数据读出。
time = nc.num2date(all_2017.variables['time'][:],'days since 1800-1-1 00:00:00').data
#输出：array([cftime.DatetimeGregorian(1891, 1, 1, 0, 0, 0, 0),
cftime.DatetimeGregorian(1891, 2, 1, 0, 0, 0, 0),
cftime.DatetimeGregorian(1891, 3, 1, 0, 0, 0, 0), …,
cftime.DatetimeGregorian(2016, 10, 1, 0, 0, 0, 0),
cftime.DatetimeGregorian(2016, 11, 1, 0, 0, 0, 0),
cftime.DatetimeGregorian(2016, 12, 1, 0, 0, 0, 0)], dtype=object)
‘’‘

#选经纬度范围
use_2017=all_2017.sel(latitude=slice(33,30),longitude=slice(122,124))
use_2017['swh'][1].plot(x='longitude',y='latitude')

#插值，原网格0.5X0.5,插成0.1X0.1
interp_2017=use_2017.interp(latitude=np.linspace(33,30,31),longitude=np.linspace(122, 124,21),method='linear')

all_2017.to_netcdf('E://2017.nc')

zong=xr.concat((use2017,use2018,use2019,use2020),dim='time')
ar_z=zong['swh'].values

#normalization
from sklearn.preprocessing import MinMaxScaler
scaler=MinMaxScaler(feature_range=(0,1))
tr_z=scaler.fit_transform(ar_z.reshape(ar_z.shape[0],-1)).reshape(ar_z.shape)
#print(ar_z.min(),ar_z.max())
print(tr_z.min().round(5),tr_z.max().round(5))

#orin as target
orin_z=[]
for i in range(len(tr_z)):
    se=np.random.uniform(-0.005,0.005,(31,21))
    a=tr_z[i]+se
    orin_z.append(a)
    
#split7:3
step=8
x_tr=orin_z[:24544]
x_te=orin_z[24544:]
y_tr=tr_z[:24544]
y_te=tr_z[24544:]
    
len(tr_z)-step+1
X_train=[]
Y_train=[]
X_test=[]
Y_test=[]

def process(array1,array2,list1,list2):
    for i in range(len(array1)-step*2+1):
        global X_train,Y_train  #global 全局变量， nonlocal 局部变量使用
        x_one_tr=array1[i:i+step]
        X_train.append(x_one_tr)
        y_one_tr=array2[i+step:i+step+step]
        Y_train.append(y_one_tr)
    X_train=np.array(X_train)
    Y_train=np.array(Y_train)    
    for j in range(0,len(list1)-step*2+1,step*2):
        global X_test,Y_test
        x_one_te=list1[j:j+step]
        X_test.append(x_one_te)
        y_one_te=list2[j+step:j+step+step]
        Y_test.append(y_one_te)
    X_test=np.array(X_test)
    Y_test=np.array(Y_test)
    return X_train,Y_train,X_test,Y_test

X_train,Y_train,X_test,Y_test=process(x_tr,y_tr,x_te,y_te) 


#BTW
import dateutil.parser  #这个库来将日期字符串转成统一的datatime时间格式
sdt = dateutil.parser.parse("2016-1-1T00:00:00")
 #动态变化图
import imageio
frames = []  
for i in range(12):  
    frames.append(imageio.imread(str(i)+'.jpg'))  
# Save them as frames into a gif   
imageio.mimsave('动图.gif', frames, 'GIF', duration = 0.8) 

#查找固定纬度/经度范围的，返回的是索引
long= nc.variables['longitude'][:]  
lati= nc.variables['latitude'][:] 
print(np.argwhere(lati==4),np.argwhere(lati==54),
np.argwhere(long==73+180),np.argwhere(long==133+180))

#绘图
from mpl_toolkits.basemap import Basemap
lon_0 = lons.mean()
lat_0 = lats.mean()
m = Basemap(lat_0=lat_0, lon_0=lon_0)
# 绘制经纬线
m.drawparallels(np.arange(-90., 91., 20.), labels=[1,0,0,0], fontsize=10)
m.drawmeridians(np.arange(-180., 181., 40.), labels=[0,0,0,1], fontsize=10)
# Add Coastlines, States, and Country Boundaries
m.drawcoastlines()
m.drawstates()
m.drawcountries()

# Add Colorbar
cbar = m.colorbar(cs, location='bottom', pad="10%")
cbar.set_label(tlml_units)

# Add Title
plt.title('Surface Air Temperature')
plt.show()

