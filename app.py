import gradio as gr
from cs import RegulationMonitor
import json
import os
from datetime import datetime, timedelta

def load_sources():
    monitor = RegulationMonitor()
    sources = []
    for src in monitor.config['sources']:
        if src['type'] == 'unece':
            for version in src['known_versions']:
                sources.append([
                    f"{src['name']} ({version['version']})",
                    version['url']
                ])
    return sources

def format_update_results(results):
    """更新結果を表形式に整理"""
    rows = []
    for r in results:
        rows.append([
            r["name"].split(" (")[0],  # バージョン情報を分離
            r.get("version", ""),
            r.get("date", ""),
            r["url"],
            r["status"],
            r["timestamp"]
        ])
    return rows

def check_updates(start_date, end_date):
    monitor = RegulationMonitor()
    results = monitor.check_for_updates(start_date, end_date)
    return format_update_results(results)

def find_new_versions():
    monitor = RegulationMonitor()
    new_versions = monitor.find_unece_versions()
    if new_versions:
        return f"新しいバージョンが {len(new_versions)} 件見つかりました:\n" + "\n".join(
            f"• {v['version']} ({v['date']}): {v['url']}"
            for v in new_versions
        )
    return "新しいバージョンは見つかりませんでした。"

def analyze_url(url):
    monitor = RegulationMonitor()
    result = monitor.analyze_page(url)
    if result["status"] == "success":
        return "\n".join([
            "推奨セレクタ:",
            *[f"• {selector}" for selector in result["suggested_selectors"]]
        ])
    else:
        return f"エラーが発生しました: {result['error']}"

def add_source(name, url, selector):
    if not name or not url or not selector:
        return "名前、URL、セレクタを入力してください。", load_sources()
    
    try:
        monitor = RegulationMonitor()
        # テスト取得を実行
        content = monitor.get_page_content(url, selector)
        if not content:
            return "指定されたセレクタでコンテンツを取得できませんでした。セレクタを確認してください。", load_sources()
        
        monitor.config["sources"].append({
            "name": name,
            "url": url,
            "selector": selector,
            "last_hash": ""
        })
        monitor.save_config()
        return "監視対象を追加しました。", load_sources()
    except Exception as e:
        return f"エラーが発生しました: {str(e)}", load_sources()

def create_ui():
    with gr.Blocks(title="法規制監視システム") as app:
        gr.Markdown("# 法規制監視システム")
        
        with gr.Tab("監視対象一覧"):
            with gr.Row():
                start_date = gr.Textbox(
                    label="開始日 (YYYY-MM-DD)",
                    value=(datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
                )
                end_date = gr.Textbox(
                    label="終了日 (YYYY-MM-DD)",
                    value=datetime.now().strftime("%Y-%m-%d")
                )
            
            sources_output = gr.Dataframe(
                headers=["名前", "URL"],
                value=load_sources(),
                interactive=False
            )
            with gr.Row():
                check_button = gr.Button("更新をチェック", variant="primary")
                find_versions_button = gr.Button("新バージョン検索")

            version_result = gr.Textbox(
                label="新バージョン検索結果",
                interactive=False,
                lines=3
            )
            
            update_output = gr.Dataframe(
                label="更新チェック結果",
                headers=["名前", "バージョン", "日付", "URL", "状態", "チェック時刻"],
                interactive=False,
                wrap=True
            )
            
            check_button.click(
                fn=check_updates,
                inputs=[start_date, end_date],
                outputs=update_output
            )
            
            find_versions_button.click(
                fn=find_new_versions,
                outputs=version_result
            )
        
        with gr.Tab("監視対象設定"):
            gr.Markdown("### 監視対象の追加")
            with gr.Row():
                name_input = gr.Textbox(label="名前")
                url_input = gr.Textbox(label="URL")

            analyze_button = gr.Button("URLを解析")
            selector_suggestions = gr.Textbox(
                label="セレクタの候補",
                interactive=False,
                lines=5
            )
            
            selector_input = gr.Textbox(
                label="セレクター",
                placeholder="解析結果から適切なセレクタを選択して入力してください",
                lines=2
            )
            
            with gr.Row():
                add_button = gr.Button("追加", variant="primary")
            
            result_output = gr.Textbox(
                label="操作結果",
                interactive=False
            )
            
            gr.Markdown("### 監視対象一覧")
            sources_list = gr.Dataframe(
                headers=["名前", "URL"],
                value=load_sources(),
                interactive=False
            )
            
            add_button.click(
                fn=add_source,
                inputs=[name_input, url_input, selector_input],
                outputs=[result_output, sources_list]
            )
            
            # URL解析のイベントハンドラ
            analyze_button.click(
                fn=analyze_url,
                inputs=[url_input],
                outputs=selector_suggestions
            )

    return app

if __name__ == "__main__":
    app = create_ui()
    app.launch(share=False)