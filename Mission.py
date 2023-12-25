# coding:utf-8
import math

import Arm
import BRTRobot
import VNAData
import socket
import threading
import json
import numpy as np
import pandas as pd

import SystemLogger

from DataMail import DataMail
from time import sleep, time, localtime

MissionLogger = SystemLogger.logger_init("MissionLogger", "./Log/system.log")  # 日志管理器


class Mission(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        self.Arm = Arm.Arm(Calibrate=True)  # 机械臂运动解算对象
        self.OriginWorld = None  # 机械臂末端世界坐标+欧拉角[x, y, z, u, v, w]
        self.OriginJoint = None  # 机械臂关节角度坐标[J1, J2, J3, J4, J5, J6]
        self.Data = []  # 保存的数据，包含坐标和VNA数据
        self.MovePoints = []  # 移动的点世界坐标
        self.CheckFlag = False  # 检查标志位
        self.MoveFlag = False  # 移动标志位
        self.MissionState = "stop"  # 移动状态，有stop, ready, finished, running, pause, error
        self.MoveNum = 0  # 移动到的点个数
        self.MoveNumber = 0  # 需要移动到的点个数
        self.OnePointTime = 0  # 一个点测量的时间
        self.CostTime = 0  # 已经花掉的时间
        self.MissionTime = 0  # 任务创建的时间
        self.angle = 0.0  # 玻璃围绕Z轴的旋转角度

        # 任务设置相关变量
        self.a_min = 0
        self.a_max = 0
        self.b_min = 0
        self.b_max = 0
        self.a_step = 0
        self.b_step = 0
        self.mode = 'xOy'
        self.S_mode = "21"
        self.f_min = 0  # 扫描频率最小值
        self.f_max = 0  # 扫描频率最大值
        self.f_step = 0  # 扫描频率步长
        self.f_times = 1  # 扫描一点重复次数
        self.save_folder = 'D:\workspace\AutoScanPlatform\Data'
        self.save_file = 'tmp'
        self.to_mailaddr = ''
        try:
            self.load_conf()
            for i in range(5):
                # 取消启动后自动回到上次保存位置, 设置为通过获取当前位置进行初始化连接测试
                # ret = BRTRobot.setWorldCoordinate(self.OriginWorld)
                ret, self.OriginWorld = BRTRobot.getWorldCoordinate()
                BRTRobot.waitMoving()
                if (ret):
                    break
                elif (i == 4):
                    self.MissionState = "error"
                    MissionLogger.error('ARM Connection Wrong: Check your connection')
                else:
                    MissionLogger.error('ARM Connection Wrong: Retrying')
        except:
            pass
        pass

    '''
        @description: 初始化机器人，获取机器人当前的位置
        @param {}
        @return {}
    '''

    def mission_initialize(self, angle):
        self.angle = float(angle)
        ret1, self.OriginWorld = BRTRobot.getWorldCoordinate()
        ret2, self.OriginJoint = BRTRobot.getJointCoordinate()
        if not (ret1 and ret2):
            self.MissionState = "error"
            MissionLogger.error('ARM Connection Wrong: Check your connection')
        else:
            MissionLogger.info('Get Coordinate Successfully')
        self.save_conf()

    '''
        @description: 获取沿xOy, xOz, yOz平面移动各个边的step点
        @param {}
        @return {}
    '''

    def get_move_points(self):
        self.MovePoints.clear()
        AStep_num = int((self.a_max - self.a_min) / self.a_step + 1)
        BStep_num = int((self.b_max - self.b_min) / self.b_step + 1)
        Mode_AIndex = {'xOy': 0, 'xOz': 0, 'yOz': 1}
        Mode_BIndex = {'xOy': 1, 'xOz': 2, 'yOz': 2}

        if self.CheckFlag:
            # 预检模式移动到初始框的四个点
            point_bias = [(0, 0), (0, 1), (1, 1), (1, 0)]
            for i in point_bias:
                point = [0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
                point[Mode_AIndex[self.mode]] += self.a_min + self.a_step * AStep_num * i[0]
                point[Mode_BIndex[self.mode]] += self.b_min + self.b_step * BStep_num * i[1]
                # 旋转角度
                x_position = point[0]
                y_position = point[1]
                point[0] = x_position * math.cos(math.pi / 180.0 * - self.angle) - y_position * math.sin(
                    math.pi / 180.0 * - self.angle)
                point[1] = x_position * math.sin(math.pi / 180.0 * - self.angle) + y_position * math.cos(
                    math.pi / 180.0 * - self.angle)
                self.MovePoints.append(point)
        else:
            # 扫描模式移动到初始框的所有点
            for i in range(AStep_num):
                for j in range(BStep_num):
                    point = [0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
                    point[Mode_AIndex[self.mode]] += self.a_min + self.a_step * i
                    point[Mode_BIndex[self.mode]] += self.b_min + self.b_step * j
                    # 旋转角度
                    x_position = point[0]
                    y_position = point[1]
                    point[0] = x_position * math.cos(math.pi / 180.0 * - self.angle) - y_position * math.sin(
                        math.pi / 180.0 * - self.angle)
                    point[1] = x_position * math.sin(math.pi / 180.0 * - self.angle) + y_position * math.cos(
                        math.pi / 180.0 * - self.angle)
                    self.MovePoints.append(point)
        MissionLogger.info("Move Points Setted")

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

    def scan_mode(self, a_min=0.0, a_max=0.0, b_min=0.0, b_max=0.0, a_step=5.0, b_step=5.0, mode='xOy', CheckFlag=True):
        para_name = ['a_min', 'a_max', 'b_min', 'b_max', 'a_step', 'b_step', 'mode', 'CheckFlag']
        for i in para_name:
            exec('self.{} = {}'.format(i, i))
        self.MissionState = 'ready'
        self.MoveNum = 0
        self.Data = None
        self.get_move_points()
        self.MoveNumber = self.MovePoints.__len__()
        self.OnePointTime = 0
        date_now = localtime(time())
        self.MissionTime = "{:0>2d}{:0>2d}{:0>2d}{:0>2d}".format(date_now.tm_mon, date_now.tm_mday, date_now.tm_hour,
                                                                 int(date_now.tm_min / 10) * 10)

    '''
        @description: 读取配置
        @param {}
        @return {}
    '''

    def load_conf(self):
        conf_file = open('./MissionConf.json', 'r')
        conf = json.load(conf_file)
        conf_name = [
            'OriginWorld', 'OriginJoint', 'angle',
            'a_min', 'a_max', 'b_min', 'b_max', 'a_step', 'b_step',
            'mode',
            'f_min', 'f_max', 'f_step', 'f_times', 'S_mode',
            'save_folder', 'save_file', 'to_mailaddr'
        ]
        for i in conf_name:
            exec('self.{} = conf[\'{}\']'.format(i, i))
        return conf

    '''
        @description: 保存配置
        @param {}
        @return {}
    '''

    def save_conf(self):
        conf = {}
        conf_name = [
            'OriginWorld', 'OriginJoint', 'angle',
            'a_min', 'a_max', 'b_min', 'b_max', 'a_step', 'b_step',
            'mode',
            'f_min', 'f_max', 'f_step', 'f_times', 'S_mode',
            'save_folder', 'save_file', 'to_mailaddr'
        ]
        for i in conf_name:
            exec('conf[\'{}\'] = self.{}'.format(i, i))
        try:
            conf_file = open('./MissionConf.json', 'w')
            json.dump(conf, conf_file, indent=4)
            MissionLogger.info("Save Configure Success")
        except:
            MissionLogger.info("Save Configure Failed")

    '''
        @description: 获取配置
        @param {}
        @return {}
    '''

    def get_conf(self):
        conf = {}
        conf_name = [
            'OriginWorld', 'OriginJoint', 'angle',
            'a_min', 'a_max', 'b_min', 'b_max', 'a_step', 'b_step',
            'mode',
            'f_min', 'f_max', 'f_step', 'f_times', 'S_mode',
            'save_folder', 'save_file', 'to_mailaddr'
        ]
        for i in conf_name:
            exec('conf[\'{}\'] = self.{}'.format(i, i))
        conf_json = json.dumps(conf)
        return conf_json

    '''
        @description: 获取配置
        @param {}
        @return {}
    '''

    def get_state(self):
        TotalTime = self.OnePointTime * self.MoveNumber
        TotalTimeH = int(TotalTime / 60 / 60)
        TotalTimeM = int((TotalTime - TotalTimeH * 60 * 60) / 60)
        TotalTimeS = int(TotalTime - TotalTimeH * 60 * 60 - TotalTimeM * 60)
        LeftTime = self.OnePointTime * (self.MoveNumber - self.MoveNum)
        LeftTimeH = int(LeftTime / 60 / 60)
        LeftTimeM = int((LeftTime - LeftTimeH * 60 * 60) / 60)
        LeftTimeS = int(LeftTime - LeftTimeH * 60 * 60 - LeftTimeM * 60)
        full_path = "{}/{}_{}_{}_{}.csv".format(self.save_folder, self.MissionTime, self.save_file, self.mode,
                                                self.S_mode)
        S_full_path = "{}/{}_{}_{}_{}_S.csv".format(self.save_folder, self.MissionTime, self.save_file, self.mode,
                                                    self.S_mode)
        state = {
            'state': self.MissionState,
            'MoveNum': self.MoveNum,
            'MoveNumber': self.MoveNumber,
            'OnePointTime': self.OnePointTime,
            'TotalTimeH': TotalTimeH,
            'TotalTimeM': TotalTimeM,
            'TotalTimeS': TotalTimeS,
            'LeftTimeH': LeftTimeH,
            'LeftTimeM': LeftTimeM,
            'LeftTimeS': LeftTimeS,
            'full_path': full_path,
            'S_full_path': S_full_path
        }
        return json.dumps(state)

    '''
        @description: 获取配置
        @param {
            float a_min, a_max, b_min, b_max: 第一个和第二个参数的
        }
        @return {}
    '''

    def get_range(self, a_min, a_max):
        a_min = float(a_min)
        a_max = float(a_max)
        a_min_available = 0
        a_max_available = 0
        b_min_available = 0
        b_max_available = 0
        Mode_AIndex = {'xOy': 0, 'xOz': 0, 'yOz': 1}
        Mode_BIndex = {'xOy': 1, 'xOz': 2, 'yOz': 2}
        # 获得a变量可以到达的最小值
        while (a_min_available > -2000):
            point = self.OriginWorld.copy()
            point[Mode_AIndex[self.mode]] = point[Mode_AIndex[self.mode]] + a_min_available
            if (BRTRobot.judgeWorldCoordinate(point)):
                a_min_available -= 5.0
            else:
                a_min_available += 5.0
                break
        # 获得a变量可以到达的最大值
        while (a_max_available < 2000):
            point = self.OriginWorld.copy()
            point[Mode_AIndex[self.mode]] = point[Mode_AIndex[self.mode]] + a_max_available
            if (BRTRobot.judgeWorldCoordinate(point)):
                a_max_available += 5.0
            else:
                a_max_available -= 5.0
                break
        # 获得b变量可以到达的最小值
        while (b_min_available > -2000):
            point1 = self.OriginWorld.copy()
            point1[Mode_BIndex[self.mode]] = point1[Mode_BIndex[self.mode]] + b_min_available
            point2 = self.OriginWorld.copy()
            point2[Mode_AIndex[self.mode]] = point2[Mode_AIndex[self.mode]] + a_min
            point2[Mode_BIndex[self.mode]] = point2[Mode_BIndex[self.mode]] + b_min_available
            point3 = self.OriginWorld.copy()
            point3[Mode_AIndex[self.mode]] = point3[Mode_AIndex[self.mode]] + a_max
            point3[Mode_BIndex[self.mode]] = point3[Mode_BIndex[self.mode]] + b_min_available
            if (BRTRobot.judgeWorldCoordinate(point1) and BRTRobot.judgeWorldCoordinate(
                    point2) and BRTRobot.judgeWorldCoordinate(point3)):
                b_min_available -= 5.0
            else:
                b_min_available += 5.0
                break
        # 获得b变量可以到达的最大值
        while (b_max_available < 2000):
            point1 = self.OriginWorld.copy()
            point1[Mode_BIndex[self.mode]] = point1[Mode_BIndex[self.mode]] + b_max_available
            point2 = self.OriginWorld.copy()
            point2[Mode_AIndex[self.mode]] = point2[Mode_AIndex[self.mode]] + a_min
            point2[Mode_BIndex[self.mode]] = point2[Mode_BIndex[self.mode]] + b_max_available
            point3 = self.OriginWorld.copy()
            point3[Mode_AIndex[self.mode]] = point3[Mode_AIndex[self.mode]] + a_max
            point3[Mode_BIndex[self.mode]] = point3[Mode_BIndex[self.mode]] + b_max_available
            if (BRTRobot.judgeWorldCoordinate(point1) and BRTRobot.judgeWorldCoordinate(
                    point2) and BRTRobot.judgeWorldCoordinate(point3)):
                b_max_available += 5.0
            else:
                b_max_available -= 5.0
                break
        available_range = {
            'a_min_available': a_min_available,
            'a_max_available': a_max_available,
            'b_min_available': b_min_available,
            'b_max_available': b_max_available
        }
        return json.dumps(available_range)
        pass

    '''
        @description: 获取S参数并保存
        @param {}
        @return {}
    '''

    def get_S_parameter(self):
        # 根据采集次数获取数据
        for i in range(int(self.f_times)):
            MissionLogger.info("Getting VNA Data: {}, {}, {}".format(self.f_min, self.f_max, self.f_step))
            # 5次内尝试获取数据，全部失败获得全部NULL
            for _ in range(5):
                res, PointVNAData = VNAData.get_vnadata(self.f_min, self.f_max, self.f_step, self.S_mode)
                if (res):
                    break
            # 拼接数据
            PointVNADataName = ['Freq', 'E_r', 'E_i']
            if i == 0:
                PdALLData = pd.DataFrame(data=PointVNAData, columns=PointVNADataName)
            else:
                PdALLData = PdALLData.append(pd.DataFrame(data=PointVNAData, columns=PointVNADataName))
        # 保存数据
        PdALLData = PdALLData.reset_index(drop=True)
        PdALLData.to_csv(
            "{}/{}_{}_{}_{}_S参数.csv".format(self.save_folder, self.MissionTime, self.save_file, self.mode,
                                              self.S_mode))
        # 发送邮件
        if (self.to_mailaddr != ''):
            data_mail = DataMail(to_addr=self.to_mailaddr,
                                 mail_title='S Parameter Get Successfully',
                                 mail_text="Configuration: \r\n    S parameter:{S_mode}\r\n    Frequency(GHz): {f_min} ~ {f_max}". \
                                 format(S_mode=self.S_mode, f_min=self.f_min, f_max=self.f_max),
                                 data_path="{}/{}_{}_{}_{}_S参数.csv".format(self.save_folder, self.MissionTime,
                                                                             self.save_file, self.mode, self.S_mode)
                                 )
            data_mail.setDaemon(True)
            data_mail.start()
        pass

    '''
        @description: 运行线程
        @param {}
        @return {}
    '''

    def run(self):
        while 1:
            try:
                # 状态为运动
                if self.MissionState == 'running':
                    # 所有点移动完毕
                    if self.MoveNum >= self.MovePoints.__len__():
                        # 回到初始位置
                        self.MoveNum = 0
                        BRTRobot.setWorldCoordinate(np.array(self.OriginWorld))
                        BRTRobot.waitMoving()
                        MissionLogger.info("Move Finished")
                        # self.MoveFlag = False
                        # 扫描模式保存数据
                        if not self.CheckFlag:
                            self.MissionState = "saving"
                            MissionLogger.info("Saving data file")
                            # 重排列名
                            DataColumns = ['x', 'y', 'z', 'Freq', 'E_r', 'E_i']
                            self.Data = self.Data[DataColumns].reset_index(drop=True)
                            self.Data.to_csv(
                                "{}/{}_{}_{}_{}.csv".format(self.save_folder, self.MissionTime, self.save_file,
                                                            self.mode, self.S_mode))
                            # 可以发送邮件则发送邮件
                            if self.to_mailaddr != '':
                                data_mail = DataMail(to_addr=self.to_mailaddr,
                                                     mail_title='Scan Finished Successfully',
                                                     mail_text="Scan Configuration: \r\n    Mode:{mode}\r\n    S parameter:{S_mode}\r\n    Range(mm):{a_length} x {b_length}\r\n    Frequency(GHz): {f_min} ~ {f_max}". \
                                                     format(mode=self.mode, S_mode=self.S_mode,
                                                            a_length=(self.a_max - self.a_min),
                                                            b_length=(self.b_max - self.b_min), f_min=self.f_min,
                                                            f_max=self.f_max),
                                                     data_path="{}/{}_{}_{}_{}.csv".format(self.save_folder,
                                                                                           self.MissionTime,
                                                                                           self.save_file, self.mode,
                                                                                           self.S_mode)
                                                     )
                                data_mail.setDaemon(True)
                                data_mail.start()
                        self.MissionState = "finished"
                    else:
                        if self.MoveNum == 1:
                            start_time = time()
                        # 模式选择速度，预检比较快
                        if self.CheckFlag:
                            speed = 100
                        else:
                            speed = 60

                        # 移动进入下一个点
                        self.MissionState = "running"
                        for i in range(5):
                            res1 = True
                            res2 = True
                            # 没有进入下一个点前先复位
                            if self.MoveNum == 0:
                                res1 = BRTRobot.setWorldCoordinate(np.array(self.OriginWorld))
                                res2 = BRTRobot.waitMoving()
                            res3 = BRTRobot.setWorldCoordinate(
                                np.array(self.MovePoints[self.MoveNum]) + np.array(self.OriginWorld), speed)
                            res4 = BRTRobot.waitMoving()
                            if res1 and res2 and res3 and res4:
                                break
                            elif i < 4:
                                MissionLogger.error('ARM Connection Wrong: Retrying')
                            else:
                                MissionLogger.error('ARM Connection Wrong: Check your connection')
                                self.MissionState = "error"
                        if self.MissionState == "error":
                            if self.to_mailaddr != '':
                                data_mail = DataMail(to_addr=self.to_mailaddr,
                                                     mail_title='!!!Auto Scan Wrong!!!',
                                                     mail_text='There is a wrong happened in Scan system',
                                                     data_path=""
                                                     )
                                data_mail.setDaemon(True)
                                data_mail.start()
                            continue

                        # 扫描模式获取数据
                        if not self.CheckFlag:
                            arr_len = 0
                            all_point_vna_data = []
                            PointVNADataName = ['Freq', 'E_r', 'E_i']
                            for i in range(int(self.f_times)):
                                MissionLogger.info(
                                    "Getting VNA Data: {}, {}, {}".format(self.f_min, self.f_max, self.f_step))
                                for _ in range(5):
                                    res, PointVNAData = VNAData.get_vnadata(self.f_min, self.f_max, self.f_step,
                                                                            self.S_mode)
                                    if res:
                                        break
                                # 旧版逻辑未计算平均值，已弃用
                                # if i == 0:
                                #     PdALLData = pd.DataFrame(data=PointVNAData, columns=PointVNADataName)
                                # else:
                                #     PdALLData = PdALLData.append(pd.DataFrame(data=PointVNAData, columns=PointVNADataName))

                                # 多次扫描数值相加以计算平均值
                                arr_len = len(PointVNAData)
                                if i == 0:
                                    all_point_vna_data = PointVNAData
                                else:
                                    for j in range(arr_len):
                                        all_point_vna_data[j][1] = float(all_point_vna_data[j][1]) + float(PointVNAData[j][1])
                                        all_point_vna_data[j][2] = float(all_point_vna_data[j][2]) + float(PointVNAData[j][2])

                            for i in range(arr_len):
                                all_point_vna_data[i][1] = float(all_point_vna_data[i][1]) / float(self.f_times)
                                all_point_vna_data[i][2] = float(all_point_vna_data[i][2]) / float(self.f_times)
                            PdALLData = pd.DataFrame(data=all_point_vna_data, columns=PointVNADataName)

                            # 添加坐标列
                            PdALLData['x'] = self.MovePoints[self.MoveNum][0]
                            PdALLData['y'] = self.MovePoints[self.MoveNum][1]
                            PdALLData['z'] = self.MovePoints[self.MoveNum][2]
                            if (self.MoveNum == 0):
                                self.Data = PdALLData
                            else:
                                self.Data = self.Data.append(PdALLData)
                            # 扫描模式保存数据
                            if self.MoveNum % 20 == 0:
                                if not self.CheckFlag:
                                    # 重排列名
                                    DataColumns = ['x', 'y', 'z', 'Freq', 'E_r', 'E_i']
                                    tmp_Data = self.Data.copy()
                                    tmp_Data = tmp_Data[DataColumns].reset_index(drop=True)
                                    tmp_Data.to_csv(
                                        "{}/{}_{}_{}_{}.csv".format(self.save_folder, self.MissionTime, self.save_file,
                                                                    self.mode, self.S_mode))
                        if self.MoveNum == 1:
                            self.OnePointTime = time() - start_time
                        self.MoveNum += 1
                else:
                    sleep(1)
            except Exception as err:
                MissionLogger.error("UNKOWN ERROR HAPPENED")

    '''
        @description: 获取x，y，z边界范围u
        @return {json.dumps(available_range)}
    '''

    def get_all_range(self):
        ret1, self.OriginWorld = BRTRobot.getWorldCoordinate()
        if not ret1:
            self.MissionState = "error"
            MissionLogger.error('ARM Connection Wrong: Check your connection')
        else:
            MissionLogger.info('Get Coordinate Successfully')

        min_available = [0, 0, 0, 0, 0, 0]
        max_available = [0, 0, 0, 0, 0, 0]
        for i in range(6):
            # 获得point[i]变量可以到达的最小值
            while min_available[i] > -2000:
                point = self.OriginWorld.copy()
                point[i] = point[i] + min_available[i]
                if BRTRobot.judgeWorldCoordinate(point):
                    min_available[i] -= 5.0
                else:
                    min_available[i] += 5.0
                    break
            # 获得point[i]变量可以到达的最大值
            while max_available[i] < 2000:
                point = self.OriginWorld.copy()
                point[i] = point[i] + max_available[i]
                if BRTRobot.judgeWorldCoordinate(point):
                    max_available[i] += 5.0
                else:
                    max_available[i] -= 5.0
                    break
            min_available[i] = 0 if min_available[i] > 0 else min_available[i]
            max_available[i] = 0 if max_available[i] < 0 else max_available[i]

        available_range = {
            'x_min_available': min_available[0],
            'x_max_available': max_available[0],
            'y_min_available': min_available[1],
            'y_max_available': max_available[1],
            'z_min_available': min_available[2],
            'z_max_available': max_available[2],
            'u_min_available': min_available[3],
            'u_max_available': max_available[3],
            'v_min_available': min_available[4],
            'v_max_available': max_available[4],
            'w_min_available': min_available[5],
            'w_max_available': max_available[5]
        }
        return json.dumps(available_range)
        pass


if __name__ == "__main__":
    BRTMission = Mission()
    sleep(1)
    pass
