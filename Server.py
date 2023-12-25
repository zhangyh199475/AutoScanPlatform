# coding:utf-8
import json

import Mission
import BRTRobot

from flask import request, Flask
from Mission import Mission

app = Flask(__name__, static_url_path='/resource', static_folder='./resource')
BRTMission = None

'''
    @description: 移动位置api
    @param {
        str axis: 坐标名
        str step: 坐标移动步长
    }
    @return {}
'''


@app.route('/move', methods=['POST'])
def move_init():
    if request.method == 'POST':
        axis = request.form.get('axis')
        step = request.form.get('step')
        axis_dict = {"x": 0, "y": 1, "z": 2, "u": 3, "v": 4, "w": 5}
        _, WordCoordinate_now = BRTRobot.getWorldCoordinate()
        WordCoordinate_now[axis_dict[axis]] += float(step)
        if BRTRobot.judgeWorldCoordinate(WordCoordinate_now):
            BRTRobot.setWorldCoordinate(WorldCoordinate=WordCoordinate_now)
            return "DONE"
        return "Out of range"


'''

    @description: 复位位置api
    @param {}
    @return {}
'''


@app.route('/reset', methods=['POST'])
def reset():
    BRTRobot.setJointCoordinate([-90, -30, -30, 0, 60, 0])
    BRTMission.mission_initialize(angle=0.0)
    BRTMission.save_conf()
    return "DONE"


@app.route('/reset_angle', methods=['POST'])
def reset_angle():
    axis_dict = {"x": 0, "y": 1, "z": 2, "u": 3, "v": 4, "w": 5}
    _, WordCoordinate_now = BRTRobot.getWorldCoordinate()
    WordCoordinate_now[axis_dict["u"]] = 90.0
    WordCoordinate_now[axis_dict["v"]] = 0.0
    WordCoordinate_now[axis_dict["w"]] = 0.0
    BRTRobot.setWorldCoordinate(WorldCoordinate=WordCoordinate_now)
    return "DONE"


'''
    @description: 复位中心api，反复使用可能会带来误差
    @param {}
    @return {}
'''


@app.route('/reset_center', methods=['POST'])
def reset_center():
    origin_world = BRTMission.load_conf()
    print(origin_world['OriginWorld'])
    BRTRobot.setWorldCoordinate(origin_world['OriginWorld'])
    BRTMission.save_conf()
    return "DONE"


'''
    @description: 获取配置api
    @param {}
    @return {}
'''


@app.route('/get_conf', methods=['POST'])
def get_conf():
    return BRTMission.get_conf()


'''
    @description: 保存配置
    @param {}
    @return {}
'''


@app.route('/save_conf', methods=['POST'])
def save_conf():
    if request.method == 'POST':
        angle = request.form.get('angle')
        BRTMission.mission_initialize(angle=angle)
        return "DONE"


'''
    @description: 预检或扫描api
    @param {}
    @return {}
'''


@app.route('/move_mode/<move_mode>', methods=['POST'])
def move_mode(move_mode):
    if request.method == 'POST':
        if (move_mode == 'check'):
            check_flag = True
        elif (move_mode == 'scan'):
            check_flag = False
        paras = []
        paras_name = ['a_min', 'a_max', 'b_min', 'b_max', 'a_step', 'b_step', 'mode']
        for i in paras_name:
            paras.append(request.form.get(i))
        BRTMission.scan_mode(float(paras[0]), float(paras[1]), float(paras[2]), float(paras[3]), float(paras[4]),
                             float(paras[5]), paras[6], CheckFlag=check_flag)
        # BRTMission.angle = request.form.get('angle_text')
        BRTMission.f_min = request.form.get('f_min')
        BRTMission.f_max = request.form.get('f_max')
        BRTMission.f_step = request.form.get('f_step')
        BRTMission.f_times = request.form.get('f_times')
        BRTMission.S_mode = request.form.get('S_mode')
        BRTMission.save_folder = request.form.get('save_folder')
        BRTMission.save_file = request.form.get('save_file')
        BRTMission.to_mailaddr = request.form.get('to_mailaddr')
        BRTMission.save_conf()
        return "DONE"


'''
    @description: 移动api, 通过改变状态实现
    @param {}
    @return {}
'''


@app.route('/run', methods=['POST'])
def run():
    if request.method == 'POST':
        if (BRTMission.MissionState == 'running'):
            BRTMission.MissionState = 'pause'
        elif (
                BRTMission.MissionState == 'ready' or BRTMission.MissionState == 'pause' or BRTMission.MissionState == 'error'):
            BRTMission.MissionState = 'running'
        return "DONE"


'''
    @description: 获取S参数api
    @param {}
    @return {}
'''


@app.route('/get_S_parameter', methods=['POST'])
def get_S_parameter():
    if request.method == 'POST':
        paras = []
        paras_name = ['a_min', 'a_max', 'b_min', 'b_max', 'a_step', 'b_step', 'mode']
        for i in paras_name:
            paras.append(request.form.get(i))
        BRTMission.scan_mode(float(paras[0]), float(paras[1]), float(paras[2]), float(paras[3]), float(paras[4]),
                             float(paras[5]), paras[6])
        BRTMission.f_min = request.form.get('f_min')
        BRTMission.f_max = request.form.get('f_max')
        BRTMission.f_step = request.form.get('f_step')
        BRTMission.f_times = request.form.get('f_times')
        BRTMission.S_mode = request.form.get('S_mode')
        BRTMission.save_folder = request.form.get('save_folder')
        BRTMission.save_file = request.form.get('save_file')
        BRTMission.to_mailaddr = request.form.get('to_mailaddr')
        BRTMission.save_conf()
        BRTMission.get_S_parameter()
        return "DONE"


'''
    @description: 移动状态api
    @param {}
    @return {}
'''


@app.route('/state', methods=['POST'])
def state():
    if request.method == 'POST':
        return BRTMission.get_state()


'''
    @description: 获取扫描面范围api
    @param {}
    @return {}
'''


@app.route('/range', methods=['POST'])
def range():
    if request.method == 'POST':
        a_min = request.form.get('a_min')
        a_max = request.form.get('a_max')
        return BRTMission.get_range(a_min, a_max)


'''
    @description: 获取x,y,z边界范围api
    @param {}
    @return {}
'''


@app.route('/all_range', methods=['GET'])
def all_range():
    return BRTMission.get_all_range()


'''
    @description: 任务设置页
    @param {}
    @return {}
'''


@app.route('/mission', methods=['GET', "POST"])
def MissionPage():
    if request.method == 'GET':
        return app.send_static_file('html/mission.html')
    elif request.method == 'POST':
        pass
    pass


'''
    @description: 初始化页
    @param {}
    @return {}
'''


@app.route('/', methods=['GET', 'POST'])
def InitPage():
    if request.method == 'GET':
        return app.send_static_file('html/index.html')
    elif request.method == 'POST':
        pass


if __name__ == '__main__':
    # 启动运行
    BRTMission = Mission()
    BRTMission.setDaemon(True)
    BRTMission.start()
    app.run(host='0.0.0.0', debug=True)
