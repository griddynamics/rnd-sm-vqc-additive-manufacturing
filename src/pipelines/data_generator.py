import os
import pathlib
import random
import sys

import bpy
import yaml
import numpy as np
from scipy.stats import halfnorm

dir_path = os.path.dirname(os.path.realpath(__file__))
sys.path.insert(0, os.path.dirname(dir_path))

from src.utils.cameras import create_cameras_around_object
from src.utils.anomaly_utils import anomaly_function
from src.utils.mesh_utils import add_original_mesh, remove_default_object, load_main_object_mesh, bisect_function
from src.utils.point_cloud_utils import delete_non_visible_vertices, mesh_to_point_clouds, random_cloud_points


def create_bisect(mesh_path, config):

    mesh_name = pathlib.Path(mesh_path).stem

    # Load main object mesh
    remove_default_object()
    load_main_object_mesh(mesh_path)

    num_of_bisect = config['model']['num_of_bisect']

    # Create bisects at given location
    return bisect_function(
        mesh_name, 
        mesh_path, 
        config['input_paths']['mesh_path_reference'], 
        num_of_bisect
    )


def create_anomaly(mesh_path, file_path, config):

    mesh_name_tmp = pathlib.Path(mesh_path).stem
    mesh = bpy.context.scene.objects[mesh_name_tmp]

    sigma_random = halfnorm.rvs(
        loc=config['anomaly_settings']['sigma_loc'], 
        scale=config['anomaly_settings']['sigma_scale'], 
        size=1
    )
    strength_random = halfnorm.rvs(
        loc=config['anomaly_settings']['strength_loc'], 
        scale=config['anomaly_settings']['strength_scale'], 
        size=1
    )
    influence_radius = halfnorm.rvs(
        loc=config['anomaly_settings']['influence_radius_loc'], 
        scale=config['anomaly_settings']['influence_radius_scale'], 
        size=1
    )
    pull_prob = max(0, min(config['anomaly_settings']['pull_prob'], 1))
    direction_sign = np.random.choice([-1,1], size=1, p=[1-pull_prob, pull_prob])
    anomaly_vertices = anomaly_function(
        mesh, 
        sigma=sigma_random, 
        strength=strength_random, 
        direction=(0, 0, 1), 
        influence_radius=influence_radius,
        direction_sign=direction_sign
        )
    
    # bpy.ops.export_mesh.stl(
    #     filepath= file_path+".stl", 
    #     check_existing=False, 
    #     use_mesh_modifiers=False)

    return anomaly_vertices


def create_point_cloud(
        mesh_path,
        file_path, 
        config,
        fraction_of_points=0.1,
        randomization=True,
        anomaly=False
    ):

     # Generate reference point clouds
    remove_default_object()
    load_main_object_mesh(mesh_path)

    anomaly_vertices = []
    if anomaly:
        anomaly_vertices = create_anomaly(mesh_path, file_path, config)

    obj = bpy.context.scene.objects[pathlib.Path(mesh_path).stem]
    point_cloud, labels = mesh_to_point_clouds(
        obj, 
        sample_size=3*len(obj.data.vertices), 
        anomaly_vertices=anomaly_vertices
    )

    random_cloud_points(
        point_cloud, 
        file_path, 
        fraction_of_points, 
        randomization=randomization,
        labels=labels
    )


def generate_point_clouds(config, mesh_paths):

    # Check if folder exists
    for folder in ["reference",  "normal", "anomaly"]:
        os.makedirs(
            os.path.join(config['input_paths']['point_cloud_path'], folder), 
            exist_ok=True
        )

    # Setup cameras
    load_main_object_mesh(config['file_paths']['model_path'])
    cameras = create_cameras_around_object(
        bpy.data.objects[pathlib.Path(config['file_paths']['model_path']).stem], 
        config['camera_setting']["radius"], 
        config['camera_setting']["height"], 
        config['camera_setting']["num_of_cameras"]
    )

    for mesh_path in mesh_paths:
        # Generate reference point clouds
        file_path = os.path.abspath(
                os.path.join(
                    config['input_paths']['point_cloud_path'], 'reference', 
                    pathlib.Path(mesh_path).stem
        ))
        # Generate reference point clouds
        remove_default_object()
        load_main_object_mesh(mesh_path)

        mesh_path_vray = delete_non_visible_vertices(
            bpy.context.scene.objects[pathlib.Path(mesh_path).stem], 
            cameras, 
            file_path+"_vray.stl"
        )

        create_point_cloud(
            mesh_path_vray, 
            file_path, 
            config, 
            randomization = False
        )

        # Generate normal variations of point clouds
        for version in range(config['model']['num_generations']):
            create_point_cloud(
                mesh_path_vray,
                os.path.abspath(os.path.join(
                    config['input_paths']['point_cloud_path'], 'normal', 
                    f"{pathlib.Path(mesh_path).stem.replace('reference', 'normal')}_v{version}"
                )), 
                config
            )

            # Generate anomaly variations of point clouds
            create_point_cloud(
                mesh_path_vray, 
                os.path.abspath(os.path.join(
                    config['input_paths']['point_cloud_path'], 'anomaly', 
                    f"{pathlib.Path(mesh_path).stem.replace('reference', 'anomaly')}_v{version}"
                )), 
                config,
                anomaly=True
            )


def pipeline_generate_data(
    config
):
    print("Generating data")
    for path in config['input_paths'].values():
        os.makedirs(path, exist_ok=True)

    # Add original mesh object to dataset
    mesh_paths = [add_original_mesh(config)]

    # Create bisect
    mesh_paths += create_bisect(mesh_paths[0], config)

    # Create point clouds
    generate_point_clouds(config, mesh_paths)

    return mesh_paths


if __name__ == '__main__':

    config_path = os.path.join(
        os.path.abspath(
            os.path.join(dir_path, os.pardir)
            ), 
        'config'
    )

    with open(os.path.join(config_path, 'main_config.yaml')) as file:
        config = yaml.safe_load(file)   

    # Set random seed to be reproducible
    random.seed(int(config['seed']))

    mesh_dict = pipeline_generate_data(config)
    
    