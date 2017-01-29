import numpy as np
import pickle
import os

dir_track = '/home/omari/Dropbox/Bug_Tracking/videos/CS1_not_tracking_3d_points.p'
if os.path.exists(dir_track):
    data = open(dir_track, 'rb')
    X3d, Y3d, Z3d, X3d_poly, Y3d_poly, Z3d_poly = pickle.load(data)
    print '3D tracks found and loaded'
else:
    print 'no 3D tracks found'

####
frames = xrange(len(X3d))
####
