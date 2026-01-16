
from datetime import datetime
import pymysql
from django.contrib.auth import logout



def get_db_connection():
    return pymysql.connect(
        host='127.0.0.1',
        port=3308,
        user='root',
        password='mysql',
        database='farm',
        charset='utf8',
        cursorclass=pymysql.cursors.DictCursor
    )


# 登录
def login_view(request):
    if request.method == 'POST':
        un = request.POST.get('jobNumber')
        pw = request.POST.get('plotCode')

        db = get_db_connection()
        cursor = db.cursor(pymysql.cursors.DictCursor)

        # 1. 验证用户（建议字段名根据你数据库真实情况对齐，比如 u_id, role）
        sql = "SELECT * FROM sys_user WHERE username = %s AND password = %s"
        cursor.execute(sql, [un, pw])
        user = cursor.fetchone()
        db.close()

        if user:
            # 2. 存入 Session
            # 确保这里 user['u_id'] 拿出来的是数字 2 或 3
            request.session['u_id'] = user['u_id']
            request.session['user_name'] = user['username']
            request.session['user_role'] = user['role']

            # 3. --- 分流逻辑：根据角色去不同的页面 ---
            if user['role'] == '管理员':
                return redirect('/plot_admin/')  # 管理员专属路由
            else:
                return redirect('/plot_staff/')  # 员工专属路由
        else:
            return render(request, 'login.html', {'error': '工号或密码错误'})

    return render(request, 'login.html')

def order_list(request):
    # 从 session 拿到角色，这样 HTML 才知道显示哪个返回按钮
    role = request.session.get('user_role')
    current_status = request.GET.get('status', '待采摘')

    db = get_db_connection()
    cursor = db.cursor(pymysql.cursors.DictCursor)

    # 这里的查询逻辑保持你原来的不变
    sql = "SELECT * FROM farm_order WHERE order_status = %s"
    cursor.execute(sql, [current_status])
    orders = cursor.fetchall()
    db.close()

    # 关键：在这里把 role 传给模板
    return render(request, 'order_list.html', {
        'orders': orders,
        'current_status': current_status,
        'role': role  # 必须加这一行
    })

def order_list_view(request):
    # 1. 获取身份
    role = request.session.get('user_role')
    current_status = request.GET.get('status', '待采摘')

    db = get_db_connection()
    cursor = db.cursor(pymysql.cursors.DictCursor)

    # 2. 查询订单（这里以管理员看全部为例，如果是员工可以增加 WHERE 过滤）
    sql = "SELECT * FROM farm_order WHERE order_status = %s"
    cursor.execute(sql, [current_status])
    orders = cursor.fetchall()

    db.close()

    # 3. 必须把 role 传给模板
    return render(request, 'order_list.html', {
        'orders': orders,
        'current_status': current_status,
        'role': role  # <--- 关键点
    })
def update_delivery(request):
    if request.method == 'POST':
        o_id = request.POST.get('o_id')
        t_no = request.POST.get('t_no')
        role = request.session.get('user_role')

        # 执行数据库更新更新...
        # UPDATE farm_order SET tracking_no = %s, order_status = '待配送' WHERE o_id = %s

        messages.success(request, f"订单 #{o_id} 已成功发货！")

        # 同样根据身份跳转回对应的订单列表页（带上当前状态参数）
        return redirect(f'/order_list/?status=待配送')




def register_view(request):
    if request.method == 'POST':
        username = request.POST.get('jobNumber')
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirm_password')

        if not username or not password:
            return render(request, 'register.html', {'error': '工号和密码不能为空'})

        if password != confirm_password:
            return render(request, 'register.html', {'error': '两次输入的密码不一致'})

        db = None
        try:
            db = get_db_connection()
            cursor = db.cursor()

            # 3. 检查工号（username）是否已经存在
            check_sql = "SELECT u_id FROM sys_user WHERE username = %s"
            cursor.execute(check_sql, [username])
            if cursor.fetchone():
                return render(request, 'register.html', {'error': '该工号已存在，请直接登录'})

            # 4. 执行插入操作 (role 默认为 staff)
            insert_sql = "INSERT INTO sys_user (username, password, role) VALUES (%s, %s, %s)"
            cursor.execute(insert_sql, [username, password, '员工'])

            # 5. 【重要】手动提交事务
            db.commit()

            # 注册成功，重定向到登录页面
            return redirect('/')

        except Exception as e:
            # 如果发生错误，可以回滚（虽然 INSERT 失败通常不需要回滚，但这是好习惯）
            if db:
                db.rollback()
            print(f"注册报错: {e}")
            return render(request, 'register.html', {'error': f'服务器内部错误: {e}'})

        finally:
            # 6. 【重要】关闭连接
            if db:
                db.close()

    # 如果是 GET 请求，直接显示注册页面
    return render(request, 'register.html')



