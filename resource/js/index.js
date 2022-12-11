/*
 * @Author: zsh zsh1282984748@163.com
 * @Date: 2022-11-22 09:05:58
 * @LastEditors: zsh zsh1282984748@163.com
 * @LastEditTime: 2022-12-11 11:12:04
 * @FilePath: \ArmScan\resource\js\index.js
 * @Description: 首页js脚本
 */
// 移动末端位置
function move(axis, direct){
    var step = document.getElementById(axis+"_select").value
    $.post('/move', {'axis': axis, 'step': step, 'direct': direct});
}

// 重置末端位置到原点
function reset(){
    $.post('/reset')
}

// 重置末端位置到设置的中心点
function reset_center(){
    $.post('/reset_center')
}

// 完成初始化并跳转到下一页
function initialize(){
    $.post('/save_conf')
    window.location.href="/mission"
}
// 不完成初始化直接跳转到下一页
function to_mission(){
    window.location.href="/mission"
}