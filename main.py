import cadquery as cq
import os

tol = 0.2 # Tolerance
wall = 0.4 # Minimum wall width, if aligned with

# USB standard measurements
usb_conn_width = 12
usb_conn_height = 4.5
usb_conn_depth = 12 * 1.5 # Debugging for easier grip
usb_conn_platform_y = [0.4 - tol, 1.9 + tol * 3]
usb_conn_platform_height = usb_conn_platform_y[1] - usb_conn_platform_y[0]
usb_conn_platform_width = usb_conn_width - wall*2

# Create a basic connector that will fit in a USB female tightly
usb_conn = (
    cq.Workplane("XY")
    .box(usb_conn_width, usb_conn_height, usb_conn_depth, centered=[True, False, True])
    .faces("<Z")
    .workplane()
    .transformed(offset=(0, -usb_conn_platform_y[0] - usb_conn_platform_height/2, 0))
    .rect(usb_conn_platform_width, usb_conn_platform_y[1]-usb_conn_platform_y[0])
    .cutThruAll()
)

obj = usb_conn 


# ================== SHOW / EXPORT BOILERPLATE CODE ==================

with open('obj.stl', 'w') as out:
    cq.exporters.exportShape(obj, 'STL', out, tolerance=0.01, angularTolerance=0.01)