# 增：新增记录
def add_record(request):
    if request.method == "POST":
        p_id, crop, p_date = request.POST.get('p_id'), request.POST.get('crop'), request.POST.get('p_date')
        u_id = request.session.get('user_id')
        conn = get_db_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute("INSERT INTO planting_record (p_id, u_id, crop, plant_date) VALUES (%s, %s, %s, %s)",
                               (p_id, u_id, crop, p_date))
                cursor.execute("UPDATE farm_plot SET status = '种植中' WHERE p_id = %s", (p_id,))
                conn.commit()
        finally:
            conn.close()
    return redirect('user_dash')


def update_status(request, p_id):
    if request.method == "POST":
        new_status = request.POST.get('status')
        my_id = request.session.get('u_id')
        role = request.session.get('user_role')

        with connection.cursor() as cursor:
            if role == '管理员':
                # 管理员可以修改该地块最新的那条种植记录
                # 这里的 p_id 对应你表里的 A01, B01 等
                sql = "UPDATE planting_record SET record_status = %s WHERE p_id = %s"
                cursor.execute(sql, [new_status, p_id])
            else:
                # 员工只能修改【属于自己】且【地块编号匹配】的记录
                # 这样就实现了“只能管自己的地”
                sql = "UPDATE planting_record SET record_status = %s WHERE p_id = %s AND u_id = %s"
                cursor.execute(sql, [new_status, p_id, my_id])

        # 成功提示
        messages.success(request, f"地块 {p_id} 的种植状态已更新为：{new_status}")

    return redirect('/plot_manage/')


def plot_staff_view(request):
    my_id = request.session.get('u_id')

    db = get_db_connection()
    cursor = db.cursor(pymysql.cursors.DictCursor)

    # 精准查询：只查这名员工负责的种植记录
    sql = """
          SELECT r.u_id, \
                 p.p_id, \
                 r.crop, \
                 r.record_status, \
                 r.plant_date,
                 DATEDIFF(CURDATE(), r.plant_date) as days_passed
          FROM planting_record r
                   JOIN farm_plot p ON r.p_id = p.p_id
          WHERE r.u_id = %s \
          """
    cursor.execute(sql, [my_id])
    my_plots = cursor.fetchall()

    # 员工关心的指标：我有几块地，几个订单
    cursor.execute("SELECT COUNT(*) as count FROM farm_order WHERE order_status = '待采摘'")
    order_count = cursor.fetchone()['count']

    db.close()
    # 指向专门的员工界面
    return render(request, 'plot_staff.html', {
        'plots': my_plots,
        'order_count': order_count,
        'role': '员工',
        'my_id': my_id
    })


def plot_admin_view(request):
    db = get_db_connection()
    cursor = db.cursor(pymysql.cursors.DictCursor)

    sql = """
          SELECT p.*, r.crop, r.record_status, r.u_id as responsible_id
          FROM farm_plot p
                   LEFT JOIN planting_record r ON p.p_id = r.p_id \
          """
    cursor.execute(sql)
    all_plots = cursor.fetchall()

    cursor.execute("SELECT COUNT(*) as total FROM farm_order")
    total_orders = cursor.fetchone()['total']

    db.close()
    return render(request, 'plot_admin.html', {
        'plots': all_plots,
        'total_orders': total_orders,
        'role': '管理员'
    })



from django.db import connection
from django.shortcuts import render, redirect
import datetime


