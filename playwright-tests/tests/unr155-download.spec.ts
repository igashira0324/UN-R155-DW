import { test, expect } from '@playwright/test';
import path from 'path';
import fs from 'fs';
import https from 'https';

interface PdfLink {
  href: string;
  text: string;
  date: Date;
}

test('UN-R155の最新PDFをダウンロード', async ({ page, context }) => {
  test.setTimeout(180000);
  
  try {
    console.log('アクセス開始...');

    // ページにアクセス
    await page.goto('https://unece.org/transport/vehicle-regulations-wp29/standards/addenda-1958-agreement-regulations-141-160', {
      waitUntil: 'networkidle',
      timeout: 90000
    });

    await page.waitForLoadState('domcontentloaded');
    console.log('規則リストページにアクセス完了');

    // 直接PDFリンクを探す
    const pdfLinks = await page.evaluate((): PdfLink[] => {
      // すべてのリンクを取得
      const links = Array.from(document.querySelectorAll('a[href*=".pdf"]')) as HTMLAnchorElement[];
      const results: PdfLink[] = [];

      for (const link of links) {
        const href = link.href;
        // R155の英語版PDFを探す
        if (href.toLowerCase().includes('155') && href.toLowerCase().match(/155.*e.*\.pdf$/)) {
          // URLから日付を抽出
          const dateMatch = href.match(/(\d{4})[-\/](\d{2})/);
          if (dateMatch) {
            results.push({
              href: href,
              text: link.textContent || '',
              date: new Date(parseInt(dateMatch[1]), parseInt(dateMatch[2]) - 1)
            });
          }
        }
      }
      return results;
    });

    console.log(`\n=== 検出されたPDFリンク ===`);
    pdfLinks.forEach((link, index) => {
      console.log(`${index + 1}. URL: ${link.href}`);
      console.log(`   テキスト: ${link.text}`);
      console.log(`   日付: ${link.date.toLocaleDateString()}\n`);
    });

    if (pdfLinks.length === 0) {
      throw new Error('英語版のPDFリンクが見つかりませんでした');
    }

    // 最新のリンクを取得
    const latestLink = pdfLinks.reduce((latest, current) => 
      current.date > latest.date ? current : latest
    );

    console.log(`最新のPDFリンク: ${latestLink.href}`);
    console.log(`日付: ${latestLink.date.toLocaleDateString()}`);

    // ファイル名の生成
    const dateStr = latestLink.date.toISOString().substring(0, 10).replace(/-/g, '');
    const fileName = `${dateStr}-UN-R155.pdf`;
    
    // ダウンロードの準備
    const downloadPath = path.join(process.cwd(), 'playwright-tests', 'downloads');
    if (!fs.existsSync(downloadPath)) {
      fs.mkdirSync(downloadPath, { recursive: true });
    }

    const filePath = path.join(downloadPath, fileName);

    // 既存ファイルのチェック
    if (fs.existsSync(filePath)) {
      console.log(`ファイル ${fileName} は既に存在します。ダウンロードをスキップします。`);
      return;
    }

    // PDFファイルを直接ダウンロード
    console.log('PDFのダウンロード開始...');

    await new Promise<void>((resolve, reject) => {
      const file = fs.createWriteStream(filePath);
      https.get(latestLink.href, (response) => {
        response.pipe(file);
        file.on('finish', () => {
          file.close();
          resolve();
        });
      }).on('error', (err) => {
        fs.unlink(filePath, () => {});
        reject(err);
      });
    });

    // ファイルの検証
    expect(fs.existsSync(filePath)).toBeTruthy();
    const stats = fs.statSync(filePath);
    expect(stats.size).toBeGreaterThan(0);

    console.log(`PDFが正常にダウンロードされました: ${filePath}`);
    console.log(`ファイルサイズ: ${stats.size} bytes`);

  } catch (error) {
    console.error('テスト実行中にエラーが発生:', error);
    throw error;
  }
});