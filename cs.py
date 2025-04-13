import requests
from bs4 import BeautifulSoup
import hashlib
import json
import time
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import logging
import schedule
from datetime import datetime

class RegulationMonitor:
    def __init__(self, config_file="config.json"):
        """
        法規・制度・ガイドラインの更新を監視するクラス
        
        Args:
            config_file (str): 設定ファイルのパス
        """
        self.config_file = config_file
        self.load_config()
        self.setup_logging()
        
    def load_config(self):
        """設定ファイルを読み込む"""
        try:
            # 強制的に新しい構造で初期化
            if False and os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    self.config = json.load(f)
            else:
                # デフォルト設定
                self.config = {
                    "sources": [
                        {
                            "name": "UN-R155",
                            "type": "unece",
                            "base_url": "https://unece.org/transport/documents",
                            "known_versions": [
                                {
                                    "url": "https://unece.org/transport/documents/2021/03/standards/un-regulation-no-155-cyber-security-and-cyber-security",
                                    "version": "original",
                                    "date": "2021-03",
                                    "last_hash": ""
                                },
                                {
                                    "url": "https://unece.org/transport/documents/2024/03/standards/un-regulation-no-155-amendment-2",
                                    "version": "amendment1",
                                    "date": "2022-11",
                                    "last_hash": ""
                                },
                                {
                                    "url": "https://unece.org/transport/documents/2022/11/standards/un-regulation-no-155-amend1-0",
                                    "version": "amendment1",
                                    "date": "2022-11",
                                    "last_hash": ""
                                },
                                {
                                    "url": "https://unece.org/transport/documents/2021/03/standards/un-regulation-no-155-cyber-security-and-cyber-security",
                                    "version": "original",
                                    "date": "2021-03",
                                    "last_hash": ""
                                }
                            ],
                            "search_patterns": [
                                r"un-regulation-no-155",
                                r"regulation-155",
                                r"regulation.*155.*amendment",
                                r"addendum.*154.*regulation.*155"
                            ]
                        }
                    ],
                    "notification": {
                        "email": {
                            "enabled": False,
                            "smtp_server": "smtp.example.com",
                            "smtp_port": 587,
                            "username": "your_email@example.com",
                            "password": "your_password",
                            "sender": "your_email@example.com",
                            "recipients": ["recipient@example.com"]
                        }
                    },
                    "check_interval_hours": 24,
                    "log_file": "regulation_monitor.log"
                }
                self.save_config()
        except Exception as e:
            print(f"設定ファイルの読み込みエラー: {e}")
            raise
    
    def save_config(self):
        """設定ファイルを保存する"""
        with open(self.config_file, 'w', encoding='utf-8') as f:
            json.dump(self.config, f, ensure_ascii=False, indent=4)
    
    def setup_logging(self):
        """ロギングの設定"""
        log_file = self.config.get("log_file", "regulation_monitor.log")
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file, encoding='utf-8'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger("RegulationMonitor")
    def get_page_content(self, url, selector):
        """
        指定されたURLからコンテンツを取得し、セレクタに基づいて必要な部分を抽出
        
        Args:
            url (str): 取得するウェブページのURL
            selector (str): 抽出するHTML要素のCSSセレクタ
            
        Returns:
            str: 抽出されたコンテンツ
        """
        def try_selectors(soup, base_selector):
            """複数のセレクタバリエーションを試行"""
            selectors = [
                base_selector,
                f"#{base_selector}",
                f".{base_selector}",
                *[s.strip() for s in base_selector.split()],
                "main", "article", "div.content", "div.main-content"
            ]
            
            for sel in selectors:
                try:
                    elements = soup.select(sel)
                    if elements:
                        return elements
                except Exception:
                    continue
            return None

        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
                'Accept-Language': 'en-US,en;q=0.9',
                'Accept-Encoding': 'gzip, deflate, br',
                'Connection': 'keep-alive',
                'Cache-Control': 'max-age=0',
                'sec-ch-ua': '"Chromium";v="122", "Not(A:Brand";v="24", "Google Chrome";v="122"',
                'sec-ch-ua-mobile': '?0',
                'sec-ch-ua-platform': '"Windows"',
                'Sec-Fetch-Dest': 'document',
                'Sec-Fetch-Mode': 'navigate',
                'Sec-Fetch-Site': 'none',
                'Sec-Fetch-User': '?1',
                'Upgrade-Insecure-Requests': '1'
            }
            
            session = requests.Session()
            
            # リトライ処理
            max_retries = 3
            retry_delay = 2  # seconds
            
            for attempt in range(max_retries):
                try:
                    response = session.get(
                        url,
                        headers=headers,
                        timeout=30,
                        verify=True,
                        allow_redirects=True
                    )
                    response.raise_for_status()
                    break
                except requests.exceptions.RequestException as e:
                    if attempt == max_retries - 1:
                        raise
                    self.logger.warning(f"リトライ {attempt + 1}/{max_retries}: {str(e)}")
                    time.sleep(retry_delay * (attempt + 1))
            
            # レスポンスの詳細をログに記録
            self.logger.info(f"URL: {url}")
            self.logger.info(f"Status Code: {response.status_code}")
            self.logger.info(f"Content Type: {response.headers.get('content-type', 'unknown')}")
            
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            contents = try_selectors(soup, selector)
            
            if not contents:
                available_classes = [cls for tag in soup.find_all() for cls in tag.get('class', [])]
                available_ids = [tag.get('id') for tag in soup.find_all() if tag.get('id')]
                main_tags = soup.find_all(['main', 'article', 'div'])
                
                self.logger.warning(f"コンテンツ取得の詳細情報:")
                self.logger.warning(f"- 試行したセレクタ: {selector}")
                self.logger.warning(f"- 利用可能なクラス: {', '.join(set(available_classes[:10]))}")
                self.logger.warning(f"- 利用可能なID: {', '.join(set(available_ids[:10]))}")
                self.logger.warning(f"- メインタグ数: main={len(soup.find_all('main'))}, article={len(soup.find_all('article'))}")
                
                # HTMLの一部をログに記録（デバッグ用）
                html_sample = str(soup)[:500]
                self.logger.debug(f"HTML Sample:\n{html_sample}")
                
                return ""
            
            # テキスト抽出とクリーニング
            texts = []
            for content in contents:
                # インラインスクリプトとスタイルを除去
                [s.decompose() for s in content.find_all(['script', 'style'])]
                # テキストを抽出し、余分な空白を除去
                text = ' '.join(content.get_text(separator=' ').split())
                if text:
                    texts.append(text)
            
            return "\n".join(texts)
        except requests.exceptions.RequestException as e:
            self.logger.error(f"ページの取得中にエラーが発生しました（URL: {url}）: {e}")
            return ""

    def analyze_page(self, url):
        """
        ページの構造を解析してセレクタの候補を提示
        
        Args:
            url (str): 解析するウェブページのURL
            
        Returns:
            dict: 解析結果
        """
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            response = requests.get(url, headers=headers, timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 主要なコンテナ要素の候補を収集
            main_containers = []
            for tag in ['main', 'article', 'div.content', 'div.main-content']:
                elements = soup.select(tag)
                if elements:
                    main_containers.extend(elements)
            
            # クラス名とIDの収集
            classes = {}
            ids = {}
            
            for tag in soup.find_all():
                # クラスの収集
                for cls in tag.get('class', []):
                    if cls not in classes:
                        classes[cls] = 0
                    classes[cls] += 1
                
                # IDの収集
                if tag.get('id'):
                    if tag.get('id') not in ids:
                        ids[tag.get('id')] = 0
                    ids[tag.get('id')] += 1
            
            # 最も頻出する要素を選択
            common_classes = sorted(classes.items(), key=lambda x: x[1], reverse=True)[:5]
            common_ids = sorted(ids.items(), key=lambda x: x[1], reverse=True)[:5]
            
            return {
                "url": url,
                "status": "success",
                "suggested_selectors": [
                    f"main",
                    f"article",
                    f"div.content",
                    *[f".{cls}" for cls, _ in common_classes],
                    *[f"#{id}" for id, _ in common_ids]
                ]
            }
            
        except requests.exceptions.RequestException as e:
            return {
                "url": url,
                "status": "error",
                "error": str(e)
            }
            return ""
    
    def calculate_hash(self, content):
        """
        コンテンツのMD5ハッシュを計算
        
        Args:
            content (str): ハッシュを計算するコンテンツ
            
        Returns:
            str: 計算されたMD5ハッシュ値
        """
        return hashlib.md5(content.encode('utf-8')).hexdigest()
    
    def find_unece_versions(self):
        """
        UNECE文書の新しいバージョンを検索
        """
        source = next((s for s in self.config["sources"] if s["type"] == "unece"), None)
        if not source:
            return []

        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5'
            }
            
            session = requests.Session()
            response = session.get(source["base_url"], headers=headers, timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            all_links = soup.find_all('a', href=True)
            
            # 既知のURLを収集
            known_urls = {v["url"] for v in source["known_versions"]}
            new_versions = []
            
            for link in all_links:
                url = link['href']
                if not url.startswith('http'):
                    url = f"https://unece.org{url}"
                
                if url in known_urls:
                    continue
                
                for pattern in source["search_patterns"]:
                    if re.search(pattern, url, re.IGNORECASE):
                        date_match = re.search(r'/(\d{4})/(\d{2})/', url)
                        if date_match:
                            year, month = date_match.groups()
                            new_versions.append({
                                "url": url,
                                "version": f"new_version_{len(source['known_versions']) + len(new_versions) + 1}",
                                "date": f"{year}-{month}",
                                "last_hash": "",
                                "content": None
                            })
                        break
            
            return new_versions
        except Exception as e:
            self.logger.error(f"新バージョン検索中にエラー: {e}")
            return []

    def check_for_updates(self, start_date=None, end_date=None):
        """
        指定期間内のソースの更新をチェック
        
        Args:
            start_date (str, optional): 開始日（YYYY-MM-DD形式）
            end_date (str, optional): 終了日（YYYY-MM-DD形式）
        """
        self.logger.info("更新チェックを開始します")
        results = []
        
        # 新しいバージョンの検索
        source = next((s for s in self.config["sources"] if s["type"] == "unece"), None)
        if source:
            new_versions = self.find_unece_versions()
            if new_versions:
                self.logger.info(f"新しいバージョンが見つかりました: {len(new_versions)}個")
                # 新しいバージョンをknown_versionsに追加
                source["known_versions"].extend(new_versions)
                self.save_config()
        
            # 各バージョンのコンテンツをチェック
            for version in source["known_versions"]:
                self.logger.info(f"バージョン {version['version']} をチェックしています...")
                content = self.get_page_content(version["url"], "main")
                
                result = {
                    "name": f"{source['name']} ({version['version']})",
                    "url": version["url"],
                    "version": version["version"],
                    "date": version.get("date", "不明"),
                    "status": "不明",
                    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }
                
                if content:
                    current_hash = self.calculate_hash(content)
                    if not version["last_hash"]:
                        result["status"] = "初回チェック"
                    elif version["last_hash"] != current_hash:
                        result["status"] = "更新あり"
                    else:
                        result["status"] = "更新なし"
                    version["last_hash"] = current_hash
                else:
                    result["status"] = "取得失敗"
                
                results.append(result)
        
        # 設定ファイルを保存
        self.save_config()
        
        return results
    
    def send_notification(self, updates):
        """
        更新の通知を送信
        
        Args:
            updates (list): 更新された情報のリスト
        """
        message = "以下の法規・制度・ガイドラインに更新がありました：\n\n"
        for update in updates:
            message += f"- {update['name']}\n  URL: {update['url']}\n  更新日時: {update['timestamp']}\n\n"
        
        self.logger.info(message)
        
        # メール通知が有効な場合は送信
        email_config = self.config["notification"]["email"]
        if email_config["enabled"]:
            try:
                # メール作成
                msg = MIMEMultipart()
                msg["From"] = email_config["sender"]
                msg["To"] = ", ".join(email_config["recipients"])
                msg["Subject"] = "法規・制度・ガイドライン更新通知"
                
                msg.attach(MIMEText(message, "plain", "utf-8"))
                
                # メール送信
                server = smtplib.SMTP(email_config["smtp_server"], email_config["smtp_port"])
                server.starttls()
                server.login(email_config["username"], email_config["password"])
                server.send_message(msg)
                server.quit()
                
                self.logger.info("メール通知を送信しました")
            except Exception as e:
                self.logger.error(f"メール送信エラー: {e}")
    
    def run_scheduled(self):
        """スケジュールに基づいて定期的に実行"""
        interval_hours = self.config.get("check_interval_hours", 24)
        
        self.logger.info(f"監視を開始しました（チェック間隔: {interval_hours}時間）")
        
        # 初回実行
        self.check_for_updates()
        
        # スケジュール設定
        schedule.every(interval_hours).hours.do(self.check_for_updates)
        
        try:
            while True:
                schedule.run_pending()
                time.sleep(60)  # 1分ごとにチェック
        except KeyboardInterrupt:
            self.logger.info("監視を終了しました")

# コマンドラインから実行する場合
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="法規・制度・ガイドラインの更新を監視するツール")
    parser.add_argument("--config", default="config.json", help="設定ファイルのパス")
    parser.add_argument("--once", action="store_true", help="1回だけ実行して終了する場合に指定")
    args = parser.parse_args()
    
    monitor = RegulationMonitor(args.config)
    
    if args.once:
        monitor.check_for_updates()
    else:
        monitor.run_scheduled()