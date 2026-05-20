# AlphaPilot Pro V9.2 - GitHub 推送指南

## 📋 快速推送流程

每次修改代码后,只需执行以下 3 步即可同步到 GitHub:

```bash
# 1. 添加所有修改的文件到暂存区
git add .

# 2. 提交修改并添加描述信息
git commit -m "描述你的修改内容"

# 3. 推送到远程仓库
git push
```

---

## 🔧 详细操作说明

### 一、首次配置(仅需一次)

如果你在其他电脑上克隆了项目,需要先配置远程仓库:

```bash
# 添加远程仓库地址
git remote add origin https://github.com/zhenqiangliang6-coder/AlphaPilot-Pro-V9.2.git

# 将当前分支重命名为 main
git branch -M main

# 首次推送(设置上游分支)
git push -u origin main
```

### 二、日常推送流程

#### 场景 1: 小改动推送

```bash
# 查看修改状态
git status

# 添加所有修改
git add .

# 提交并描述修改
git commit -m "修复动态止盈前缀判断BUG"

# 推送
git push
```

#### 场景 2: 分模块提交(推荐)

如果同时修改了多个模块,建议分开提交:

```bash
# 先提交风控模块的修改
git add risk/
git commit -m "优化止损策略:调整30/68开头股票阈值"

# 再提交策略模块的修改
git add strategies/
git commit -m "新增弱势市场量比动态调整逻辑"

# 最后推送所有提交
git push
```

#### 场景 3: 撤销未提交的修改

```bash
# 撤销工作区的修改(谨慎使用!)
git checkout -- <文件名>

# 从暂存区移除文件(保留工作区修改)
git reset HEAD <文件名>
```

---

## 📝 提交信息规范

### 推荐的提交信息格式

```
<类型>: <简短描述>

<详细说明>(可选)
```

### 常用类型前缀

- `feat`: 新功能 (例如: `feat: 新增集合竞价精英卖出策略`)
- `fix`: 修复BUG (例如: `fix: 修复股票代码格式标准化问题`)
- `docs`: 文档更新 (例如: `docs: 更新README添加部署说明`)
- `refactor`: 代码重构 (例如: `refactor: 优化信号总线分发逻辑`)
- `test`: 测试相关 (例如: `test: 新增T+1合规性测试用例`)
- `chore`: 构建/工具链 (例如: `chore: 更新.gitignore排除日志文件`)

### 示例

```bash
# ✅ 好的提交信息
git commit -m "fix: 修复动态止盈模块股票代码前缀判断BUG"
git commit -m "feat: 新增弱势市场量比阈值动态调整功能"
git commit -m "docs: 补充GitHub推送操作指南"

# ❌ 避免的提交信息
git commit -m "修改"
git commit -m "update"
git commit -m "fix bug"
```

---

## 🔍 常用 Git 命令速查

### 查看状态

```bash
# 查看工作区状态
git status

# 查看提交历史
git log --oneline -10

# 查看某次提交的详细内容
git show <commit-hash>
```

### 查看差异

```bash
# 查看工作区与暂存区的差异
git diff

# 查看暂存区与最后一次提交的差异
git diff --cached

# 查看两个版本之间的差异
git diff HEAD~2 HEAD
```

### 分支管理

```bash
# 查看所有分支
git branch -a

# 创建新分支
git branch feature-new-strategy

# 切换分支
git checkout feature-new-strategy

# 合并分支
git merge feature-new-strategy
```

### 回退操作

```bash
# 撤销最近一次提交(保留修改)
git reset --soft HEAD~1

# 撤销最近一次提交(丢弃修改)
git reset --hard HEAD~1

# 回退到指定版本
git reset --hard <commit-hash>
```

---

## ⚠️ 注意事项

### 1. 敏感信息保护

`.gitignore` 已配置排除以下敏感文件:
- `.env` (包含 API Token、账户ID等)
- `logs/` (日志文件)
- `data/*.json` (个人配置数据)
- `signals/*.json` (信号数据)

**严禁**将 `.env` 文件提交到公开仓库!

### 2. 推送前检查

```bash
# 确认没有遗漏重要文件
git status

# 确认提交信息清晰
git log -1

# 预览将要推送的内容
git diff --stat origin/main..HEAD
```

### 3. 冲突处理

如果推送时提示冲突:

```bash
# 先拉取远程最新代码
git pull origin main

# 解决冲突后重新提交
git add .
git commit -m "merge: 解决冲突"
git push
```

### 4. 大文件处理

如果有大文件(如数据集、模型文件),建议使用 Git LFS:

