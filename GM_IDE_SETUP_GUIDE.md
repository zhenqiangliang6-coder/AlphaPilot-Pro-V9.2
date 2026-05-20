# 🎯 掘金IDE配置与下单问题排查指南

**Alphapilot智能体团队**  
**作者**: 梁子羿、侯沣睿、梁茹真  
**邮箱**: 497720537@qq.com | **电话**: 13392077558

---

## 📋 问题背景

在VSCode中运行掘金策略时，下单接口报错 `"无效的ACCOUNT_ID"`，但在掘金终端中可以手动下单。

**目标**: 在掘金IDE中直接运行策略，排除VSCode环境干扰，定位问题根源。

---

## 🔧 第一步: 在掘金IDE中配置 Python 解释器

### 方法1: 通过系统设置（推荐）

#### 1.1 打开系统设置
- 点击掘金终端顶部菜单栏最右侧的 **"系统设置"** (齿轮图标 ⚙️)

#### 1.2 查找Python配置
在系统设置窗口中，按以下顺序查找：

```
系统设置
├─ 基本设置
├─ 策略设置  ← 重点查看这里
│  ├─ Python环境
│  ├─ 解释器路径
│  └─ 自定义Python
├─ 运行环境
└─ 高级设置
```

#### 1.3 设置解释器路径
找到输入框后，填入：
```
D:\mpython\quant_env\Scripts\python.exe
```

#### 1.4 保存并重启
- 点击 **"应用"** 或 **"确定"**
- **完全退出掘金终端**
- 重新启动掘金终端
- 重新连接账户

---

### 方法2: 通过策略编辑器

#### 2.1 打开策略编辑器
1. 点击顶部菜单 **"量化研究"** 或 **"策略交易"**
2. 新建一个策略或打开现有策略

#### 2.2 查找运行配置
在策略编辑器界面：
1. 查找右上角的 **"设置"** 或 **"配置"** 图标
2. 点击 **"运行环境"** 或 **"解释器"**
3. 选择 **"自定义Python"**
4. 输入路径：`D:\mpython\quant_env\Scripts\python.exe`

---

### 方法3: 如果掘金不支持自定义解释器

某些版本的掘金终端**强制使用内置Python**，此时需要将 `gm` 库安装到掘金的Python环境。

#### 3.1 找到掘金的Python路径

打开PowerShell，运行：
```powershell
# 方法A: 查看掘金安装目录
Get-ChildItem "C:\Program Files\MyQuant" -Recurse -Filter "python.exe" | Select-Object FullName

# 方法B: 查看常见安装位置
Get-ChildItem "C:\Users\$env:USERNAME\AppData" -Recurse -Filter "python.exe" | Select-Object FullName
```

#### 3.2 安装 gm 库到掘金Python

假设找到掘金Python路径为 `C:\xxx\python.exe`，运行：
```powershell
C:\xxx\python.exe -m pip install gm
```

---

## 🧪 第二步: 在掘金IDE中创建测试策略

### 2.1 创建新策略

1. 点击顶部菜单 **"量化研究"**
2. 点击 **"新建策略"**
3. 策略名称: `TestOrderExecution`
4. 策略类型: **Python**
5. 点击 **"确定"**

### 2.2 编写测试代码

在策略编辑器中，粘贴以下代码：

```python
# coding=utf-8
from __future__ import print_function, absolute_import
from gm.api import *

def init(context):
    """策略初始化"""
    print("=" * 60)
    print("🧪 下单测试策略启动")
    print("=" * 60)
    
    # 1. 查询账户资金
    print("\n💰 [步骤1] 查询账户")
    try:
        cash = get_cash()
        if cash:
            print(f"   ✅ 账户查询成功")
            print(f"   账户ID: {cash.account_id}")
            print(f"   可用资金: ¥{cash.available:,.2f}")
        else:
            print(f"   ❌ 账户查询返回空")
    except Exception as e:
        print(f"   ❌ 账户查询失败: {e}")
    
    # 2. 测试下单
    print("\n📈 [步骤2] 测试下单")
    print(f"   标的: SHSE.688295")
    print(f"   数量: 100 股")
    print(f"   类型: 市价单")
    
    try:
        result = order_volume(
            symbol='SHSE.688295',
            volume=100,
            side=OrderSide_Buy,
            order_type=OrderType_Market,
            position_effect=PositionEffect_Open
        )
        print(f"   ✅ 下单成功!")
        print(f"   订单号: {result[0].order_id}")
        print(f"\n{'='*60}")
        print(f"🎉 测试成功! 下单功能正常")
        print(f"{'='*60}")
    except Exception as e:
        print(f"   ❌ 下单失败: {e}")
        print(f"\n{'='*60}")
        print(f"💡 失败原因分析:")
        print(f"   1. 账户未连接 - 请在'账户管理'中连接账户")
        print(f"   2. 不在交易时段 - 精准撮合账户需交易时段")
        print(f"   3. Token权限不足 - 联系掘金客服")
        print(f"{'='*60}")
    
    # 停止策略
    stop()


if __name__ == '__main__':
    run(
        strategy_id='test_order_execution',
        filename='TestOrderExecution.py',
        mode=MODE_LIVE,
        token='fdf08e9d00c4da3b635c2616724ddae3f7793562'
    )
```

