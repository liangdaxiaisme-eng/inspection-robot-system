#!/usr/bin/env python3
import requests

url = "http://10.151.175.24:5000/"
response = requests.get(url)

print("=== 页面诊断报告 ===\n")

# 检查关键元素
checks = {
    "巡检地图": "巡检地图",
    "巡检记录": "巡检记录",
    "图像识别": "图像识别",
    "SLAM 建图": "SLAM",
    "统计分析": "统计分析",
    "drawMap 函数": "function drawMap",
    "drawSLAM 函数": "function drawSLAM",
    "loadInitialData 函数": "function loadInitialData",
    "mapCanvas": 'id="mapCanvas"',
    "slamCanvas": 'id="slamCanvas"',
    "机器人列表": "robot-list",
    "生产区": "生产区",
    "装配区": "装配区",
    "仓库": "仓库",
    "质检区": "质检区",
}

print("关键元素检查:")
for name, text in checks.items():
    count = response.text.count(text)
    status = "✅" if count > 0 else "❌"
    print(f"  {status} {name}: {count} 次")

print("\n=== 诊断完成 ===")
