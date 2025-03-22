# 学生成绩管理系统

一个简单而实用的学生成绩管理系统，基于Flask框架开发，帮助学生记录、管理和分析自己的考试成绩。

## 功能特点

- 📝 **成绩记录管理**：轻松添加、编辑和删除各科成绩
- 📊 **数据可视化**：直观的图表展示成绩趋势和分布
- 📱 **响应式设计**：在任何设备上都能获得良好的使用体验
- 🔒 **用户账户系统**：安全的注册和登录功能
- 📤 **数据导出**：支持导出成绩为Excel和PDF格式

## 安装指南

### 前置要求

- Python 3.8+
- pip (Python包管理器)

### 安装步骤

1. 克隆仓库
```bash
git clone https://github.com/your-username/student-score-manager.git
cd student-score-manager
```

2. 创建并激活虚拟环境（推荐）
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS/Linux
python -m venv venv
source venv/bin/activate
```

3. 安装依赖
```bash
pip install -r requirements.txt
```

4. 运行应用
```bash
python app.py
```

5. 打开浏览器访问
```
http://127.0.0.1:5000/
```

## 使用指南

1. **注册账户**：首次使用需创建个人账户
2. **登录系统**：使用注册的账户登录
3. **添加成绩**：点击"添加成绩"按钮记录新的考试成绩
4. **查看统计**：在仪表板查看成绩统计和趋势图表
5. **导出数据**：使用导出功能将成绩导出为Excel或PDF格式

## 技术栈

- **后端**：Flask, SQLAlchemy, Flask-Login
- **前端**：HTML5, CSS3, JavaScript, Bootstrap 5
- **数据库**：SQLite
- **数据可视化**：Chart.js
- **报表生成**：ReportLab, pandas

## 文件结构

```
student-score-manager/
│
├── app.py                 # 应用主文件
├── requirements.txt       # 项目依赖
├── instance/              # 数据库文件目录
│   └── scores.db          # SQLite数据库
├── static/                # 静态资源
│   ├── css/               # 样式表
│   ├── js/                # JavaScript文件
│   └── fonts/             # 字体文件
└── templates/             # HTML模板
    ├── base.html          # 基础模板
    ├── index.html         # 首页
    ├── dashboard.html     # 仪表板页面
    ├── login.html         # 登录页面
    ├── register.html      # 注册页面
    └── add_score.html     # 添加成绩页面
```

## 注意事项

- 导出PDF功能需要中文字体支持，Windows用户通常无需额外配置
- 该应用仅为学习目的开发，不建议用于存储敏感或重要数据

## 贡献指南

欢迎贡献代码或提出改进建议！请：

1. Fork本仓库
2. 创建您的特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交您的更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启一个Pull Request

## 许可证

本项目采用MIT许可证 - 详情请参阅 [LICENSE](LICENSE) 文件 