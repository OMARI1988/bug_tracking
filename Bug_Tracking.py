from Tkinter import *
import tkMessageBox
import cv2
from PIL import Image, ImageTk
import os
import Tkconstants, tkFileDialog
from tkFileDialog import askopenfilename
import time
import numpy as np
import colorsys
import pickle
import transform as ts
from mpl_toolkits.mplot3d import Axes3D
import matplotlib.pyplot as plt
import functions_3d as func_3d
import sys
import imageio
# from moviepy.editor import *

"""
Latest-updates
/// add the read calibration function
/// add the original bug to tracking
/// move the curser to the start frame of tracking
/// fix the camera model returned image
"""

"""
To-do
add bug disapeared
see if I can make it exe
"""

# http://www.python-course.eu/tkinter_text_widget.php check this for text messages
class App():
    """docstring for App"""
    def __init__(self, master):
        # variables
        self.directory = os.path.dirname(os.path.realpath(__file__))+"\\"
        # self.directory = '/home/omari/Dropbox/Bug_Tracking/codes/'
        self.master = master
        self.dir_opt = {}
        self._Track = {}
        self._Track_number = 0
        self._Max_Track_number = 8
        self.dir = 'none'
        self.video_len = 0
        self._fgbg2 = cv2.BackgroundSubtractorMOG2(-300,150,False)
        self.bin_0 = 255
        self.bin_1 = 11
        self.bin_2 = 5
        self.bin_3 = 10
        self.bin_4 = 5
        self._HSV_tuples = [(x*1.0/self._Max_Track_number, 1.0, 1.0) for x in range(self._Max_Track_number)]
        _colors = map(lambda x: colorsys.hsv_to_rgb(*x), self._HSV_tuples)
        self._colors = {}
        for i,j in zip(_colors,['Rx','Ry','Rz','Rxy','Rxz','Ryz','Rxyz','Real']):
            self._colors[j] = i
        self.fix_track_flag = 0
        self.ignore_track_flag = 0
        self.init_track_flag = 0
        self.init_Rx_track_flag = 0
        self.init_Ry_track_flag = 0
        self.init_Rz_track_flag = 0
        self.fixing_track_flag = 0
        self.track_to_fix = None
        self.calibrations = {}
        self.X3d = []
        self.Y3d = []
        self.Z3d = []
        self.X3d_s = []
        self.Y3d_s = []
        self.Z3d_s = []
        self.R = []

        #flags
        self.play_flag = 0
        self.track_flag = 0
        self.init_track_flag = 0
        self.view_low_flag = 0
        self.view_camera_flag = 0
        self.init_center_flag = 0

        # GUI
        self.row = 0
        # browse folder
        Label(master, text="video").grid(row=self.row, column=0, pady=10, padx=2, sticky=W+E)
        self.label_browse = Label(master, text="please select a video")
        self.label_browse.grid(row=self.row, column=1, columnspan=2, pady=10, padx=2, sticky=W+E)
        self.button_dir = Button(master, text='add video', command=self.askfile)
        self.button_dir.grid(row=self.row, column=3, pady=10, padx=2, sticky=W+E)
        self.button_dir.configure(activebackground = "LIGHTBLUE")  # Set activebackground color to LIGHTBLUE
        self.row+=1
        #
        # # bug type
        # bug_type = ("Choose ..", "Calopteryx splendens", "Ischnura elegans", "Libellula quadrimaculata", "Orthetrum cancellatum", "Sympetrum striolatum")
        # Label(master, text="species").grid(row=self.row, pady=10, padx=2, sticky=W+E)
        # self.variable = StringVar(master)
        # self.variable.set(bug_type[0]) # default value
        # self.menu_species = OptionMenu(master, self.variable, *bug_type)
        # self.menu_species.grid(row=self.row, padx=2, column=1, columnspan=2, stick="ew")
        # self.menu_species.configure(bg = "WHITE")  # Set background color to WHITE
        # self.menu_species.configure(activebackground = "LIGHTBLUE")  # Set activebackground color to LIGHTBLUE
        # self.button_load = Button(master, text="Load", command=self.button_load_callback)
        # self.button_load.grid(row=self.row, padx=2, column=3, sticky=W+E)
        # self.button_load.configure(activebackground = "LIGHTBLUE")  # Set activebackground color to LIGHTBLUE
        # self.row+=1

        # video control
        self.photo_init = ImageTk.PhotoImage(Image.open(self.directory+'images/init.png'))
        self.frame_0 = Button(master, image=self.photo_init, command=self.first_frame_callback, height = 30)
        self.frame_0.grid(row=self.row, column=0, padx=2, pady=4, sticky=W+E)

        self.photo_pause = ImageTk.PhotoImage(Image.open(self.directory+'images/pause.png'))
        self.pause = Button(master, image=self.photo_pause, command=self.pause_callback, height = 30)
        self.pause.grid(row=self.row, column=1, padx=2, pady=4, sticky=W+E)

        self.photo_play = ImageTk.PhotoImage(Image.open(self.directory+'images/play.png'))
        self.play = Button(master, image=self.photo_play, command=self.play_callback, height = 30)
        self.play.grid(row=self.row, column=2, padx=2, pady=4, sticky=W+E)

        self.photo_end = ImageTk.PhotoImage(Image.open(self.directory+'images/end.png'))
        self.end = Button(master, image=self.photo_end, command=self.final_frame_callback, height = 30)
        self.end.grid(row=self.row, column=3, padx=2, pady=4, sticky=W+E)
        self.row+=1

        self.prev_frame = Button(master, text='prev frame', command=self.prev_frame_callback, height = 1)
        self.prev_frame.grid(row=self.row, column=0, columnspan=2, padx=2, pady=10, sticky=W+E)

        self.next_frame = Button(master, text='next frame', command=self.next_frame_callback)
        self.next_frame.grid(row=self.row, column=2, columnspan=2, padx=2, pady=10, sticky=W+E)

        self.row+=1

        # separator
        separator = Frame(height=5, bd=1, relief=SUNKEN)
        separator.grid(row=self.row, columnspan=4, sticky="ew")
        separator.configure(padx=5, pady=15)
        self.row+=1

        # sliders for calibration
        # Non-zero value assigned to the pixels for which the condition is satisfied. See the details below.
        self.button_bin_thresh_0 = Button(master, text='Threshold1', command=self.message_1)
        self.button_bin_thresh_0.grid(row=self.row, column=0, padx=2, columnspan=1, sticky=W+E)
        self.scale_bin_thresh_0 = Scale(master, from_=1, to=255, orient=HORIZONTAL, command=self.scale_bin0_callback)
        self.scale_bin_thresh_0.grid(row=self.row, column=1, columnspan=3,pady=5, sticky=W+E+N+S)
        self.scale_bin_thresh_0.set(255)
        self.row+=1
        # Size of a pixel neighborhood that is used to calculate a threshold value for the pixel: 3, 5, 7, and so on.
        self.button_bin_thresh_1 = Button(master, text='Threshold2', command=self.message_2)
        self.button_bin_thresh_1.grid(row=self.row, column=0, padx=2, columnspan=1, sticky=W+E)
        self.scale_bin_thresh_1 = Scale(master, from_=3, to=39, orient=HORIZONTAL, command=self.scale_bin1_callback)
        self.scale_bin_thresh_1.grid(row=self.row, column=1, columnspan=3,pady=5, sticky=W+E+N+S)
        self.scale_bin_thresh_1.set(39)
        self.row+=1
        #Constant subtracted from the mean or weighted mean (see the details below). Normally, it is positive but may be zero or negative as well.
        self.button_bin_thresh_2 = Button(master, text='Threshold3', command=self.message_3)
        self.button_bin_thresh_2.grid(row=self.row, column=0, padx=2, columnspan=1, sticky=W+E)
        self.scale_bin_thresh_2 = Scale(master, from_=0, to=39, orient=HORIZONTAL, command=self.scale_bin2_callback)
        self.scale_bin_thresh_2.grid(row=self.row, column=1, columnspan=3,pady=5, sticky=W+E+N+S)
        self.scale_bin_thresh_2.set(39)
        self.row+=1
        #Largest size of a contour
        self.button_bin_thresh_3 = Button(master, text='Threshold4', command=self.message_4)
        self.button_bin_thresh_3.grid(row=self.row, column=0, padx=2, columnspan=1, sticky=W+E)
        self.scale_bin_thresh_3 = Scale(master, from_=2, to=400, orient=HORIZONTAL, command=self.scale_bin3_callback)
        self.scale_bin_thresh_3.grid(row=self.row, column=1, columnspan=3,pady=5, sticky=W+E+N+S)
        self.scale_bin_thresh_3.set(60)
        self.row+=1
        #smallest size of a contour
        self.button_bin_thresh_4 = Button(master, text='Threshold5', command=self.message_5)
        self.button_bin_thresh_4.grid(row=self.row, column=0, padx=2, columnspan=1, sticky=W+E)
        self.scale_bin_thresh_4 = Scale(master, from_=1, to=399, orient=HORIZONTAL, command=self.scale_bin4_callback)
        self.scale_bin_thresh_4.grid(row=self.row, column=1, columnspan=3,pady=5, sticky=W+E+N+S)
        self.scale_bin_thresh_4.set(1)
        self.row+=1

        self.view_low = Button(master, text='view low-level (off)', command=self.view_low_callback)
        self.view_low.grid(row=self.row, column=0, padx=2, columnspan=4, pady=10, sticky=W+E)

        # self.view_low = Button(master, text='mirrors center', command=self.center_callback)
        # self.view_low.grid(row=self.row, column=2, padx=2, columnspan=2, pady=10, sticky=W+E)
        self.row+=1

        # separator
        separator = Frame(height=5, bd=1, relief=SUNKEN)
        separator.grid(row=self.row, columnspan=4, sticky="ew")
        separator.configure(padx=5, pady=15)
        self.row+=1

        # tracking control
        th = 1

        self.camera_model = Button(master, text='view model', command=self.view_camera_model, height = th)
        self.camera_model.grid(row=self.row, column=0, columnspan=2, rowspan=1, padx=2, pady=10, sticky=W+E)

        self.start_track_frame = Button(master, text='first tracking frame', command=self.go_to_track_frame_callback, height = th)
        self.start_track_frame.grid(row=self.row, column=2, columnspan=2, rowspan=1, padx=2, pady=10, sticky=W+E)
        self.row+=1

        self.start_track = Button(master, text='init track Rx', command=self.init_Rx_track_callback, height = th)
        self.start_track.grid(row=self.row, column=0, columnspan=1, padx=2, pady=10, sticky=W+E)

        self.start_track = Button(master, text='init track Ry', command=self.init_Ry_track_callback, height = th)
        self.start_track.grid(row=self.row, column=1, columnspan=1, padx=2, pady=10, sticky=W+E)

        self.start_track = Button(master, text='init track Rz', command=self.init_Rz_track_callback, height = th)
        self.start_track.grid(row=self.row, column=2, columnspan=1, padx=2, pady=10, sticky=W+E)

        self.start_track = Button(master, text='init track bug', command=self.init_R_track_callback, height = th)
        self.start_track.grid(row=self.row, column=3, columnspan=1, padx=2, pady=10, sticky=W+E)
        self.row+=1

        self.start_track = Button(master, text='init track Rxy', command=self.init_Rxy_track_callback, height = th)
        self.start_track.grid(row=self.row, column=0, columnspan=1, padx=2, pady=10, sticky=W+E)

        self.start_track = Button(master, text='init track Rxz', command=self.init_Rxz_track_callback, height = th)
        self.start_track.grid(row=self.row, column=1, columnspan=1, padx=2, pady=10, sticky=W+E)

        self.start_track = Button(master, text='init track Ryz', command=self.init_Ryz_track_callback, height = th)
        self.start_track.grid(row=self.row, column=2, columnspan=1, padx=2, pady=10, sticky=W+E)

        self.start_track = Button(master, text='init track Rxyz', command=self.init_Rxyz_track_callback, height = th)
        self.start_track.grid(row=self.row, column=3, columnspan=1, padx=2, pady=10, sticky=W+E)
        self.row+=1

        self.save_track = Button(master, text='ignore track', command=self.ignore_tracks_callback, height = th)
        self.save_track.grid(row=self.row, column=0, columnspan=2, padx=2, pady=10, sticky=W+E)

        self.fix_track = Button(master, text='stop fixing', command=self.stop_fixing_callback, height = th)
        self.fix_track.grid(row=self.row, column=2, columnspan=2, padx=2, pady=10, sticky=W+E)
        self.row+=1

        self.save_track = Button(master, text='save tracks', command=self.save_tracks_callback, height = th)
        self.save_track.grid(row=self.row, column=0, columnspan=2, padx=2, pady=10, sticky=W+E)

        self.fix_track = Button(master, text='fix track', command=self.fix_tracks_callback, height = th)
        self.fix_track.grid(row=self.row, column=2, columnspan=2, padx=2, pady=10, sticky=W+E)
        self.row+=1
        #
        # self.save_track = Button(master, text='No Bug', command=self.no_bug_callback)
        # self.save_track.grid(row=self.row, column=0, columnspan=1, padx=2, pady=10, sticky=W+E)
        #
        # self.save_track = Button(master, text='Bug is Back', command=self.bug_back_callback)
        # self.save_track.grid(row=self.row, column=1, columnspan=1, padx=2, pady=10, sticky=W+E)
        # self.row+=1

        # separator
        separator = Frame(height=5, bd=1, relief=SUNKEN)
        separator.grid(row=self.row, columnspan=4, sticky="ew")
        separator.configure(padx=5, pady=15)
        self.row+=1

        # plotting control
        self.load_calib = Button(master, text='Load calibration', command=self.calibration_callback, height = th)
        self.load_calib.grid(row=self.row, column=0, padx=2, columnspan=2, pady=10, sticky=W+E)

        self.view_tracks = Button(master, text='compute 3D', command=self.compute_3d_callback, height = th)
        self.view_tracks.grid(row=self.row, column=2, padx=2, columnspan=2, pady=10, sticky=W+E)
        self.row+=1

        self.save_3D = Button(master, text='save 3D', command=self.save_3d_callback, height = th)
        self.save_3D.grid(row=self.row, column=0, columnspan=2, padx=2, pady=10, sticky=W+E)

        # Results
        self.view_3D = Button(master, text='view 3D tracks', command=self.view_3D_callback, height = th)
        self.view_3D.grid(row=self.row, column=2, columnspan=2, padx=2, pady=10, sticky=W+E)

        # self.view_3D_sp = Button(master, text='view spline 3D', command=self.view_3D_callback, height = th)
        # self.view_3D_sp.grid(row=self.row, column=2, columnspan=2, padx=2, pady=10, sticky=W+E)
        self.row+=1

        # separator
        separator = Frame(height=5, bd=1, relief=SUNKEN)
        separator.grid(row=self.row, columnspan=4, sticky="ew")
        separator.configure(padx=5, pady=15)
        self.row+=1

        # exit Button
        self.exit_button = Button(master, text='Exit', command=self.exit, height = th+th)
        self.exit_button.grid(row=self.row, column=0, columnspan=4, padx=2, pady=10, sticky=W+E)
        self.row+=1

        # empty labels
        self.L_empty1 = Label(master).grid(row=self.row,column=0, pady=50, padx=60, sticky=W+E)
        self.L_empty2 = Label(master).grid(row=self.row,column=1, pady=50, padx=60, sticky=W+E)
        self.L_empty3 = Label(master).grid(row=self.row,column=2, pady=50, padx=60, sticky=W+E)
        self.L_empty4 = Label(master).grid(row=self.row,column=3, pady=50, padx=60, sticky=W+E)
        self.row+=1

        # images
        self.image = Canvas(height=1024, width=1024)
        self.image.grid(row=1, rowspan=self.row, column=5)
        self.image.bind("<Button-1>", self.mouse_callback)
        self.load_video()

        # slider
        self.scale_l = Scale(master, from_=1, to=self.video_len, orient=HORIZONTAL, command=self.scale_callback)
        self.scale_l.grid(row=0, column=5, pady=5, sticky=W+E)

    def message_1(self):
        tkMessageBox.showinfo("Help","Non-zero value assigned to the pixels for which the condition is satisfied.")

    def message_2(self):
        tkMessageBox.showinfo("Help","Size of a pixel neighborhood that is used to calculate a threshold value for the pixel: 3, 5, 7, and so on.")

    def message_3(self):
        tkMessageBox.showinfo("Help","Constant subtracted from the mean or weighted mean. Normally, it is positive but may be zero or negative as well..")

    def message_4(self):
        tkMessageBox.showinfo("Help","Largest size of a contour. Has to be bigger than Threshold5")

    def message_5(self):
        tkMessageBox.showinfo("Help","smallest size of a contour. Has to be smaller than Threshold4")

    #############################################################################
    # Functions                                                                 #
    #############################################################################
    def exit(self):
        self.master.destroy()
        sys.exit()

    def view_camera_model(self):
        if self.view_camera_flag == 0:
            self.update_image(0,0,'model')
            self.view_camera_flag = 1
            self.camera_model.configure(text='hide model')
        else:
            if self._frames != []:
                self.update_image(int(self.scale_l.get()),0,'')
            else:
                self.update_image(0,0,'init')
            self.view_camera_flag = 0
            self.camera_model.configure(text='view model')

    def calibration_callback(self):
        dir_calib = askopenfilename()
        if os.path.exists(dir_calib):
            data = open(dir_calib, 'rb')
            for count,line in enumerate(data):
                if count == 0:
                    names = line.split('\r')[0].split(',')
                if count == 1:
                    valus = line.split('\r')[0].split(',')
            for i,j in zip(names,valus):
                self.calibrations[i] = float(j)
            alpha, beta, gamma = self.calibrations['Rx'],self.calibrations['Ry'],self.calibrations['Rz']
            xaxis, yaxis, zaxis = [1, 0, 0], [0, 1, 0], [0, 0, 1]
            Rx = ts.rotation_matrix(alpha, xaxis)
            Ry = ts.rotation_matrix(beta, yaxis)
            Rz = ts.rotation_matrix(gamma, zaxis)
            R = ts.concatenate_matrices(Rx, Ry, Rz)
            self.R = R[:-1,:-1]
            print 'calibrations found and loaded'
        else:
            print 'no calibrations found, please make sure they exist in the same video directory.'

    # def center_callback(self):
    #     if self._frames != []:
    #         self.init_center_flag = 1
    #         print 'click on the point where mirrors intersect'
    #     else:
    #         print "please load a video first"

    # def askdirectory(self):
    #     self.dir = tkFileDialog.askdirectory(**self.dir_opt)
    #     self.label_browse.configure(text = '...'+self.dir[-30:-1])
    #     self.load_video()

    def askfile(self):
        self.update_image(0,0,'wait')
        Tk().withdraw()
        self.dir = askopenfilename()
        self.label_browse.configure(text = '...'+self.dir[-30:-1])
        self.load_video()

    def button_load_callback(self):
        if self.new_vid:
            r = self.variable_r.get()
            self.file_meta.write('region_id:'+str(self.RegionIDs[r])+'\n')
            self.file_meta.write('region:'+r+'\n')
            self.new_vid = 0
        act = ''

    def prev_frame_callback(self):
        self.scale_l.set(int(self.scale_l.get())-1)

    def next_frame_callback(self):
        self.scale_l.set(int(self.scale_l.get())+1)

    def load_video(self):
        self._frames = []
        self._Track = {}
        self.fixed = {}
        self._Min = {}
        if self.dir == 'none':
            print "please select a video"
            self.update_image(0,0,'init')
        else:
            self._vid = imageio.get_reader(self.dir)
            for i, im in enumerate(self._vid):
                self._frames.append(im)
                self.fixed[i+1] = []
            # self._cap = cv2.VideoCapture(self.dir)
            # count = 1
            # while(1):
            #     ret, frame = self._cap.read()
            #     if ret:
                    # self._frames.append(frame)
                    # self.fixed[count] = []
                    # count += 1
            #     else:
            #         break
            self.video_len = len(self._frames)
            self.scale_l = Scale(self.master, from_=1, to=self.video_len, orient=HORIZONTAL, command=self.scale_callback)
            # print 'this happened'
            self.scale_l.grid(row=0 , column=5, pady=5, sticky=W+E)
            ######################
            # LOAD the 2D tracks #
            ######################
            dir_track = self.dir.split('.')[0]+'_tracks.p'
            if os.path.exists(dir_track):
                data = open(dir_track, 'rb')
                self._Track, fixed, self._Min = pickle.load(data)
                if type(fixed) is dict:
                    self.fixed = fixed
                else:
                    print 'this is an old tracking file, please update and save tracks.'
                self._Max_Track_number = len(self._Track.keys())
                self.track_flag = 1
                print '2D tracks found and loaded'
            else:
                print 'no 2D tracks found'
            ##############################
            # LOAD the calibration files #
            ##############################
            # dir_calib = self.dir.split('.')[0]+'_calibration.csv'
            # if os.path.exists(dir_calib):
            #     data = open(dir_calib, 'rb')
            #     for count,line in enumerate(data):
            #         if count == 0:
            #             names = line.split('\r')[0].split(',')
            #         if count == 1:
            #             valus = line.split('\r')[0].split(',')
            #     for i,j in zip(names,valus):
            #         self.calibrations[i] = float(j)
            #     alpha, beta, gamma = self.calibrations['Rx'],self.calibrations['Ry'],self.calibrations['Rz']
            #     xaxis, yaxis, zaxis = [1, 0, 0], [0, 1, 0], [0, 0, 1]
            #     Rx = ts.rotation_matrix(alpha, xaxis)
            #     Ry = ts.rotation_matrix(beta, yaxis)
            #     Rz = ts.rotation_matrix(gamma, zaxis)
            #     R = ts.concatenate_matrices(Rx, Ry, Rz)
            #     self.R = R[:-1,:-1]
            #     print 'calibrations found and loaded'
            # else:
            #     print 'no calibrations found, please make sure they exist in the same video directory.'
            ######################
            # LOAD the 3D points #
            ######################
            dir_track = self.dir.split('.')[0]+'_3d_points.p'
            if os.path.exists(dir_track):
                data = open(dir_track, 'rb')
                self.X3d, self.Y3d, self.Z3d,self.X3d_s,self.Y3d_s,self.Z3d_s = pickle.load(data)
                print '3D tracks found and loaded'
            else:
                print 'no 3D tracks found'

    def play_callback(self):
        self.play_flag = 1

    def pause_callback(self):
        self.play_flag = 0

    def first_frame_callback(self):
        self.play_flag = 0
        self.scale_l.set(int(1))

    def final_frame_callback(self):
        self.play_flag = 0
        self.scale_l.set(int(self.video_len))

    def scale_callback(self, val):
        if int(val)<10:         val_str = '0000'+str(val)
        elif int(val)<100:      val_str = '000'+str(val)
        elif int(val)<1000:     val_str = '00'+str(val)
        elif int(val)<10000:    val_str = '0'+str(val)
        elif int(val)<100000:   val_str = str(val)
        other = 0
        self.update_image(val,val_str,other)

    def scale_bin0_callback(self, val):
        self.bin_0 = int(val)

    def scale_bin1_callback(self, val):
        if int(val) % 2 == 1:
            self.bin_1 = int(val)
        else:
            self.bin_1 = int(val)-1

    def scale_bin2_callback(self, val):
        self.bin_2 = int(val)

    def scale_bin3_callback(self, val):
        self.bin_3 = int(val)
        if self.bin_3<=self.bin_4:
            self.scale_bin_thresh_3.set(self.bin_4+1)

    def scale_bin4_callback(self, val):
        self.bin_4 = int(val)
        if self.bin_3<=self.bin_4:
            self.scale_bin_thresh_4.set(self.bin_3-1)

    def update_image(self,val,val_str,other):
        img = []
        if other=='init':
            img = cv2.imread(self.directory+'images/empty.jpg')
        elif other=='wait':
            img = cv2.imread(self.directory+'images/wait.jpg')
        elif other=='model':
            img = cv2.imread(self.directory+'images/camera_model.jpg')
        else:
            if self._frames != []:
                img = self._frames[int(val)-1]
                self.img = img.copy()
                self._process_img()
                if self.track_flag:
                    self._track_frame()
                img = self.img

        if img != []:
            img = cv2.cvtColor(img.astype(np.uint8), cv2.COLOR_BGR2RGBA)
            img = Image.fromarray(img)
            self.photo = ImageTk.PhotoImage(img)
            self.image.create_image(512,512, image=self.photo)

    def view_low_callback(self):
        if self.view_low_flag:
            self.view_low_flag = 0
            self.view_low.configure(text='view low-level (off)')
        else:
            self.view_low_flag = 1
            self.view_low.configure(text='view low-level (on)')

    def save_tracks_callback(self):
        if self._frames != []:
            if self._Track != {}:
                pkl = self.dir.split('.')[0]+'_tracks.p'
                txt = self.dir.split('.')[0]+'_tracks.txt'
                print 'saving the tracks in '+txt
                F = open(txt, 'w')
                for n in self._Track:
                    # print n
                    F.write('Track number:'+str(n)+'\n')
                    for i in sorted(self._Track[n].keys()):
                        F.write('frame_'+str(i)+':'+str(int(self._Track[n][i][0]))+','+str(int(self._Track[n][i][1]))+'\n')
                F.close()
                print 'saving the tracks in '+pkl
                to_be_saved = [self._Track, self.fixed, self._Min]
                pickle.dump(to_be_saved, open(pkl, 'wb'))
            else:
                print "please initiate the tracks first"
        else:
            print "please load a video first"

    def _initiate_new_track(self):
        if self._frames != []:
            self.init_track_flag = 1
            self.ignore_track_flag = 0
            self.fix_track_flag = 0
            self.fixing_track_flag = 0
            print 'click on '+self._track_name+' Bug reflection'
        else:
            print "please load a video first"

    def init_R_track_callback(self):
        self._track_name = 'Real'
        self._initiate_new_track()

    def init_Rx_track_callback(self):
        self._track_name = 'Rx'
        self._initiate_new_track()

    def init_Ry_track_callback(self):
        self._track_name = 'Ry'
        self._initiate_new_track()

    def init_Rz_track_callback(self):
        self._track_name = 'Rz'
        self._initiate_new_track()

    def init_Rxy_track_callback(self):
        self._track_name = 'Rxy'
        self._initiate_new_track()

    def init_Rxz_track_callback(self):
        self._track_name = 'Rxz'
        self._initiate_new_track()

    def init_Ryz_track_callback(self):
        self._track_name = 'Ryz'
        self._initiate_new_track()

    def init_Rxyz_track_callback(self):
        self._track_name = 'Rxyz'
        self._initiate_new_track()

    def ignore_tracks_callback(self):
        if self._frames != []:
            if self._Track != {}:
                print 'click on the track you wish to ignore/remove'
                self.ignore_track_flag = 1
                self.fix_track_flag = 0
                self.fixing_track_flag = 0
                self.init_track_flag = 0
            else:
                print "please initiate the tracks first"
        else:
            print "please load a video first"

    def fix_tracks_callback(self):
        if self._frames != []:
            if self._Track != {}:
                print 'go to where you want to start fixing and then click on the track you wish to fix'
                self.fix_track_flag = 1
                self.ignore_track_flag = 0
                self.fixing_track_flag = 0
                self.init_track_flag = 0
            else:
                print "please initiate the tracks first"
        else:
            print "please load a video first"

    def stop_fixing_callback(self):
        print 'stopped fixing tracks mode. Will play the video to finish tracking.'
        self.scale_l.set(int(self.scale_l.get())-5)
        self.play_flag = 1
        self.fixing_track_flag = 0

    def fix_track_callback_function(self,x2,y2):
        print 'please click on the bug location'
        self.fixing_track_flag = 1
        self.view_low_flag = 0
        self.view_low.configure(text='view low-level (off)')
        if x2 != 0:
            frame = int(self.scale_l.get())-5
            [x1,y1] = self._Track[self.track_to_fix][frame]
            for i in range(1,6):
                x = i*x2/5 + (5-i)*x1/5
                y = i*y2/5 + (5-i)*y1/5
                self._Track[self.track_to_fix][frame+i] = [x,y]
                self.fixed[frame+i].append(self.track_to_fix)
        if self.video_len == int(self.scale_l.get()):
            self.fixing_track_flag = 0
        else:
            self.scale_l.set(int(self.scale_l.get())+5)

    def mouse_callback(self,event):
        if self.init_track_flag:
            print "clicked at", event.x, event.y
            self._Track[self._track_name] = {};
            self._Track[self._track_name][int(self.scale_l.get())] = [event.x,event.y]
            self._Min[self._track_name] = [np.inf,[]]
            self.init_track_flag = 0
            self.track_flag = 1

        if self.init_center_flag:
            print "clicked at", event.x, event.y
            self.init_center_flag = 0

        if self.fixing_track_flag:
            print "clicked at", event.x, event.y
            x = event.x
            y = event.y
            self.fix_track_callback_function(x,y)

        if self.fix_track_flag:
            minimum = 100000
            print "clicked at", event.x, event.y
            x = event.x
            y = event.y
            for T in self._Track:
                for f in self._Track[T]:
                    distance = np.sqrt((self._Track[T][f][0]-x)**2 + (self._Track[T][f][1]-y)**2)
                    if distance < minimum:
                        self.track_to_fix = T
                        minimum = distance
            print 'You choose to fix track : ',self.track_to_fix
            self.fixed[int(self.scale_l.get())].append(self.track_to_fix)
            ################ FIX ME NEXT
            self.fix_track_callback_function(0,0)
            self.fix_track_flag = 0

        if self.ignore_track_flag:
            minimum = 100000
            print "clicked at", event.x, event.y
            x = event.x
            y = event.y
            for T in self._Track:
                for f in self._Track[T]:
                    distance = np.sqrt((self._Track[T][f][0]-x)**2 + (self._Track[T][f][1]-y)**2)
                    if distance < minimum:
                        self.track_to_delete = T
                        minimum = distance
            print 'You choose to remove track : ',self.track_to_delete
            del self._Track[self.track_to_delete]
            del self._Min[self.track_to_delete]
            self.ignore_track_flag = 0
            self.update_image(int(self.scale_l.get()),0,'')
            # self.scale_l.set(int(self.scale_l.get()))

    def _show_frame(self):
        if self._frames != []:
            if self.play_flag:
                if self.video_len == int(self.scale_l.get()):
                    self.scale_l.set(0)
                else:
                    self.scale_l.set(int(self.scale_l.get())+1)
        self.image.after(10, self._show_frame)

    def _process_img(self):
        gray_image = cv2.cvtColor(self.img, cv2.COLOR_BGR2GRAY)
        th = cv2.adaptiveThreshold(gray_image, self.bin_0, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, self.bin_1, self.bin_2)
        image = cv2.cvtColor(th, cv2.COLOR_GRAY2BGR)
        fgmask = self._fgbg2.apply(image)
        contours, t = cv2.findContours(fgmask,cv2.RETR_TREE,cv2.CHAIN_APPROX_SIMPLE)
        if self.view_low_flag:
            cv2.drawContours(self.img, contours, -1, (0,0,255), 2)
        for c in contours:
            if cv2.contourArea(c) < self.bin_3 and cv2.contourArea(c) > self.bin_4:
                (x,y),radius = cv2.minEnclosingCircle(c)
                center = (int(x),int(y))
                radius = int(radius)
                if radius<25:
                    if self.track_flag:
                        for T in self._Track.keys():
                            if int(self.scale_l.get())-1 in self._Track[T]:
                                distance = np.sqrt((self._Track[T][int(self.scale_l.get())-1][0]-x)**2 + (self._Track[T][int(self.scale_l.get())-1][1]-y)**2)
                                if distance < self._Min[T][0]:
                                    self._Min[T][1] = [x,y]
                                    self._Min[T][0] = distance
                    if self.view_low_flag:
                        cv2.circle(self.img,center,(3),(0,255,0),2)

    def _track_frame(self):
        if self.track_flag:
            img = self.img.copy()
            self.img = np.multiply(self.img,0.5,casting="unsafe")
            for T in self._Track.keys():
                if T not in self.fixed[int(self.scale_l.get())]:
                    if self._Min[T][0] < 30:
                        self._Track[T][int(self.scale_l.get())] = self._Min[T][1]
                    elif int(self.scale_l.get())-1 in self._Track[T]:
                        self._Track[T][int(self.scale_l.get())] = self._Track[T][int(self.scale_l.get())-1]
                self._Min[T][0] = np.inf
                self._Min[T][1] = []
                keys = sorted(self._Track[T].keys())
                for i in range(len(keys)-1):
                    A = self._Track[T][keys[0]+i]
                    B = self._Track[T][keys[0]+i+1]
                    cv2.line(img,(int(A[0]),int(A[1])),(int(B[0]),int(B[1])),(self._colors[T][0]*255,self._colors[T][1]*255,self._colors[T][2]*255),2)
            self.img = np.add(self.img,np.multiply(img,0.5,casting="unsafe"),casting="unsafe") # for transparency

    def go_to_track_frame_callback(self):
        frame = 1
        for T in self._Track.keys():
            frame = min(self._Track[T].keys())
        self.scale_l.set(int(frame))

    def compute_3d_callback(self):
            if self._frames != []:
                self.three_d_functions.calibrations = self.calibrations
                self.three_d_functions.R = self.R
                self.three_d_functions._Track = self._Track
                self.three_d_functions.compute_3d_callback()
                self.X3d = self.three_d_functions.X3d
                self.Y3d = self.three_d_functions.Y3d
                self.Z3d = self.three_d_functions.Z3d

                self.X3d_s = self.three_d_functions.X3d_s
                self.Y3d_s = self.three_d_functions.Y3d_s
                self.Z3d_s = self.three_d_functions.Z3d_s
            else:
                print "please load a video first"

    def save_3d_callback(self):
        self.three_d_functions.dir = self.dir
        self.three_d_functions._save_3d_points()

    def view_3D_callback(self):
        if self._frames != []:
            f = plt.figure()
            ax = f.add_subplot(121, projection='3d')
            n = len(self.X3d)
            col = 0.0
            for x,y,z in zip(self.X3d, self.Y3d, self.Z3d):
                ax.scatter(x, y, z, c=(col/n,0,(n-col)/n), marker='o')
                col+=1.0
            ax.set_xlabel('X axis')
            ax.set_ylabel('Y axis')
            ax.set_zlabel('Z axis')
            ax.set_title('raw 3d points')
            ax = f.add_subplot(122, projection='3d')
            n = len(self.X3d_s)
            col = 0.0
            for x,y,z in zip(self.X3d_s, self.Y3d_s, self.Z3d_s):
                ax.scatter(x, y, z, c=(col/n,0,(n-col)/n), marker='o')
                col+=1.0
            ax.set_xlabel('X axis')
            ax.set_ylabel('Y axis')
            ax.set_zlabel('Z axis')
            ax.set_title('4th diff smoothing')
            plt.show()
        else:
            print "please load a video first"

def main():
    root = Tk()
    App1 = App(root)
    App1._show_frame()
    App1.three_d_functions = func_3d.compute_3d()
    root.mainloop()

if __name__=="__main__":
    main()
