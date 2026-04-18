#!/usr/bin/env python3
"""
工厂分布式智能巡检机器人系统 - 后端主程序
Factory Distributed Intelligent Inspection Robot System
"""

import os
import json
import time
import math
import random
import threading
import uuid
from datetime import datetime, timedelta
from io import BytesIO

from flask import Flask, render_template, jsonify, request, send_from_directory
from flask_socketio import SocketIO, emit
from PIL import Image
import numpy as np

app = Flask(__name__)
app.config['SECRET_KEY'] = 'inspection-robot-2024'
app.config['UPLOAD_FOLDER'] = os.path.join(os.path.dirname(__file__), 'static', 'uploads')
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max upload

socketio = SocketIO(app, cors_allowed_origins="*", async_mode='eventlet')

# ============================================================
# 数据存储 (实际项目会用数据库，这里用内存模拟)
# ============================================================

# 巡检点位 —— 800x520 真实工厂平面图坐标
INSPECTION_POINTS = [
    {"id": "P001", "name": "1号变压器", "x": 130, "y": 100, "type": "transformer", "status": "normal"},
    {"id": "P002", "name": "2号变压器", "x": 300, "y": 100, "type": "transformer", "status": "normal"},
    {"id": "P003", "name": "高压开关柜A", "x": 130, "y": 260, "type": "switch_cabinet", "status": "normal"},
    {"id": "P004", "name": "高压开关柜B", "x": 260, "y": 260, "type": "switch_cabinet", "status": "warning"},
    {"id": "P005", "name": "低压配电室", "x": 520, "y": 140, "type": "distribution", "status": "normal"},
    {"id": "P006", "name": "电容器组", "x": 520, "y": 260, "type": "capacitor", "status": "normal"},
    {"id": "P007", "name": "控制室", "x": 680, "y": 380, "type": "control_room", "status": "normal"},
    {"id": "P008", "name": "充电站", "x": 100, "y": 440, "type": "charging_station", "status": "normal"},
]

# 机器人状态
ROBOTS = {
    "R001": {
        "id": "R001", "name": "巡检机器人-1号", "status": "patrolling",
        "battery": 78, "x": 200, "y": 180, "speed": 0.8,
        "sensors": {"lidar": "ok", "camera": "ok", "infrared": "ok", "temp_humi": "ok"},
        "current_task": "日常巡检-上午班", "last_inspection": "2026-04-19 09:30:00",
        "total_distance": 1245.6, "fault_count": 3
    },
    "R002": {
        "id": "R002", "name": "巡检机器人-2号", "status": "charging",
        "battery": 23, "x": 100, "y": 440, "speed": 0,
        "sensors": {"lidar": "ok", "camera": "ok", "infrared": "warning", "temp_humi": "ok"},
        "current_task": None, "last_inspection": "2026-04-19 08:15:00",
        "total_distance": 2103.4, "fault_count": 1
    },
    "R003": {
        "id": "R003", "name": "巡检机器人-3号", "status": "idle",
        "battery": 95, "x": 650, "y": 300, "speed": 0,
        "sensors": {"lidar": "ok", "camera": "ok", "infrared": "ok", "temp_humi": "ok"},
        "current_task": None, "last_inspection": "2026-04-19 07:00:00",
        "total_distance": 856.2, "fault_count": 0
    }
}

# 巡检记录
INSPECTION_LOGS = []
ALERTS = []

# 图像识别结果模拟
RECOGNITION_RESULTS = [
    {"type": "压板状态", "result": "正常", "confidence": 0.98, "detail": "所有压板处于合位状态"},
    {"type": "仪表读数", "result": "正常", "confidence": 0.95, "detail": "电流表读数 125.3A，电压表 10.2kV"},
    {"type": "红外测温", "result": "异常", "confidence": 0.91, "detail": "检测到接头温度 78.5°C，超过阈值 70°C"},
    {"type": "设备外观", "result": "正常", "confidence": 0.97, "detail": "设备外壳完好，无渗漏油迹象"},
    {"type": "开关状态", "result": "正常", "confidence": 0.99, "detail": "断路器处于合闸位置"},
    {"type": "油位检测", "result": "警告", "confidence": 0.88, "detail": "变压器油位偏低，建议补充"},
]

