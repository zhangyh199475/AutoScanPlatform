#coding:utf-8
from cmath import acos, pi, sqrt
import json
from re import T
import numpy as np
from math import radians, sin, cos, atan2, acos
from scipy.spatial.transform import Rotation as R


# 机械臂对象
class Arm:
    # 对象初始化 
    def __init__(self, ConfPath="./ArmConf.json", Calibrate=True) -> None:
        self.DH_theta = []
        self.DH_d = []
        self.DH_a = []
        self.DH_alpha = []
        self.Angle_min = []
        self.Angle_max = []
        self.__loadConf(ConfPath, Calibrate)

    '''
        @description: 初始化过程中从json文件中载入参数
        @param {
            string ConfPath: 配置文件存放位置，默认和脚本一个目录
            bool Calibrate: 决定是否使用校准参数，默认为True，使用校准参数，置为Flase使用手册标准参数
        }
        @return {}
    '''
    def __loadConf(self, ConfPath, Calibrate=True): 
        ArmConfFile = open(ConfPath, "r")
        ArmConfJson = json.load(ArmConfFile)
        ArmConfFile.close()
        if(Calibrate): 
            DH = "DH_calibrate"
        else: 
            DH = "DH_manual"
        self.DH_theta = ArmConfJson[DH]["theta"]
        self.DH_d = ArmConfJson[DH]["d"]
        self.DH_a = ArmConfJson[DH]["a"]
        self.DH_alpha = ArmConfJson[DH]["alpha"]
        self.Angle_min = ArmConfJson["Angle"]["min"]
        self.Angle_max = ArmConfJson["Angle"]["max"]
        self.Joint_num = self.DH_theta.__len__()
    
    '''
        @description: 传入四个DH参数，输出一个T矩阵，用于轴与轴之间的坐标位置变换
        @param {
            float theta: DH参数x轴绕z轴偏转角theta
            float d: DH参数z轴位置偏移
            float a: DH参数x轴位置偏移
            float alpha: DH参数z轴绕x轴偏转角alpha
        }
        @return {
            np.darry(4, 4) matrix: 坐标位置变换矩阵
        }
    '''
    def __getDHMatrix(self, theta, d, a, alpha): 
        alpha = alpha / 180 * np.pi
        theta = theta / 180 * np.pi
        return np.array([
            [cos(theta), -sin(theta)*cos(alpha),    sin(theta)*sin(alpha),      a*cos(theta) ], 
            [sin(theta), cos(theta)*cos(alpha),     -cos(theta)*sin(alpha),     a*sin(theta) ],
            [0,          sin(alpha),                cos(alpha),                 d], 
            [0,          0,                         0,                          1]])


    '''
        @description: 获取腕部坐标
        @param {
            float [x, y, z, u, v, w]: 世界坐标(x, y, z)和xyz欧拉角(u, v, w)
        }
        @return {
            float [WristX, WristY, WristZ]: 腕部世界坐标(x, y, z)
        }
    '''
    def getWristCoordinate(self, x, y, z, u, v, w): 
        # 将xyz欧拉角转换成zyx欧拉角（先x，后y最后z），最后转动z轴更好计算末端z轴和世界坐标系x, y, z的夹角余弦
        # xyz一般用u, v, w表示，zxy一般用alpha, beta, gamma表示，即pitch, roll, yaw
        # print('x, y, z, u, v, w: %f, %f, %f, %f, %f, %f'% (x, y, z, u, v, w))
        R_Matrix = R.from_euler('xyz', [u, v, w], degrees=True).as_matrix()
        # print('R_Matrix:', R_Matrix)
        [alpha, beta, gamma] = R.from_matrix(R_Matrix).as_euler('zyx', degrees=True)
        # print('[alpha, beta, gamma]: %f, %f, %f'%( alpha , beta, gamma))

        # 通过x, y轴旋转角beta, gamma计算夹角余弦并乘最后一个轴的长度转换到腕部坐标
        WristX = x - sin(beta / 180 * np.pi) * self.DH_d[5]
        WristY = y - sin(-gamma / 180 * np.pi) * cos(beta / 180 * np.pi) * self.DH_d[5]
        WristZ = z - cos(-gamma / 180 * np.pi) * cos(beta / 180 * np.pi) * self.DH_d[5]
        # print('[WristX, WristY, WristZ] : %f, %f, %f' % (WristX, WristY, WristZ))
        return [WristX, WristY, WristZ]

    '''
        @description: Forward Kinematics, 正解机器人末端世界坐标系
        @param {
            float Ji: i = [1, 6]，表示1-6轴角度，绕z轴正方向的逆时针方向为正（右手螺旋法则）
        }
        @return {
            float [x, y, z, u, v, w]: 世界坐标(x, y, z)和xyz欧拉角(u, v, w)
        }
    '''
    def armFK(self, J1=0.0, J2=0.0, J3=0.0, J4=0.0, J5=0.0, J6=0.0): 
        Js = [J1, J2, J3, J4, J5, J6]
        DH_matrixes = []
        Tn = None
        
        # 计算T1-T6一共6个变换矩阵
        for i in range(self.Joint_num): 
            DH_matrixes.append(self.__getDHMatrix(self.DH_theta[i] + Js[i], self.DH_d[i], self.DH_a[i], self.DH_alpha[i]))
        
        # 变换矩阵连乘获得姿态和位置矩阵Tn
        for i in range(self.Joint_num):
            if i == 0 : 
                Tn = DH_matrixes[i]
            else: 
                Tn = np.matmul(Tn, DH_matrixes[i])
        
        # 提取M_tmp中的位置和旋转矩阵，并将旋转矩阵转化为欧拉角
        WorldCoordinate = [Tn[0, 3], Tn[1, 3], Tn[2, 3]]
        Eulers = R.from_matrix(Tn[:3, :3]).as_euler('xyz', degrees=True)

        # 欧拉角末端放到列表中返回
        for i in Eulers: 
            WorldCoordinate.append(i) 
        
        # print(self.getWristCoordinate(WorldCoordinate[0], WorldCoordinate[1], WorldCoordinate[2], WorldCoordinate[3], WorldCoordinate[4], WorldCoordinate[5]))
        return WorldCoordinate

    '''
        @description: Inverse Kinematics, 逆解机器人轴角度（尚未完成！！！）
        @param {
            float [x, y, z, u, v, w]: 世界坐标(x, y, z)和xyz欧拉角(u, v, w)
        }
        @return {
            float Ji: i = [1, 6]，表示1-6轴角度，绕z轴正方向的逆时针方向为正（右手螺旋法则）
        }
    '''
    def armIK(self, x = 0.0, y = 0.0, z = 0.0, u = 0.0, v = 0.0, w = 0.0):
        [WristX, WristY, WristZ] = self.getWristCoordinate(x, y, z, u, v, w)

        L_23 = self.DH_a[1]
        L_34 = sqrt(self.DH_a[2]**2 + self.DH_d[3]**2).real
        L_25 = sqrt(WristX**2 + WristY**2).real - self.DH_a[0] 
        L_24 = sqrt(L_25**2 + (WristZ - self.DH_d[0])**2).real
        A_234 = acos((L_24**2 - L_23**2 - L_34**2) / (-2 * L_23 * L_34))
        A_425 = atan2((WristZ - self.DH_d[0]), L_25)
        A_324 = acos((L_34**2 - L_23**2 - L_24**2) / (-2 * L_23 * L_24))
        
        J1 = atan2(WristY, WristX)
        J2 = A_324 + A_425 - np.pi / 2
        J3_bias = atan2(abs(self.DH_a[2]), abs(self.DH_d[3]))
        J3 = A_234 - J3_bias - np.pi / 2
        Js = [J1, J2, J3]

        # 获得最后三个角度的旋转矩阵
        Ts = []
        T_tmp = None
        for i in range(3): 
            Ts.append(self.__getDHMatrix(self.DH_theta[i] + Js[i], self.DH_d[i], self.DH_a[i], self.DH_alpha[i]))
            if (i == 0): 
                T_tmp = Ts[0]
            else: 
                T_tmp = np.matmul(T_tmp, Ts[i])
        Matrix_All = R.from_euler('xyz', [u, v, w], degrees=True).as_matrix()
        Matrix_36 = np.matmul(np.matrix(T_tmp[:3, :3]).I, Matrix_All)
        [J4, J5, J6] = R.from_matrix(Matrix_36).as_euler('zyx', degrees=True)
        Js = [J1 / np.pi * 180, J2 / np.pi * 180, J3 / np.pi * 180, J4, J5, J6]
        # Js = np.array(Js) / np.pi * 180

        self.armFK(Js[0], Js[1], Js[2], Js[3], Js[4], Js[5]) 
        return Js


if __name__ == "__main__": 
    BRTArm = Arm(Calibrate = True)
    A = [0.0, 0.0, 0.0, 30.0, 30.0, 90.0]
    A_res = BRTArm.armFK(A[0], A[1], A[2], A[3], A[4], A[5]) 
    print(np.around(np.array(A_res) * 100) / 100)
    A_res_res = BRTArm.armIK(A_res[0], A_res[1], A_res[2], A_res[3], A_res[4], A_res[5])
    print(np.around(np.array(A_res_res) * 100) / 100)
    
    print("================")
    
    B = [30.0, 30.0, 30.0, 30.0, 30.0, 0.0]
    B_res = BRTArm.armFK(B[0], B[1], B[2], B[3], B[4], B[5])
    print(np.around(np.array(B_res) * 1000) / 1000)
    B_res_res = BRTArm.armIK(B_res[0], B_res[1], B_res[2], B_res[3], B_res[4], B_res[5])
    print(np.around(np.array(B_res_res) * 1000) / 1000)
