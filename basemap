import matplotlib.pyplot as plt
import numpy as np
from mpl_toolkits.basemap import Basemap

----------------------------------------------------
#纯地图
# 设置图形尺寸
fig = plt.figure(figsize=(16, 10))

# 定义目标区域的中心坐标
lat_center = (58 + 73) / 2  # 纬度中心点 65.5°N
# 考虑跨 180 度经线，将经度范围转换为 -180 到 180 度
lon_min = 167
lon_max = 195
lon_center = ((lon_min + lon_max) % 360) - 180

# 计算地图物理尺寸（单位：米）
lat_span = 73 - 58  # 纬度跨度 15 度
# 计算经度跨度，考虑跨 180 度经线
lon_span = (lon_max - lon_min) % 360

# 设置地图宽高（增加 10% 余量）
width = lon_span * 111000 * np.cos(np.radians(lat_center)) * 1.1
height = lat_span * 111000 * 1.1

# 配置兰伯特方位等积投影
mymap = Basemap(
    projection='laea',  # 兰伯特方位等积投影
    lat_0=lat_center,  # 中心纬度 65.5°N
    lon_0=lon_center,  # 中心经度
    width=width,  # 地图物理宽度
    height=height,  # 地图物理高度
    resolution='i',  # 中等分辨率
    area_thresh=1000  # 过滤小面积水域
)

mymap.drawcoastlines(linewidth=0.5)
mymap.bluemarble()

# 绘制经纬线（自定义标注）
# 纬度圈（58°N 到 73°N，间隔 2°）
mymap.drawparallels(
    np.arange(58, 74, 2),
    labels=[1, 0, 0, 0],
    fontsize=15,
    color='gray'
)

# 经线标注转换函数
def lon_label(lon):
    if lon > 180:
        return f"{360 - lon}°W"
    else:
        return f"{lon}°E"

# 绘制经线（从 lon_min 到 lon_max，间隔 2°）
meridians = np.arange(lon_min, lon_max, 5)
for meridian in meridians:
    lon_show = meridian % 360
    mymap.drawmeridians(
        [lon_show],
        labels=[0, 0, 0, 1],
        fontsize=15,
        linewidth=0.5,
        labelstyle='+/-',
        fmt=lon_label
    )

# 调整子图布局，使地图显示更完整
plt.subplots_adjust(left=0.1, right=0.9, top=0.9, bottom=0.1)

plt.show()


-------------------------------------------------------------------------------
#有变量
import netCDF4 as nc
import xarray as xr

from mpl_toolkits.basemap import Basemap
import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns


pic=xr.open_dataset(r"D:\Dredging_forecasting_system_Near_China_sea\FEWS-NCS\trunk\Archive\2024\05\GoG\18\external_forecasts\GFS_000000\GFS_Forecast.nc")
pic.variables.keys()
pl=pic.sel(y=slice(26,35),x=slice(119,128))
pl.variables.keys()
windu=pl['Wind_speed_u_direction'][6]  #2,4,6
windv=pl['Wind_speed_v_direction'][6]


fig=plt.figure(figsize=(8,8))
mymap=Basemap(llcrnrlon=119,llcrnrlat=26,urcrnrlon=128,urcrnrlat=35,
              projection='cyl',resolution='i')
mymap.drawcoastlines()
mymap.fillcontinents(color='lightgray')


lon=np.arange(119,128.5,0.25 )
lat=np.arange(36,26.5,-0.25 )
mymap.drawparallels(np.arange(26,35.0001,2),labels=[1,0,0,0])
mymap.drawmeridians(np.arange(119,128.001,2),labels=[0,0,0,1])
LON,LAT=np.meshgrid(lon,lat)
x,y=mymap(LON,LAT)

#fig=mymap.contourf(LON, LAT, check,30,cmap=plt.cm.YlGnBu)
#mymap.colorbar(fig)

stride=2
windu_sub=windu[::stride,::stride]
windv_sub=windv[::stride,::stride]
x_sub=x[::stride,::stride]
y_sub=y[::stride,::stride]
wind_speed=np.sqrt(windu**2+windv**2)

q=mymap.quiver(x_sub, y_sub, windu_sub, windv_sub,  
               wind_speed[::stride,::stride],
               cmap='Greys',
               scale=300,
               width=0.002,
               headwidth=3,
               headlength=4.5)
plt.quiverkey(q, X=0.85, Y=0.1, U=10, label='10m/s', labelpos='E',coordinates='figure')
plt.show()
