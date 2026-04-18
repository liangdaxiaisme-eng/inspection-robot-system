#!/usr/bin/env python3
import re

# 读取文件
with open('/home/adminm/.openclaw/workspace/inspection-robot-system/templates/index.html', 'r', encoding='utf-8') as f:
    content = f.read()

# 新的 drawMap 函数
new_drawMap = '''    // ============================================================
    // 地图绘制
    // ============================================================
    function drawMap() {
        const canvas = document.getElementById('mapCanvas');
        const ctx = canvas.getContext('2d');
        const rect = canvas.getBoundingClientRect();
        canvas.width = rect.width * (window.devicePixelRatio || 1);
        canvas.height = rect.height * (window.devicePixelRatio || 1);
        ctx.scale(window.devicePixelRatio || 1, window.devicePixelRatio || 1);
        
        const W = rect.width, H = rect.height;
        const scaleX = W / 550, scaleY = H / 420;
        
        // 背景
        ctx.fillStyle = '#f5f7fa';
        ctx.fillRect(0, 0, W, H);
        
        // 工厂外框
        ctx.strokeStyle = '#2c3e50';
        ctx.lineWidth = 4;
        ctx.strokeRect(20 * scaleX, 20 * scaleY, 500 * scaleX, 380 * scaleY);
        
        // 填充不同区域背景
        // 生产区（左上）
        ctx.fillStyle = 'rgba(52, 152, 219, 0.1)';
        ctx.fillRect(25 * scaleX, 25 * scaleY, 240 * scaleX, 180 * scaleY);
        
        // 装配区（右上）
        ctx.fillStyle = 'rgba(46, 204, 113, 0.1)';
        ctx.fillRect(285 * scaleX, 25 * scaleY, 240 * scaleX, 180 * scaleY);
        
        // 仓库（左下）
        ctx.fillStyle = 'rgba(155, 89, 182, 0.1)';
        ctx.fillRect(25 * scaleX, 235 * scaleY, 240 * scaleX, 160 * scaleY);
        
        // 质检区（右下）
        ctx.fillStyle = 'rgba(243, 156, 18, 0.1)';
        ctx.fillRect(285 * scaleX, 235 * scaleY, 240 * scaleX, 160 * scaleY);
        
        // 区域分隔线
        ctx.strokeStyle = '#bdc3c7';
        ctx.lineWidth = 2;
        ctx.setLineDash([5, 5]);
        
        // 垂直分隔线
        ctx.beginPath();
        ctx.moveTo(265 * scaleX, 25 * scaleY);
        ctx.lineTo(265 * scaleX, 405 * scaleY);
        ctx.stroke();
        
        // 水平分隔线
        ctx.beginPath();
        ctx.moveTo(25 * scaleX, 215 * scaleY);
        ctx.lineTo(525 * scaleX, 215 * scaleY);
        ctx.stroke();
        
        ctx.setLineDash([]);
        
        // 区域标签
        ctx.fillStyle = '#2c3e50';
        ctx.font = 'bold 14px sans-serif';
        ctx.textAlign = 'center';
        
        // 生产区标签
        ctx.fillText('生产区', 145 * scaleX, 110 * scaleY);
        
        // 装配区标签
        ctx.fillText('装配区', 405 * scaleX, 110 * scaleY);
        
        // 仓库标签
        ctx.fillText('仓库', 145 * scaleX, 320 * scaleY);
        
        // 质检区标签
        ctx.fillText('质检区', 405 * scaleX, 320 * scaleY);
        
        // 巡检路径
        ctx.strokeStyle = '#3498db';
        ctx.lineWidth = 2;
        ctx.setLineDash([5, 5]);
        const points = inspectionPoints;
        if (points.length > 1) {
            ctx.beginPath();
            ctx.moveTo(points[0].x * scaleX, points[0].y * scaleY);
            for (let i = 1; i < points.length; i++) {
                ctx.lineTo(points[i].x * scaleX, points[i].y * scaleY);
            }
            ctx.stroke();
        }
        ctx.setLineDash([]);
        
        // 巡检点
        for (const p of points) {
            const x = p.x * scaleX, y = p.y * scaleY;
            ctx.beginPath();
            ctx.arc(x, y, 10, 0, Math.PI * 2);
            ctx.fillStyle = p.type === 'charging_station' ? '#ff9800' : 
                           p.status === 'warning' ? '#e74c3c' : '#2ecc71';
            ctx.fill();
            ctx.strokeStyle = 'white';
            ctx.lineWidth = 2;
            ctx.stroke();
            
            // 标签
            ctx.fillStyle = '#2c3e50';
            ctx.font = '11px sans-serif';
            ctx.textAlign = 'center';
            ctx.fillText(p.name, x, y - 16);
        }
        
        // 机器人
        const robotColors = {
            patrolling: '#2980b9', charging: '#d35400', idle: '#7f8c8d', returning: '#8e44ad'
        };
        for (const [id, robot] of Object.entries(robots)) {
            const x = robot.x * scaleX, y = robot.y * scaleY;
            
            // 运动轨迹光晕
            if (robot.status === 'patrolling') {
                ctx.beginPath();
                ctx.arc(x, y, 18, 0, Math.PI * 2);
                ctx.fillStyle = 'rgba(41, 128, 185, 0.2)';
                ctx.fill();
            }
            
            // 机器人主体
            ctx.beginPath();
            ctx.arc(x, y, 12, 0, Math.PI * 2);
            ctx.fillStyle = robotColors[robot.status] || '#7f8c8d';
            ctx.fill();
            ctx.strokeStyle = 'white';
            ctx.lineWidth = 2;
            ctx.stroke();
            
            // 机器人图标
            ctx.fillStyle = 'white';
            ctx.font = 'bold 11px sans-serif';
            ctx.textAlign = 'center';
            ctx.textBaseline = 'middle';
            ctx.fillText(id.slice(-1), x, y);
            
            // 名称标签
            ctx.fillStyle = '#2c3e50';
            ctx.font = '11px sans-serif';
            ctx.textBaseline = 'bottom';
            ctx.fillText(robot.name, x, y - 18);
            
            // 电量标签
            ctx.fillStyle = robot.battery > 50 ? '#27ae60' : robot.battery > 20 ? '#e67e22' : '#c0392b';
            ctx.font = '10px sans-serif';
            ctx.textBaseline = 'top';
            ctx.fillText(`${robot.battery}%`, x, y + 16);
        }
    }'''

# 替换 drawMap 函数
pattern = r'    // ============================================================\n    // 地图绘制\n    // ============================================================\n    function drawMap\(\) \{[\s\S]*?    \}'
content = re.sub(pattern, new_drawMap, content)

# 写回文件
with open('/home/adminm/.openclaw/workspace/inspection-robot-system/templates/index.html', 'w', encoding='utf-8') as f:
    f.write(content)

print("✅ 地图已更新为工厂 2D 平面图")
