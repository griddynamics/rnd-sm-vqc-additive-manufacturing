import os
import pathlib

import bpy
import numpy as np
from mathutils import Vector


def add_original_mesh(config):

    main_mesh_path = config['file_paths']['model_path']
    main_mesh_name = pathlib.Path(main_mesh_path).stem

    remove_default_object()
    load_main_object_mesh(main_mesh_path)
    file_path = os.path.join(
        config['input_paths']['mesh_path_reference'], 
        f"reference_{main_mesh_name}.stl"
    )
    bpy.ops.export_mesh.stl(filepath= file_path)
    remove_default_object()

    return file_path


def remove_default_object():
    '''Removes all materials, objects and textures in scene
    '''
    # for o in bpy.data.objects:
    #     bpy.data.objects.remove(o)

    for obj in bpy.data.objects:
        if obj.type != 'CAMERA':
            if obj.type != 'LIGHT':
                bpy.data.objects.remove(obj)

    for o in bpy.context.scene.objects:
        if o.type != 'CAMERA':
            if o.type != 'LIGHT': 
                bpy.ops.object.delete(use_global=False)
                bpy.data.objects.remove(bpy.data.objects[o.name], do_unlink=True)

    for material in bpy.data.materials:
        material.user_clear()
        bpy.data.materials.remove(material)

    for texture in bpy.data.textures:
        bpy.data.textures.remove(texture)


def load_main_object_mesh(mesh_path):
    '''Loads blender mesh from given path
    Params:
        path (str) - path to mesh'''
    
    bpy.ops.import_mesh.stl(filepath=mesh_path)
    bpy.ops.object.mode_set( mode = 'OBJECT' ) # Make sure we're in object mode
    bpy.ops.object.origin_set( type = 'ORIGIN_GEOMETRY' ) # Move object origin to center of geometry
    bpy.ops.object.location_clear()


def get_object_center(o):
    '''Calculates bounding box center
    Params:
        o (bpy.data.object) - objects whose center to calculate
    Returns:
    local_bbox_center (mathutils.Vector) - center of mass for object
    '''
    local_bbox_center = 0.125 * sum((Vector(b) for b in o.bound_box), Vector())
    return local_bbox_center


def get_norm_factor(object, size):
    '''Calculates normalization factor so scaling of object is between 0 and 1
    Note: Vertex coordinates still have a larger value but object is then rendered as smaller
    Params:
    object (bpy.data.object) - Object used to calculate scaling factor
    size (int: default 1) - Value to which to normalize to'''
    x = object.dimensions.x
    y = object.dimensions.y 
    z = object.dimensions.z
    return size / max([x, y, z])


def normalize_object_size(object, size):
    '''Applies resize scale to object
    Params:
    context (bpy.context)
    size (int) - unit to scale to'''

    scale_back = max(object.dimensions)
    object.scale *= size / scale_back

    return scale_back


def bisect_function(
    obj_name, 
    input_path, 
    output_path,
    num_of_bisect=10
    ):
    '''Generates bisects of given object and saves them as .stl files at given location
    Params:
    obj_name (str) - name of object to find in bpy.data.objects to be used as key
    input_path (str) - path to .stl file to be bisected
    output_path (str) - path to which bisected .stl mesh will be saved
    num_of_bisect (int) - number of bisects to be created'''

    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_mesh.stl(filepath=input_path)
    bpy.ops.object.mode_set(mode='OBJECT') 
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)

    # Calculates bounding box axis
    bb = list((Vector(b) for b in bpy.data.objects[obj_name].bound_box))
    _, _, z = tuple(bb[i] - bb[0] for i in (4, 3, 1))

    files_location = []
    for suffix, i in enumerate(np.linspace(0, int(z[-1]), num=num_of_bisect)): 
        if i == 0:
            continue
        bpy.ops.wm.read_factory_settings(use_empty=True)
        bpy.ops.import_mesh.stl(filepath=input_path)
        bpy.ops.object.mode_set(mode='OBJECT') 
        bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)

        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_all(action='SELECT')
        bpy.ops.mesh.bisect(plane_co=(0, 0, i),
                            plane_no=(0, 0, i+1),
                            use_fill=True,
                            clear_inner=False,
                            clear_outer=True,
                            threshold=0.001,
                            cursor=1002)
        file_path = os.path.join(output_path, f"{pathlib.Path(input_path).stem}_bisect_{suffix}.stl")
        bpy.ops.export_mesh.stl(filepath= file_path)
        files_location.append(file_path)

    return files_location     