def planting_plan(request):
    conn = get_db_connection()
    cursor = conn.cursor(pymysql.cursors.DictCursor)

    try:
        if request.method == "POST":
            p_id = request.POST.get('p_id')
            u_id = request.POST.get('u_id')
            crop = request.POST.get('crop')
            today = datetime.date.today().strftime('%Y-%m-%d')

            # 1. 插入种植记录
            cursor.execute("""
                           INSERT INTO planting_record (p_id, u_id, crop, plant_date, record_status)
                           VALUES (%s, %s, %s, %s, '生长中')
                           """, [p_id, u_id, crop, today])

            # 2. 修改地块状态
            cursor.execute("UPDATE farm_plot SET status = '种植中' WHERE p_id = %s", [p_id])

            return redirect('/plot_admin/')

        # 查询空闲地块
        cursor.execute("SELECT p_id, area FROM farm_plot WHERE status = '空闲'")
        free_plots = cursor.fetchall()

        # 查询员工
        cursor.execute("SELECT u_id, username FROM sys_user WHERE role = '员工'")
        all_staff = cursor.fetchall()

        return render(request, 'planting_plan.html', {
            'free_plots': free_plots,
            'all_staff': all_staff,
            'now_month': datetime.datetime.now().month,
            'recommend_crops': "番茄, 辣椒"
        })

    finally:
        cursor.close()
        conn.close()

def harvest_record(request):
    db = get_db_connection()
    cursor = db.cursor(pymysql.cursors.DictCursor)

    if request.method == 'POST':
        r_id = request.POST.get('r_id')
        p_id = request.POST.get('p_id')
        amount = request.POST.get('amount')
        quality = request.POST.get('quality')

        try:
            # 更新记录状态为已收获
            cursor.execute("UPDATE planting_record SET record_status='已收获', harvest_date=CURDATE() WHERE r_id=%s",
                           [r_id])
            # 释放地块
            cursor.execute("UPDATE farm_plot SET STATUS='空闲' WHERE p_id=%s", [p_id])
            db.commit()
            return redirect('/plot_staff/')
        finally:
            db.close()

    # 查询所有种植中的记录供选择采摘
    cursor.execute("SELECT r_id, p_id, crop FROM planting_record WHERE record_status != '已收获'")
    active_records = cursor.fetchall()
    db.close()
    return render(request, 'harvest_record.html', {'records': active_records})




# 1. 订单管理与采摘清单
def order_list(request):
    status_filter = request.GET.get('status', '待采摘')
    db = get_db_connection()
    cursor = db.cursor(pymysql.cursors.DictCursor)

    # 支持按状态筛选，并关联地块方便“采摘清单”查看
    sql = "SELECT * FROM farm_order WHERE order_status = %s"
    cursor.execute(sql, [status_filter])
    orders = cursor.fetchall()
    db.close()
    return render(request, 'order_list.html', {'orders': orders, 'current_status': status_filter})


# 2. 配送与售后处理
def update_delivery(request):
    if request.method == 'POST':
        o_id = request.POST.get('o_id')
        action = request.POST.get('action')
        db = get_db_connection()
        cursor = db.cursor()

        # 仅保留发货逻辑
        if action == 'ship':
            t_no = request.POST.get('t_no')
            cursor.execute("""
                           UPDATE farm_order
                           SET order_status='待配送',
                               tracking_no=%s
                           WHERE o_id = %s
                           """, [t_no, o_id])

        db.commit()
        db.close()

    # 根据操作后的状态自动跳转回对应的选项卡
    status = request.POST.get('current_status', '待采摘')
    return redirect(f'/order_list/?status={status}')


