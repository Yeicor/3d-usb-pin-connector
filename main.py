# ================== IMPORTS BOILERPLATE ==================
import cadquery as cq
import os
from_cq_editor = False
if 'show_object' in globals(): # If using cq-editor, only render the final object
    from_cq_editor = True
    show = show_object
else:
    show = lambda *args, **kwargs: print("Ignoring show(...) as cq-editor was not detected")
    debug = lambda *args, **kwargs: print("Ignoring debug(...) as cq-editor was not detected")
tol = 0.2 # Tolerance
wall = 0.4 # Minimum wall width, if aligned with

# ================== PARAMETERS ==================
# USB
usb_conn_width = 12
usb_conn_height = 4.5
usb_conn_depth = 10
usb_conn_platform_y = [0.4 - tol, 1.9 + tol * 3]
usb_conn_platform_height = usb_conn_platform_y[1] - usb_conn_platform_y[0]
usb_conn_platform_width = usb_conn_width - wall*2

# Pins
pin_conn_size = cq.Vector(0.8, 0.8, 6)
pin_handle_size = cq.Vector(2.7, 2.7, 14.1)
pin_sep = 7 # Distance between the centers of the power and ground pins

# ================== MODELLING ==================
# Create a basic connector that will fit in a USB
usb_box = (
    cq.Workplane("XY")
    .box(usb_conn_width, usb_conn_height, usb_conn_depth + wall, centered=[True, False, True])
)
usb_conn = (
    usb_box
    .faces("<Z")
    .workplane()
    .transformed(offset=(0, -usb_conn_platform_y[0] - usb_conn_platform_height/2, 0))
    .rect(usb_conn_platform_width, usb_conn_platform_y[1]-usb_conn_platform_y[0])
    .cutBlind(-usb_conn_depth)
)

# Create the box and holes for the pins
#debug(usb_conn.faces(">Z"))
pin_box_extrusion = pin_handle_size.z + pin_conn_size.z - usb_conn_depth
pin_box_height_adjust = pin_conn_size.y - wall
pin_box = (
    usb_conn
    .faces(">Z")
    .workplane(centerOption="CenterOfMass")
    .transformed(offset=cq.Vector(0, pin_box_height_adjust, 0))
    .rect(pin_sep + pin_handle_size.x + wall * 2, pin_handle_size.y + wall * 2)
    .extrude(pin_box_extrusion)
)
pin_conn = (
    pin_box
    .faces(">Z")
    .workplane(centerOption="CenterOfMass")
    .pushPoints([cq.Vector(-pin_sep/2, 0, 0), cq.Vector(pin_sep/2, 0, 0)])
    .rect(pin_handle_size.x, pin_handle_size.y)
    .cutBlind(-pin_handle_size.z)
    .pushPoints([cq.Vector(-pin_sep/2, 0, 0), cq.Vector(pin_sep/2, 0, 0)])
    .rect(pin_conn_size.x, pin_conn_size.y)
    .cutBlind(-pin_handle_size.z - pin_conn_size.z)
)

# ================== SHOW / EXPORT BOILERPLATE ==================
final_obj = pin_conn
if 'show_object' in globals(): # If using cq-editor, only render the final object
    show_object(final_obj, name="final_obj")
else: # Otherwise, export stl
    with open('obj.stl', 'w') as out:
        cq.exporters.exportShape(final_obj, 'STL', out, tolerance=0.01, angularTolerance=0.01)