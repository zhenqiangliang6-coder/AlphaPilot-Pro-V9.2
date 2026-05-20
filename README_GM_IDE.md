# 🚀 AlphaPilot Pro - 掘金量化平台开发指南

**Alphapilot智能体团队**  
**作者**: 梁子羿、侯沣睿、梁茹真  
**邮箱**: 497720537@qq.com | **电话**: 13392077558

---

## ⚡ 必读！核心机制

### 🎯 最重要的规则

```
策略ID (strategy_id) 必须与掘金终端中创建的策略实例ID完全一致！
```

**这不是可选配置，而是掘金量化平台的核心运行机制！**

📖 **立即阅读完整说明**: [🔗 核心机制与开发规范总结](./CORE_MECHANISM_SUMMARY.md)

---

## 📖 快速开始

### 第一步：了解核心机制（必读）

打开 **[CORE_MECHANISM_SUMMARY.md](./CORE_MECHANISM_SUMMARY.md)**  
这份文档详细解释了：
- ✅ 掘金量化的账户绑定机制
- ✅ 为什么 strategy_id 必须匹配
- ✅ 完整的开发流程（经过实战验证）
- ✅ 常见问题与解决方案

### 第二步：选择开发方式

#### 方式A: 在掘金IDE中运行（推荐新手）

1. 在掘金终端创建策略实例
2. 获取生成的 [strategy_id](file://d:\mpython\config\settings.py#L30-L30)
3. 同步代码到策略目录
4. 在掘金IDE中点击"运行"

📚 **详细指南**: [GM_IDE_WORKFLOW_GUIDE.md](./GM_IDE_WORKFLOW_GUIDE.md)

#### 方式B: 在VSCode中运行（推荐熟练后）

1. 确保掘金终端已打开且账户已连接
2. 在VSCode中编辑代码（使用正确的 [strategy_id](file://d:\mpython\config\settings.py#L30-L30)）
3. 运行一键启动脚本

```powershell
cd D:\mpython
.\start_in_vscode.ps1
```

📚 **详细指南**: [VS_CODE_RUN_GUIDE.md](./VS_CODE_RUN_GUIDE.md)

---

## 📂 文档索引

### 核心文档（必读）

| 文档 | 重要性 | 说明 |
|------|--------|------|
| **[核心机制总结](./CORE_MECHANISM_SUMMARY.md)** | ⭐⭐⭐⭐⭐ | **掘金量化核心机制、strategy_id规则、完整开发流程** |
| [掘金IDE工作流指南](./GM_IDE_WORKFLOW_GUIDE.md) | ⭐⭐⭐⭐ | 在掘金IDE中开发的完整文档 |
| [VSCode运行指南](./VS_CODE_RUN_GUIDE.md) | ⭐⭐⭐⭐ | 在VSCode中运行的详细步骤 |

### 快速参考

| 文档 | 说明 |
|------|------|
| [快速参考卡](./QUICK_REFERENCE.txt) | 一页纸速查（路径、命令、账户信息） |
| [README](./README_GM_IDE.md) | 文档索引 |

### 工具脚本

| 脚本 | 用途 |
|------|------|
| [start_in_vscode.ps1](./start_in_vscode.ps1) | 一键启动策略（自动检查环境） |
| [sync_to_gm_ide.ps1](./sync_to_gm_ide.ps1) | 同步代码到掘金IDE策略目录 |

---

## 🎯 开发流程速查

```
┌─────────────────────────────────────────────────────────────┐
│                    开发流程                                   │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  1️⃣  在掘金终端创建策略实例（仅首次）                        │
│     → 获取 strategy_id                                      │
│                                                             │
│  2️⃣  在VSCode中编辑 main.py                                │
│     → 使用正确的 strategy_id                                │
│     → 编写策略逻辑                                           │
│     → 保存 (Ctrl+S)                                         │
│                                                             │
│  3️⃣  运行策略                                               │
│     方式A: .\start_in_vscode.ps1                           │
│     方式B: python main.py --mode live                      │
│     方式C: 在掘金IDE中点击"运行"                             │
│                                                             │
│  4️⃣  监控日志                                               │
│     → 观察控制台输出                                         │
│     → 检查错误信息                                           │
│     → 验证功能正常                                           │
│                                                             │
│  5️⃣  迭代开发                                               │
│     → 修改代码 → 重启策略 → 测试                            │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## ✅ 检查清单

### 启动前必须确认

- [ ] 掘金终端已打开
- [ ] 账户已连接（状态: 已连接）
- [ ] 策略实例已创建
- [ ] 代码中的 strategy_id 与终端一致
- [ ] 虚拟环境已激活
- [ ] 依赖包已安装（gm, dotenv, watchdog）
- [ ] 配置文件正确（.env, settings.py）

---

## 💡 常见问题

### Q: 为什么报错"无效的ACCOUNT_ID"？

**A**: strategy_id 与掘金终端策略实例不匹配。

**解决**: 
1. 在掘金终端查看策略属性，复制 strategy_id
2. 修改 main.py 中的 run() 函数
3. 重新运行

详细解答: [CORE_MECHANISM_SUMMARY.md](./CORE_MECHANISM_SUMMARY.md)

---

### Q: 如何在VSCode中运行策略？

**A**: 使用一键启动脚本

```powershell
cd D:\mpython
.\start_in_vscode.ps1
```

前提条件: 掘金终端已打开且账户已连接

详细步骤: [VS_CODE_RUN_GUIDE.md](./VS_CODE_RUN_GUIDE.md)

---

### Q: 如何同步代码到掘金IDE？

**A**: 运行同步脚本

```powershell
.\sync_to_gm_ide.ps1
```

详细流程: [GM_IDE_WORKFLOW_GUIDE.md](./GM_IDE_WORKFLOW_GUIDE.md)

---

## 📞 技术支持

遇到问题时，请提供：
1. 完整的错误日志
2. 代码中的 [strategy_id](file://d:\mpython\config\settings.py#L30-L30)
3. 掘金终端中策略实例的 [strategy_id](file://d:\mpython\config\settings.py#L30-L30)
4. 当前操作步骤

**联系方式**:
- 📧 邮箱: 497720537@qq.com
- 📱 电话: 13392077558

---

## 🎉 总结

### 核心要点

1. **strategy_id 必须匹配** - 这是掘金量化的核心机制
2. **掘金终端必须运行** - 策略依赖终端的账户上下文
3. **filename 使用相对路径** - 避免相对导入错误

### 成功标志

看到以下日志 = 策略正常运行：
- ✅ 连接行情服务成功
- ✅ 连接交易服务成功
- ✅ 账户资金查询成功
- ✅ 持仓查询成功
- ✅ 心跳日志持续输出

---

**祝您开发顺利！** 🚀

**记住: strategy_id 必须与掘金终端中创建的策略实例ID完全一致！** 🎯