# ============================================================
# 机器人运动模拟
# ============================================================

def generate_patrol_path(robot_id):
    """为每台机器人生成巡检路径（排除充电站）"""
    points = [p for p in INSPECTION_POINTS if p["type"] != "charging_station"]
    random.shuffle(points)
    return points

# 每台巡检中机器人的路径队列和当前目标索引
_patrol_routes = {}
_patrol_idx = {}

def _get_next_target(robot_id, robot):
    """获取该机器人的下一个巡检目标"""
    if robot_id not in _patrol_routes or not _patrol_routes[robot_id]:
        _patrol_routes[robot_id] = generate_patrol_path(robot_id)
        _patrol_idx[robot_id] = 0

    route = _patrol_routes[robot_id]
    idx = _patrol_idx[robot_id]
    target = route[idx]
    _patrol_idx[robot_id] = (idx + 1) % len(route)
    return target

def simulate_robot_movement():
    """后台线程：模拟机器人运动"""
    TICK = 0.1  # 100ms 一次，动画更流畅
    while True:
        for robot_id, robot in ROBOTS.items():
            if robot["status"] == "patrolling":
                # 如果没有当前目标，分配一个
                if "current_target" not in robot or robot["current_target"] is None:
                    robot["current_target"] = _get_next_target(robot_id, robot)

                target = robot["current_target"]
                dx = target["x"] - robot["x"]
                dy = target["y"] - robot["y"]
                dist = math.sqrt(dx * dx + dy * dy)

                if dist > 3:
                    # 每 tick 移动 speed 像素（speed=0.8 → 每秒约8px）
                    step = min(robot["speed"], dist)
                    robot["x"] += dx / dist * step
                    robot["y"] += dy / dist * step
                    robot["battery"] = max(0, robot["battery"] - 0.005)
                    robot["total_distance"] += step * 0.01
                else:
                    # 到达巡检点
                    robot["x"] = target["x"]
                    robot["y"] = target["y"]

                    log = {
                        "id": str(uuid.uuid4())[:8],
                        "robot_id": robot_id,
                        "robot_name": robot["name"],
                        "point_id": target["id"],
                        "point_name": target["name"],
                        "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        "result": random.choice(["正常", "正常", "正常", "警告", "正常"]),
                        "details": random.choice(RECOGNITION_RESULTS)
                    }
                    INSPECTION_LOGS.insert(0, log)
                    if len(INSPECTION_LOGS) > 100:
                        INSPECTION_LOGS.pop()

                    if log["result"] == "警告":
                        alert = {
                            "id": str(uuid.uuid4())[:8],
                            "robot_id": robot_id,
                            "point": target["name"],
                            "message": f"{target['name']}发现异常: {log['details']['detail']}",
                            "level": "warning",
                            "time": log["time"],
                            "acknowledged": False
                        }
                        ALERTS.insert(0, alert)
                        if len(ALERTS) > 50:
                            ALERTS.pop()

                    # 短暂停留后前往下一个目标
                    robot["current_target"] = None

                # 电池低自动充电
                if robot["battery"] < 20:
                    robot["current_target"] = None
                    robot["status"] = "returning"
                    robot["current_task"] = "返回充电"

            elif robot["status"] == "returning":
                cx, cy = 100, 440
                dx = cx - robot["x"]
                dy = cy - robot["y"]
                dist = math.sqrt(dx * dx + dy * dy)
                if dist > 3:
                    step = min(2.0, dist)
                    robot["x"] += dx / dist * step
                    robot["y"] += dy / dist * step
                else:
                    robot["x"] = cx
                    robot["y"] = cy
                    robot["status"] = "charging"
                    robot["current_task"] = None

            elif robot["status"] == "charging":
                robot["battery"] = min(100, robot["battery"] + 0.3)
                if robot["battery"] >= 100:
                    robot["status"] = "idle"

            elif robot["status"] == "idle":
                if random.random() < 0.02:
                    robot["status"] = "patrolling"
                    robot["speed"] = 0.8
                    robot["current_task"] = f"日常巡检-{random.choice(['上午', '下午', '夜间'])}班"
                    robot["current_target"] = None

        # 广播状态（每 0.5s 一次，减少前端压力）
        now = time.time()
        if now - getattr(simulate_robot_movement, '_last_emit', 0) >= 0.5:
            simulate_robot_movement._last_emit = now
            socketio.emit('robot_update', {
                'robots': {k: {kk: vv for kk, vv in v.items() if kk not in ('sensors', 'current_target')}
                           for k, v in ROBOTS.items()},
                'timestamp': datetime.now().strftime("%H:%M:%S")
            })

        time.sleep(TICK)

