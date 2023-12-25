/*
 * @Author: zsh zsh1282984748@163.com
 * @Date: 2022-11-22 09:05:58
 * @LastEditors: zsh zsh1282984748@163.com
 * @LastEditTime: 2022-12-11 11:08:47
 * @FilePath: \ArmScan\resource\js\index.js
 * @Description: 任务页js脚本
 */
// 启动时加载配置
$(function() 
{
    $.post('/get_conf', {}, function(data,status){
        conf_json = JSON.parse(data);
        var confs = [
            'a_min', 'a_max', 'b_min', 'b_max', 'a_step', 'b_step',
            'mode', 
            'f_min', 'f_max', 'f_step', 'f_times', 'S_mode', 
            'save_folder', 'save_file', 'to_mailaddr'
        ];
        for (var i = 0, len = confs.length; i < len; i++) {
            document.getElementById(confs[i]).value = conf_json[confs[i]];
        }
    });
});

// 定时执行函数
var int=self.setInterval("interval_func()",500);
function interval_func() {
    mode_select();
    get_state();
    get_range();
}

// 根据选择框渲染页面
function mode_select(){
    // 模式对应文本变量
    var mode_to_text = {"xOy": ["坐标X:", "坐标Y:"], "xOz": ["坐标X:", "坐标Z:"], "yOz": ["坐标Y:", "坐标Z:"]};

    // 获取模式和对应标签页，并且修改
    var mode = document.getElementById('mode');
    var a = document.getElementById('a');
    var b = document.getElementById('b');
    a.innerHTML = mode_to_text[mode.value][0];
    b.innerHTML = mode_to_text[mode.value][1];
};

// 选择是预检模式还是扫描模式
function move_mode(move){
    var post_name = ['a_min', 'a_max', 'b_min', 'b_max', 'a_step', 'b_step', 'mode', 'f_min', 'f_max', 'f_step', 'f_times', 'S_mode', 'save_folder', 'save_file', 'to_mailaddr']
    var post_json = {}
    for (var i = 0, len = post_name.length; i < len; i++) {
        post_json[post_name[i]] = document.getElementById(post_name[i]).value;
    }
    if (move == 'check') {
        $.post('/move_mode/check', post_json);
        document.getElementById("scan_info").innerHTML = "[当前模式]:预检";
    }
    else if(move == 'scan') {
        $.post('/move_mode/scan', post_json);
        document.getElementById("scan_info").innerHTML = "[当前模式]:扫描"
    }
};

// 返回上一页
function back(){ window.location.href="/"; }

// 启动
function move(){ $.post('/run'); }

// 获取S参数并保存
function get_S_parameter(){ 
    var post_name = ['a_min', 'a_max', 'b_min', 'b_max', 'a_step', 'b_step', 'mode', 'f_min', 'f_max', 'f_step', 'f_times', 'S_mode', 'save_folder', 'save_file', 'to_mailaddr']
    var post_json = {}
    for (var i = 0, len = post_name.length; i < len; i++) {
        post_json[post_name[i]] = document.getElementById(post_name[i]).value;
    }
    $.post('/get_S_parameter', post_json); 
}

// 回到设定的中心点
function reset_center(){
    $.post('/reset_center')
}

// 获取当前状态并渲染页面
function get_state(){
    $.post('/state', data={}, function(data, status){
        state_to_text = {
            'stop': '[当前状态]:已停止', 
            'ready': '[当前状态]:已准备', 
            'finished': '[当前状态]:已完成，请重新选择模式后启动', 
            'running': '[当前状态]:运行中',
            'pause': '[当前状态]:已暂停', 
            'error': '[当前状态]:发生错误，请检查连接过后选择模式'
        }
        // 设定模式以及渲染按键状态
        var state = JSON.parse(data)['state'];
        document.getElementById("move_info").innerHTML = state_to_text[state];
        if (state == 'finished' || state == 'stop') {
            document.getElementById("start_button").disabled = 'disable';
        }
        else {
            document.getElementById("start_button").removeAttribute('disabled');
        }
        if (state == 'running') {
            document.getElementById("check_button").disabled = 'disable';
            document.getElementById("scan_button").disabled = 'disable';
            document.getElementById("start_button").innerHTML = '暂停';
        }
        else {
            document.getElementById("check_button").removeAttribute('disabled');
            document.getElementById("scan_button").removeAttribute('disabled');
            document.getElementById("start_button").innerHTML = '启动';
        }

        // 设定进度
        var MoveNum = JSON.parse(data)['MoveNum'];
        var MoveNumber = JSON.parse(data)['MoveNumber'];
        if (Number(MoveNum) == 0) {
            document.getElementById("process_info").innerHTML = '[当前进度]:0.00%'; 
        }
        else {
            document.getElementById("process_info").innerHTML = '[当前进度]:' + String((Number(MoveNum) / Number(MoveNumber) * 100).toFixed(2)) + "%"; 
        }

        // 设定时间信息
        var OnePointTime = JSON.parse(data)['OnePointTime'];
        if (Number(OnePointTime) == 0) {
            document.getElementById("total_time").innerHTML = '[预计时间]:未知'; 
            document.getElementById("left_time").innerHTML = '[剩余时间]:未知'; 
        }
        else {
            total_time_h = JSON.parse(data)['TotalTimeH'];
            total_time_m = JSON.parse(data)['TotalTimeM'];
            total_time_s = JSON.parse(data)['TotalTimeS'];
            left_time_h = JSON.parse(data)['LeftTimeH'];
            left_time_m = JSON.parse(data)['LeftTimeM'];
            left_time_s = JSON.parse(data)['LeftTimeS'];
            document.getElementById("total_time").innerHTML = '[预计时间]:' + total_time_h.toString() + ':' + total_time_m.toString() + ':' + total_time_s.toString(); 
            document.getElementById("left_time").innerHTML = '[剩余时间]:' + left_time_h.toString() + ':' + left_time_m.toString() + ':' + left_time_s.toString(); 
        }

        // 设定路径信息
        var full_path = JSON.parse(data)['full_path'];
        var S_full_path = JSON.parse(data)['S_full_path'];
        document.getElementById("full_path").innerHTML = '[文件路径]:' + full_path; 
        document.getElementById("S_full_path").innerHTML = '[S参数文件路径]:' + S_full_path; 
    })
}

// 
function get_range(){
    var a_min = document.getElementById('a_min').value;
    var a_max = document.getElementById('a_max').value;
    var post_json = {'a_min': a_min, 'a_max': a_max}
    $.post('/range', post_json, function(data, status){
        var a_min_available = JSON.parse(data)['a_min_available'];
        var a_max_available = JSON.parse(data)['a_max_available'];
        var b_min_available = JSON.parse(data)['b_min_available'];
        var b_max_available = JSON.parse(data)['b_max_available'];
        document.getElementById("a_available").innerHTML = '[范围]: [ ' + a_min_available.toString() + ' ~ ' + a_max_available.toString() + ' ]'; 
        document.getElementById("b_available").innerHTML = '[范围]: [ ' + b_min_available.toString() + ' ~ ' + b_max_available.toString() + ' ]'; 
    })
}