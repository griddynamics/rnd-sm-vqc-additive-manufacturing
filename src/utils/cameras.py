import math

import bpy
import open3d as o3d
from mathutils import Vector, Matrix

from src.utils.mesh_utils import  get_norm_factor, get_object_center


def get_trajectory_camera_file(bpy_obj, file_path="camera_traj.json"):
    '''Creates and saves camera trajectory file for point cloud allignment
    Params: 
    bpy_obj (bpy.data.obj) - object used to calculate camera trajectories
    file_path (str) - path to save to'''
    scene = bpy_obj.context.scene
    camera_poses = []
    camera_trajectory = o3d.camera.PinholeCameraTrajectory()
    for camera_name in sorted(bpy_obj.data.cameras.keys()):

        # reference to intrinsic matrix calculation
        # https://mcarletti.github.io/articles/blenderintrinsicparams/#:~:text=The%20intrinsic%20matrix%20K%20is,point%20of%20the%20image%20frame).
        camera_data = bpy_obj.data.cameras[camera_name]

        scale = scene.render.resolution_percentage / 100
        width = scene.render.resolution_x * scale # px
        height = scene.render.resolution_y * scale # px

        focal = camera_data.lens # mm
        sensor_width = camera_data.sensor_width # mm
        sensor_height = camera_data.sensor_height # mm
        pixel_aspect_ratio = scene.render.pixel_aspect_x / scene.render.pixel_aspect_y

        if (camera_data.sensor_fit == 'VERTICAL'):
            # the sensor height is fixed (sensor fit is horizontal), 
            # the sensor width is effectively changed with the pixel aspect ratio
            s_u = width / sensor_width / pixel_aspect_ratio 
            s_v = height / sensor_height
        else: # 'HORIZONTAL' and 'AUTO'
            # the sensor width is fixed (sensor fit is horizontal), 
            # the sensor height is effectively changed with the pixel aspect ratio
            pixel_aspect_ratio = scene.render.pixel_aspect_x / scene.render.pixel_aspect_y
            s_u = width / sensor_width
            s_v = height * pixel_aspect_ratio / sensor_height

        # parameters of intrinsic calibration matrix
        fx = focal * s_u
        fy = focal * s_v
        cx = width / 2
        cy = height / 2
        # skew = 0 # only use rectangular pixels
        # intrinsic_matrix = [fx, skew, cx, 0, fy, cy, 0, 0, 1]
        
        # object_center = bpy.data.objects['lattice_test4']
        camera_object = bpy.data.objects[camera_name]

        # reference to extrinsic matrix
        # http://www.land-of-kain.de/docs/python_blender/
        RT = camera_object.matrix_world.inverted()
        extrinsic_matrix = RT * Matrix(np.diag([1., 1., -1., 1.]))

        intrinsic_matrix = o3d.camera.PinholeCameraIntrinsic(int(width), int(height), fx, fy, cx, cy)
        camera_o3d = o3d.camera.PinholeCameraParameters()
        camera_o3d.extrinsic = extrinsic_matrix
        camera_o3d.intrinsic = intrinsic_matrix

        # Add the camera to the list
        camera_poses.append(camera_o3d)

    camera_trajectory.parameters = camera_poses
    o3d.io.write_pinhole_camera_trajectory(file_path, camera_trajectory)    
    return True


def create_cameras_around_object(obj, radius, height, num_cams, normalization=1):
    """
    Create a circle of cameras around an object.

    Args:
        obj: The Blender object to create the cameras around.
        radius: The radius of the circle of cameras.
        height: The height above the object that the cameras should be placed.
        num_cams: The number of cameras to create.

    Returns:
        A list of the created cameras.
    """
    cameras = []

    # Get the location of the object
    obj_center = get_object_center(obj)
    norm_factor = get_norm_factor(obj, normalization)
    # Create cameras in a circle around the object
    for i in range(num_cams):
        # Calculate the angle for this camera
        angle = i * 2 * math.pi / num_cams

        # Calculate the position of the camera
        x = obj.location.x + radius * math.cos(angle)
        y = obj.location.y + radius * math.sin(angle)
        z = obj.location.z + height

        # Create a new camera
        cam = bpy.data.cameras.new("Camera" + str(i))
        cam_obj = bpy.data.objects.new("Camera" + str(i), cam)
        cam.lens=35.0
        
        bpy.context.scene.collection.objects.link(cam_obj)

        # Position and aim the camera
        cam_obj.location = Vector((x, y, z))
        direction = cam_obj.location - (obj_center * norm_factor)

        rot = direction.to_track_quat('Z', 'Y').to_matrix().to_4x4()
        loc = Matrix.Translation(cam_obj.location)

        cam_obj.matrix_world =  loc @ rot

        # Add the camera to the list of cameras
        cameras.append(cam_obj)

    return cameras
