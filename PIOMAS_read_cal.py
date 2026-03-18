#关于PIOMAS数据的下载与处理  标量与矢量数据的lon，lat网格是不同的
from PyPIOMAS.PyPIOMAS import PyPIOMAS
import xarray as xr
import gzip
import numpy as np
from scipy.spatial import KDTree
import pandas as pd
import os



variables=['hiday','icevel' ] #hiday冰厚、icevel冰速
years=list(range(2014,2025))
out_dir=r'J:\cqz_temp_HS\NEP\piomas\velcity'
download=PyPIOMAS(out_dir, variables, years)
print(download)

download.download()
download.unzip()
download.to_netcdf(r'J:\cqz_temp_HS\NEP\piomas\vel.nc')  #冰厚可以组合成一个nc，但冰速不可以

ice_thick=xr.open_dataset(r'J:\cqz_temp_HS\NEP\piomas.nc')
x=ice_thick['x'].values
y=ice_thick['y'].values
year=ice_thick['year'].values

ncol=360 #经度
nrow=120 #纬度

lon=x.reshape( nrow, ncol)
lat=y.reshape( nrow, ncol)

#做mask ，哪些位置是海
kmt=np.zeros((nrow, ncol), dtype=np.int32)
mask=r'J:\cqz_temp_HS\NEP\piomas\io.dat_360_120.output'
with open(mask, 'r') as f:
    for j in range(nrow):
        line=f.readline().strip()
        for i in range(ncol):
            val=int(line[i*2:i*2+2])
            kmt[j,i]=val   #里面的值是海水的分层数
mm=np.where(kmt>0,1,0)   

#需要数据的点位
points={
        'A':(66.167,190.467),
        'B':(77.0167, 167.333),
        'C':(71.75, 159.633),
        'D':(73.9167, 155.7167),
        'E':(77.05, 150),
        'F':(77.75, 105),
        'G':(78.067, 93),
        'H':(76.8833, 84.833)
        }


#冰厚部分
hidayy=ice_thick['hiday'].values
thick=hidayy.reshape(11,365, nrow, ncol)

lons_rad=np.radians(x)
lats_rad=np.radians(y)

px=np.cos(lats_rad)*np.cos(lons_rad)
py=np.cos(lats_rad)*np.sin(lons_rad)
pz=np.sin(lats_rad)

gp=np.column_stack([px,py,pz])
tree=KDTree(gp)

point_idx={}
for name,(la, lo) in points.items():
    rlon=np.radians(lo)
    rlat=np.radians(la)
    xt=np.cos(rlat)*np.cos(rlon)
    yt=np.cos(rlat)*np.sin(rlon)
    zt=np.sin(rlat)
    
    dist,idx_flat=tree.query([xt,yt,zt])
    idx_2d=np.unravel_index(idx_flat, (nrow, ncol))
    point_idx[name]=idx_2d
    print(f"{name}: 最近网格点 -> (lat_idx={idx_2d[0]}, lon_idx={idx_2d[1]}), "
          f"经度={lon[idx_2d]:.3f}°, 纬度={lat[idx_2d]:.3f}°, mask={mm[idx_2d]}")

#选择需要的时间范围
day_start=181  #7/1
day_end=304  #11/1  是exclusive的
#days_in_period=day_end-day_start  #是123
extracted={}
for name,(i,j) in point_idx.items():
    point_data=thick[:,:,i,j]
   # if mask[i, j]==0:
       # print(f"警告：点 {name} 对应的网格 mask 为 0（陆地），数据可能无效")
        # 可设为 NaN
      #  point_data = np.full_like(point_data, np.nan)
    extracted[name]=point_data[:,day_start:day_end]

all_dates = []
yrs=np.arange(2014,2025 )
for yr in yrs:
    start=f'{yr}-07-01'
    end=f'{yr}-10-31'
    dates_yr=pd.date_range(start,end, freq='D')
    all_dates.extend(dates_yr)

data= np.zeros((len(list(points.keys())), len(all_dates)))
lon_vals, lat_vals=[],[]
for i, name in enumerate(list(points.keys())):
    arr=extracted[name]
    data[i,:]=arr.flatten()
    lon_vals.append(points[name][1])
    lat_vals.append(points[name][0])
    
da=xr.DataArray(
    data,
    dims=('point','time'),
    coords={
        'point':list(points.keys()),
        'time':all_dates,
        'longitude':('point', lon_vals),
        'latitude':('point', lat_vals),
        },
    attrs={'unit':'m', 'long_name':'sea ice thickness'}
    )
da.to_netcdf(r'J:\cqz_temp_HS\NEP\piomas_sea_ice_thickness_use.nc')

#冰速部分
lonlat=np.loadtxt(r'J:\cqz_temp_HS\NEP\piomas\velcity\grid.dat.pop', dtype=np.float32)
total=ncol*nrow
ulat=lonlat[0:int(total/10)].reshape((nrow, ncol ))
ulon=lonlat[int(total/10):int(total*2/10)].reshape((nrow, ncol ))
HTN=lonlat[int(total*2/10):int(total*3/10)].reshape((nrow, ncol ))
HTE=lonlat[int(total*3/10):int(total*4/10)].reshape((nrow, ncol ))
HUS=lonlat[int(total*4/10):int(total*5/10)].reshape((nrow, ncol ))
HUW=lonlat[int(total*5/10):int(total*6/10)].reshape((nrow, ncol ))
ann=lonlat[int(total*6/10):int(total*7/10)].reshape((nrow, ncol ))

