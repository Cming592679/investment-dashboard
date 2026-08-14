#!/bin/bash
cd /home/cc/AI-project/investment-dashboard

# 个人数据目录（真实持仓/历史/预测，不进 git）
export PERSONAL_DATA_DIR=/home/cc/Acai-Knowledge/workspace/personal-investment-data

/usr/lib/google-cloud-sdk/platform/bundledpythonunix/bin/python3 app.py
