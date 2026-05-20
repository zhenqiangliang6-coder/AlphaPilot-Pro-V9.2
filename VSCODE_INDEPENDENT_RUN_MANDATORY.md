# VSCode 独立运行掘金策略的强制规范

## 🔴 核心要求：Strategy ID 必须严格同步

### 问题背景
在 VSCode 中独立运行掘金量化策略时，经常出现 `{"status": 1020, "message": "无效的ACCOUNT_ID"}` 错误。

### 根本原因
**代码中的 `strategy_id` 与掘金终端（IDE）中创建的策略实例 ID 不一致！**

---

## ✅ 强制执行流程

### 第一步：在掘金终端创建策略实例
1. 打开掘金交易终端（GUI）
2. 进入"策略管理"或"我的策略"
3. 点击"新建策略"
4. **复制生成的策略 ID**（格式如：`a62d366d-3c78-11f1-8563-1ece51d839d6`）
   - ⚠️ 这个 ID 是系统自动生成的，**不要手动修改**
   - ⚠️ 包含连字符和大小写字母，必须完全一致

### 第二步：同步 Strategy ID 到代码
1. 打开 VSCode 中的 [main.py](file://d:\mpython\main.py) 文件
2. 找到 `if __name__ == '__main__':` 块
3. 修改 `run()` 函数的 `strategy_id` 参数：

```python
if __name__ == '__main__':
    run(strategy_id='a62d366d-3c78-11f1-8563-1ece51d839d6',  # ← 必须与掘金终端一致！
        filename='main.py',
        mode=MODE_LIVE,
        token='fdf08e9d00c4da3b635c2616724ddae3f7793562')
```

### 第三步：在掘金终端连接账户
1. 在掘金终端中找到刚才创建的策略实例
2. 点击"连接账户"或"激活"
3. 确保状态显示为"已连接"或"运行中"
4. **不要关闭掘金终端**（它负责管理账户上下文）

### 第四步：在 VSCode 中运行
1. 确认掘金终端中的策略实例处于"已连接"状态
2. 在 VSCode 中右键 [main.py](file://d:\mpython\main.py) → "Run Python File in Terminal"
3. 或使用快捷键 `F5` 启动调试
4. 策略将成功启动并可以执行交易指令

---

## ❌ 常见错误及解决方案

### 错误 1：无效的 ACCOUNT_ID
**现象**：
```json
{"status": 1020, "message": "无效的ACCOUNT_ID"}
```

**原因**：
- 代码中的 `strategy_id` 与掘金终端中的策略实例 ID 不一致
- 或者掘金终端中未创建对应的策略实例

**解决**：
1. 检查掘金终端中策略实例的 ID
2. 复制到代码中的 `run(strategy_id='...')` 参数
3. 确保完全一致（包括大小写和连字符）

### 错误 2：无法下单/交易失败
**现象**：
策略启动成功，但 `order_volume` 等交易 API 调用失败

**原因**：
- 掘金终端中的策略实例未连接账户
- 或者账户未登录/未激活

**解决**：
1. 在掘金终端中确认策略实例状态为"已连接"
2. 检查账户是否已登录且资金充足
3. 重启掘金终端并重新连接账户

### 错误 3：ModuleNotFoundError: No module named 'gm'
**现象**：
```
ModuleNotFoundError: No module named 'gm'
```

**原因**：
- VSCode 使用的 Python 解释器与掘金终端不一致
- 或者未安装 `gm` 库

**解决**：
1. 在 VSCode 中选择正确的 Python 解释器（与掘金终端一致）
2. 运行 `pip install gm python-dotenv`
3. 重启 VSCode

---

## 📋 检查清单（每次运行前必查）

在 VSCode 中运行策略前，请确认以下事项：

- [ ] **掘金终端已启动并登录账户**
- [ ] **在掘金终端中创建了策略实例**
- [ ] **代码中的 `strategy_id` 与掘金终端中的策略实例 ID 完全一致**
- [ ] **掘金终端中的策略实例状态为"已连接"**
- [ ] **`filename` 参数使用相对路径（如 `'main.py'`）**
- [ ] **`run()` 函数包裹在 `if __name__ == '__main__':` 块中**
- [ ] **VSCode 使用的 Python 解释器已安装 `gm` 库**

---

## 🎯 最佳实践

### 1. 固定使用一个策略实例
- 在掘金终端中创建一个策略实例后，**不要频繁删除重建**
- 每次只需要同步 `strategy_id` 到代码即可
- 建议将 `strategy_id` 保存在配置文件中统一管理

### 2. 使用配置文件管理 Strategy ID
在 [config/settings.py](file://d:\mpython\config\settings.py) 中添加：
```python
# 掘金策略配置
GM_STRATEGY_ID = 'a62d366d-3c78-11f1-8563-1ece51d839d6'
GM_TOKEN = 'fdf08e9d00c4da3b635c2616724ddae3f7793562'
```

在 [main.py](file://d:\mpython\main.py) 中使用：
```python
if __name__ == '__main__':
    from config import settings
    run(strategy_id=settings.GM_STRATEGY_ID,
        filename='main.py',
        mode=MODE_LIVE,
        token=settings.GM_TOKEN)
```

### 3. 创建同步脚本
编写 PowerShell 脚本自动同步 strategy_id：
```powershell
# sync_strategy_id.ps1
$NEW_ID = Read-Host "请输入掘金终端中的新 Strategy ID"
(Get-Content config\settings.py) -replace "GM_STRATEGY_ID = '.*'", "GM_STRATEGY_ID = '$NEW_ID'" | Set-Content config\settings.py
Write-Host "Strategy ID 已更新为: $NEW_ID"
```

---

## ⚠️ 重要提醒

1. **严禁在代码中调用 `login()` 或传入 `account_id` 参数**
   - 账户上下文由掘金终端管理
   - 代码中只需提供 `strategy_id` 和 `token`

2. **严禁使用绝对路径作为 `filename` 参数**
   - 必须使用相对路径：`filename='main.py'`
   - 否则会导致相对导入错误

3. **掘金终端必须保持运行**
   - 关闭掘金终端会导致策略无法执行交易
   - 即使代码在 VSCode 中运行，也需要掘金终端提供账户上下文

4. **每次修改 strategy_id 后必须重启策略**
   - 停止当前运行的策略
   - 重新启动以加载新的 strategy_id

---

## 📞 技术支持

如遇到其他问题，请参考：
- [ARCHITECTURE_V9.1.md](file://d:\mpython\ARCHITECTURE_V9.1.md) - 系统架构说明
- [QUICK_START_V9.1.md](file://d:\mpython\QUICK_START_V9.1.md) - 快速开始指南
- [GM_CONNECTION_WARNING_EXPLANATION.md](file://d:\mpython\GM_CONNECTION_WARNING_EXPLANATION.md) - 连接问题详解

**Alphapilot智能体团队**  
邮箱: 497720537@qq.com | 电话: 13392077558
