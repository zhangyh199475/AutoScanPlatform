import BRTRobot

Coordinate = []
mode = 'xOy'

def get_range(a_min, a_max): 
    a_min = float(a_min)
    a_max = float(a_max)
    a_min_available = 0
    a_max_available = 0
    b_min_available = 0
    b_max_available = 0
    Mode_AIndex = {'xOy': 0, 'xOz': 0, 'yOz': 1}
    Mode_BIndex = {'xOy': 1, 'xOz': 2, 'yOz': 2}
    # 获得a变量可以到达的最小值
    while(a_min_available > -2000): 
        point = Coordinate.copy()
        point[Mode_AIndex[mode]] = point[Mode_AIndex[mode]] + a_min_available
        if (BRTRobot.judgeWorldCoordinate(point)): 
            a_min_available -= 5.0
        else: 
            a_min_available += 5.0
            break
    # 获得a变量可以到达的最大值
    while(a_max_available < 2000): 
        point = Coordinate.copy()
        point[Mode_AIndex[mode]] = point[Mode_AIndex[mode]] + a_max_available
        if (BRTRobot.judgeWorldCoordinate(point)): 
            a_max_available += 5.0
        else: 
            a_max_available -= 5.0
            break
    # 获得b变量可以到达的最小值
    while(b_min_available > -2000): 
        point1 = Coordinate.copy()
        point1[Mode_BIndex[mode]] = point1[Mode_BIndex[mode]] + b_min_available
        point2 = Coordinate.copy()
        point2[Mode_AIndex[mode]] = point2[Mode_AIndex[mode]] + a_min
        point2[Mode_BIndex[mode]] = point2[Mode_BIndex[mode]] + b_min_available
        point3 = Coordinate.copy()
        point3[Mode_AIndex[mode]] = point3[Mode_AIndex[mode]] + a_max
        point3[Mode_BIndex[mode]] = point3[Mode_BIndex[mode]] + b_min_available
        if (BRTRobot.judgeWorldCoordinate(point1) and BRTRobot.judgeWorldCoordinate(point2) and BRTRobot.judgeWorldCoordinate(point3)): 
            b_min_available -= 5.0
        else: 
            b_min_available += 5.0
            break
    # 获得b变量可以到达的最大值
    while(b_max_available < 2000): 
        point1 = Coordinate.copy()
        point1[Mode_BIndex[mode]] = point1[Mode_BIndex[mode]] + b_max_available
        point2 = Coordinate.copy()
        point2[Mode_AIndex[mode]] = point2[Mode_AIndex[mode]] + a_min
        point2[Mode_BIndex[mode]] = point2[Mode_BIndex[mode]] + b_max_available
        point3 = Coordinate.copy()
        point3[Mode_AIndex[mode]] = point3[Mode_AIndex[mode]] + a_max
        point3[Mode_BIndex[mode]] = point3[Mode_BIndex[mode]] + b_max_available
        if (BRTRobot.judgeWorldCoordinate(point1) and BRTRobot.judgeWorldCoordinate(point2) and BRTRobot.judgeWorldCoordinate(point3)): 
            b_max_available += 5.0
        else: 
            b_max_available -= 5.0
            break
    return [a_min_available, a_max_available, b_min_available, b_max_available]
if __name__ == '__main__': 
    ret, Coordinate = BRTRobot.getWorldCoordinate()
    print(BRTRobot.judgeWorldCoordinate(Coordinate))
    Coordinate1 = Coordinate.copy()
    Coordinate1[0] = Coordinate1[0] - 500
    Coordinate1[1] = Coordinate1[1] + 100
    print(BRTRobot.judgeWorldCoordinate(Coordinate1))
    Coordinate1[1] = Coordinate1[1] + 10
    print(BRTRobot.judgeWorldCoordinate(Coordinate1))
    print(get_range(-5, 0))