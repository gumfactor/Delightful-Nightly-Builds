const { test, expect } = require('@playwright/test');
const path = require('path');

const page_url = 'file://' + path.resolve(__dirname, '..', 'index.html');

test.beforeEach(async ({ page }) => {
  await page.goto(page_url);
  await expect(page.getByTestId('m-rms')).not.toHaveText('–');
});

test('loads with the focus preset selected and plausible level readouts', async ({ page }) => {
  await expect(page.getByTestId('preset-focus')).toHaveAttribute('aria-pressed', 'true');
  const rms = parseFloat(await page.getByTestId('m-rms').textContent());
  expect(rms).toBeCloseTo(-40, 0);
  const aWeighted = parseFloat(await page.getByTestId('m-a').textContent());
  expect(aWeighted).toBeLessThan(rms + 1);
});

test('spectrum canvas is actually drawn', async ({ page }) => {
  const painted = await page.getByTestId('spectrum').evaluate((canvas) => {
    const data = canvas.getContext('2d').getImageData(0, 0, canvas.width, canvas.height).data;
    for (let i = 3; i < data.length; i += 4) if (data[i] !== 0) return true;
    return false;
  });
  expect(painted).toBe(true);
});

test('choosing a preset updates the sliders and the spectrum readouts', async ({ page }) => {
  const before = await page.getByTestId('m-a').textContent();
  await page.getByTestId('preset-sleep').click();
  await expect(page.getByTestId('preset-sleep')).toHaveAttribute('aria-pressed', 'true');
  await expect(page.getByTestId('out-slope')).toContainText('brown');
  await expect(page.getByTestId('out-lp')).toHaveText('1200 Hz');
  await expect(page.getByTestId('m-a')).not.toHaveText(before);
});

test('moving a slider clears the preset highlight and relabels the colour', async ({ page }) => {
  await page.getByTestId('slope').fill('0');
  await expect(page.getByTestId('out-slope')).toContainText('white');
  await expect(page.getByTestId('preset-focus')).toHaveAttribute('aria-pressed', 'false');
});

test('tinnitus preset enables the notch and shows its centre frequency', async ({ page }) => {
  await page.getByTestId('preset-tinnitus').click();
  await expect(page.getByTestId('notch-on')).toBeChecked();
  await expect(page.getByTestId('out-notch-freq')).toHaveText('4.00 kHz');
});

test('pitch match centres the notch on the chosen test tone', async ({ page }) => {
  await page.getByTestId('pitch').fill('500');
  const pitchText = await page.getByTestId('out-pitch').textContent();
  await page.getByTestId('pitch-apply').click();
  await expect(page.getByTestId('notch-on')).toBeChecked();
  await expect(page.getByTestId('out-notch-freq')).toHaveText(pitchText);
  await expect(page.getByTestId('status')).toContainText('Notch centred');
});

test('volume slider shows dBFS and changes the meters one-for-one', async ({ page }) => {
  await page.getByTestId('level').fill('-30');
  await expect(page.getByTestId('out-level')).toHaveText('-30 dBFS');
  await expect(page.getByTestId('m-rms')).toHaveText('-30.0');
});

test('play and stop toggle the transport state', async ({ page }) => {
  await page.getByTestId('play').click();
  await expect(page.getByTestId('play')).toHaveAttribute('data-state', 'playing');
  await page.getByTestId('timer').selectOption('15');
  await expect(page.getByTestId('timer-left')).toContainText('left');
  await page.getByTestId('play').click();
  await expect(page.getByTestId('play')).toHaveAttribute('data-state', 'stopped');
  await expect(page.getByTestId('timer-left')).toHaveText('');
});

test('share link encodes the current sound and a fresh page restores it', async ({ page }) => {
  await page.getByTestId('preset-waves').click();
  await page.getByTestId('share').click();
  const hash = await page.evaluate(() => location.hash);
  expect(hash.length).toBeGreaterThan(10);
  await page.goto(page_url + hash);
  await page.reload();
  await expect(page.getByTestId('out-lp')).toHaveText('2500 Hz');
  await expect(page.getByTestId('out-slope')).toContainText('brown');
});

test('a corrupt share link falls back to the default sound instead of breaking', async ({ page }) => {
  await page.goto(page_url + '#%7Bbroken');
  await page.reload();
  await expect(page.getByTestId('preset-focus')).toHaveAttribute('aria-pressed', 'true');
});

test('seamless-loop export downloads a valid stereo WAV', async ({ page }) => {
  const [download] = await Promise.all([page.waitForEvent('download'), page.getByTestId('export-loop').click()]);
  expect(download.suggestedFilename()).toBe('noise-lab-loop.wav');
  const stream = await download.createReadStream();
  const chunks = [];
  for await (const chunk of stream) chunks.push(chunk);
  const bytes = Buffer.concat(chunks);
  expect(bytes.toString('ascii', 0, 4)).toBe('RIFF');
  expect(bytes.readUInt16LE(22)).toBe(2);
  expect(bytes.length).toBe(44 + (1 << 18) * 4);
  await expect(page.getByTestId('status')).toContainText('Exported loop');
});

test('page does not scroll sideways at phone width', async ({ page }) => {
  const overflow = await page.evaluate(() => document.documentElement.scrollWidth - window.innerWidth);
  expect(overflow).toBeLessThanOrEqual(0);
});
