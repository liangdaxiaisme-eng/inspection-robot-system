# 巡检机器人系统部署文档

## 部署信息

- **版本**: v1.0 (commit 2daaee5)
- **部署路径**: `/home/adminm/.openclaw/workspace/inspection-robot-system/`
- **访问地址**: http://10.151.175.24:5000/
- **部署时间**: 2026-04-19 05:28

## 项目来源

GitHub: https://github.com/liangdaxiaisme-eng/inspection-robot-system

特定版本：https://github.com/liangdaxiaisme-eng/inspection-robot-system/tree/2daaee5e0c26012d6462a67e5f7119b2888941e0

## 部署步骤

### 1. 克隆项目
```bash
cd /home/adminm/.openclaw/workspace
git clone https://github.com/liangdaxiaisme-eng/inspection-robot-system.git
cd inspection-robot-system
git checkout 2daaee5e0c26012d6462a67e5f7119b2888941e0
```

### 2. 创建虚拟环境
```bash
python3 -m venv venv
```

### 3. 安装依赖
```bash
./venv/bin/pip install -r requirements.txt
```

### 4. 启动应用
```bash
./venv/bin/python app.py &
```

## 功能模块

### 1. 巡检地图 & 机器人实时位置
- 实时显示 3 个机器人的位置
- 显示巡检路径和巡检点
- 机器人状态：巡检中、充电中、空闲、返回中

### 2. 巡检记录
- 查看所有巡检记录
- 按时间排序
- 显示巡检点状态

### 3. 图像识别
- 上传设备图像进行智能识别
- 支持 YOLOv8 模型
- 实时识别结果

### 4. SLAM 建图
- 实时显示 SLAM 地图
- 机器人定位和导航
- 地图探索进度

### 5. 统计分析
- 机器人总数
- 活跃机器人数量
- 今日巡检次数
- 巡检点总数
- 活跃告警数量
- 历史数据图表

## 系统状态

- ✅ **应用运行中**: PID 151739
- ✅ **API 正常**: 3 个机器人数据
- ✅ **外部访问**: http://10.151.175.24:5000/
- ✅ **所有功能**: 正常工作

## 维护命令

### 重启应用
```bash
pkill -f "python.*app.py"
cd /home/adminm/.openclaw/workspace/inspection-robot-system
./venv/bin/python app.py &
```

### 查看日志
```bash
ps aux | grep "app.py"
```

### 停止应用
```bash
pkill -f "python.*app.py"
```

## 注意事项

1. **版本选择**: 使用 commit 2daaee5，这是包含完整 Flask Web Dashboard 的版本
2. **依赖安装**: 确保使用 Python 3.12+ 和虚拟环境
3. **端口占用**: 确保 5000 端口未被占用
4. **模型文件**: yolov8n.pt 模型文件已包含在项目中

---

**部署完成！** 🎉

访问地址：**http://10.151.175.24:5000/**
