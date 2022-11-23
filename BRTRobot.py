#coding:utf-8
import socket
import json
import numpy as np

from Arm import Arm
from time import sleep
from math import sqrt

# 机器人连接设置
BRT_ip = "192.168.4.4" # 机器人默认IP
BRT_port = 9760 # 机器人默认端口
BRT_speed = 60 # 机器人默认移动速度
MovingCheckGap = 0.01 # 检查机器人移动状态间隔
socket.setdefaulttimeout(3) # 连接检测默认最长时间
BRTArm = Arm(Calibrate = True)


'''
    @description: 获取伯朗特机器人的世界坐标系
    @param {}
    @return {
        ret: 尝试连接状态，True为正常False为失败
        float [x, y, z, u, v, w]: 世界坐标：x, y, z, 欧拉角：u, v, w
    }
'''
def getWorldCoordinate(): 
    try: 
        BRT_connector = socket.socket()
        BRT_connector.connect((BRT_ip, BRT_port))
        getWorldCoordinate_json = {
                "dsID":"www.hc-system.com.RemoteMonitor",
                "reqType": "query",
                "packID": "0",
                "queryAddr":["world-0", "world-1", "world-2", "world-3", "world-4", "world-5"]
        }
        BRT_connector.send(json.dumps(getWorldCoordinate_json).encode("ascii"))
        WorldCoordinate_msg = BRT_connector.recv(1024) .decode('ascii')
        WorldCoordinate = json.loads(WorldCoordinate_msg)["queryData"]
        print("[World Coordinate]:", WorldCoordinate)
        BRT_connector.close()
        return [True, list(np.array(WorldCoordinate).astype(np.float64))]
    except: 
        return [False, None]

'''
    @description: 获取伯朗特机器人的关节坐标系
    @param {}
    @return {
        ret: 尝试连接状态，True为正常False为失败
        float [J1-J6]: J1-J6的关节角度
    }
'''
def getJointCoordinate():
    try: 
        BRT_connector = socket.socket()
        BRT_connector.connect((BRT_ip, BRT_port))
        getJointCoordinate_json = {
                "dsID":"www.hc-system.com.RemoteMonitor",
                "reqType": "query",
                "packID": "0",
                "queryAddr":["axis-0", "axis-1", "axis-2", "axis-3", "axis-4", "axis-5"]
        }
        BRT_connector.send(json.dumps(getJointCoordinate_json).encode("ascii"))
        JointCoordinate_msg = BRT_connector.recv(1024) .decode('ascii')
        JointCoordinate = json.loads(JointCoordinate_msg)["queryData"]
        print("[Joint Coordinate]:", JointCoordinate)
        BRT_connector.close()
        return [True, list(np.array(JointCoordinate).astype(np.float64))]
    except: 
        return [False, None]

'''
    @description: 获取伯朗特机器人的运动状态
    @param {}
    @return {
        ret: 尝试连接状态，True为正常False为失败
        float MoveState: 运动状态，False为正在运动，不可操作，反之则相反
    }
'''
def getMoveState():
    try: 
        BRT_connector = socket.socket()
        BRT_connector.connect((BRT_ip, BRT_port))
        getMoveState_json = {
                "dsID":"www.hc-system.com.RemoteMonitor",
                "reqType": "query",
                "packID": "0",
                "queryAddr":["isMoving"]
        }
        BRT_connector.send(json.dumps(getMoveState_json).encode("ascii"))
        getMoveState_msg = BRT_connector.recv(1024) .decode('ascii')
        MoveState = json.loads(getMoveState_msg)["queryData"]
        BRT_connector.close()
        if(MoveState[0] == "1"): 
            return [True, True]
        else: 
            return [True, False]
    except: 
        return [False, True]

