#!/bin/bash

# スクリプトのディレクトリに移動
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
cd "$SCRIPT_DIR"

# cronの設定ファイルを開く
(crontab -l 2>/dev/null; echo "0 21 * * * $SCRIPT_DIR/run_download.sh") | crontab -

echo "cronが設定されました。毎日21:00に実行されます。"