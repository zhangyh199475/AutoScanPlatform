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

// 完成初始化并跳转到上一页
function initialize(){
    $.post('/save_conf')
    window.location.href="/mission"
}