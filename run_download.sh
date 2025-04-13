#!/bin/bash

# スクリプトのディレクトリに移動
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
cd "$SCRIPT_DIR"

# Node.jsとnpmが利用可能か確認
if ! command -v node &> /dev/null; then
    echo "Node.jsがインストールされていません"
    echo "インストール方法: sudo apt install nodejs npm"
    exit 1
fi

# 必要なディレクトリが存在することを確認
mkdir -p playwright-tests/downloads

# Playwrightのテストを実行
npx playwright test playwright-tests/tests/unr155-download.spec.ts

# 実行結果をログに記録
echo "$(date '+%Y-%m-%d %H:%M:%S') - Download script executed" >> regulation_monitor.log
