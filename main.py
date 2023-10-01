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
wall_min = 0.4 # Minimum wall width, if aligned with
wall = wall_min * 3

# ================== PARAMETERS ==================
# USB
usb_conn_width = 12
usb_conn_height = 4.5
usb_conn_depth = 10
usb_conn_platform_y = [0.4 - tol, 1.9 + tol * 3]
usb_conn_platform_height = usb_conn_platform_y[1] - usb_conn_platform_y[0]
usb_conn_platform_width = usb_conn_width - wall_min*2

# Pins
pin_conn_size = cq.Vector(0.8, 0.8, 6)
pin_handle_size = cq.Vector(2.7, 2.7, 14.1)
pin_sep = 7 # Distance between the centers of the power and ground pins

# ================== MODELLING ==================
# Create a basic connector that will fit in a USB
usb_box = (
    cq.Workplane("XY")
    .box(usb_conn_width, usb_conn_height, usb_conn_depth + wall_min, centered=[True, False, True])
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
pin_box_extrusion = pin_handle_size.z + pin_conn_size.z - usb_conn_depth + wall
pin_box = (
    usb_conn
    .faces(">Z")
    .workplane(centerOption="CenterOfMass")
    .rect(usb_conn_width, usb_conn_height)
    .extrude(pin_box_extrusion)
)
pin_box_height_adjust = pin_conn_size.y - wall_min
pin_conn = (
    pin_box
    .faces(">Z")
    .workplane(centerOption="CenterOfMass")
    .transformed(offset=cq.Vector(0, pin_box_height_adjust, 0))
    # Cable
    .pushPoints([cq.Vector(-pin_sep/2, 0, 0), cq.Vector(pin_sep/2, 0, 0)])
    .rect(pin_conn_size.x + tol, (pin_conn_size.y + tol) * 2) # Hack for easier cut later
    .cutBlind(-wall)
    # Handle
    .transformed(offset=cq.Vector(0, 0, -wall))
    .pushPoints([cq.Vector(-pin_sep/2, 0, 0), cq.Vector(pin_sep/2, 0, 0)])
    .rect(pin_handle_size.x + tol, pin_handle_size.y + tol)
    .cutBlind(-pin_handle_size.z)
    # Pin
    .transformed(offset=cq.Vector(0, 0, -pin_handle_size.z))
    .pushPoints([cq.Vector(-pin_sep/2, 0, 0), cq.Vector(pin_sep/2, 0, 0)])
    .rect(pin_conn_size.x + tol, pin_conn_size.y + tol)
    .cutBlind(-pin_conn_size.z)
)

# Now split the connector into two parts that get inserted at the same time
# Required for printing without supports
one_part_connector = pin_conn
bb = one_part_connector.val().BoundingBox()
cutPeakZ = bb.center.z - bb.zlen/3
cutBaseHeight = bb.center.y - wall_min
cutExtraHeight = wall_min*1.5
cut_width_eps = 0.001
split_pattern_surface = (
    cq.Workplane("YZ")
    .moveTo(cutBaseHeight - cut_width_eps, bb.zmin)
    .lineTo(cutBaseHeight, bb.zmin)
    .lineTo(cutBaseHeight, cutPeakZ)
    .lineTo(cutBaseHeight + cutExtraHeight, cutPeakZ)
    .lineTo(cutBaseHeight, cutPeakZ +  + wall)
    .lineTo(cutBaseHeight, bb.zmax)
    .lineTo(cutBaseHeight - cut_width_eps, bb.zmax)
    .lineTo(cutBaseHeight- cut_width_eps, cutPeakZ + wall - cut_width_eps)
    .lineTo(cutBaseHeight + cutExtraHeight - cut_width_eps*2, cutPeakZ + cut_width_eps)
    .lineTo(cutBaseHeight- cut_width_eps, cutPeakZ + cut_width_eps)
    .close() 
    .extrude(usb_conn_width/2, both=True)
)
ignore_middle_cut = (
    cq.Workplane("XY")
    .transformed(offset=(0, 0, -wall_min))
    .box(bb.xlen - wall_min*2, bb.ylen*2, usb_conn_depth)
)
#debug(ignore_middle_cut)
split_pattern_surface = (
    split_pattern_surface
    .cut(ignore_middle_cut)
)
#debug(split_pattern_surface)

conn_parts_merged = (
    one_part_connector
    .cut(split_pattern_surface)
    .solids() 
)
conn_parts = [cq.Workplane(x) for x in conn_parts_merged.vals()]

# ================== SHOW / EXPORT BOILERPLATE ==================
final_objs = conn_parts
if 'show_object' in globals(): # If using cq-editor, only render the final object
    for i, final_obj in enumerate(final_objs):
        show_object(final_obj, name="final_obj_{}".format(i))
else: # Otherwise, export stl
    for i, final_obj in enumerate(final_objs):
        with open('obj_{}.stl'.format(i), 'w') as out:
            cq.exporters.exportShape(final_obj, 'STL', out, tolerance=0.01, angularTolerance=0.01)