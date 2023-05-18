import os
import random
import sys

import yaml

dir_path = os.path.dirname(os.path.realpath(__file__))
sys.path.insert(0, os.path.dirname(dir_path))

from src.pipelines.data_generator import pipeline_generate_data
from src.pipelines.image_render import (
    pipeline_generate_renders, generate_mesh_list
)

if __name__ == '__main__':

    config_path = os.path.join(
        dir_path, 
        'config'
    )

    with open(os.path.join(config_path, 'main_config.yaml')) as file:
        config = yaml.safe_load(file)   

    # Set random seed to be reproducible
    random.seed(int(config['seed']))

    # mesh_dict = generate_mesh_list(config)
    print("Generating point clouds...")
    mesh_dict = pipeline_generate_data(config)

    
    
    
    