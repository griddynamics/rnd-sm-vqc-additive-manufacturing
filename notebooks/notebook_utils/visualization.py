import open3d as o3d
import numpy as np
import pandas as pd


def color_channels(model, path_csv):
    df_ex = pd.read_csv(path_csv)
    red_channel = model.predict_proba(df_ex.loc[:, ['x','y','z','dist']].values)[:,1]
    green = np.zeros(red_channel.shape[0])
    blue = 1-red_channel
    return np.vstack((red_channel, green, blue)).T
    
def visualize_anomaly(model, path_csv, path_pcd):
    pcd_anomaly = o3d.io.read_point_cloud(path_pcd)
    pcd_anomaly.colors = o3d.utility.Vector3dVector(color_channels(model, path_csv))
    return pcd_anomaly

