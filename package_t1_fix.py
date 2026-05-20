# -*- coding: utf-8 -*-
"""
T+1修复文件打包脚本

功能说明：
将本次T+1修复涉及的所有文件打包成一个ZIP文件，方便复制到其他策略文件夹

作者: Alphapilot智能体团队
成员: 梁子羿、侯沣睿、梁茹真
邮箱: 497720537@qq.com | 电话: 13392077558
"""
import os
import zipfile
import shutil
from datetime import datetime


def create_t1_fix_package():
    """创建T+1修复文件包"""
    
    # 获取当前目录
    current_dir = os.path.dirname(os.path.abspath(__file__))
    
    # 定义需要打包的文件列表
    files_to_package = [
        # 核心修改文件
        ("risk/stop_loss.py", "核心修改 - 止损模块"),
        ("risk/dynamic_take_profit.py", "核心修改 - 动态止盈模块"),
        ("strategies/auction_strategy.py", "核心修改 - 集合竞价策略"),
        
        # 工具文件
        ("diagnose_t1_compliance.py", "工具 - T+1诊断脚本"),
        ("test_t1_sandbox.py", "工具 - T+1沙盒测试"),
        
        # 文档文件
        ("T1_COMPLIANCE_FIX_REPORT.md", "文档 - 详细修复报告"),
        ("T1_QUICK_REFERENCE.md", "文档 - 快速参考指南"),
        ("FIX_SUMMARY.md", "文档 - 修复总结"),
    ]
    
    # 生成ZIP文件名（带时间戳）
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    zip_filename = f"T1_Fix_Package_{timestamp}.zip"
    zip_path = os.path.join(current_dir, zip_filename)
    
    print("="*60)
    print("AlphaPilot Pro V9.1 - T+1修复文件打包工具")
    print("作者: Alphapilot智能体团队")
    print("="*60)
    print(f"\n目标文件: {zip_filename}")
    print(f"保存位置: {zip_path}\n")
    
    # 检查文件是否存在
    missing_files = []
    existing_files = []
    
    for file_path, description in files_to_package:
        full_path = os.path.join(current_dir, file_path)
        if os.path.exists(full_path):
            existing_files.append((file_path, description))
            print(f"✅ 找到: {file_path} - {description}")
        else:
            missing_files.append(file_path)
            print(f"❌ 缺失: {file_path} - {description}")
    
    if missing_files:
        print(f"\n⚠️  警告: 以下文件不存在:")
        for f in missing_files:
            print(f"   - {f}")
    
    if not existing_files:
        print("\n❌ 错误: 没有找到任何可打包的文件！")
        return False
    
    # 创建ZIP文件
    try:
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for file_path, description in existing_files:
                full_path = os.path.join(current_dir, file_path)
                
                # 保持目录结构
                arc_name = file_path.replace('\\', '/')
                zipf.write(full_path, arc_name)
                
                # 获取文件大小
                file_size = os.path.getsize(full_path)
                size_str = format_size(file_size)
                
                print(f"📦 已打包: {file_path} ({size_str})")
        
        # 输出总结
        total_size = sum(os.path.getsize(os.path.join(current_dir, f)) 
                        for f, _ in existing_files)
        
        print(f"\n{'='*60}")
        print("✅ 打包完成！")
        print(f"{'='*60}")
        print(f"📁 ZIP文件: {zip_filename}")
        print(f"📊 文件数量: {len(existing_files)} 个")
        print(f"💾 总大小: {format_size(total_size)}")
        print(f"📍 保存位置: {zip_path}")
        print(f"{'='*60}")
        
        # 生成使用说明
        readme_content = generate_readme(existing_files)
        readme_path = os.path.join(current_dir, "T1_FIX_README.txt")
        with open(readme_path, 'w', encoding='utf-8') as f:
            f.write(readme_content)
        
        print(f"\n📝 使用说明已生成: T1_FIX_README.txt")
        print(f"{'='*60}")
        
        return True
        
    except Exception as e:
        print(f"\n❌ 打包失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def format_size(size_bytes):
    """格式化文件大小"""
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.2f} KB"
    else:
        return f"{size_bytes / (1024 * 1024):.2f} MB"


def generate_readme(existing_files):
    """生成使用说明"""
    content = """================================================================================
AlphaPilot Pro V9.1 - T+1修复文件包使用说明
作者: Alphapilot智能体团队
成员: 梁子羿、侯沣睿、梁茹真
邮箱: 497720537@qq.com | 电话: 13392077558
================================================================================

📦 文件包内容
--------------------------------------------------------------------------------

"""
    
    for file_path, description in existing_files:
        content += f"  • {file_path}\n    {description}\n\n"
    
    content += """
📋 安装步骤
--------------------------------------------------------------------------------

1. 解压ZIP文件到目标策略文件夹

2. 覆盖以下核心文件（建议先备份原文件）：
   - risk/stop_loss.py
   - risk/dynamic_take_profit.py
   - strategies/auction_strategy.py

3. （可选）添加工具文件：
   - diagnose_t1_compliance.py
   - test_t1_sandbox.py

4. （可选）查看文档了解详细信息：
   - T1_COMPLIANCE_FIX_REPORT.md
   - T1_QUICK_REFERENCE.md
   - FIX_SUMMARY.md

✅ 验证安装
--------------------------------------------------------------------------------

运行诊断脚本验证T+1约束是否正确实施：

    python diagnose_t1_compliance.py

运行沙盒测试验证逻辑：

    python test_t1_sandbox.py

🎯 核心改进
--------------------------------------------------------------------------------

1. T+1交易制度约束：
   - 所有卖出操作使用 can_use_volume（可卖数量）
   - 今日买入的股票不会被卖出
   - 日志明确显示"总持仓"和"可卖数量"

2. 集合竞价策略优化：
   - 修复了 ticks 变量未定义的错误
   - 增强了执行日志输出
   - 添加了详细的统计信息

📞 技术支持
--------------------------------------------------------------------------------

如有问题，请联系：
- 邮箱: 497720537@qq.com
- 电话: 13392077558
- 团队: Alphapilot智能体团队

================================================================================
最后更新: 2026-04-23
================================================================================
"""
    
    return content


if __name__ == "__main__":
    success = create_t1_fix_package()
    
    if success:
        print("\n✨ 提示: 请将生成的ZIP文件复制到其他策略文件夹并解压")
    else:
        print("\n⚠️  提示: 打包失败，请检查文件路径")
