import { test, expect } from '@playwright/test';

test('サンプルテスト: example.comにアクセスしてタイトルを確認', async ({ page }) => {
  // example.comにアクセス
  await page.goto('https://example.com/');

  // タイトルを確認
  await expect(page).toHaveTitle('Example Domain');

  // h1要素のテキストを確認
  const heading = page.locator('h1');
  await expect(heading).toHaveText('Example Domain');

  // ページ内のテキストが含まれているか確認
  const content = page.locator('p');
  await expect(content).toContainText('This domain is for use in illustrative examples');
});