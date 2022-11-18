#coding:utf-8
import Mission
import BRTRobot

from flask import request, Flask
from Mission import Mission

app = Flask(__name__, static_url_path='/resource', static_folder = './resource')
BRTMission = None

'''
    @description: 移动位置api
    @param {
        str axis: 坐标名
        str step: 坐标移动步长
        str direct: 正负方向
    }
    @return {}
'''
@app.route('/move', methods=['POST'])
def move_init(): 
    if request.method == 'POST':
        axis = request.form.get('axis')
        step = request.form.get('step')
        direct = request.form.get('direct')
        axis_dict = {
            "x": 0, 
            "y": 1, 
            "z": 2, 
            "u": 3,
            "v": 4, 
            "w": 5
        }
        WordCoordinate_now = BRTRobot.getWorldCoordinate()
        WordCoordinate_now[axis_dict[axis]] += float(step) * float(direct)
        print(WordCoordinate_now)
        BRTRobot.setWorldCoordinate(WorldCoordinate=WordCoordinate_now)
        return "DONE"

'''
    @description: 复位位置api
    @param {}
    @return {}
'''
@app.route('/reset', methods=['POST'])
def reset(): 
    BRTRobot.setJointCoordinate([-90, -30, -30, 0, 60, 0])
    BRTMission.mission_initialize()
    BRTMission.save_conf()
    return "DONE"

'''
    @description: 复位中心api
    @param {}
    @return {}
'''
@app.route('/reset_center', methods=['POST'])
def reset_center(): 
    BRTRobot.setWorldCoordinate(BRTMission.OriginWorld)
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
    return BRTMission.mission_initialize()

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
        BRTMission.scan_mode(float(paras[0]), float(paras[1]), float(paras[2]), float(paras[3]), float(paras[4]), float(paras[5]), paras[6], check=check_flag)
        BRTMission.f_min = request.form.get('f_min')
        BRTMission.f_max = request.form.get('f_max')
        BRTMission.f_step = request.form.get('f_step')
        BRTMission.f_times = request.form.get('f_times')
        BRTMission.S_mode = request.form.get('S_mode')
        BRTMission.save_folder = request.form.get('save_folder')
        BRTMission.save_file = request.form.get('save_file')
        BRTMission.save_conf()
        return "DONE"

'''
    @description: 移动api
    @param {}
    @return {}
'''
@app.route('/run', methods=['POST'])
def run(): 
    if request.method == 'POST':
        # BRTMission.MoveFlag = not BRTMission.MoveFlag
        if (BRTMission.MissionState == 'running') : 
            BRTMission.MissionState = 'pause'
            # BRTMission.MoveFlag = False
        elif (BRTMission.MissionState == 'ready' or BRTMission.MissionState == 'pause' or BRTMission.MissionState == 'error') : 
            BRTMission.MissionState = 'running'
            # BRTMission.MoveFlag = True
        # print(BRTMission.MoveFlag)
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
    @description: 任务设置页
    @param {}
    @return {}
'''
@app.route('/mission', methods=['GET', "POST"])
def MissionPage():
    if request.method == 'GET': 
        MissionPage_file = open('mission.html', 'r', encoding='utf-8')
        MissionPage_context = ''
        for i in MissionPage_file: 
            MissionPage_context += i
        MissionPage_file.close
        return MissionPage_context
    elif request.method == 'POST': 
        pass
    pass 

'''
    @description: 初始化页
    @param {}
    @return {}
'''
@app.route('/', methods = ['GET', 'POST'])
def InitPage():
    if request.method == 'GET': 
        InitPage_file = open('index.html', 'r', encoding='utf-8')
        InitPage_context = ''
        for i in InitPage_file: 
            InitPage_context += i
        InitPage_file.close()
        return InitPage_context
    elif request.method == 'POST': 
        pass


if __name__ == '__main__':
    # 启动运行
    BRTMission = Mission()
    BRTMission.setDaemon(True)
    BRTMission.start()
    app.run(host='0.0.0.0', debug=True)