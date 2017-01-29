import numpy as np
import pickle
# from sklearn.preprocessing import PolynomialFeatures
# from sklearn import linear_model

class compute_3d():
    """docstring for compute_3d."""
    def __init__(self):
        self.calibrations = {}
        self.R = []
        self._Track = {}
        self._all_ranges = 1
        self.X3d = []
        self.Y3d = []
        self.Z3d = []
        # self.X3d_poly = []
        # self.Y3d_poly = []
        # self.Z3d_poly = []
        self.X3d_s = []
        self.Y3d_s = []
        self.Z3d_s = []

    ########################################
    # compute the 3d points from 2d tracks #
    ########################################
    def compute_3d_callback(self):
        ok = 1
        if len(self._Track.keys()):
            print '  - tracks are available: ',self._Track.keys()
        else:
            print '  - tracks are not available, please initiate the 2D tracks.'
            ok *= 0

        if self.calibrations != {}:
            print '  - calibrations are available'
        else:
            print '  - please add calibration file to the video directory'
            ok = 0
        if ok:
            tracks = self._Track.keys()
            frames = sorted(self._Track[tracks[0]].keys())
            self._all_ranges = 1
            self.X3d = [500]; self.Y3d = [500]; self.Z3d = [500]
            for frame in frames:
                self._get_3D_point(frame, self.X3d[-1], self.Y3d[-1], self.Z3d[-1])
            print '  - finished processing 3d points'
            # self._poly_regression(frames)
            self._4th_diff_smoothing(frames)

    ###############################################################
    # compute a single 3d points from a single frame of 2d tracks #
    ###############################################################
    def _get_3D_point(self,frame,X3d,Y3d,Z3d):
        # assumptions
        Xo = self.calibrations['Tx']
        Yo = self.calibrations['Ty']
        Zo = self.calibrations['Tz']
        fx = self.calibrations['fx']
        fy = self.calibrations['fy']
        r11=self.R[0,0];r12=self.R[0,1];r13=self.R[0,2]
        r21=self.R[1,0];r22=self.R[1,1];r23=self.R[1,2]
        r31=self.R[2,0];r32=self.R[2,1];r33=self.R[2,2]

        Ax = {}; Bx = {}; Cx = {}; Ay = {}; By = {}; Cy = {}; Dx = {}; Dy = {}
        for key in self._Track:
            X_2d = self._Track[key][frame][0]-self.calibrations['dimx']/2.0;
            Y_2d = self.calibrations['dimy']/2.0+100 - self._Track[key][frame][1]
            Ax[key] = X_2d*r31 + fx*r11
            Ay[key] = Y_2d*r31 + fy*r21
            Bx[key] = X_2d*r32 + fx*r12
            By[key] = Y_2d*r32 + fy*r22
            Cx[key] = X_2d*r33 + fx*r13
            Cy[key] = Y_2d*r33 + fy*r23
            Dx[key] = Ax[key]*Xo + Bx[key]*Yo + Cx[key]*Zo
            Dy[key] = Ay[key]*Xo + By[key]*Yo + Cy[key]*Zo

        if self._all_ranges:
            all_ranges = [1.0,10.0,100.0,1000.0,10000.0]
            step = 100
        else:
            all_ranges = [100.0,1000.0]
            step = 200

        for i in all_ranges:
            X = np.arange(X3d-1000/i,X3d+1000/i,step/i)
            Y = np.arange(Y3d-1000/i,Y3d+1000/i,step/i)
            Z = np.arange(Z3d-1000/i,Z3d+1000/i,step/i)
            min = 10000000
            for x in X:
                for y in Y:
                    for z in Z:
                        Val = 0
                        for key in self._Track:
                            if key == 'Real': sgn = [1,1,1]
                            if key == 'Rx': sgn = [-1,1,1]
                            if key == 'Ry': sgn = [1,-1,1]
                            if key == 'Rz': sgn = [1,1,-1]
                            if key == 'Rxy': sgn = [-1,-1,1]
                            if key == 'Rxz': sgn = [-1,1,-1]
                            if key == 'Ryz': sgn = [1,-1,-1]
                            if key == 'Rxyz': sgn = [-1,-1,-1]
                            Val += (np.abs(sgn[0]*Ax[key]*x + sgn[1]*Bx[key]*y + sgn[2]*Cx[key]*z - Dx[key]))**2
                            Val += (np.abs(sgn[0]*Ay[key]*x + sgn[1]*By[key]*y + sgn[2]*Cy[key]*z - Dy[key]))**2
                        Val = np.sqrt(Val)
                        if Val<=min:
                            min=Val
                            X3d = x; Y3d = y; Z3d = z

        if self._all_ranges:
            self.X3d = [X3d]; self.Y3d = [Y3d]; self.Z3d = [Z3d]
            self._all_ranges = 0
        else:
            self.X3d.append(X3d)
            self.Y3d.append(Y3d)
            self.Z3d.append(Z3d)
        print '  - processed frame: ',frame,' the 3D xyx values: %.1f,%.1f,%.1f' %(X3d,Y3d,Z3d)

    ##############################
    # save the 3d points to file #
    ##############################
    def _save_3d_points(self):
        ok = 1
        if len(self._Track.keys()):
            print '  - tracks are available: ',self._Track.keys()
        else:
            print '  - tracks are not available, please initiate the 2D tracks.'
            ok *= 0
        if ok:
            tracks = self._Track.keys()
            frames = sorted(self._Track[tracks[0]].keys())
            pkl = self.dir.split('.')[0]+'_3d_points.p'
            txt = self.dir.split('.')[0]+'_3d_points.txt'
            print 'saving the 3d tracks in '+txt
            F = open(txt, 'w')
            for frame,x,y,z,x2,y2,z2 in zip(frames,self.X3d,self.Y3d,self.Z3d,self.X3d_s,self.Y3d_s,self.Z3d_s):
                F.write('frame_'+str(frame)+','+str(x)+','+str(y)+','+str(z)+','+str(x2)+','+str(y2)+','+str(z2)+'\n')
            F.close()
            print 'saving the 3d tracks in '+pkl
            to_be_saved = [self.X3d, self.Y3d, self.Z3d, self.X3d_s, self.Y3d_s, self.Z3d_s]
            pickle.dump(to_be_saved, open(pkl, 'wb'))

    ###################################
    # Polynomial regression 4th order #
    ###################################
    # def _poly_regression(self,frames):
    #     self.poly = PolynomialFeatures(degree=4)
    #     F = []
    #     XYZ = []
    #     for f,x,y,z in zip(frames, self.X3d, self.Y3d, self.Z3d):
    #         F.append([f])
    #         XYZ.append([x/100.0,y/100.0,z/100.0])
    #
    #     X_ = self.poly.fit_transform(F)
    #     predict_ = self.poly.fit_transform(F)
    #     clf = linear_model.LinearRegression()
    #     clf.fit(X_, XYZ)
    #     self.X3d_poly,self.Y3d_poly,self.Z3d_poly = [],[],[]
    #     for i in clf.predict(predict_):
    #         self.X3d_poly.append(int(i[0]*100)/100.0)
    #         self.Y3d_poly.append(int(i[1]*100)/100.0)
    #         self.Z3d_poly.append(int(i[2]*100)/100.0)

    ###################################
    # 4th diff smoothing              #
    ###################################
    def _4th_diff_smoothing(self,frames):
        self.X3d_s = self._sub_4th_diff_smoothing(self.X3d,frames)
        self.Y3d_s = self._sub_4th_diff_smoothing(self.Y3d,frames)
        self.Z3d_s = self._sub_4th_diff_smoothing(self.Z3d,frames)

    ###################################
    # 4th diff smoothing              #
    ###################################
    def _sub_4th_diff_smoothing(self,X3d,frames):
        d1 = {}
        d2 = {}
        d3 = {}
        d4 = {}
        X_smooth = []
        # computing the first diff
        for i in range(1,len(frames)):
            d1[i] = X3d[i-1] - X3d[i]

        # computing the 2nd diff
        for i in range(2,len(frames)):
            d2[i] = d1[i-1] - d1[i]

        # computing the 3rd diff
        for i in range(3,len(frames)):
            d3[i] = d2[i-1] - d2[i]

        # computing the 4th diff
        for i in range(4,len(frames)):
            d4[i] = d3[i-1] - d3[i]

        # compute the smoothing
        for i in range(len(frames)):
            if i == 0:
                x = X3d[0]+((1/5.0)*d3[3])+((3/35.0)*d4[4])
            elif i == 1:
                x = X3d[1]-((2/5.0)*d3[3])-((1/7.0)*d4[4])
            elif i == len(frames)-2:
                x = X3d[i]-((1/5.0)*d3[i+1])+((3/35.0)*d4[i+1])
            elif i == len(frames)-1:
                x = X3d[i]+((2/5.0)*d3[i])-((1/7.0)*d4[i])
            else:
                x = X3d[i]-((3/35.0)*d3[i+2])
            X_smooth.append(x)

        # for i,y in zip(X3d,X_smooth):
        #     print i,y
        # print '========================================='
        return X_smooth
