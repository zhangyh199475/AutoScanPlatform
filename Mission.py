#coding:utf-8
import Arm
import BRTRobot
import VNAData
import socket
import threading
import json
import numpy as np
import pandas as pd

from time import sleep

class Mission(threading.Thread): 
    def __init__(self):
        threading.Thread.__init__(self)
        self.Arm = Arm.Arm(Calibrate = True) # 机械臂运动解算对象
        self.OriginWorld = None # 机械臂末端世界坐标+欧拉角[x, y, z, u, v, w]
        self.OriginJoint = None # 机械臂关节角度坐标[J1, J2, J3, J4, J5, J6]
        self.Data = [] # 保存的数据，包含坐标和VNA数据
        self.MovePoints = [] # 移动的点世界坐标
        self.CheckFlag = False # 检查标志位
        self.MoveFlag = False # 移动标志位
        self.MissionState = "stop" # 移动状态，有stop, ready, finished, running, pause
        self.MoveNum = 0 # 移动到的点个数
        self.MoveNumber = 0 # 需要移动到的点个数
        self.CostTime = 0 # 已经花掉的时间

        # 任务设置相关变量
        self.mission_conf = [
            'a_min', 'a_max', 'b_min', 'b_max', 'a_step', 'b_step', # 移动距离相关变量
            'mode', # 模式变量
            'f_min', 'f_max', 'f_step', 'f_times', # vna数据读取相关变量
            'save_folder', 'save_file' # 保存文件相关变量
        ]
        self.a_min = 0
        self.a_max = 0
        self.b_min = 0
        self.b_max = 0
        self.a_step = 0
        self.b_step = 0
        self.mode = 'xOy'
        self.f_min = 0 # 扫描频率最小值
        self.f_max = 0 # 扫描频率最大值
        self.f_step = 0 # 扫描频率步长
        self.f_times = 1 # 扫描一点重复次数
        self.save_folder = './'
        self.save_file = 'tmp.csv'
        try: 
            self.load_conf()
            BRTRobot.setWorldCoordinate(self.OriginWorld)
            BRTRobot.waitMoving()
        except: 
            pass
        pass

    '''
        @description: 初始化机器人，获取机器人当前的位置
        @param {}
        @return {}
    '''
    def mission_initialize(self): 
        self.OriginWorld = BRTRobot.getWorldCoordinate()
        self.OriginJoint = BRTRobot.getJointCoordinate()
    
    '''
        @description: 获取沿xOy, xOz, yOz平面移动各个边的step点
        @param {}
        @return {}
    '''
    def get_move_points(self): 
        self.MovePoints.clear()
        AStep_num = int((self.a_max - self.a_min) / self.a_step)
        BStep_num = int((self.b_max - self.b_min) / self.b_step)
        Mode_AIndex = {'xOy': 0, 'xOz': 0, 'yOz': 1}
        Mode_BIndex = {'xOy': 1, 'xOz': 2, 'yOz': 2}

        if (self.CheckFlag): 
            point_bias = [(0, 0), (0, 1), (1, 1), (1, 0)]
            for i in point_bias: 
                # point = self.OriginWorld.copy()
                point = [0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
                point[Mode_AIndex[self.mode]] = point[Mode_AIndex[self.mode]] + self.a_min + self.a_step *AStep_num * i[0]
                point[Mode_BIndex[self.mode]] = point[Mode_BIndex[self.mode]] + self.b_min + self.b_step *BStep_num * i[1]
                self.MovePoints.append(point)
            # self.MovePoints.append([0.0, 0.0, 0.0, 0.0, 0.0, 0.0])
        else: 
            for i in range(AStep_num): 
                for j in range(BStep_num): 
                    # point = self.OriginWorld.copy()
                    point = [0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
                    point[Mode_AIndex[self.mode]] = point[Mode_AIndex[self.mode]] + self.a_min + self.a_step * i
                    point[Mode_BIndex[self.mode]] = point[Mode_BIndex[self.mode]] + self.b_min + self.b_step * j
                    self.MovePoints.append(point)
            # self.MovePoints.append([0.0, 0.0, 0.0, 0.0, 0.0, 0.0])
        print(self.MovePoints)
        print("[Move Points Setted]")
    
    '''
        @description: 检查或扫描
        @param {
            float a_min, a_max: x(xOy), x(xOz), y(yOz)轴的扫描范围，即坐标面的前面那个轴，单位mm
            float b_min, b_max: y(xOy), z(xOz), z(yOz)轴的扫描长度，即坐标面的后面那个轴，单位mm
            float a_step, b_step: 即a, b长度的扫描步长
            str mode: 只取xOy, xOz, yOz三种情况，使用字符串
        }
        @return {}
    '''
    def scan_mode(self, a_min=0.0, a_max=0.0, b_min=0.0, b_max=0.0, a_step=5.0, b_step=5.0, mode='xOy', check = True): 
        self.CheckFlag = check
        self.MissionState = 'ready'
        self.MoveNum = 0
        self.Data = None
        self.a_min = a_min
        self.a_max = a_max
        self.b_min = b_min
        self.b_max = b_max
        self.a_step = a_step
        self.b_step = b_step
        self.mode = mode
        self.get_move_points()
        self.MoveNumber = self.MovePoints.__len__()
    
    '''
        @description: 读取配置
        @param {}
        @return {}
    '''
    def load_conf(self): 
        conf_file = open('./MissionConf.json', 'r')
        conf = json.load(conf_file)
        self.OriginWorld = conf['word_coordinate']
        self.OriginJoint = conf['joint_coordinate'] 
        self.a_min = conf['a_min']
        self.a_max = conf['a_max']
        self.b_min = conf['b_min']
        self.b_max = conf['b_max']
        self.a_step = conf['a_step']
        self.b_step = conf['b_step']
        self.mode = conf['mode']
        self.f_min = conf['f_min']
        self.f_max = conf['f_max']
        self.f_step = conf['f_step']
        self.f_times = conf['f_times']
        self.save_folder = conf['save_folder']
        self.save_file = conf['save_file']

    '''
        @description: 保存配置
        @param {}
        @return {}
    '''
    def save_conf(self): 
        conf = {}
        conf['word_coordinate'] = list(self.OriginWorld)
        conf['joint_coordinate'] = list(self.OriginJoint)
        conf['a_min'] = self.a_min
        conf['a_max'] = self.a_max
        conf['b_min'] = self.b_min
        conf['b_max'] = self.b_max
        conf['a_step'] = self.a_step
        conf['b_step'] = self.b_step
        conf['mode'] = self.mode
        conf['f_min'] = self.f_min
        conf['f_max'] = self.f_max
        conf['f_step'] = self.f_step
        conf['f_times'] = self.f_times
        conf['save_folder'] = self.save_folder
        conf['save_file'] = self.save_file
        try: 
            conf_file = open('./MissionConf.json', 'w')
            json.dump(conf, conf_file, indent=4)
            print("[Save Configure Success]")
            pass
        except: 
            print("[Save Configure Failed]")

    '''
        @description: 获取配置
        @param {}
        @return {}
    '''
    def get_conf(self): 
        conf = {}
        conf['word_coordinate'] = list(self.OriginWorld)
        conf['joint_coordinate'] = list(self.OriginJoint)
        conf['a_min'] = self.a_min
        conf['a_max'] = self.a_max
        conf['b_min'] = self.b_min
        conf['b_max'] = self.b_max
        conf['a_step'] = self.a_step
        conf['b_step'] = self.b_step
        conf['mode'] = self.mode
        conf['f_min'] = self.f_min
        conf['f_max'] = self.f_max
        conf['f_step'] = self.f_step
        conf['f_times'] = self.f_times
        conf['save_folder'] = self.save_folder
        conf['save_file'] = self.save_file
        conf['save_file'] = self.save_file
        conf_json = json.dumps(conf)
        return conf_json

    '''
        @description: 获取配置
        @param {}
        @return {}
    '''
    def get_state(self): 
        state = {
            'state': self.MissionState, 
            'MoveNum': self.MoveNum, 
            'MoveNumber': self.MoveNumber
        }
        return json.dumps(state)

    def run(self): 
        while(1): 
            # if (self.MoveFlag): 
            if (self.MissionState == 'running'): 
                # 所有点移动完毕
                if(self.MoveNum >= self.MovePoints.__len__()) : 
                    # 回到初始位置
                    self.MoveNum = 0
                    BRTRobot.setWorldCoordinate(np.array(self.OriginWorld))
                    BRTRobot.waitMoving()
                    print("[Move Finished]")
                    # self.MoveFlag = False
                    # 扫描模式保存数据
                    if (not self.CheckFlag): 
                        self.MissionState = "saving"
                        # 重排列名
                        DataColumns = ['x', 'y', 'z', 'Hz', 'R', 'I']
                        self.Data = self.Data[DataColumns].reset_index(drop=True)
                        self.Data.to_csv(self.save_folder + "/" + self.save_file)
                    self.MissionState = "finished"
                else: 
                    # 模式选择速度，预检比较快
                    if (self.CheckFlag): 
                        speed = 100
                    else: 
                        speed = 60
                    
                    # 移动
                    self.MissionState = "running"
                    if (self.MoveNum == 0): 
                        BRTRobot.setWorldCoordinate(np.array(self.OriginWorld))
                        BRTRobot.waitMoving()
                    print(np.array(self.MovePoints[self.MoveNum]) + np.array(self.OriginWorld))
                    BRTRobot.setWorldCoordinate(np.array(self.MovePoints[self.MoveNum]) + np.array(self.OriginWorld), speed)
                    BRTRobot.waitMoving()

                    # 扫描模式获取数据
                    if (not self.CheckFlag): 
                        for i in range(int(self.f_times)): 
                            print("[Getting VNA Data]: ", self.f_min, self.f_max, self.f_step)
                            PointVNAData = VNAData.get_vnadata(self.f_min, self.f_max, self.f_step)
                            PointVNADataName = ['Hz', 'R', 'I']
                            if (i == 0): 
                                PdALLData = pd.DataFrame(data=PointVNAData, columns=PointVNADataName)
                            else: 
                                PdALLData = PdALLData.append(pd.DataFrame(data=PointVNAData, columns=PointVNADataName))
                        # 添加坐标列
                        PdALLData['x'] = self.MovePoints[self.MoveNum][0]
                        PdALLData['y'] = self.MovePoints[self.MoveNum][1]
                        PdALLData['z'] = self.MovePoints[self.MoveNum][2]
                        # print(PdALLData)
                        if (self.MoveNum == 0): 
                            self.Data = PdALLData
                        else: 
                            self.Data = self.Data.append(PdALLData)
                        print(self.Data.shape)
                        # 扫描模式保存数据
                        if (self.MoveNum % 20 == 0): 
                            if (not self.CheckFlag): 
                                # 重排列名
                                DataColumns = ['x', 'y', 'z', 'Hz', 'R', 'I']
                                tmp_Data = self.Data.copy()
                                tmp_Data = tmp_Data[DataColumns].reset_index(drop=True)
                                tmp_Data.to_csv(self.save_folder + "/" + self.save_file)
                    self.MoveNum += 1
            else: 
                sleep(1)



if __name__ == "__main__": 
    print("asdf")
    BRTMission = Mission()
    BRTRobot.setJointCoordinate([0, -30, -30, 0, 60, 0])
    BRTRobot.waitMoving()
    sleep(1)
    pass