'''
    @description: 设置伯朗特机器人的世界坐标系
    @param {
        float x, y, z, u, v, w: 需要设置的世界坐标系值
    }
    @return {
        ret: 尝试连接状态，True为正常False为失败
    }
'''
def setWorldCoordinate(WorldCoordinate, Speed=BRT_speed): 
    [x, y, z, u, v, w] = WorldCoordinate 
    try: 
        BRT_connector = socket.socket()
        BRT_connector.connect((BRT_ip, BRT_port))
        setWorldCoordinate_json = {
            "dsID":"www.hc-system.com.HCRemoteCommand",
            "reqType":"AddRCC", 
            "emptyList":"1",
            "instructions": [
                {
                    "oneshot":"1", 
                    "action":"10", 
                    "m0":str(x), "m1":str(y), "m2":str(z), "m3":str(u), "m4":str(v), "m5":str(w), 
                    "ckStatus":"0X3F", 
                    "speed":str(Speed), 
                    "delay":"0", 
                    "smooth":"0"
                }
            ]
        }
        BRT_connector.send(json.dumps(setWorldCoordinate_json).encode("ascii"))
        set_msg = BRT_connector.recv(1024) .decode('ascii')
        set_info = json.loads(set_msg)
        print("[Set Info]:", set_info)
        BRT_connector.close()
        return True
    except: 
        return False

'''
    @description: 设置伯朗特机器人的关节坐标系
    @param {
        float [J1-J6]: 需要设置的关节坐标系值
    }
    @return {
        ret: 尝试连接状态，True为正常False为失败
    }
'''
def setJointCoordinate(JointCoordinate): 
    [J1, J2, J3, J4, J5, J6] = JointCoordinate
    try:
        BRT_connector = socket.socket()
        BRT_connector.connect((BRT_ip, BRT_port))
        setJointCoordinate_json = {
            "dsID": "www.hc-system.com.HCRemoteCommand",
            "reqType": "AddRCC", 
            "emptyList": "1",
            "instructions": [
                {
                    "oneshot": "1", 
                    "action": "4", 
                    "m0": str(J1), "m1": str(J2), "m2": str(J3), "m3": str(J4), "m4": str(J5), "m5": str(J6), 
                    "ckStatus": "0X3F", 
                    "speed": str(BRT_speed), 
                    "delay":  "0", 
                    "smooth":"0"
                }
            ]
        }
        BRT_connector.send(json.dumps(setJointCoordinate_json).encode("ascii"))
        set_msg = BRT_connector.recv(1024) .decode('ascii')
        set_info = json.loads(set_msg)
        print("[Set Info]:", set_info)
        BRT_connector.close()
        return True
    except: 
        return False

'''
    @description: 等待移动结束
    @param {}
    @return {
        ret: 获取信息是否成功，成功True，失败False
    }
'''
def waitMoving(): 
    while(1): 
        sleep(MovingCheckGap)
        ret, state = getMoveState()
        if(not ret): 
            print('[Get Move State False]: Can\'t get move state')
            return False
        if(not state): 
            break
    return True

'''
    @description: 获取当前位置可移动的范围
    @param {
        float x, y, z, u, v, w: 需要判断的世界坐标系值
    }
    @return {
        bool res: 当前输入的值是否合法，True合法，False不合法
    }
'''
def judgeWorldCoordinate(Coordinate):
    [x, y, z, u, v, w] = Coordinate 
    # 获取腕部XYZ世界坐标
    WristX, WristY, WristZ = BRTArm.getWristCoordinate(x, y, z, u, v, w)
    # 判断Z轴是否合法
    R_XY = sqrt(WristX**2 + WristY**2) # xOy平面上直线长度
    if (R_XY > 870): 
        return False
    elif (R_XY >= 260 and R_XY <= 870):
        if ((WristZ <= 50) or (WristZ <= (415.5 - sqrt(410**2 - (390 + 70 - R_XY)**2)))): 
            return False
    elif (R_XY < 260): 
        if (WristZ < (415.5 + 200)): 
            return False
    if (WristZ > (415.5 + sqrt(800**2 - (R_XY - 70)**2))): 
        return False
    return True
    # 判断XY轴是否合法
    if (WristZ < (415.5 + 230)): 
        if ((R_XY < 230) or (R_XY > sqrt())): 
            pass


if __name__ == "__main__": 
    getWorldCoordinate()
    getJointCoordinate()
    setJointCoordinate([0.0, -30.0, -30.0, 0.0, 60.0, 0.0])
    while(1): 
        print(getMoveState()[1])
        if(getMoveState()): 
            break
        sleep(0.1)
    pass