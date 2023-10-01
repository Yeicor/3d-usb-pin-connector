# A basic 3D printed connector that will:
# - Fit in the top-half of a USB
# - Connect 2 pins to power and ground

# ================== IMPORTS BOILERPLATE ==================
import cadquery as cq
import os, math
from_cq_editor = False
if 'show_object' in globals(): # If using cq-editor, only render the final object
    from_cq_editor = True
    show = show_object
else:
    show = lambda *args, **kwargs: print("Ignoring show(...) as cq-editor was not detected")
    debug = lambda *args, **kwargs: print("Ignoring debug(...) as cq-editor was not detected")

# ================== PARAMETERS ==================
# 3D printing basics
tol = 0.2 # Tolerance
wall_min = 0.4 # Minimum wall width
wall = wall_min * 3 # Recommended wall width

# USB
usb_conn_size = cq.Vector(12, 4.5, 10)
usb_conn_platform_size = cq.Vector(usb_conn_size.x - wall_min*2, usb_conn_size.y/2, usb_conn_size.z)

# Pins
pin_conn_size = cq.Vector(1, 1, 6)
pin_handle_size = cq.Vector(2.8, 2.8, 14.2)
pin_sep = 7 # Distance between the centers of the power and ground pins

# ================== MODELLING ==================

# Complete box to work on...
max_depth = wall + tol*2 + pin_handle_size.z + max(usb_conn_size.z, pin_conn_size.z + wall)
obj = (
    cq.Workplane("YZ")
    .box(usb_conn_size.x, usb_conn_size.y, max_depth, centered=[True, False, True])
)

# Add a stopper on the back for the cover...
#debug(obj.faces("<X"))
obj = (
    obj
    .faces("<X")
    .workplane()
    .pushPoints([cq.Vector(-usb_conn_size.x/2-wall, 0, 0), cq.Vector(usb_conn_size.x/2, 0, 0)])
    .rect(wall, usb_conn_size.y, centered=[False, False])
    .extrude(-wall)
)

# Without the usb platform...
#debug(obj.faces(">X"))
obj = (
    obj
    .faces(">X")
    .workplane()
    .rect(usb_conn_platform_size.x, usb_conn_platform_size.y, centered=[True, False])
    .cutBlind(-usb_conn_platform_size.z)
)

# With pin holes
#debug(obj.faces("|Z").faces(">>Z[1]"))
obj = (
    obj
    .faces("|Z").faces(">>Z[1]")
    .workplane()
    .transformed(offset=cq.Vector(-usb_conn_platform_size.z, 0, 0))
    .pushPoints([cq.Vector(0, -pin_sep/2, 0), cq.Vector(0, pin_sep/2, 0)])
    .rect(pin_conn_size.z + tol * 2, pin_conn_size.x + tol * 2, centered=[False, True])
    .cutBlind(-(pin_conn_size.y + tol * 2))
)

# With pin handle and cable holes
#debug(obj.faces("%Plane and |X").faces(">>X[2]"))
obj = (
    obj
    .faces("%Plane and |X").faces(">>X[2]")
    .workplane()
    .pushPoints([cq.Vector(-pin_sep/2, 0, 0), cq.Vector(pin_sep/2, 0, 0)])
    .rect(pin_handle_size.x + tol * 2, pin_handle_size.y + tol * 2)
    .cutBlind(-(pin_handle_size.z + tol * 2))
)

# With cable holes
#debug(obj.faces("%Plane and |X").faces(">>X[1]"))
obj = (
    obj
    .faces("%Plane and |X").faces(">>X[1]")
    .workplane()
    .pushPoints([cq.Vector(-pin_sep/2, 0, 0), cq.Vector(pin_sep/2, 0, 0)])
    .rect(pin_handle_size.x*3/4, pin_handle_size.y*3/4)
    .cutBlind(-wall)
)

# Without the need for supports and plausible assembly (remove ceilings)
#debug(obj.faces("%Plane and |Z").faces(">>Z[1] or >>Z[2]"))
to_remove = cq.Workplane()
for roof_face in obj.faces("%Plane and |Z").faces(">>Z[1] or >>Z[2]").vals():
    bb = roof_face.BoundingBox()
    bb2 = obj.val().BoundingBox()
    to_remove_iter = (
        cq.Workplane(roof_face)
        .rect(bb.xlen, bb.ylen)
        .extrude(bb2.zmin - bb.zmin)
    )
    # Combine removals
    to_remove += to_remove_iter
obj = obj - to_remove
#debug(work_box.faces("|Z").faces(">>Z[1] or >>Z[2]"))

# Extra: an optional cover that helps achieve a better connection
cover = (
    cq.Workplane("XY")
    .box(pin_handle_size.z + 2 * tol + wall, usb_conn_size.x + 2*wall, usb_conn_size.y + 2*wall, centered=[False, True, False])
    .faces("|X")
    .shell(-wall + 2*tol)
    .translate(cq.Vector(0, 0, -wall))
    
)
# Move it back to match the zmin of the object (could be done with an assembly...)
moveX = cover.val().BoundingBox().xmin - obj.val().BoundingBox().xmin
cover = cover.translate(cq.Vector(-moveX, 0, 0))
cover -= obj.shell(2*tol) + obj
# Keep the connection in place with bottom supports
#debug(cover.faces("|Z").faces(">>Z[1]"))
cover = (
    cover
    .faces("|Z").faces(">>Z[1]")
    .workplane(centerOption="CenterOfMass")
    .pushPoints([cq.Vector(wall/2, -pin_sep/2, 0), cq.Vector(wall/2, pin_sep/2, 0)])
    .rect(pin_handle_size.z, pin_handle_size.y)
    .extrude(wall)
)
# Chamfer cover to make it printable without supports
#debug(cover.edges("|Y").edges(">>Z[3]"))
cover = (
    cover
    .edges("|Y").edges(">>Z[3]")
    .chamfer(wall-0.01, 3*wall)
)
# Final filleting, except for the print surface
cover = cover.edges("(>Z or <Z or (<X and >Y) or (<X and <Y)) and (not >X)").fillet(wall/2)

# ================== SHOW / EXPORT BOILERPLATE ==================
final_objs = [obj, cover]
if 'show_object' in globals(): # If using cq-editor, only render the final object
    for i, final_obj in enumerate(final_objs):
        show_object(final_obj, name="final_obj_{}".format(i))
else: # Otherwise, export stl
    for i, final_obj in enumerate(final_objs):
        with open('obj_{}.stl'.format(i), 'w') as out:
            cq.exporters.exportShape(final_obj, 'STL', out, tolerance=0.01, angularTolerance=0.01)