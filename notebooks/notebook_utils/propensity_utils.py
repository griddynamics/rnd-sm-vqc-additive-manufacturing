import os
import pathlib
import random

import numpy as np
import pandas as pd
import open3d as o3d
from joblib import dump, load


def process_point_clouds(path1, path2):
    """
    Function that reads paths to printed object data and reference mesh data
    """
    df_anom = pd.read_csv(path1)
    df_anom[['red', 'green', 'blue']] = 0
    df_anom.loc[df_anom['label'], 'red']=1
    df_anom.loc[~df_anom['label'], 'blue']=1

    pcd_anom = o3d.geometry.PointCloud()
    pcd_anom.points = o3d.utility.Vector3dVector(df_anom.loc[:, ['x','y','z']].values)
    pcd_anom.colors = o3d.utility.Vector3dVector(df_anom.loc[:, ['red', 'green', 'blue']].values)
    
    df_refer = pd.read_csv(path2)
    df_refer[['red', 'green', 'blue']] = [0, 0, 1]

    pcd_refer = o3d.geometry.PointCloud()
    pcd_refer.points = o3d.utility.Vector3dVector(df_refer.loc[:, ['x','y','z']].values)
    pcd_refer.colors = o3d.utility.Vector3dVector(df_refer.loc[:, ['red', 'green', 'blue']].values)
    dist_pc1_pc2_transformed = pcd_anom.compute_point_cloud_distance(pcd_refer)
    
    return pcd_anom, dist_pc1_pc2_transformed

# Get item and corresponding reference item pairs
def get_reference_pairs(pairs_of_paths, path_to_point_clouds):
    for key in pairs_of_paths.keys():
        path_reference = os.path.join(path_to_point_clouds, 'reference')
        for reference_name in os.listdir(path_reference):
            if pathlib.Path(reference_name).suffix == '.csv':
                for name in os.listdir(os.path.join(path_to_point_clouds, key)):
                    word_part = reference_name.replace("reference","").replace(".csv","")
                    if pathlib.Path(name).suffix == '.csv':
                        if reference_name.find('bisect')!=-1 and name.find('bisect')!=-1:
                            if name.find(word_part)!=-1:
                                pairs_of_paths[key].append(
                                    [
                                        os.path.join(path_to_point_clouds, key, name), 
                                        os.path.join(path_reference, reference_name)
                                    ])
                        elif reference_name.find('bisect')==-1 and name.find('bisect')==-1:
                            if name.find(word_part)!=-1:
                                pairs_of_paths[key].append([
                                    os.path.join(path_to_point_clouds, key, name),  
                                    os.path.join(path_reference, reference_name)
                                ])
    return pairs_of_paths

def generate_distance_csvs(pairs_of_paths, dataset_path):
    # Process pairs of objects data in order to get
    # distances between points of object for detecting to reference object points

    dist_data =  {"anomaly": [], "normal": []} # {"object_path": [],
    os.makedirs(dataset_path, exist_ok=True)
    for key, paths in pairs_of_paths.items():
        for path1, reference_path in paths:
            pcd, dist_pc1_pc2_transformed  = process_point_clouds(path1, reference_path)
            df_processed = pd.DataFrame(
                np.hstack(
                    (np.asarray(pcd.points),
                    np.asarray(dist_pc1_pc2_transformed).reshape(-1,1), 
                    np.asarray(pcd.colors)[:,0].reshape(-1,1))
                ), 
                columns=['x','y','z','dist','label']
            )
            dist_path = os.path.join(dataset_path, pathlib.Path(path1).name)
            dist_data[key].append(dist_path)
            # dataset_dict["object_path"].append(path1)
            # dataset_dict["reference_path"].append(dist_path)
            # dataset_dict["label"].append(key)
            df_processed.to_csv(os.path.join(dist_path), index=False)

    return dist_data

def save_rf_model(rf_prop, model_save_path, train_end_time):
   # Save point model
    # model_save_path = "./model_weights"
    os.makedirs(model_save_path, exist_ok=True)

    model_path = f'{model_save_path}/[{train_end_time}] rf_propensity.joblib'

    # Transfer to drive 
    dump(rf_prop, model_path) 
    return model_path 