### 2.3 运行策略

1. 点击编辑器上方的 **"运行"** 或 **"回测"** 按钮
2. 选择 **"实盘运行"** 或 **"模拟运行"**
3. 观察控制台输出

---

## 📊 第三步: 根据测试结果排查问题

### 情况A: 掘金IDE中下单成功 ✅

**结论**: VSCode环境问题

**解决方案**:
1. 检查VSCode使用的Python解释器是否正确
2. 在VSCode中按 `Ctrl+Shift+P`，选择 "Python: Select Interpreter"
3. 选择 `D:\mpython\quant_env\Scripts\python.exe`
4. 重新运行策略

---

### 情况B: 掘金IDE中下单也失败 ❌

**可能原因**:

#### 原因1: 账户未正确连接
**解决**:
1. 进入"账户管理"
2. 断开账户
3. 等待3秒
4. 重新连接账户
5. 确认状态为"已连接"

#### 原因2: 精准撮合限制
**分析**:
- "Alphapilot量化智能学习" 账户使用**精准撮合**
- 精准撮合**只在交易时段**生效
- 当前时间如果在非交易时段，下单会失败

**解决**:
1. 切换到"模型训练学习"账户（模拟撮合，7*24小时可用）
2. 或者在交易时段（9:30-15:00）测试

#### 原因3: Token权限问题
**解决**:
1. 登录掘金官网控制台
2. 查看Token权限
3. 确认包含"交易"或"下单"权限
4. 如无权限，联系掘金客服申请

---

## 🎯 第四步: 终极测试 - 切换账户

如果上述方法都无法解决，请尝试切换到另一个账户：

### 4.1 切换到"模型训练学习"账户

1. 在掘金终端"账户管理"中
2. 找到"模型训练学习"账户
3. 点击"复制账户ID"
4. 更新 `.env` 文件:
   ```
   GM_ACCOUNT_ID=ae22ac8e-3bb9-11f1-a262-00163e022aa6
   ```

### 4.2 重新测试

```bash
# 在VSCode中
python run_strategy_in_vscode.py
```

**优势**:
- ✅ 模拟撮合，7*24小时可用
- ✅ 不受交易时段限制
- ✅ 可以立即验证下单功能

---

## 📝 排查记录表

| 步骤 | 测试环境 | 测试结果 | 下一步 |
|------|---------|---------|--------|
| 1 | VSCode + quant_env | ❌ 下单失败 | → 步骤2 |
| 2 | 掘金IDE + 内置Python | ? 待测试 | → 根据结果 |
| 3 | 掘金IDE + quant_env | ? 待测试 | → 根据结果 |
| 4 | 切换到模拟撮合账户 | ? 待测试 | → 根据结果 |

---

## 💡 常见问题

### Q1: 掘金IDE中如何查看Python解释器路径？

**A**: 
```python
# 在策略代码中添加
import sys
print(f"当前Python: {sys.executable}")
```

### Q2: 如何确认 gm 库已安装？

**A**:
```python
# 在策略代码中添加
import gm
print(f"gm 版本: {gm.__version__}")
```

### Q3: 精准撮合和模拟撮合的区别？

| 特性 | 精准撮合 | 模拟撮合 |
|------|---------|---------|
| 撮合精度 | 真实行情撮合 | 简化撮合逻辑 |
| 可用时间 | 仅交易时段 | 7*24小时 |
| 适用场景 | 实盘交易 | 策略测试 |
| 下单限制 | 严格 | 宽松 |

---

## 🚀 快速操作清单

- [ ] 1. 在掘金终端"系统设置"中查找Python配置
- [ ] 2. 设置解释器路径为 `D:\mpython\quant_env\Scripts\python.exe`
- [ ] 3. 重启掘金终端
- [ ] 4. 创建测试策略 `TestOrderExecution`
- [ ] 5. 运行策略并观察结果
- [ ] 6. 根据测试结果采取相应措施
- [ ] 7. 如需切换账户，更新 `.env` 文件

---

## 📞 需要帮助？

如果按照上述步骤仍无法解决，请提供以下信息：

1. **掘金终端版本**: （在"关于"中查看）
2. **系统设置截图**: （显示Python配置选项）
3. **测试策略输出**: （完整的控制台日志）
4. **账户状态截图**: （"账户管理"页面）

**联系方式**:
- 📧 邮箱: 497720537@qq.com
- 📱 电话: 13392077558

---

**祝您排查顺利！** 🎉
