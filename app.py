from flask import Flask, render_template, request, redirect, url_for, flash, send_file, make_response
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import os
import io
import pandas as pd
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.enums import TA_CENTER, TA_LEFT
import secrets

# 创建Flask应用
app = Flask(__name__)

# 设置密钥 - 在生产环境中使用环境变量
# 尝试从环境变量获取密钥，如果没有则生成一个随机密钥
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY') or secrets.token_hex(16)

# 确保instance文件夹存在
if not os.path.exists('instance'):
    os.makedirs('instance')

# 设置数据库路径
db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'instance', 'scores.db')
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# 初始化数据库
db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# 用户模型
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    scores = db.relationship('Score', backref='user', lazy=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

# 成绩模型
class Score(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    subject = db.Column(db.String(50), nullable=False)
    score = db.Column(db.Float, nullable=False)
    exam_date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    remarks = db.Column(db.String(200))

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# 路由：主页
@app.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    return render_template('index.html')

# 路由：用户注册
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        
        if User.query.filter_by(username=username).first():
            flash('用户名已存在')
            return redirect(url_for('register'))
        
        if User.query.filter_by(email=email).first():
            flash('邮箱已被注册')
            return redirect(url_for('register'))
        
        user = User(username=username, email=email)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        
        flash('注册成功，请登录')
        return redirect(url_for('login'))
    
    return render_template('register.html')

# 路由：用户登录
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()
        
        if user and user.check_password(password):
            login_user(user)
            return redirect(url_for('dashboard'))
        
        flash('用户名或密码错误')
    
    return render_template('login.html')

# 路由：用户登出
@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

# 路由：用户仪表板
@app.route('/dashboard')
@login_required
def dashboard():
    scores_query = Score.query.filter_by(user_id=current_user.id).order_by(Score.exam_date.desc()).all()
    
    # 将成绩对象转换为可序列化的字典
    scores = []
    for score in scores_query:
        scores.append({
            'id': score.id,
            'subject': score.subject,
            'score': score.score,
            'exam_date': score.exam_date.strftime('%Y-%m-%d'),
            'remarks': score.remarks or ''
        })
    
    return render_template('dashboard.html', scores=scores)

# 路由：添加成绩
@app.route('/add_score', methods=['GET', 'POST'])
@login_required
def add_score():
    if request.method == 'POST':
        subject = request.form.get('subject')
        score = float(request.form.get('score'))
        
        # 根据科目验证分数范围
        if subject in ['语文', '数学', '英语']:
            # 语文、数学、英语满分120分
            if score < 0 or score > 120:
                flash('语文、数学、英语的分数必须在0到120之间')
                return redirect(url_for('add_score'))
        else:
            # 其他科目满分100分
            if score < 0 or score > 100:
                flash('该科目的分数必须在0到100之间')
                return redirect(url_for('add_score'))
            
        exam_date = datetime.strptime(request.form.get('exam_date'), '%Y-%m-%d')
        remarks = request.form.get('remarks')
        
        new_score = Score(
            user_id=current_user.id,
            subject=subject,
            score=score,
            exam_date=exam_date,
            remarks=remarks
        )
        
        db.session.add(new_score)
        db.session.commit()
        flash('成绩添加成功')
        return redirect(url_for('dashboard'))
    
    return render_template('add_score.html')

# 路由：编辑成绩
@app.route('/edit_score', methods=['POST'])
@login_required
def edit_score():
    score_id = request.form.get('score_id')
    score = Score.query.filter_by(id=score_id, user_id=current_user.id).first()
    
    if not score:
        flash('成绩记录不存在或您没有权限修改')
        return redirect(url_for('dashboard'))
    
    subject = request.form.get('subject')
    score_value = float(request.form.get('score'))
    
    # 根据科目验证分数范围
    if subject in ['语文', '数学', '英语']:
        # 语文、数学、英语满分120分
        if score_value < 0 or score_value > 120:
            flash('语文、数学、英语的分数必须在0到120之间')
            return redirect(url_for('dashboard'))
    else:
        # 其他科目满分100分
        if score_value < 0 or score_value > 100:
            flash('该科目的分数必须在0到100之间')
            return redirect(url_for('dashboard'))
    
    exam_date = datetime.strptime(request.form.get('exam_date'), '%Y-%m-%d')
    remarks = request.form.get('remarks')
    
    # 更新成绩记录
    score.subject = subject
    score.score = score_value
    score.exam_date = exam_date
    score.remarks = remarks
    
    db.session.commit()
    flash('成绩修改成功')
    return redirect(url_for('dashboard'))

# 路由：删除成绩
@app.route('/delete_score', methods=['POST'])
@login_required
def delete_score():
    score_id = request.form.get('score_id')
    score = Score.query.filter_by(id=score_id, user_id=current_user.id).first()
    
    if not score:
        flash('成绩记录不存在或您没有权限删除')
        return redirect(url_for('dashboard'))
    
    db.session.delete(score)
    db.session.commit()
    flash('成绩删除成功')
    return redirect(url_for('dashboard'))

# 路由：导出成绩为Excel
@app.route('/export_excel')
@login_required
def export_excel():
    # 获取用户的所有成绩记录
    scores_query = Score.query.filter_by(user_id=current_user.id).order_by(Score.exam_date.desc()).all()
    
    # 如果没有成绩记录，返回仪表板
    if not scores_query:
        flash('没有成绩记录可供导出')
        return redirect(url_for('dashboard'))
    
    # 创建数据框
    data = []
    for score in scores_query:
        data.append({
            '科目': score.subject,
            '分数': score.score,
            '考试日期': score.exam_date.strftime('%Y-%m-%d'),
            '备注': score.remarks or ''
        })
    
    df = pd.DataFrame(data)
    
    # 创建Excel文件
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name='成绩记录', index=False)
        
        # 获取工作表
        worksheet = writer.sheets['成绩记录']
        
        # 设置列宽
        for i, col in enumerate(['A', 'B', 'C', 'D']):
            if col == 'A':  # 科目列
                worksheet.column_dimensions[col].width = 15
            elif col == 'B':  # 分数列
                worksheet.column_dimensions[col].width = 10
            elif col == 'C':  # 考试日期列
                worksheet.column_dimensions[col].width = 15
            elif col == 'D':  # 备注列
                worksheet.column_dimensions[col].width = 30
    
    output.seek(0)
    
    # 生成当前日期作为文件名的一部分
    current_date = datetime.now().strftime('%Y%m%d')
    filename = f"成绩记录_{current_user.username}_{current_date}.xlsx"
    
    return send_file(
        output,
        as_attachment=True,
        download_name=filename,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )

# 路由：导出成绩为PDF
@app.route('/export_pdf')
@login_required
def export_pdf():
    # 获取用户的所有成绩记录
    scores_query = Score.query.filter_by(user_id=current_user.id).order_by(Score.exam_date.desc()).all()
    
    # 如果没有成绩记录，返回仪表板
    if not scores_query:
        flash('没有成绩记录可供导出')
        return redirect(url_for('dashboard'))
    
    # 设置中文字体 - 直接使用宋体(SimSun)
    font_name = 'SimSun'
    simSunPath = 'C:\\Windows\\Fonts\\simsun.ttc'
    
    # 检查宋体是否存在，如果存在则注册
    if os.path.exists(simSunPath):
        # 注册SimSun字体
        try:
            if font_name not in pdfmetrics.getRegisteredFontNames():
                pdfmetrics.registerFont(TTFont(font_name, simSunPath, subfontIndex=0))
        except Exception as e:
            print(f"字体注册失败: {str(e)}")
            font_name = 'Helvetica'  # 使用默认字体
    else:
        # 如果找不到宋体，尝试使用项目中的黑体字体
        local_font_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static', 'fonts', 'simhei.ttf')
        if os.path.exists(local_font_path):
            try:
                font_name = 'SimHei'
                if font_name not in pdfmetrics.getRegisteredFontNames():
                    pdfmetrics.registerFont(TTFont(font_name, local_font_path))
            except Exception as e:
                print(f"字体注册失败: {str(e)}")
                font_name = 'Helvetica'  # 使用默认字体
        else:
            font_name = 'Helvetica'  # 使用默认字体
            print("警告：未找到中文字体，中文字符可能无法正确显示")
    
    # 创建自定义样式
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(
        name='TitleCN', 
        fontName=font_name,
        fontSize=16,
        alignment=TA_CENTER,
        spaceAfter=12
    ))
    styles.add(ParagraphStyle(
        name='NormalCN', 
        fontName=font_name,
        fontSize=10,
        alignment=TA_LEFT
    ))
    styles.add(ParagraphStyle(
        name='HeadingCN', 
        fontName=font_name,
        fontSize=12,
        alignment=TA_LEFT,
        spaceAfter=6
    ))
    
    # 创建PDF文件
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer, 
        pagesize=A4,
        rightMargin=30,
        leftMargin=30,
        topMargin=30,
        bottomMargin=30
    )
    elements = []
    
    # 添加标题
    elements.append(Paragraph(f"{current_user.username}的成绩记录", styles['TitleCN']))
    elements.append(Spacer(1, 10))
    
    # 添加导出日期
    export_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    elements.append(Paragraph(f"导出日期：{export_date}", styles['NormalCN']))
    elements.append(Spacer(1, 20))
    
    # 创建表格数据
    data = [['科目', '分数', '考试日期', '备注']]  # 表头
    
    for score in scores_query:
        # 根据科目类型确定满分
        max_score = 120 if score.subject in ['语文', '数学', '英语'] else 100
        percentage = f"{score.score}/{max_score}"
        
        data.append([
            score.subject,
            f"{score.score} ({percentage})",
            score.exam_date.strftime('%Y-%m-%d'),
            score.remarks or ''
        ])
    
    # 创建表格，宽度适应页面
    available_width = doc.width
    col_widths = [available_width * 0.2, available_width * 0.2, available_width * 0.2, available_width * 0.4]
    table = Table(data, colWidths=col_widths)
    
    # 设置表格样式
    table_style = TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.lavender),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), font_name),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
        ('TOPPADDING', (0, 0), (-1, 0), 8),
        ('FONTNAME', (0, 1), (-1, -1), font_name),
        ('GRID', (0, 0), (-1, -1), 1, colors.grey),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('ALIGN', (3, 1), (3, -1), 'LEFT'),  # 备注列左对齐
    ])
    
    # 为高分和低分设置不同颜色，使用更温和的颜色
    for i in range(1, len(data)):
        try:
            score_value = float(data[i][1].split()[0])
            max_score_value = 120 if data[i][0] in ['语文', '数学', '英语'] else 100
            
            if score_value >= max_score_value * 0.85:
                table_style.add('TEXTCOLOR', (1, i), (1, i), colors.darkgreen)
                table_style.add('FONTNAME', (1, i), (1, i), font_name)
            elif score_value < max_score_value * 0.6:
                table_style.add('TEXTCOLOR', (1, i), (1, i), colors.darkred)
                table_style.add('FONTNAME', (1, i), (1, i), font_name)
        except (ValueError, IndexError):
            # 忽略任何解析错误，使用默认颜色
            pass
    
    table.setStyle(table_style)
    elements.append(table)
    
    # 添加统计信息
    elements.append(Spacer(1, 20))
    
    # 计算平均分
    total_score = sum(score.score for score in scores_query)
    avg_score = total_score / len(scores_query) if scores_query else 0
    
    # 找出最高分和最低分
    highest_score = max(score.score for score in scores_query) if scores_query else 0
    lowest_score = min(score.score for score in scores_query) if scores_query else 0
    
    # 添加统计信息到PDF
    elements.append(Paragraph(f"统计信息：", styles['HeadingCN']))
    elements.append(Paragraph(f"总记录数：{len(scores_query)}", styles['NormalCN']))
    elements.append(Paragraph(f"平均分：{avg_score:.2f}", styles['NormalCN']))
    elements.append(Paragraph(f"最高分：{highest_score}", styles['NormalCN']))
    elements.append(Paragraph(f"最低分：{lowest_score}", styles['NormalCN']))
    
    # 构建PDF
    doc.build(elements)
    buffer.seek(0)
    
    # 生成当前日期作为文件名的一部分
    current_date = datetime.now().strftime('%Y%m%d')
    filename = f"成绩记录_{current_user.username}_{current_date}.pdf"
    
    return send_file(
        buffer,
        as_attachment=True,
        download_name=filename,
        mimetype='application/pdf'
    )

# 创建数据库表
with app.app_context():
    db.create_all()

if __name__ == '__main__':
    app.run(debug=True) 