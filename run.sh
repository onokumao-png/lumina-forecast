#!/bin/bash
# LuminaTech 受注予測アプリ 起動スクリプト
# 仮想環境が存在しない場合は自動セットアップ

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

# 仮想環境がなければ作成
if [ ! -d ".venv" ]; then
  echo "仮想環境を作成中..."
  python3 -m venv .venv
  .venv/bin/pip install -r requirements.txt
fi

echo "アプリを起動します: http://localhost:8501"
.venv/bin/streamlit run app.py
