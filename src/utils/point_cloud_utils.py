import random

import bpy
import bmesh
import numpy as np
import pandas as pd
import open3d as o3d

from bpy_extras import mesh_utils
from mathutils import Vector


def delete_non_visible_vertices(target, cameras, file_path):
    
    scene = bpy.context.scene
    mesh = target.data
    faces_set = set()

    for cam in cameras:
        frame = cam.data.view_frame(scene=scene)

        topRight = frame[0]
        bottomRight = frame[1]
        bottomLeft = frame[2]
        topLeft = frame[3]
        scale = scene.render.resolution_percentage / 100
        resolutionX = int(scene.render.resolution_x * scale) # px
        resolutionY = int(scene.render.resolution_y * scale) # px
        
        # setup vectors to match pixels
        xRange = np.linspace(topLeft[0], topRight[0], resolutionX)
        yRange = np.linspace(topLeft[1], bottomLeft[1], resolutionY)

        # calculate origin
        matrixWorld = target.matrix_world
        matrixWorldInverted = matrixWorld.inverted()
        origin = matrixWorldInverted @ cam.matrix_world.translation
        
        # iterate over all X/Y coordinates
        for x in xRange:
            for y in yRange:
                # get current pixel vector from camera center to pixel
                pixelVector = Vector((x, y, topLeft[2]))
                # rotate that vector according to camera rotation
                pixelVector.rotate(cam.matrix_world.to_quaternion())

                # calculate direction vector
                destination = matrixWorldInverted @ (pixelVector + cam.matrix_world.translation) 
                direction = (destination - origin).normalized()
                # perform the actual ray casting
                hit, location, norm, face =  target.ray_cast(origin, direction)
                
                if hit:
                    faces_set.add(face)
    
    bpy.context.view_layer.objects.active = target
    bpy.ops.object.mode_set(mode='EDIT')

    bm = bmesh.from_edit_mesh(mesh)
    bm.faces.ensure_lookup_table()
    faces_delete = []
    for f in bm.faces:
        if f.index not in faces_set:
            faces_delete.append(f)

    bmesh.ops.delete(bm, geom=list(faces_delete), context="FACES")
    bmesh.update_edit_mesh(mesh, destructive=True)

    bpy.ops.export_mesh.stl(
            filepath= file_path, 
            check_existing=False, 
            use_mesh_modifiers=False)
    
    return file_path


def mesh_to_point_clouds(
    mesh_object, 
    sample_size, 
    anomaly_vertices, 
    draw_random_points=1
):
    
    selected_vertices = []
    selected_vertices_labels = []
    me = mesh_object.data
    anomaly_polygons = set()
    anomaly_sample_size = 0
    if len(anomaly_vertices)>0:
        anomaly_vertices = set(anomaly_vertices)
        for polygon in mesh_object.data.polygons:
            for vertex in mesh_object.data.polygons[polygon.index].vertices:
                if int(vertex) in anomaly_vertices:
                    anomaly_polygons.add(polygon.index)
                    break

    me.calc_loop_triangles()
    
    triangles_select = [
        f for f in me.loop_triangles if f.polygon_index not in anomaly_polygons]

    anomaly_triangles_select = [
        f for f in me.loop_triangles if f.polygon_index in anomaly_polygons]

    if len(anomaly_vertices)>0:
        anomaly_sample_size = max(10, int(sample_size*
            len(anomaly_triangles_select)/len(triangles_select)))
    else: 
        anomaly_sample_size = 0

    normal_sample_size = sample_size-anomaly_sample_size

    surfaces = map(lambda t: t.area, triangles_select)

    choices = random.choices(
        population=triangles_select, 
        weights=surfaces, 
        k=normal_sample_size)
    
    normal_vertices = mesh_utils.triangle_random_points(
        draw_random_points, choices)
    
    selected_vertices = [v[:] for v in normal_vertices]
    selected_vertices_labels = [False]*draw_random_points*normal_sample_size

    if anomaly_sample_size>0:
        surfaces = map(lambda t: t.area, anomaly_triangles_select)

        choices = random.choices(
            population=anomaly_triangles_select, 
            weights=surfaces, 
            k=anomaly_sample_size)
        
        anomaly_vertices = mesh_utils.triangle_random_points(
            draw_random_points, choices)
        
        selected_vertices += [v[:] for v in anomaly_vertices]
        selected_vertices_labels += [True]*draw_random_points*anomaly_sample_size


    return  selected_vertices, selected_vertices_labels


def random_cloud_points(
    point_cloud,
    file_path, 
    fraction_of_points=0.1,
    fraction_of_variation=0.3,
    std_scale=1e-2,
    randomization=True,
    labels=None
):  
    dimensional_columns = ['x', 'y', 'z']
    df = pd.DataFrame(point_cloud, columns=dimensional_columns)
    if labels is None:
        df['label'] = False
    else:
        df['label'] = labels
    df_sample = df.sample(
        frac=fraction_of_points,
       #  weights=df.groupby('label')['label'].transform('count')
    )
    num_points = df_sample.shape[0]
    num_points_variation = int(num_points*fraction_of_variation)

    if randomization:
        z_idx = df_sample.sample(num_points_variation).index
        df_sample.loc[z_idx, 'z'] += (
            df_sample.loc[z_idx, 'z']*np.random.normal(
            loc=0.0, scale=std_scale, size=num_points_variation
        ))

    df_sample.to_csv(file_path+".csv", index=False)
    pcd = o3d.geometry.PointCloud()
    pcd.points = o3d.utility.Vector3dVector(df_sample.loc[:,dimensional_columns].values)
    o3d.io.write_point_cloud(file_path+".pcd", pcd)