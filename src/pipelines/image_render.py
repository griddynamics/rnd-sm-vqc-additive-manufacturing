import os
import pathlib
import random
import sys
import itertools

import bpy
import yaml
import numpy as np
import bmesh
import math
from mathutils import Vector
from scipy.stats import halfnorm

dir_path = os.path.dirname(os.path.realpath(__file__))
sys.path.insert(0, os.path.dirname(dir_path))

from src.utils.cameras import create_cameras_around_object
from src.utils.lights import (create_lights_on_half_sphere, turn_on_one_light)

# TODO: update image render pipeline
# from src.utils.model import (add_material, add_surface, add_surface_texture,
#                    change_noise_seed, load_main_object_mesh,
#                    normalize_object_size, remove_default_object)


def generate_mesh_list(config):

    mesh_dict = {}

    mesh_dict['main_object'] = config['file_paths']['model_path']

    mesh_dict['bisect'] = [
            os.path.join(config['input_paths']['bisect_mesh_path'], name)
            for name in os.listdir(config['input_paths']['bisect_mesh_path'])
            if pathlib.Path(name).suffix == '.stl'
        ]

    mesh_dict['anomaly'] = [
            os.path.join(config['input_paths']['anomaly_path'], name)
            for name in os.listdir(config['input_paths']['anomaly_path'])
            if pathlib.Path(name).suffix == '.stl'
        ]
    return mesh_dict


def generate_object_for_render(
        config, 
        obj_path,
        surface_flag=False,
        material_flag=False,
        surface_noise_flag=False
    ):

    """Create renders for the given object path and environment config."""
    

    mesh_name = pathlib.Path(obj_path).stem
    mesh = bpy.context.scene.objects[mesh_name]

    if surface_flag:
        add_surface(bpy.data.objects[mesh_name])
        add_surface_texture(
            os.path.abspath(config['file_paths']["texture_path"]), 
            bpy.data.objects["Plane"]
        )

    if material_flag:
        material = add_material(mesh, 1)

    if surface_noise_flag:
        # Change noise seed to generate different noise for each example
        change_noise_seed(material, mesh)


def render_object(camera, file_path):

    # render_gradient_mapping(mesh)
    bpy.context.scene.camera = camera
    bpy.context.scene.render.filepath = file_path
    bpy.ops.render.render(write_still=True)


def pipeline_generate_renders(
        config, 
        mesh_dict,
        reference=True, 
        normal=True, 
        anomaly=True,
    ):

    obj_path = config['file_paths']['model_path']
    mesh_name = pathlib.Path(obj_path).stem

    renders_paths = {}
    for folder in ["reference",  "normal", "anomaly"]:
        renders_paths[folder] = os.path.join(config['input_paths']['renders_path'], folder)
        os.makedirs(renders_paths[folder], exist_ok=True)

    load_main_object_mesh(obj_path)
    # Setup cameras
    cameras = create_cameras_around_object(
        bpy.data.objects[mesh_name], 
        config['camera_setting']["radius"], 
        config['camera_setting']["height"], 
        config['camera_setting']["num_of_cameras"]
    )

    # setup lights
    lights = create_lights_on_half_sphere(
        bpy.data.objects[mesh_name], 
        config['light_setting']["radius"], 
        config['light_setting']["num_lights"], 
        config['light_setting']["energy"]
    )

    if reference:
        # render reference
        for obj_path in mesh_dict['main_object']+mesh_dict['bisect']:
            for camera, light_idx in itertools.product(cameras, range(len(lights))):
                file_path = os.path.abspath(
                    os.path.join(renders_paths['reference'], 
                    f"reference_{pathlib.Path(obj_path).stem}_{camera.name}_light{light_idx:02d}.png"
                    )
                )
                remove_default_object()
                load_main_object_mesh(obj_path)
                mesh_name = pathlib.Path(obj_path).stem
                normalize_object_size(bpy.data.objects[mesh_name], 1)

                generate_object_for_render(
                    config, 
                    obj_path,
                    surface_flag=False,
                    material_flag=False,
                    surface_noise_flag=False   
                )

                turn_on_one_light(
                    lights, 
                    light_idx, 
                    config['light_setting']["energy"]
                )
                
                render_object(
                    camera, 
                    file_path
                )
                remove_default_object()
        

    # render normal
    if normal:
        for obj_path in mesh_dict['main_object']+mesh_dict['bisect']:
            for version in range(config['model']['num_generations']):
                for camera, light_idx in itertools.product(cameras, range(len(lights))):
                    file_path = os.path.abspath(
                        os.path.join(renders_paths['normal'], 
                        f"normal_{pathlib.Path(obj_path).stem}_{camera.name}_light{light_idx:02d}_version_{version}.png"
                        )
                    )
                    remove_default_object()
                    load_main_object_mesh(obj_path)
                    mesh_name = pathlib.Path(obj_path).stem
                    normalize_object_size(bpy.data.objects[mesh_name], 1)

                    generate_object_for_render(
                        config, 
                        obj_path,
                        surface_flag=True,
                        material_flag=True,
                        surface_noise_flag=True   
                    )

                    turn_on_one_light(
                        lights, 
                        light_idx, 
                        config['light_setting']["energy"]
                    )
                    
                    render_object(
                        camera, 
                        file_path
                    )
                    remove_default_object()


    # render anomaly
    if anomaly:
        for obj_path in mesh_dict['anomaly']:
            for camera, light_idx in itertools.product(cameras, range(len(lights))):
                file_path = os.path.abspath(
                    os.path.join(renders_paths['anomaly'], 
                    f"anomaly_{pathlib.Path(obj_path).stem}_{camera.name}_light{light_idx:02d}.png"
                    )
                )
                remove_default_object()
                load_main_object_mesh(obj_path)
                mesh_name = pathlib.Path(obj_path).stem
                normalize_object_size(bpy.data.objects[mesh_name], 1)

                generate_object_for_render(
                    config, 
                    obj_path,
                    surface_flag=True,
                    material_flag=True,
                    surface_noise_flag=False   
                )

                turn_on_one_light(
                    lights, 
                    light_idx, 
                    config['light_setting']["energy"]
                )
                
                render_object(
                        camera, 
                        file_path
                )
                remove_default_object()


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

    mesh_dict = generate_mesh_list(config)

    pipeline_generate_renders(config, mesh_dict)
    