alpha=np.loadtxt(r'J:\cqz_temp_HS\NEP\piomas\velcity\alpha.fortran.dat', dtype=np.float32)
angle=alpha.reshape(nrow,ncol)
kmu=np.zeros((ncol,nrow),dtype=np.int32)
for i in range(ncol-1):
    for j in range(nrow-1):
        kmu[i,j]=min(kmt[i, j], kmt[i+1, j], kmt[i, j+1], kmt[i+1, j+1])

u_list,v_list=[],[]
vel_dir=r'J:\cqz_temp_HS\NEP\piomas\velcity'
for yr in years:
    fname=f'icevel.H{yr}'
    filepath=os.path.join(vel_dir, fname)
    with open(filepath, 'rb') as f:
        raw=f.read()
    raw_vel=np.frombuffer(raw, dtype='<f4').copy()
    
    total_per_month=nrow*ncol
    n_recods=len(raw_vel)//total_per_month
    n_months=n_recods//2
    vel=raw_vel.reshape((n_months,2,nrow,ncol))
    u=vel[:,0,:,:].copy()
    v=vel[:,1,:,:].copy()
    
    angle_rad = np.radians(angle)
    cos_a = np.cos(-angle_rad)
    sin_a = np.sin(-angle_rad)
    u_geo = u * cos_a + v * sin_a
    v_geo = v * cos_a - u * sin_a
    
    u_list.append(u_geo)
    v_list.append(v_geo)
u_all = np.concatenate(u_list, axis=0)   # shape: (12*N_years, nx, ny)
v_all = np.concatenate(v_list, axis=0)

time_coords=[]
indices=[]
for y, yr in enumerate(years):
    for mon in [7,8,9,10]:
        idx = y*12 + (mon-1)          # 月份从0开始
        indices.append(idx)
        time_coords.append(np.datetime64(f'{yr}-{mon:02d}-01'))

u_sub=u_all[indices]
v_sub = v_all[indices]
lons_rad=np.radians(ulon.flatten())
lats_rad=np.radians(ulat.flatten())

px=np.cos(lats_rad)*np.cos(lons_rad)
py=np.cos(lats_rad)*np.sin(lons_rad)
pz=np.sin(lats_rad)
gp=np.column_stack([px,py,pz])

tree=KDTree(gp)

point_idx={}
for name,(la, lo) in points.items():
    rlon=np.radians(lo)
    rlat=np.radians(la)
    xt=np.cos(rlat)*np.cos(rlon)
    yt=np.cos(rlat)*np.sin(rlon)
    zt=np.sin(rlat)
    
    dist,idx_flat=tree.query([xt,yt,zt])
    idx_2d=np.unravel_index(idx_flat, (120,360))
    point_idx[name]=idx_2d
    print(f"{name}: 最近网格点 -> (lat_idx={idx_2d[0]}, lon_idx={idx_2d[1]}), "
          f"经度={ulon[idx_2d]:.3f}°, 纬度={ulat[idx_2d]:.3f}°, mask={kmu[idx_2d]}")

uu,vv=[],[]
for name,(i,j) in point_idx.items():
    us=u_sub[:,i,j]
    vs=v_sub[:,i,j]
    uu.append(us)
    vv.append(vs)

uu=np.array(uu)
vv=np.array(vv)
llp=np.array(list(points.values()))
point_names = list(points.keys())
ds=xr.Dataset(
    data_vars={
        'u': (('point','time'), uu, {'units': 'm/s', 'long_name': 'sea ice velocity (eastward)'}),
        'v': (('point','time'), vv, {'units': 'm/s', 'long_name': 'sea ice velocity (northward)'})
        }, 
    coords={
        'time':time_coords,
        'point': point_names,
        'longitude': ('point', llp[:,1]),
        'latitude': ('point', llp[:,0])
        },
    attrs={'description': 'Sea ice velocity at selected points (July–October, 2014–2024) extracted from PIOMAS'}
    )
ds.to_netcdf(r'J:\cqz_temp_HS\NEP\n_icevel_use_jul_oct_2014_2024.nc')

#离散化与先验概率
data=xr.open_dataarray(r'J:\cqz_temp_HS\NEP\piomas_sea_ice_thickness_use.nc')
thickn=data.values
thickness=pd.DataFrame(thickn.flatten(), columns=['value'])

def ice_thickness_level(data):
    if data <=0.2:
        return 1
    elif data <=0.4:
        return 2
    elif data <=0.6:
        return 3
    elif data <=0.8:
        return 4
    else:
        return 5
    
thickness['level']=thickness['value'].apply(ice_thickness_level)
probs=thickness['level'].value_counts(normalize=True).sort_index()
values=probs.values.reshape(-1,1).tolist()

data2=xr.open_dataset(r'J:\cqz_temp_HS\NEP\icevel_use_jul_oct_2014_2024.nc')
data2.variables
ice_vel=pd.DataFrame(data2['u'].values.flatten(),columns=['u'])
ice_vel['v']=data2['v'].values.flatten()
vel_u=uu.flatten()
vel_v=vv.flatten()

