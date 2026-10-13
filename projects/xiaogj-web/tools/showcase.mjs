// Human-paced E2E of the local candidate. This never connects to the original.
import { chromium } from 'playwright';
import assert from 'node:assert/strict';
import { readFile, mkdir, writeFile } from 'node:fs/promises';
import { fileURLToPath } from 'node:url';
import { resolve } from 'node:path';

const project = fileURLToPath(new URL('..', import.meta.url));
const args = process.argv.slice(2);
const headless = args.includes('--headless');
const once = args.includes('--once');
const capture = headless || args.includes('--capture');
const paceIndex = args.indexOf('--pace');
const pace = paceIndex < 0 ? 1800 : Number(args[paceIndex + 1]);
if (!Number.isFinite(pace) || pace < 0) throw Error('pace must be nonnegative');
const origin = 'http://127.0.0.1:5183';
const credentials = JSON.parse(await readFile(resolve(project, 'private/local-auth.json'), 'utf8'));
const fixture = JSON.parse(await readFile(resolve(project, 'private/reference/student-detail.json'), 'utf8'));
const detail = fixture.data;
const amountBook = JSON.parse(await readFile(resolve(project, 'enrollment-amounts-scenarios.json'), 'utf8'));
const out = resolve(project, 'private/preview/tours', new Date().toISOString().replaceAll(':', '-'));
await mkdir(out, { recursive: true });
const browser = await chromium.launch({ headless, slowMo: pace ? 160 : 0, args: ['--window-size=1280,800'] });
const browserClosed = new Promise(resolve => browser.once('disconnected', resolve));
const context = await browser.newContext({ viewport: headless ? { width: 1280, height: 720 } : null, locale: 'zh-CN' });
// Restrict both navigation and network to this local preview; no original-site requests.
await context.route('**/*', route => {
  const url = new URL(route.request().url());
  return url.origin === origin || ['data:', 'blob:'].includes(url.protocol) ? route.continue() : route.abort();
});
await context.addInitScript(() => {
  const install = () => {
    const cursor = document.createElement('div');
    cursor.id = 'local-e2e-cursor';
    cursor.style.cssText = 'position:fixed;left:0;top:0;z-index:2147483646;pointer-events:none;transform:translate(40px,40px);filter:drop-shadow(0 2px 3px #0008)';
    cursor.innerHTML = '<svg width="32" height="40" viewBox="0 0 24 32"><path d="M2 2L2 25L8 19L14 29L19 26L13 16L23 16Z" fill="#ffe14c" stroke="#17283e" stroke-width="2" stroke-linejoin="round"/></svg>';
    document.documentElement.append(cursor);
    const focus = document.createElement('div');
    focus.id = 'local-e2e-focus';
    focus.style.cssText = 'position:fixed;display:none;z-index:2147483645;pointer-events:none;border:3px solid #2096ff;border-radius:5px;box-shadow:0 0 0 4px #2096ff25;box-sizing:border-box';
    document.documentElement.append(focus);
    let target = null;
    const focusPosition = () => {
      if (!target || !target.isConnected) { focus.style.display = 'none'; return; }
      const r = target.getBoundingClientRect();
      focus.style.display = 'block'; focus.style.left = (r.left - 3) + 'px'; focus.style.top = (r.top - 3) + 'px';
      focus.style.width = (r.width + 6) + 'px'; focus.style.height = (r.height + 6) + 'px';
    };
    document.addEventListener('mousemove', event => { cursor.style.transform = `translate(${event.clientX}px,${event.clientY}px)`; }, true);
    document.addEventListener('mousedown', event => {
      const pulse = document.createElement('div');
      pulse.style.cssText = `position:fixed;left:${event.clientX - 12}px;top:${event.clientY - 12}px;width:24px;height:24px;border:3px solid #ff5d39;background:#ff5d3933;border-radius:50%;pointer-events:none;z-index:2147483647`;
      document.documentElement.append(pulse);
      pulse.animate([{ transform: 'scale(.6)', opacity: 1 }, { transform: 'scale(3)', opacity: 0 }], { duration: 850 }).finished.then(() => pulse.remove());
    }, true);
    document.addEventListener('focusin', event => { target = event.target.matches('input,textarea,select') ? event.target : null; focusPosition(); }, true);
    document.addEventListener('focusout', () => { target = null; focusPosition(); }, true);
    document.addEventListener('scroll', focusPosition, true);
    window.addEventListener('resize', focusPosition);
  };
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', install, { once: true }); else install();
});
const page = await context.newPage();
const previewClosed = Promise.race([browserClosed, new Promise(resolve => page.once('close', resolve))]);
page.setDefaultTimeout(15000);
const results = [];
let current = '';
async function caption(title, description, done = false) {
  current = title;
  await page.evaluate(({ title, description, done }) => {
    let host = document.getElementById('local-e2e-tour');
    if (!host) {
      host = document.createElement('div'); host.id = 'local-e2e-tour';
      host.style.cssText = 'position:fixed;left:16px;bottom:18px;z-index:2147483647;width:min(650px,90vw);pointer-events:none';
      document.body.append(host); host.attachShadow({ mode: 'open' });
      host.shadowRoot.innerHTML = `<style>:host{font:14px system-ui;color:#fff}.box{background:#182435f2;border:1px solid #627085;border-radius:12px;padding:13px 18px;box-shadow:0 6px 24px #0004;display:flex;gap:16px;align-items:center}.copy{flex:1}.tag{font-size:11px;color:#9dc7ff;letter-spacing:1px;margin-bottom:4px}strong{display:block;font-size:16px}p{margin:5px 0 0;color:#d4dfeb;line-height:1.45}button{pointer-events:auto;background:#31445c;color:#fff;border:1px solid #64748b;border-radius:6px;padding:8px 12px;cursor:pointer}</style><div class="box"><div class="copy"><div class="tag">本地复刻 · E2E 功能巡演</div><strong></strong><p></p></div><button>暂停</button></div>`;
      host.shadowRoot.querySelector('button').onclick = () => {
        window.__localTourPaused = !window.__localTourPaused;
        host.shadowRoot.querySelector('button').textContent = window.__localTourPaused ? '继续' : '暂停';
      };
    }
    host.shadowRoot.querySelector('strong').textContent = title;
    host.shadowRoot.querySelector('p').textContent = description;
    host.shadowRoot.querySelector('button').hidden = done;
  }, { title, description, done });
}
async function linger() {
  if (pace) await page.waitForTimeout(pace);
  while (!page.isClosed() && await page.evaluate(() => Boolean(window.__localTourPaused))) await page.waitForTimeout(150);
}
async function step(title, description, action) {
  await caption(`${results.length + 1}. ${title}`, description);
  await linger();
  await action();
  await linger();
  results.push({ title, status: 'pass' });
  if (capture) await page.screenshot({ path: resolve(out, `${String(results.length).padStart(2, '0')}.png`) });
  console.log(`✓ ${title}`);
}
// Bring the actual target into view, then let viewers see the pointer before acting.
async function reveal(locator) {
  await locator.waitFor({ state: 'visible' });
  await locator.evaluate(element => {
    const r = element.getBoundingClientRect();
    if (r.top < 135 || r.bottom > window.innerHeight - 140 || r.left < 0 || r.right > window.innerWidth)
      element.scrollIntoView({ block: 'center', inline: 'center', behavior: 'instant' });
  });
  await locator.scrollIntoViewIfNeeded();
  if (pace) await page.waitForTimeout(350);
  await locator.hover();
  if (pace) await page.waitForTimeout(450);
}
async function click(locator) { await reveal(locator); await locator.click(); }
async function check(locator) { await reveal(locator); await locator.check(); }
async function type(locator, value) {
  await click(locator);
  await locator.fill('');
  if (pace) await locator.pressSequentially(value, { delay: 65 }); else await locator.fill(value);
}
async function visible(locator) { await locator.waitFor({ state: 'visible' }); }
async function equalText(locator, expected) { await visible(locator); assert.equal((await locator.innerText()).trim(), expected); }
async function home() { await click(page.getByRole('link', { name: '校管家首页', exact: true })); await visible(page.getByRole('button', { name: '自定义首页', exact: true })); }
const decimal = value => Number(value.replaceAll(',', ''));
let expectedPrice;
try {
  await page.goto(origin);
  await visible(page.getByRole('heading', { name: '欢迎登录' }));
  await step('登录本地候选', '使用独立本地账号，展示登录页与真实 Cookie 会话。', async () => {
    await type(page.getByRole('textbox', { name: /请输入带有后缀的用户名/ }), credentials.username);
    await click(page.getByLabel('请输入密码', { exact: true }));
    await page.getByLabel('请输入密码', { exact: true }).fill(credentials.password);
    await click(page.getByRole('link', { name: '登录', exact: true }));
    await visible(page.getByRole('button', { name: '自定义首页', exact: true }));
  });
  await step('首页与待办', '查看首页卡片，展开和收起更多待办。', async () => {
    await click(page.getByRole('button', { name: '展开更多待办', exact: true }));
    await visible(page.getByRole('button', { name: '收起待办', exact: true }));
    await linger();
    await click(page.getByRole('button', { name: '收起待办', exact: true }));
  });
  await step('数据周期与趋势图', '切换本周、本月和排课点名／出勤率图表。', async () => {
    const overview = page.locator('[data-panel-title="数据概览"]');
    for (const label of ['本周', '本月', '今日']) {
      await click(overview.getByRole('button', { name: label, exact: true }));
      assert.equal(await overview.getByRole('button', { name: label, exact: true }).getAttribute('aria-pressed'), 'true');
      await linger();
    }
    for (const label of ['排课点名', '出勤率', '实收趋势']) { await click(page.getByRole('button', { name: label, exact: true })); await linger(); }
  });
  await step('背景选择与首页草稿', '查看背景选项和自定义卡片；取消草稿，不写入偏好。', async () => {
    await click(page.getByRole('button', { name: '换背景', exact: true }));
    await visible(page.getByText('更换首页背景', { exact: true })); await linger();
    await click(page.getByRole('button', { name: '换背景', exact: true }));
    await click(page.getByRole('button', { name: '自定义首页', exact: true }));
    await click(page.locator('[data-panel-title="快捷操作"]').getByRole('button', { name: '配置', exact: true }));
    const picker = page.getByRole('dialog', { name: '配置快捷操作', exact: true });
    await type(picker.getByRole('textbox', { name: '搜索功能名称', exact: true }), '报名');
    await visible(picker.getByText('全部功能', { exact: true })); await linger();
    await click(picker.getByRole('button', { name: '取消', exact: true }));
    await click(page.getByRole('button', { name: '添加卡片', exact: true }));
    await visible(page.getByRole('dialog')); await linger();
    await click(page.getByRole('dialog').locator('header').getByRole('button', { name: '关闭', exact: true }));
    await click(page.locator('.edit-footer').getByRole('button', { name: '取消', exact: true }));
    await visible(page.getByRole('button', { name: '自定义首页', exact: true }));
  });
  await step('学员列表与分页', '进入真实 MySQL 学员列表，翻页并返回第一页。', async () => {
    await click(page.getByRole('button', { name: '学员信息管理', exact: true }));
    await visible(page.locator('.student-name').first());
    await click(page.getByRole('button', { name: '下一页', exact: true }));
    await visible(page.getByText(/第 2 \/ /)); await linger();
    await click(page.getByRole('button', { name: '上一页', exact: true }));
    await visible(page.getByText(/第 1 \/ /));
  });
  await step('查询与空结果', '输入无匹配关键词，看到空结果，再清空条件查询。', async () => {
    await type(page.getByRole('textbox', { name: '学员姓名及首字母/学号/电话', exact: true }), 'rebuildnomatch20261012');
    await click(page.getByRole('link', { name: '查询', exact: true }));
    await visible(page.locator('.students-empty')); await linger();
    await click(page.getByRole('link', { name: '重置', exact: true }));
    await click(page.getByRole('link', { name: '查询', exact: true }));
    await visible(page.locator('.student-name').first());
  });
  await step('学员详情与展开', '查询已采集详情的学员，打开基本信息并展开。', async () => {
    await type(page.getByRole('textbox', { name: '学员姓名及首字母/学号/电话', exact: true }), detail.name);
    await click(page.getByRole('link', { name: '查询', exact: true }));
    await visible(page.getByRole('button', { name: detail.name, exact: true }));
    const response = await page.request.get(origin + '/api/students?search=' + encodeURIComponent(detail.name));
    assert.equal(response.status(), 200);
    const { rows } = await response.json(); const index = rows.findIndex(row => row.id === detail.id);
    assert.ok(index >= 0, 'Captured detail student must exist in the current query');
    await click(page.locator('.student-name').nth(index));
    await visible(page.getByRole('heading', { name: detail.name, exact: true }));
    await click(page.getByRole('link', { name: '展开', exact: true }));
    await visible(page.getByRole('heading', { name: '基本信息', exact: true })); await linger();
    await click(page.getByRole('link', { name: '收起', exact: true }));
  });
  await step('学费、课消和积分页签', '展示已观察的默认表格；筛选和写入仍未完成。', async () => {
    for (const name of ['学费', '课消明细', '积分']) {
      await click(page.locator('.student-detail-tabs li').filter({ hasText: new RegExp('^' + name + '$') }));
      await visible(page.locator('.student-tab-content table')); await linger();
    }
    await click(page.getByRole('link', { name: '返回', exact: true }));
    await visible(page.locator('.students-query'));
  });
  await step('新学员报名表', '进入报名页，展示字段与年级选项；不提交报名。', async () => {
    await home(); await click(page.getByRole('button', { name: '新学员报名', exact: true }));
    await visible(page.getByRole('textbox', { name: '姓名', exact: true }));
    assert.ok(await page.getByRole('combobox', { name: '年级', exact: true }).locator('option').count() > 1);
  });
  await step('课程查询和重置', '打开课程目录，查询空结果，再恢复代表性课程列表。', async () => {
    await click(page.getByRole('button', { name: '选课', exact: true }));
    const dialog = page.getByRole('dialog', { name: '选择课程', exact: true });
    await visible(dialog.locator('tbody input[type=checkbox]').first());
    await type(dialog.getByRole('textbox', { name: '请输入课程名称', exact: true }), 'rebuildnomatch20261012');
    await click(dialog.getByRole('button', { name: /查询/ }));
    await visible(dialog.getByText('未查找到相关数据', { exact: true })); await linger();
    await click(dialog.getByRole('button', { name: '重置', exact: true }));
    await visible(dialog.locator('tbody input[type=checkbox]').first());
  });
  await step('课程勾选与清空', '勾选后出现在已选列表，清空后数量归零，再确定入表。', async () => {
    const dialog = page.getByRole('dialog', { name: '选择课程', exact: true });
    await check(dialog.locator('tbody input[type=checkbox]').first());
    await visible(dialog.getByText(/已选择：\s*1/)); await linger();
    await click(dialog.getByRole('button', { name: '清空', exact: true }));
    await visible(dialog.getByText(/已选择：\s*0/)); await linger();
    await check(dialog.locator('tbody input[type=checkbox]').first());
    await click(dialog.getByRole('button', { name: '确定', exact: true }));
    await visible(page.getByRole('textbox', { name: '数量', exact: true }));
    expectedPrice = decimal(await page.locator('.enrollment-charge td').nth(3).innerText());
  });
  await step('数量与优惠金额联动', '复跑共同金额场景：数量 2、优惠 10，核对实际金额与失焦格式。', async () => {
    for (const scenario of amountBook.cases) {
      await type(page.getByRole('textbox', { name: '数量', exact: true }), scenario.quantity);
      await page.getByRole('textbox', { name: '数量', exact: true }).press('Tab');
      if (scenario.discount !== null) {
        await type(page.getByRole('textbox', { name: '优惠金额', exact: true }), scenario.discount);
        await page.getByRole('textbox', { name: '优惠金额', exact: true }).press('Tab');
      }
      const quantity = await page.getByRole('textbox', { name: '数量', exact: true }).inputValue();
      const discount = await page.getByRole('textbox', { name: '优惠金额', exact: true }).inputValue();
      assert.equal(quantity, scenario.expectedResult.quantity);
      assert.equal(discount, scenario.expectedResult.discount);
      const amount = page.locator('.enrollment-charge td').nth(9);
      const expected = (expectedPrice * Number(quantity) - Number(discount)).toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
      await equalText(amount, expected); await amount.scrollIntoViewIfNeeded(); await linger();
    }
    await click(page.getByRole('button', { name: '移除收费项目', exact: true }));
    await visible(page.getByText('请选择要收费的课程或物品', { exact: true }));
  });
  await step('物品选择与清空', '展示物品目录、空结果、勾选和清空，然后确认入表。', async () => {
    await click(page.getByRole('button', { name: '选物品', exact: true }));
    const dialog = page.getByRole('dialog', { name: '选择物品', exact: true });
    await visible(dialog.locator('tbody input[type=checkbox]').first());
    await type(dialog.getByRole('textbox', { name: '物品名称/编码', exact: true }), 'rebuildnomatch20261012');
    await click(dialog.getByRole('button', { name: /查询/ }));
    await visible(dialog.getByText('未找到相关记录。', { exact: true })); await linger();
    await click(dialog.getByRole('button', { name: '重置', exact: true }));
    await visible(dialog.locator('tbody input[type=checkbox]').first());
    await check(dialog.locator('tbody input[type=checkbox]').first());
    await visible(dialog.getByText(/已选择：\s*1/)); await linger();
    await click(dialog.getByRole('button', { name: '清空', exact: true }));
    await visible(dialog.getByText(/已选择：\s*0/));
    await check(dialog.locator('tbody input[type=checkbox]').first());
    await click(dialog.getByRole('button', { name: '确定', exact: true }));
    await visible(page.locator('.charge-stored'));
    assert.equal(await page.locator('.charge-stored td').nth(4).innerText(), '1');
  });
  await step('恢复与交付边界', '刷新丢弃未提交表单。完整收费、订单、权限与严格视觉仍未完成。', async () => {
    await page.reload();
    await visible(page.getByText('请选择要收费的课程或物品', { exact: true }));
    await home();
  });
  await caption('巡演完成 · ' + results.length + ' 个本地场景通过', '你可以手动继续查看。完整 1:1、收费提交与持久化尚未完成；关闭此浏览器结束预览。', true);
  await writeFile(resolve(out, 'result.json'), JSON.stringify({ status: 'pass', scope: 'local candidate feature showcase only', results }, null, 2));
  console.log('巡演完成；这不是原版与候选的完整 1:1 验收。');
  if (!once) await previewClosed;
} catch (error) {
  const safe = String(error).replaceAll(credentials.password, '[redacted]').replaceAll(credentials.username, '[local-account]');
  const interrupted = page.isClosed() || !browser.isConnected();
  await writeFile(resolve(out, 'result.json'), JSON.stringify({ status: interrupted ? 'interrupted' : 'fail', current, error: safe, results }, null, 2));
  if (!page.isClosed()) {
    await caption('巡演停在：' + current, '此步骤没有通过，未跳过失败。详见 private/preview/tours/ 下回执。', true).catch(() => {});
    await page.screenshot({ path: resolve(out, 'failure.png') }).catch(() => {});
  }
  if (interrupted) console.log('预览浏览器已关闭，巡演提前结束。');
  else { console.error(safe); process.exitCode = 1; }
  if (!interrupted && !once && !headless) await previewClosed;
} finally {
  await context.request.post(origin + '/api/auth/logout', { data: {}, headers: { Origin: origin } }).catch(() => {});
  await browser.close();
}