def generate_historical_data():
    """生成历史统计数据"""
    data = {
        "daily_inspections": [],
        "fault_trend": [],
        "battery_usage": [],
        "alarm_stats": {"normal": 0, "warning": 0, "critical": 0}
    }
    now = datetime.now()
    for i in range(7):
        d = now - timedelta(days=6-i)
        data["daily_inspections"].append({
            "date": d.strftime("%m-%d"),
            "count": random.randint(15, 35)
        })
        data["fault_trend"].append({
            "date": d.strftime("%m-%d"),
            "count": random.randint(0, 5)
        })
        data["battery_usage"].append({
            "date": d.strftime("%m-%d"),
            "avg_battery": round(random.uniform(55, 85), 1)
        })
    
    data["alarm_stats"]["normal"] = random.randint(80, 120)
    data["alarm_stats"]["warning"] = random.randint(5, 15)
    data["alarm_stats"]["critical"] = random.randint(0, 3)
    return data

# ============================================================
# 路由
# ============================================================

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/robots')
def get_robots():
    return jsonify(list(ROBOTS.values()))

@app.route('/api/robots/<robot_id>')
def get_robot(robot_id):
    robot = ROBOTS.get(robot_id)
    if robot:
        return jsonify(robot)
    return jsonify({"error": "Robot not found"}), 404

@app.route('/api/robots/<robot_id>/command', methods=['POST'])
def robot_command(robot_id):
    robot = ROBOTS.get(robot_id)
    if not robot:
        return jsonify({"error": "Robot not found"}), 404
    
    cmd = request.json.get('command')
    if cmd == 'start_patrol':
        robot['status'] = 'patrolling'
        robot['speed'] = 0.8
        robot['current_task'] = f'手动巡检-{datetime.now().strftime("%H:%M")}'
        return jsonify({"status": "ok", "message": f"{robot['name']} 开始巡检"})
    elif cmd == 'stop':
        robot['status'] = 'idle'
        robot['current_task'] = None
        return jsonify({"status": "ok", "message": f"{robot['name']} 已停止"})
    elif cmd == 'charge':
        robot['status'] = 'returning'
        robot['current_task'] = '返回充电'
        return jsonify({"status": "ok", "message": f"{robot['name']} 返回充电"})
    return jsonify({"error": "Unknown command"}), 400

@app.route('/api/points')
def get_points():
    return jsonify(INSPECTION_POINTS)

@app.route('/api/logs')
def get_logs():
    limit = request.args.get('limit', 20, type=int)
    return jsonify(INSPECTION_LOGS[:limit])

@app.route('/api/alerts')
def get_alerts():
    return jsonify(ALERTS)

