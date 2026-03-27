#关于数据缺失填充————汇总

import numpy as np
import pandas as pd
from statsmodels.tsa.seasonal import STL
from scipy import interpolate
from sklearn.metrics import mean_squared_error
from prophet import Prophet
from scipy.optimize import curve_fit

#STL
def stl_interpolate(series, period=365):
    """
    使用 STL 分解 + 插值填补缺失值
    :param series: pd.Series，时间索引为日期
    :param period: 周期（天数）
    :return: 填补后的 Series
    """
    # 获取连续整数时间索引（用于插值）
    t = np.arange(len(series))
    
    # 创建临时 Series，用于 STL 分解（需无缺失，故先用简单插值临时填充）
    # 为减少对分解的影响，先用线性插值粗略填充
    tmp = series.interpolate(method='linear', limit_area='inside').fillna(method='bfill').fillna(method='ffill')
    
    # 应用 STL 分解
    try:
        stl = STL(tmp, period=period, robust=True)
        res = stl.fit()
        trend = res.trend
        seasonal = res.seasonal
        residual = res.resid
    except Exception as e:
        print(f"STL 分解失败，使用简单线性插值替代。错误信息：{e}")
        return series.interpolate(method='linear', limit_area='inside').fillna(method='bfill').fillna(method='ffill')
    
    # 对趋势分量进行插值（样条或线性，趋势通常平滑）
    trend_interp = pd.Series(trend, index=series.index)
    trend_interp = trend_interp.interpolate(method='spline', order=3, limit_area='inside')
    trend_interp = trend_interp.fillna(method='bfill').fillna(method='ffill')
    
    # 对季节分量进行插值（周期性，可直接使用原值，因为 STL 已给出全序列）
    seasonal_interp = pd.Series(seasonal, index=series.index)
    # 季节分量一般无缺失，但若分解边界有 NaN，进行填充
    seasonal_interp = seasonal_interp.interpolate(method='linear', limit_area='inside').fillna(method='bfill').fillna(method='ffill')
    
    # 对残差分量进行线性插值（随机性强）
    residual_interp = pd.Series(residual, index=series.index)
    residual_interp = residual_interp.interpolate(method='linear', limit_area='inside').fillna(method='bfill').fillna(method='ffill')
    
    # 重构
    filled = trend_interp + seasonal_interp + residual_interp
    # 限制在合理范围内（假设速度在 0~2 m/s）
    filled = filled.clip(lower=0, upper=2)
    
    # 对于原序列中本来就有的非缺失值，保持原值（避免插值误差）
    filled = filled.where(series.isnull(), series)
    
    return filled

#相似日填充
def similar_day_fill(series, window=7):  #比较好的拟合效果
    """用相邻年份同一天的均值填充缺失"""
    filled = series.copy()
    for idx in filled[filled.isnull()].index:
        # 获取同月同日的数据（前后各几年）
        month_day = (idx.month, idx.day)
        # 寻找所有年份中相同月日的值（允许前后几天偏移）
        candidates = []
        for year in range(idx.year - 3, idx.year + 4):
            if year == idx.year:
                continue
            try:
                candidate_date = idx.replace(year=year)
                if candidate_date in series.index:
                    val = series.loc[candidate_date]
                    if not pd.isna(val):
                        candidates.append(val)
            except:
                continue
        if candidates:
            filled.loc[idx] = np.mean(candidates)
        else:
            # 如果没有找到，用前后时间插值
            filled.loc[idx] = series.interpolate(method='linear').loc[idx]
    return filled

#多项式与傅里叶
def fill_with_poly_fourier(series, poly_deg=2, fourier_terms=3, period=365):
    """
    使用多项式+傅里叶级数拟合时间序列，填补缺失值
    """
    # 将时间转换为从0开始的天数
    t = (series.index - series.index[0]).days.values
    y = series.values
    
    # 观测到的非缺失索引
    obs_mask = ~np.isnan(y)
    t_obs = t[obs_mask]
    y_obs = y[obs_mask]
    
    # 构建设计矩阵：多项式特征 + 傅里叶特征
    X_poly = np.vstack([t_obs**i for i in range(poly_deg+1)]).T
    X_fourier = np.column_stack([
        np.sin(2*np.pi*k*t_obs/period) for k in range(1, fourier_terms+1)
    ] + [
        np.cos(2*np.pi*k*t_obs/period) for k in range(1, fourier_terms+1)
    ])
    X = np.column_stack([X_poly, X_fourier])
    
    # 最小二乘求解系数
    coeffs, _, _, _ = np.linalg.lstsq(X, y_obs, rcond=None)
    
    # 预测所有时间点
    X_full_poly = np.vstack([t**i for i in range(poly_deg+1)]).T
    X_full_fourier = np.column_stack([
        np.sin(2*np.pi*k*t/period) for k in range(1, fourier_terms+1)
    ] + [
        np.cos(2*np.pi*k*t/period) for k in range(1, fourier_terms+1)
    ])
    X_full = np.column_stack([X_full_poly, X_full_fourier])
    y_pred = X_full @ coeffs
    
    # 构建填充后的 Series
    filled = pd.Series(y_pred, index=series.index)
    # 用原观测值覆盖
    filled.loc[obs_mask] = y_obs
    # 限制合理范围
    filled = filled.clip(0, 2)
    return filled

def prophet_fill(series, yearly_seasonality=True, weekly_seasonality=False):
    """
    用 Prophet 拟合整个时间序列，填补缺失值
    """
    df_prophet = series.reset_index()
    df_prophet.columns = ['ds', 'y']
    # Prophet 要求列名为 ds 和 y
    model = Prophet(yearly_seasonality=yearly_seasonality, 
                    weekly_seasonality=weekly_seasonality,
                    interval_width=0.95)
    model.fit(df_prophet)
    # 预测所有日期
    future = model.make_future_dataframe(periods=0, include_history=True)
    forecast = model.predict(future)
    filled = forecast.set_index('ds')['yhat']
    # 用原始观测值覆盖预测值
    filled = filled.where(series.isnull(), series)
    return filled



