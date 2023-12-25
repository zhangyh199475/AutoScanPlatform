/*
 * @Author: zsh zsh1282984748@163.com
 * @Date: 2022-11-22 09:05:58
 * @LastEditors: zsh zsh1282984748@163.com
 * @LastEditTime: 2022-12-11 11:12:04
 * @FilePath: \ArmScan\resource\js\index.js
 * @Description: 首页js脚本
 */

 // 定时执行函数
var int=self.setInterval("interval_func()",1000);
function interval_func() {
    get_all_range()
}

// 移动末端位置
function move(axis){
    var step = document.getElementById(axis+"_text").value
    if (step <= 100 && step >= -100) {
        if (axis == "angle") {
            axis = "w"
            step = -step
            document.getElementById("angle_text").disabled = 'disable'
            document.getElementById("angle_confirm_btn").disabled = 'disable'
            document.getElementById("angle_reset_button").removeAttribute('disabled')
        }
        $.post('/move', {'axis': axis, 'step': step}, function(data, status){
            var para = document.getElementById(axis + "_alert")
            if (data == "DONE") {
                para.style.visibility='hidden'
            } else {
                para.style.visibility='visible'
                document.getElementById(para).innerHTML = '超出范围，请调整参数重试！'
            }
        })
    }
}

// 重置末端位置到原点
function reset(){
    $.post('/reset')
}

function reset_angle(){
    $.post('/reset_angle')
    document.getElementById("angle_reset_button").disabled = 'disable'
    document.getElementById("angle_text").removeAttribute('disabled')
    document.getElementById("angle_confirm_btn").removeAttribute('disabled')
}

// 重置末端位置到设置的中心点
function reset_center(){
    $.post('/reset_center')
}

// 完成初始化并跳转到下一页
function initialize(){
    var angle = document.getElementById("angle_text").value
    $.post('/save_conf', {'angle': angle})
    window.location.href="/mission"
}
// 不完成初始化直接跳转到下一页
function to_mission(){
    window.location.href="/mission"
}

// 获取x,y,z边界范围
function get_all_range(){
    $.get('/all_range', function(data, status){
        var x_min_available = JSON.parse(data)['x_min_available']
        var x_max_available = JSON.parse(data)['x_max_available']
        var y_min_available = JSON.parse(data)['y_min_available']
        var y_max_available = JSON.parse(data)['y_max_available']
        var z_min_available = JSON.parse(data)['z_min_available']
        var z_max_available = JSON.parse(data)['z_max_available']
        var u_min_available = JSON.parse(data)['u_min_available']
        var u_max_available = JSON.parse(data)['u_max_available']
        var v_min_available = JSON.parse(data)['v_min_available']
        var v_max_available = JSON.parse(data)['v_max_available']
        var w_min_available = JSON.parse(data)['w_min_available']
        var w_max_available = JSON.parse(data)['w_max_available']
        document.getElementById('x_available').innerHTML = '[范围]: [ ' + x_min_available.toString() + ' ~ ' + x_max_available.toString() + ' ]'
        document.getElementById('y_available').innerHTML = '[范围]: [ ' + y_min_available.toString() + ' ~ ' + y_max_available.toString() + ' ]'
        document.getElementById('z_available').innerHTML = '[范围]: [ ' + z_min_available.toString() + ' ~ ' + z_max_available.toString() + ' ]'
        document.getElementById('u_available').innerHTML = '[范围]: [ ' + u_min_available.toString() + ' ~ ' + u_max_available.toString() + ' ]'
        document.getElementById('v_available').innerHTML = '[范围]: [ ' + v_min_available.toString() + ' ~ ' + v_max_available.toString() + ' ]'
        document.getElementById('w_available').innerHTML = '[范围]: [ ' + w_min_available.toString() + ' ~ ' + w_max_available.toString() + ' ]'
    })
}

function judge_value(axis){
    var direction_arr = ['x', 'y', 'z']
    var angle_arr = ['u', 'v', 'w']
    var text_id = axis + '_text'
    var btn_id = axis + '_confirm_btn'
    var alert_id = axis + '_alert'
    if (direction_arr.includes(axis)) {
        if (document.getElementById(text_id).value > 100 || document.getElementById(text_id).value < -100) {
            document.getElementById(btn_id).disabled = 'disable'
            document.getElementById(alert_id).innerHTML = '单次移动仅限-100mm-100mm，请重新输入！'
            document.getElementById(alert_id).style.visibility='visible'
        } else {
            document.getElementById(btn_id).removeAttribute('disabled')
            document.getElementById(alert_id).style.visibility='hidden'
        }
    } else if (angle_arr.includes(axis)) {
        if (document.getElementById(text_id).value > 45 || document.getElementById(text_id).value < -45) {
            document.getElementById(btn_id).disabled = 'disable'
            document.getElementById(alert_id).innerHTML = '单次转动仅限-45°-45°，请重新输入！'
            document.getElementById(alert_id).style.visibility='visible'
        } else {
            document.getElementById(btn_id).removeAttribute('disabled')
            document.getElementById(alert_id).style.visibility='hidden'
        }
    } else {
        if (document.getElementById(text_id).value > 90 || document.getElementById(text_id).value < -90) {
            document.getElementById(btn_id).disabled = 'disable'
            document.getElementById(alert_id).innerHTML = '角度调整仅限-90°-90°，请重新输入！'
            document.getElementById(alert_id).style.visibility='visible'
        } else {
            document.getElementById(btn_id).removeAttribute('disabled')
            document.getElementById(alert_id).style.visibility='hidden'
        }
    }
}