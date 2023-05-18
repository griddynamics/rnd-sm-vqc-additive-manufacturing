import bpy
import math
import mathutils
import random

def create_lights_on_half_sphere(obj, radius, num_lights, energy):
    """
    Create random lights on an imaginary half sphere above the object's center location.

    Args:
        obj: The Blender object to create the lights around.
        radius: The radius of the imaginary half sphere.
        num_lights: The number of lights to create.
        energy: The energy of the lights.

    Returns:
        A list of the created lights.
    """
    lights = []

    # Get the location of the object
    loc = obj.location

    # Create lights on a half sphere above the object's center location
    for i in range(num_lights):
        # Generate random spherical coordinates
        theta = random.uniform(0, math.pi/2)  # elevation angle
        phi = random.uniform(0, 2*math.pi)  # azimuthal angle

        # Calculate the Cartesian coordinates of the point on the half sphere
        x = loc.x + radius * math.sin(theta) * math.cos(phi)
        y = loc.y + radius * math.sin(theta) * math.sin(phi)
        z = loc.z + radius * math.cos(theta)

        # Create a new light
        light_data = bpy.data.lights.new(name="Light" + str(i), type='POINT')
        light_data.energy = energy

        # Create a new object with the light data
        light_obj = bpy.data.objects.new(name="Light" + str(i), object_data=light_data)

        # Link the object to the scene
        bpy.context.scene.collection.objects.link(light_obj)

        # Position the light object
        light_obj.location = mathutils.Vector((x, y, z))

        # Add the light to the list of lights
        lights.append(light_obj)

    return lights

def turn_on_one_light(lights, index, energy):
    """
    Turn on one light at a time and keep the rest off.

    Args:
        lights: A list of light objects.
        index: The index of the light to turn on.
    """
    for i, light in enumerate(lights):
        if i == index:
            light.data.energy = energy  # Turn on the selected light
        else:
            light.data.energy = 0.0  # Turn off all other lights