@app.route('/api/alerts/<alert_id>/acknowledge', methods=['POST'])
def ack_alert(alert_id):
    for alert in ALERTS:
        if alert['id'] == alert_id:
            alert['acknowledged'] = True
            return jsonify({"status": "ok"})
    return jsonify({"error": "Alert not found"}), 404

@app.route('/api/stats')
def get_stats():
    stats = {
        "total_robots": len(ROBOTS),
        "active_robots": sum(1 for r in ROBOTS.values() if r['status'] == 'patrolling'),
        "charging_robots": sum(1 for r in ROBOTS.values() if r['status'] == 'charging'),
        "total_points": len(INSPECTION_POINTS),
        "today_inspections": len(INSPECTION_LOGS),
        "active_alerts": sum(1 for a in ALERTS if not a['acknowledged']),
        "avg_battery": round(sum(r['battery'] for r in ROBOTS.values()) / len(ROBOTS), 1),
        "historical": generate_historical_data()
    }
    return jsonify(stats)

@app.route('/api/recognize', methods=['POST'])
def recognize_image():
    """图像识别接口 - YOLOv8 + OpenCV 真实识别"""
    if 'image' not in request.files:
        return jsonify({"error": "No image uploaded"}), 400
    
    file = request.files['image']
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400
    
    try:
        from detector import full_analysis
        result = full_analysis(file)
        
        # 保存标注后的图片
        annotated_path = None
        if result.get("annotated_image"):
            annotated_name = f"annotated_{uuid.uuid4().hex[:8]}.jpg"
            annotated_path = os.path.join(app.config['UPLOAD_FOLDER'], annotated_name)
            result["annotated_image"].save(annotated_path, quality=85)
            result["annotated_url"] = f"/static/uploads/{annotated_name}"
        
        # 不返回图片对象
        result.pop("annotated_image", None)
        
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/slam/map')
def get_slam_map():
    """返回SLAM建图数据（模拟）"""
    # 生成模拟的地图数据
    grid = np.zeros((40, 60), dtype=int)
    # 模拟墙壁
    grid[0, :] = 1; grid[39, :] = 1
    grid[:, 0] = 1; grid[:, 59] = 1
    # 内部墙壁
    grid[10:12, 10:50] = 1
    grid[20:22, 5:45] = 1
    grid[30:32, 15:55] = 1
    grid[5:30, 15:16] = 1
    grid[15:35, 35:36] = 1
    
    map_data = {
        "width": 60,
        "height": 40,
        "resolution": 0.05,  # 5cm per cell
        "origin": {"x": 0, "y": 0},
        "grid": grid.tolist(),
        "robot_positions": {rid: {"x": int(r["x"]/10), "y": int(r["y"]/10)} for rid, r in ROBOTS.items()},
        "inspection_points": [{"id": p["id"], "x": int(p["x"]/10), "y": int(p["y"]/10), "name": p["name"]} for p in INSPECTION_POINTS]
    }
    return jsonify(map_data)

# ============================================================
# WebSocket 事件
# ============================================================

@socketio.on('connect')
def handle_connect():
    emit('connected', {'message': '已连接到巡检机器人管理系统'})

@socketio.on('request_update')
def handle_request_update():
    emit('robot_update', {
        'robots': {k: {kk: vv for kk, vv in v.items() if kk != 'sensors'} for k, v in ROBOTS.items()},
        'timestamp': datetime.now().strftime("%H:%M:%S")
    })

# ============================================================
# 启动
# ============================================================

if __name__ == '__main__':
    # 确保上传目录存在
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    
    # 启动机器人模拟线程
    sim_thread = threading.Thread(target=simulate_robot_movement, daemon=True)
    sim_thread.start()
    
    print("=" * 50)
    print("  工厂分布式智能巡检机器人系统")
    print("  Factory Distributed Inspection Robot System")
    print("=" * 50)
    print(f"  访问地址: http://0.0.0.0:5000")
    print("=" * 50)
    
    socketio.run(app, host='0.0.0.0', port=5000, debug=False)
