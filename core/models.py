from django.db import models

# 1. 系统用户表 (对应 sys_user)
class SysUser(models.Model):
    u_id = models.AutoField(primary_key=True)
    username = models.CharField(unique=True, max_length=20)
    password = models.CharField(db_column='PASSWORD', max_length=20) # SQL里是大写
    role = models.CharField(max_length=10, default='员工')
    phone = models.CharField(max_length=20, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'sys_user'

# 2. 地块表 (对应 farm_plot)
class FarmPlot(models.Model):
    p_id = models.CharField(max_length=50, primary_key=True, verbose_name="地块编号")
    area = models.FloatField(verbose_name="面积(亩)")
    soil = models.CharField(max_length=20, blank=True, null=True)
    status = models.CharField(
        max_length=20,
        choices=[('free', '空闲'), ('planted', '已种植'), ('maintenance', '维护中')],
        default='free',
        verbose_name="状态"
    )

    class Meta:
        managed = False
        db_table = 'farm_plot'  # 确保表名正确映射
        verbose_name = '农田地块'
        verbose_name_plural = '农田地块'

    def __str__(self):
        return f"{self.p_id} ({self.area}亩)"



# 3. 种植记录表 (对应 planting_record)
class PlantingRecord(models.Model):
    r_id = models.AutoField(primary_key=True)
    # 关联地块
    p_id = models.ForeignKey(FarmPlot, models.DO_NOTHING, db_column='p_id', blank=True, null=True)
    # 关联负责人
    u_id = models.ForeignKey(SysUser, models.DO_NOTHING, db_column='u_id', blank=True, null=True)
    crop = models.CharField(max_length=20)
    plant_date = models.DateField(blank=True, null=True)
    harvest_date = models.DateField(blank=True, null=True)
    record_status = models.CharField(max_length=10, default='生长中')

    class Meta:
        managed = False
        db_table = 'planting_record'

# 4. 农资消耗表 (对应 farm_input)
class FarmInput(models.Model):
    i_id = models.AutoField(primary_key=True)
    # 关联哪次种植
    r_id = models.ForeignKey(PlantingRecord, models.DO_NOTHING, db_column='r_id', blank=True, null=True)
    type = models.CharField(db_column='TYPE', max_length=10, blank=True, null=True)
    name = models.CharField(db_column='NAME', max_length=20, blank=True, null=True)
    count = models.FloatField(db_column='COUNT', blank=True, null=True)
    use_date = models.DateField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'farm_input'

# 5. 订单信息表 (对应 farm_order) - 用于“实时订单”模块
class FarmOrder(models.Model):
    o_id = models.AutoField(primary_key=True)
    # 关联种植记录（通过种植记录知道是哪个地块产出的）
    r_id = models.ForeignKey('PlantingRecord', models.DO_NOTHING, db_column='r_id', blank=True, null=True)
    buyer_name = models.CharField(max_length=50)
    product_name = models.CharField(max_length=50) # 冗余作物名称方便查询
    quantity = models.FloatField()
    unit_price = models.FloatField()
    total_amount = models.FloatField()
    order_date = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=10, default='待发货') # 待发货/已发货/已完成

    class Meta:
        managed = False
        db_table = 'farm_order'

# 6. 环境监测表 (对应 sensor_data) - 用于“全场监测”的数值显示
class SensorData(models.Model):
    s_id = models.AutoField(primary_key=True)
    # 关联地块
    p_id = models.ForeignKey('FarmPlot', models.DO_NOTHING, db_column='p_id')
    temp = models.FloatField(verbose_name="温度")
    humidity = models.FloatField(verbose_name="湿度")
    soil_moisture = models.FloatField(verbose_name="土壤水分")
    light = models.FloatField(verbose_name="光照强度")
    record_time = models.DateTimeField(auto_now_add=True)

    class Meta:
        managed = False
        db_table = 'sensor_data'