import random
import math

import bpy
from mathutils import Vector


def find_highest_vertex_on_xy_plane(mesh):

    # Select random vertex to generate anomaly on
    rdm = random.choice(mesh.vertices)

    # Choose a random point in the bounding box on the X-Y plane
    x = rdm.co[0]
    y = rdm.co[1]
    point = (x, y, 0.0)

    # Find the vertex in the mesh with the highest Z-coordinate value at that point
    highest_vertex = None
    highest_z = float('-inf')

    for vertex in mesh.vertices:
        if math.isclose(vertex.co.z, highest_z, rel_tol=1e-6):
            # This vertex has the same Z-coordinate as the highest vertex so far
            # We'll choose one of them randomly
            if random.random() < 0.5:
                highest_vertex = vertex
        elif vertex.co.z > highest_z and math.isclose(vertex.co.x, point[0], rel_tol=1) and math.isclose(vertex.co.y, point[1], rel_tol=1):
            # This vertex has a higher Z-coordinate than the current highest vertex, and is at the same X-Y point
            highest_vertex = vertex
            highest_z = vertex.co.z

    return highest_vertex


def find_nearby_vertices_influence(mesh_object, vertex, influence_radius, sigma):
    
    mesh = mesh_object.data
    selected_vertices = []
    for nearby_vertex in mesh.vertices:
        # Calculate the distance between the vertices
        distance = (Vector(nearby_vertex.co) - vertex.co).length

        # Apply the influence of the sigma parameter
        influence = math.exp(-distance**2 / (2*sigma**2))

        # Check if the nearby vertex is within the influence radius
        if distance <= influence_radius:
            # Add the vertex to the list of selected vertices
            selected_vertices.append((nearby_vertex, influence))

    return selected_vertices


def anomaly_function(
        mesh_object, 
        sigma, 
        strength, 
        direction, 
        influence_radius=1, 
        direction_sign=1
        ):

    """# Get a mesh object by name
    mesh_object = bpy.data.objects['Cube']

    # Define the parameters for the pull function
    sigma = 0.1
    strength = 0.05
    direction = (1, 0, 0)
    push = True
    """

    if not mesh_object.data.vertices:
        print("Mesh has no vertices")
        return
    
    # Get the mesh data from the object
    mesh = mesh_object.data

    if not mesh.vertex_colors:
        mesh.vertex_colors.new()
    color_layer = mesh.vertex_colors['Col']

    # Get a list of vertices that face the Z axis and are at the top surface level
    center_vertex = find_highest_vertex_on_xy_plane(mesh)
    nearby_vertices = find_nearby_vertices_influence(mesh_object, center_vertex, influence_radius, sigma)

    normal =  Vector((0,0,1)) # mathutils.geometry.normal([v.co for v,i in nearby_vertices]) # Vector((0,0,1)) #  
    normal.z *= abs(normal.z) * direction_sign

    strengths = {}
    for vertex, influence in nearby_vertices:
        direction = normal * strength * influence
        # Add the direction of pull to the vertex's location
        vertex.co += direction
        strengths[vertex.index] = abs(strength * influence)

    max_strength = max(strengths.values())

    vertex_indices = set([vertex.index for vertex, _ in nearby_vertices])
    for poly in mesh.polygons:
        for loop_index in poly.loop_indices:
            loop_vert_index = mesh.loops[loop_index].vertex_index
            if loop_vert_index in vertex_indices:
                color_layer.data[loop_index].color = (strengths[loop_vert_index]/max_strength, 0, 1 - strengths[loop_vert_index]/max_strength, 1.0)
            else:
                color_layer.data[loop_index].color = (0.0, 0.0, 1.0, 1.0)

    selected_vertices = set([vertex.index for vertex, _ in nearby_vertices])

    # Update the mesh
    mesh.update()

    return selected_vertices


def render_gradient_mapping(mesh_obj):

    mesh = mesh_obj.data

    # Load material
    anomaly_material = bpy.data.materials.get("AnomalyMaterial")
    if anomaly_material is None:
        anomaly_material = bpy.data.materials.new(name = "AnomalyMaterial")
        
    anomaly_material.use_nodes = True
        
    # Link material to mesh
    if mesh.materials:
        mesh.materials[0] = anomaly_material
    else:
        mesh.materials.append(anomaly_material)
        

    # ---------- MANAGE NODES OF SHADER EDITOR ----------

    # Get node tree from the material
    nodes = anomaly_material.node_tree.nodes
    principled_bsdf_node = nodes.get("Principled BSDF")

    # Get Vertex Color Node, create it if it does not exist in the current node tree
    vertex_color_node = None
    if not "VERTEX_COLOR" in [node.type for node in nodes]:
        vertex_color_node = nodes.new(type = "ShaderNodeVertexColor")
    else:
        vertex_color_node = nodes.get("Vertex Color")

    # Set the vertex_color layer we created at the beginning as input
    vertex_color_node.layer_name = "Col"

    # Link Vertex Color Node "Color" output to Principled BSDF Node "Base Color" input
    anomaly_material.node_tree.links.new(vertex_color_node.outputs[0], principled_bsdf_node.inputs[0])

    return anomaly_material