```bash
# 安装 Git LFS
git lfs install

# 跟踪大文件类型
git lfs track "*.pkl"
git lfs track "*.h5"

# 提交 .gitattributes
git add .gitattributes
git commit -m "chore: 配置Git LFS跟踪大文件"
```

---

## 🚀 高级技巧

### 1. 一键推送脚本

创建 `push_to_github.bat` (Windows):

```batch
@echo off
echo ========================================
echo   AlphaPilot Pro V9.2 - 快速推送
echo ========================================
echo.

git status
echo.
echo 请输入提交信息:
set /p commit_msg=

if "%commit_msg%"=="" (
    echo 错误: 提交信息不能为空!
    pause
    exit /b 1
)

git add .
git commit -m "%commit_msg%"
git push

echo.
echo ✅ 推送成功!
pause
```

使用方法:
```bash
.\push_to_github.bat
```

### 2. PowerShell 一键推送脚本

创建 `push_to_github.ps1`:

```powershell
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  AlphaPilot Pro V9.2 - 快速推送" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

git status
Write-Host ""

$commit_msg = Read-Host "请输入提交信息"

if ([string]::IsNullOrWhiteSpace($commit_msg)) {
    Write-Host "错误: 提交信息不能为空!" -ForegroundColor Red
    exit 1
}

git add .
git commit -m $commit_msg
git push

Write-Host ""
Write-Host "✅ 推送成功!" -ForegroundColor Green
```

使用方法:
```powershell
.\push_to_github.ps1
```

### 3. 自动添加时间戳

```bash
# 在提交信息中自动添加日期
git commit -m "fix: 修复BUG ($(date +%Y-%m-%d))"
```

---

## 📊 推送记录示例

```bash
# 第一次推送(已完成)
git add .
git commit -m "Initial commit: AlphaPilot Pro V9.2 quant trading system"
git push -u origin main

# 第二次推送(已完成)
git add .gitignore
git commit -m "Update .gitignore to exclude sensitive files and test artifacts"
git push

# 未来的推送...
git add .
git commit -m "feat: 新增XXX功能"
git push
```

---

## 🆘 常见问题

### Q1: 推送时提示需要输入用户名密码?

**解决方案**: 使用 Personal Access Token (PAT)

1. 访问: https://github.com/settings/tokens
2. 生成新的 Token (勾选 `repo` 权限)
3. 推送时使用 Token 代替密码

或者配置 SSH key:
```bash
# 生成 SSH key
ssh-keygen -t ed25519 -C "zhenqiangliang6@gmail.com"

# 添加到 GitHub
# 复制 ~/.ssh/id_ed25519.pub 内容到 GitHub Settings > SSH Keys

# 修改远程地址为 SSH
git remote set-url origin git@github.com:zhenqiangliang6-coder/AlphaPilot-Pro-V9.2.git
```

### Q2: 误提交了敏感文件怎么办?

**紧急处理**:
```bash
# 1. 从 Git 历史中彻底删除文件
git filter-branch --force --index-filter \
  'git rm --cached --ignore-unmatch .env' \
  --prune-empty --tag-name-filter cat -- --all

# 2. 强制推送(会覆盖远程历史)
git push origin main --force

# 3. 立即在 GitHub 上撤销该 Token/密钥
```

**预防措施**: 确保 `.gitignore` 正确配置!

### Q3: 如何查看谁在什么时候修改了什么?

```bash
# 查看文件的修改历史
git log --follow -- <文件名>

# 查看每行代码的最后修改者
git blame <文件名>

# 图形化查看历史
gitk
```

---

## 📚 相关资源

- **项目仓库**: https://github.com/zhenqiangliang6-coder/AlphaPilot-Pro-V9.2
- **Git 官方文档**: https://git-scm.com/doc
- **GitHub 帮助**: https://docs.github.com/cn

---

## 💡 最佳实践总结

1. **频繁提交**: 小的、原子化的提交更容易追踪和管理
2. **清晰的提交信息**: 让团队成员(或未来的自己)能快速理解修改内容
3. **推送前检查**: 确认没有遗漏文件或提交敏感信息
4. **定期同步**: 多人协作时及时拉取最新代码,避免冲突
5. **备份重要数据**: Git 不是备份工具,重要数据仍需额外备份

---

**最后提醒**: 量化交易系统涉及真实资金,推送前务必确认:
- ✅ 不包含 `.env` 等敏感配置文件
- ✅ 核心策略逻辑经过充分测试
- ✅ 提交信息清晰可追溯

祝交易顺利! 🚀💰
