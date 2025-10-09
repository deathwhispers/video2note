#!/bin/bash
# =============================
# 一键运行 video2note 项目
# =============================

echo "===================="
echo "🚀 开始运行 video2note"
echo "===================="

# 激活虚拟环境（可选）
# source venv/bin/activate

# 安装依赖
pip install -r requirements.txt

# 执行主流程
python -m src.main

echo "===================="
echo "✅ Pipeline 执行完成"
echo "===================="
