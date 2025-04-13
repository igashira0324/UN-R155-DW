UN-R155 PDF Downloader
=======================

概要
----
このツールは、UNECEのウェブサイトから最新のUN-R155（サイバーセキュリティ規則）の
英語版PDFファイルを自動的にダウンロードします。

機能
----
- UNECEウェブサイトから最新のUN-R155文書を自動検出
- 英語版PDFファイルの自動ダウンロード
- 日付ベースのファイル名管理（YYYYMMDD-UN-R155.pdf）
- 既存ファイルの重複ダウンロード防止
- ダウンロードしたファイルの整合性チェック
- Ubuntu環境での実行をサポート
- 毎日21:00に定期実行

必要条件
--------
- Node.js
- npm
- Playwright
- Git

Ubuntuへの展開
------------
1. 必要なパッケージをインストール:
   sudo apt update
   sudo apt install nodejs npm

2. GitHubからリポジトリをクローン:
   git clone https://github.com/igashira0324/YOUR_REPOSITORY_NAME.git

3. プロジェクトディレクトリに移動:
   cd YOUR_REPOSITORY_NAME

4. 依存パッケージのインストール:
   npm install

5. Playwrightブラウザのインストール:
   npx playwright install

6. スクリプトの実行権限を付与:
   chmod +x run_download.sh
   chmod +x setup_cron.sh

定期実行設定
----------
1. cronを設定:
   ./setup_cron.sh

使用方法
-------
以下のコマンドを実行して、テストを実行できます：
./run_download.sh

ダウンロードしたファイルは以下のディレクトリに保存されます：
playwright-tests/downloads/

ファイル名形式：YYYYMMDD-UN-R155.pdf
（YYYYMMDDは文書の公開日）

GitHubへの公開手順
----------------
1. GitHubで新しいリポジトリを作成（igashira0324/[リポジトリ名]）
2. ローカルリポジトリを初期化:
   git init
3. ファイルをリポジトリに追加:
   git add .
4. 変更をコミット:
   git commit -m "Initial commit"
5. リモートリポジトリを設定:
   git remote add origin https://github.com/igashira0324/[リポジトリ名].git
6. リポジトリをプッシュ:
   git push -u origin main

注意事項
-------
- 既に最新版のPDFファイルが存在する場合、ダウンロードはスキップされます
- ファイル名の日付は、UNECEサイトでの文書公開日を示します
- インターネット接続が必要です
- GitHubリポジトリへのプッシュ時には、.gitignoreファイルが正しく設定されていることを確認してください

エラー対応
--------
エラーが発生した場合は、以下を確認してください：
1. インターネット接続
2. UNECEウェブサイトのアクセス可否
3. Node.jsとnpmのインストール状態
4. Playwrightの設定
5. cronが正しく設定されているか
6. GitHubリポジトリの設定