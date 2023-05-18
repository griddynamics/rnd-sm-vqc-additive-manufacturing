import random
import bpy

from src.utils.mesh_utils import  get_norm_factor, get_object_center


def combine_materials(mat1_name, mat2_name, new_mat_name):
    # Get the two materials to be combined
    mat1 = bpy.data.materials.get(mat1_name)
    mat2 = bpy.data.materials.get(mat2_name)
    
    # Create a new material to hold the combined properties
    new_mat = bpy.data.materials.new(name=new_mat_name)
    
    # Combine the material properties
    for prop in mat1.keys():
        new_mat[prop] = mat1[prop]
    for prop in mat2.keys():
        new_mat[prop] = mat2[prop]
    
    # Assign the new material to all objects that use the original materials
    for obj in bpy.context.scene.objects:
        if obj.material_slots:
            for slot in obj.material_slots:
                if slot.material == mat1 or slot.material == mat2:
                    slot.material = new_mat
    
    # Remove the original materials
    bpy.data.materials.remove(mat1)
    bpy.data.materials.remove(mat2)

    return new_mat_name


def add_material(obj, scale, anomaly_material=None):
    """
    Adds surface material, texture, noise and surface deformation to object
    Params:
        obj (bpy.data.object)- Blender object of type bpy.data.object
        scale (float) - scale factor of 
    Returns:
        material (bpy.data.materials)
    """
    
    if anomaly_material is None:
        # Add material
        material = bpy.data.materials.new(name="Material1")
        obj.data.materials.append(material)
        material.use_nodes=True
    else:
        # Load material
        material = bpy.data.materials.get(anomaly_material)


    mat_node_tree = material.node_tree
    mat_nodes = mat_node_tree.nodes
    mat_links = mat_node_tree.links

    # Set material properties
    # mat_nodes['Principled BSDF'].inputs["Metallic"].default_value=1.0
    # mat_nodes['Principled BSDF'].inputs["Metallic"].default_value=0.7

    # Add texture to material
    mat_node_tree.nodes.new("ShaderNodeTexCoord")
    mat_node_tree.nodes.new("ShaderNodeMapping")
    mat_node_tree.nodes.new("ShaderNodeTexMusgrave")

    # Add noise
    mat_node_tree.nodes["Musgrave Texture"].musgrave_type = "MULTIFRACTAL"
    mat_node_tree.nodes["Musgrave Texture"].musgrave_dimensions = "3D"
    mat_node_tree.nodes["Musgrave Texture"].inputs['Scale'].default_value = scale # scale range
    mat_node_tree.nodes["Musgrave Texture"].inputs['Detail'].default_value = 0.7
    # mat_node_tree.nodes["Musgrave Texture"].location = Vector([random.randrange(0, 250) for _ in range(2)])
    mat_links.new(mat_nodes['Principled BSDF'].inputs[0], mat_node_tree.nodes["Musgrave Texture"].outputs[0])
    mat_links.new(mat_nodes['Musgrave Texture'].inputs[0], mat_node_tree.nodes["Mapping"].outputs[0])
    mat_links.new(mat_node_tree.nodes["Mapping"].inputs[0], mat_node_tree.nodes["Texture Coordinate"].outputs[3])
    
    return material


def change_noise_seed(material, obj):
    '''
    Changes surface noise location and scale creating variation between different items using random.randrange() function
    Params:
        material (bpy.data.materials) - material to which noise should be changed
        obj (bpy.data.object) - Blender object which receives the noise change
    '''
    # Moves noise texture to create a different pattern
    mat_node_tree = material.node_tree
    mat_node_tree.nodes["Mapping"].inputs["Rotation"].default_value.x = random.randrange(100)
    mat_node_tree.nodes["Mapping"].inputs["Rotation"].default_value.y = random.randrange(100)
    mat_node_tree.nodes["Mapping"].inputs["Rotation"].default_value.z = random.randrange(100)
    mat_node_tree.nodes["Mapping"].inputs["Location"].default_value.x = random.randrange(100)
    mat_node_tree.nodes["Mapping"].inputs["Location"].default_value.y = random.randrange(100)
    mat_node_tree.nodes["Mapping"].inputs["Location"].default_value.z = random.randrange(100)
    
    # Adds displace modifier which adds geometric bumps and crevaces 
    modifier = obj.modifiers.new(name="Displace", type='DISPLACE')

    # Noise basis. Cloud gives smoother noise than other tested noise patterns
    modifier.texture = bpy.data.textures.new('Clouds', type="CLOUDS")
    # Determines intensity of deform
    modifier.strength = random.randrange(0,12)/10

    # Size of bumps and holes
    bpy.data.textures["Clouds"].noise_scale = random.randrange(0, 2500)/100 
    bpy.data.textures["Clouds"].noise_basis = "VORONOI_F2_F1"
    bpy.data.textures["Clouds"].noise_type = "SOFT_NOISE"
    bpy.ops.object.modifier_apply(modifier="Clouds")
    return modifier


def add_surface(obj, size=1.2):
    """Adds plane to under center of object on which it is displayed
    Params:
    obj (bpy.data.object) - Object under which plane is positioned
    size (int) - scale of object which is parsed"""
    norm_factor = get_norm_factor(obj, 1)
    obj_center = get_object_center(obj)
    plane_location = (obj_center[0] * norm_factor, obj_center[1] * norm_factor, -0.02)
    plane = bpy.ops.mesh.primitive_plane_add(
        size=size,
        align="WORLD",
        location=plane_location)
    

def add_surface_texture(texture_path, obj):
    """Adds texture to surface on which object is displayed
    Params:
    texture_path (str) - path to texture iamge
    obj (bpy.data.object) - obj to which texture is applied"""

    # Add material
    mat = bpy.data.materials.new(name="New_Mat")
    mat.use_nodes = True
    # Generate surface
    bsdf = mat.node_tree.nodes["Principled BSDF"]
    texImage = mat.node_tree.nodes.new('ShaderNodeTexImage')
    texImage.image = bpy.data.images.load(texture_path)
    mat.node_tree.links.new(bsdf.inputs['Base Color'], texImage.outputs['Color'])

    ob = bpy.context.view_layer.objects.active

    # Assign it to object
    if ob.data.materials:
        ob.data.materials[0] = mat
    else:
        ob.data.materials.append(mat)
    
