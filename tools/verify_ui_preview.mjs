// Invoke from the persistent Playwright session, passing its existing page.
// The QA server renders native C frames and links synthetic storage adapters.
import assert from 'node:assert/strict';
import { mkdir, writeFile } from 'node:fs/promises';

export async function verifyUI({ page, url, output }) {
  await mkdir(output, { recursive: true });
  const checks = [], browserErrors = [];
  const onError = error => browserErrors.push(String(error));
  const onConsole = message => { if (message.type() === 'error') onError(message.text()); };
  page.on('pageerror', onError);
  page.on('console', onConsole);
  const state = () => page.evaluate(() => window.qaState());
  const check = (name, condition) => { assert.ok(condition, name); checks.push(name); };
  const capture = name => page.screenshot({ path: `${output}/final-interactive-${name}.png` });
  async function press(key) {
    const previous = await state();
    await page.keyboard.press(key);
    await page.waitForFunction(frame => window.qaState().exited ||
      (window.qaState().frame > frame && Number(document.querySelector('canvas').dataset.frame) === window.qaState().frame), previous.frame);
    return state();
  }
  async function down(count) { for (let i = 0; i < count; i++) await press('ArrowDown'); }
  async function copySelection() { await press('t'); await down(1); return press('Enter'); }
  async function drawerHighlights() {
    return page.evaluate(() => {
      const ctx=document.querySelector('canvas').getContext('2d');
      return [205,287,369,480].map(y=>{const p=ctx.getImageData(42,y,1,1).data;return p[0]===58 && p[1]===55 && p[2]===57;});
    });
  }
  const onlyRow = (rows,index) => rows.every((on,i)=>on===(i===index));
  async function reset() {
    const response = await page.request.post(`${url}/api/reset`);
    assert.ok(response.ok(), 'Synthetic host resets');
    await page.goto(`${url}/explorer?clean`);
    await page.waitForFunction(() => document.querySelector('canvas').dataset.ready === 'true');
  }
  async function hotplug(command) {
    await page.evaluate(command => window.qaHotplug(command), command);
    return state();
  }
  try {
    await page.setViewportSize({ width: 1920, height: 1080 });
    await reset();
    check('Phone grid opens', (await state()).view === 1);
    check('Grid down moves four', (await press('ArrowDown')).selected === 4);
    await press('ArrowUp');
    check('Folder opens', (await press('Enter')).depth === 1);
    check('Folder back returns to root', (await press('Escape')).depth === 0);
    check('Grid up clamps at first tile', (await press('ArrowUp')).selected === 0);
    check('List view opens', (await press('v')).list === 1);
    await capture('list');
    check('List down moves one', (await press('ArrowDown')).selected === 1);
    check('Grid restores list selection', (await press('v')).selected === 1);
    await press('ArrowLeft');
    check('Options opens', (await press('t')).view === 7);
    await down(3);
    const before = await state(), after = await press('Enter');
    check('Disabled Rename keeps menu open and sends no protocol command', after.view === 7 && after.menu_index === 3 && before.mtp_writes === after.mtp_writes);
    await capture('rename-disabled');
    await press('Escape');
    const idle=await state();
    const square=await press('c');
    check('Square does not copy or send a protocol command', square.clipboard === 0 && square.view===idle.view && square.mtp_writes===idle.mtp_writes);
    const r3=await press('Delete');
    check('R3 does not open deletion or send a protocol command', r3.view===idle.view && r3.mtp_writes===idle.mtp_writes);
    check('Options Copy still sets clipboard', (await copySelection()).clipboard === 1);
    await press('t');
    await down(5);
    check('Properties opens', (await press('Enter')).view === 6);
    await capture('properties');
    await press('Escape');
    await press('t'); await down(4);
    check('Options Delete requires review', (await press('Enter')).view === 9);
    await capture('delete-review');
    check('Delete review cancels', (await press('Escape')).view === 1);
    await copySelection();
    await press('ArrowLeft');
    check('Drawer has one Phone highlight', onlyRow(await drawerHighlights(),0));
    await press('ArrowDown');
    check('Drawer highlight moves exclusively to USB', onlyRow(await drawerHighlights(),1));
    await press('ArrowRight');
    check('USB opens from device rail', (await state()).location === 2);
    const nativeIdle=await state();await press('c');const nativeR3=await press('Delete');
    check('Square and R3 are inactive on native storage too', nativeR3.view===nativeIdle.view && nativeR3.clipboard===nativeIdle.clipboard && nativeR3.selected===nativeIdle.selected);
    await press('t');
    await down(6);
    check('Paste requires review', (await press('Enter')).view === 9);
    await capture('paste-review');
    check('Review confirmation enters production progress', (await press('Enter')).progress === 2);
    check('X hides active progress', (await press('Enter')).hidden === 1);
    await capture('transfer-hidden');
    check('X restores active progress', (await press('Enter')).hidden === 0);
    await capture('transfer-visible');
    check('Circle leaves synthetic transfer', (await press('Escape')).progress === 0);
    await press('ArrowLeft');
    await press('ArrowDown');
    check('Internal storage opens', (await state()).location === 1);
    check('Drawer highlight moves exclusively to Internal Storage', onlyRow(await drawerHighlights(),2));
    await press('ArrowDown');
    check('Settings remains reachable after devices', (await state()).settings === 1);
    check('Only Settings is highlighted; active storage loses highlight', onlyRow(await drawerHighlights(),3));
    await capture('settings-focus');
    await press('ArrowUp');
    check('Up from Settings restores exclusive storage focus', onlyRow(await drawerHighlights(),2));
    await press('ArrowDown');
    await press('Escape');
    check('Closing drawer restores active storage highlight', onlyRow(await drawerHighlights(),2) && (await state()).drawer===0);
    await press('ArrowLeft');await press('ArrowDown');
    check('Settings opens', (await press('Enter')).view === 10);
    check('Settings menu retains exclusive Settings highlight', onlyRow(await drawerHighlights(),3));
    await down(4);
    check('Diagnostics opens', (await press('Enter')).view === 4);
    await capture('diagnostics');
    check('Diagnostics returns to Settings', (await press('Escape')).view === 10);
    await press('ArrowDown');
    check('Controller guide opens', (await press('Enter')).view === 11);
    await capture('controls');
    await press('Escape');
    await press('Escape');
    await press('Escape');
    check('Touchpad refresh retains native location', (await press('r')).location === 1);
    await reset();
    await press('Enter');
    await press('ArrowLeft');
    await press('ArrowDown');
    await press('ArrowUp');
    await press('ArrowRight');
    check('Phone folder resumes after switching devices', (await state()).depth === 1);
    await press('t');
    check('Phone unplug during Options falls back to internal storage', (await hotplug('p0')).location === 1);
    await capture('phone-removed');
    await hotplug('p1');
    await press('ArrowLeft');
    await press('ArrowUp');
    await press('ArrowRight');
    check('USB remains selectable after reconnect', (await state()).location === 2);
    check('Active USB unplug falls back to internal storage', (await hotplug('u0')).location === 1);
    await capture('usb-removed');
    const fit = await page.evaluate(() => ({ width: innerWidth, height: innerHeight,
      scrollWidth: document.documentElement.scrollWidth, scrollHeight: document.documentElement.scrollHeight,
      canvas: document.querySelector('canvas').getBoundingClientRect().toJSON() }));
    check('Full native surface fits with no scrolling', fit.width === fit.scrollWidth && fit.height === fit.scrollHeight && fit.canvas.x === 0 && fit.canvas.y === 0 && fit.canvas.width === 1920 && fit.canvas.height === 1080);
    await press('ArrowLeft');
    await press('ArrowDown');
    await press('Enter');
    await down(6);
    check('Settings Exit ends synthetic explorer', (await press('Enter')).exited === true);
    check('No browser console or page errors', browserErrors.length === 0);
    const result = { checks, browserErrors, viewport: fit,
      notes: 'Production controller/renderer; synthetic devices and progress. Native mutation adapter is not linked. This does not verify PS4 behavior.' };
    await writeFile(`${output}/final-functional-results.json`, JSON.stringify(result, null, 2) + '\n');
    return result;
  } finally {
    page.off('pageerror', onError);
    page.off('console', onConsole);
  }
}
