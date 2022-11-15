import socket
import json
import numpy as np
from time import sleep


BRT_ip = "192.168.4.4"
BRT_port = 9760
BRT_speed = 60
MovingCheckGap = 0.01
socket.setdefaulttimeout(3)

'''
    @description: 获取伯朗特机器人的世界坐标系
    @param {}
    @return {
        float [x, y, z, u, v, w]: 世界坐标：x, y, z, 欧拉角：u, v, w
    }
'''
def getWorldCoordinate(): 
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
    return np.array(WorldCoordinate).astype(np.float64)

'''
    @description: 获取伯朗特机器人的关节坐标系
    @param {}
    @return {
        float [J1-J6]: J1-J6的关节角度
    }
'''
def getJointCoordinate():
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
    return np.array(JointCoordinate).astype(np.float64)

'''
    @description: 获取伯朗特机器人的运动状态
    @param {}
    @return {
        float MoveState: 运动状态，False为正在运动，不可操作，反之则相反
    }
'''
def getMoveState():
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
        return True
    else: 
        return False

'''
    @description: 设置伯朗特机器人的世界坐标系
    @param {
        float x, y, z, u, v, w: 需要设置的世界坐标系值
    }
    @return {}
'''
def setWorldCoordinate(WorldCoordinate, Speed=BRT_speed): 
    [x, y, z, u, v, w] = WorldCoordinate 
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

'''
    @description: 设置伯朗特机器人的关节坐标系
    @param {
        float [J1-J6]: 需要设置的关节坐标系值
    }
    @return {}
'''
def setJointCoordinate(JointCoordinate): 
    [J1, J2, J3, J4, J5, J6] = JointCoordinate
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

'''
    @description: 等待移动结束
    @param {}
    @return {}
'''
def waitMoving(): 
    while(1): 
        sleep(MovingCheckGap)
        if(not getMoveState()): 
            break

'''
    @description: 获取当前位置可移动的范围
    @param {
        float x, y, z, a_min, a_max, b_min, b_max, mod: 当前坐标x, y, z, 移动范围a, b值最小值最大值, 模式
    }
    @return {
        
    }
'''
def getRange(x, y, z, a_min, a_max, b_min, b_max, mod='xOy'): 
    if (mod == 'xOy'): 
        return getRange_xOy(x, y, z, a_min, a_max, b_min, b_max)
    elif (mod == 'xOz'): 
        return getRange_xOz(x, y, z, a_min, a_max, b_min, b_max) 
    else: 
        return getRange_yOz(x, y, z, a_min, a_max, b_min, b_max)

def getRange_xOy(x, y, z, a_min, a_max, b_min, b_max):
    pass

def getRange_xOz(x, y, z, a_min, a_max, b_min, b_max):
    pass

def getRange_yOz(x, y, z, a_min, a_max, b_min, b_max):
    pass

if __name__ == "__main__": 
    getWorldCoordinate()
    getJointCoordinate()
    setJointCoordinate([0.0, -30.0, -30.0, 0.0, 60.0, 0.0])
    while(1): 
        print(getMoveState())
        if(getMoveState()): 
            break
        sleep(0.1)
    pass