def admin_operation(request):
    db = get_db_connection()
    cursor = db.cursor(pymysql.cursors.DictCursor)

    # 1. 履约率计算
    cursor.execute("SELECT COUNT(*) as total, COUNT(tracking_no) as shipped FROM farm_order")
    o_data = cursor.fetchone()
    rate = (o_data['shipped'] / o_data['total'] * 100) if o_data['total'] > 0 else 0

    # 2. 客单价计算 (基于 customer 表的消费总额除以订单数，或直接平均消费)
    cursor.execute("SELECT AVG(total_spent) as avg_value FROM farm_customer")
    avg_val_res = cursor.fetchone()
    avg_value = round(avg_val_res['avg_value'] or 0, 2)

    # 3. VIP 营收占比 (前3名大客户贡献额 / 总额)
    cursor.execute("SELECT SUM(total_spent) as total_rev FROM farm_customer")
    total_rev_res = cursor.fetchone()
    total_rev = total_rev_res['total_rev'] or 1
    cursor.execute("SELECT SUM(total_spent) as vip_rev FROM (SELECT total_spent FROM farm_customer ORDER BY total_spent DESC LIMIT 3) t")
    vip_rev = cursor.fetchone()['vip_rev'] or 0
    vip_ratio = round((vip_rev / total_rev) * 100, 1)

    # 4. 作物资源分布
    cursor.execute("""
        SELECT crop, COUNT(*)                                               as count, 
        ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM planting_record), 1) as percent
        FROM planting_record GROUP BY crop
    """)
    resource_stats = cursor.fetchall()

    # 5. 种植-订单缺口分析 (后端直接处理好 gap 和 abs_gap)
    cursor.execute("""
        SELECT a.crop, (a.planned - IFNULL(b.ordered, 0)) as gap,
        ABS(a.planned - IFNULL(b.ordered, 0)) as abs_gap
        FROM (SELECT crop, COUNT(*) as planned FROM planting_record WHERE record_status='生长中' GROUP BY crop) a
        LEFT JOIN (SELECT crop_name, SUM(count) as ordered FROM farm_order WHERE order_status='待采摘' GROUP BY crop_name) b
        ON a.crop = b.crop_name
    """)
    matching_gap = cursor.fetchall()

    db.close()
    # 使用 dict 明确传递变量，防止 locals() 混入多余数据
    return render(request, 'admin_operation.html', {
        'rate': rate,
        'avg_value': avg_value,
        'vip_ratio': vip_ratio,
        'resource_stats': resource_stats,
        'matching_gap': matching_gap
    })


def logout_view(request):
    logout(request) # 清除 session
    return redirect('/') # 退出后跳转回登录页


def plot_admin_view(request):
    db = get_db_connection()
    cursor = db.cursor(pymysql.cursors.DictCursor)

    # 1. 基础地块列表（关联查询）
    sql_plots = """
                SELECT p.*, r.crop, r.record_status
                FROM farm_plot p
                         LEFT JOIN planting_record r ON p.p_id = r.p_id \
                """
    cursor.execute(sql_plots)
    plots = cursor.fetchall()

    # 2. 统计地块状态分布 (饼图数据1)
    # 假设核心逻辑：有 record_status 且不是“已收获”的算“种植中”，否则算“空闲”
    cursor.execute("""
                   SELECT CASE
                              WHEN record_status IS NULL OR record_status = '已收获' THEN '空闲中'
                              ELSE '种植中' END as status_name,
                          COUNT(*)              as value
                   FROM farm_plot p
                            LEFT JOIN planting_record r ON p.p_id = r.p_id
                   GROUP BY status_name
                   """)
    status_data = cursor.fetchall()  # 结果示例: [{'status_name': '种植中', 'value': 3}, ...]

    # 3. 统计作物占比 (饼图数据2)
    cursor.execute("""
                   SELECT crop as name, COUNT(*) as value
                   FROM planting_record
                   WHERE record_status != '已收获'
                     AND crop IS NOT NULL
                   GROUP BY crop
                   """)
    crop_data = cursor.fetchall()

    db.close()

    # 转换为 ECharts 需要的 JSON 格式（或者直接在模板里处理）
    return render(request, 'plot_admin.html', {
        'plots': plots,
        'status_data': status_data,
        'crop_data': crop_data,
        'role': '管理员'
    })

from django.shortcuts import redirect
from django.contrib import messages

def update_delivery(request):
    if request.method == "POST":
        o_id = request.POST.get('o_id')
        tracking_no = request.POST.get('t_no')

        db = get_db_connection() # 使用你之前的数据库连接函数
        cursor = db.cursor()

        try:
            # 执行更新：修改状态为“待配送”，并填入物流单号
            sql = "UPDATE farm_order SET order_status = '待配送', tracking_no = %s WHERE o_id = %s"
            cursor.execute(sql, [tracking_no, o_id])
            db.commit()
        except Exception as e:
            db.rollback()
        finally:
            db.close()

    return redirect('/order_list/?status=待配送')

