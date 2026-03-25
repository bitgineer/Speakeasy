/**
 * End-to-end tests for critical hotspot flows identified in blast radius analysis.
 *
 * Tests cover the highest-risk execution flows:
 * - Hotkey-triggered recording flows (proc_0, proc_1, proc_2, proc_3)
 * - Push-to-talk mode (proc_39, proc_40, proc_120, proc_121)
 * - Toggle mode (proc_42, proc_72)
 * - Setup and registration flows (proc_30-32, proc_119-120)
 */

import { test, expect } from './fixtures/electron-app';

test.describe('Hotspot: Hotkey Recording Flows', () => {
    test.beforeEach(async ({ page }) => {
        // Ensure app is loaded and model is ready
        await page.waitForSelector('text=Dashboard', { timeout: 10000 });
    });

    /**
     * Test proc_0: HandleStart → TranscriptionRecord
     * Test proc_1: HandleStart → Delete
     *
     * Critical flow: User starts recording via hotkey
     */
    test('should start recording via hotkey and create transcription record', async ({ page }) => {
        // Navigate to dashboard
        await expect(page).toHaveURL(/.*#\//);

        // Wait for model to be loaded
        await page.waitForSelector('text=Model: loaded', { timeout: 15000 });

        // Trigger start recording via IPC (simulating hotkey)
        const recordingStarted = await page.evaluate(() => {
            return window.electron.ipcRenderer.invoke('transcribe:start');
        });

        expect(recordingStarted).toBeTruthy();

        // Verify UI shows recording indicator
        await expect(page.locator('[data-testid="recording-indicator"]')).toBeVisible({ timeout: 5000 });

        // Verify state change to RECORDING
        const state = await page.evaluate(() => {
            return window.electron.ipcRenderer.invoke('transcribe:state');
        });

        expect(state).toBe('RECORDING');

        // Take screenshot
        await page.screenshot({ path: 'test-results/screenshots/hotkey-recording-start.png' });
    });

    /**
     * Test proc_2: HandleStop → TranscriptionRecord
     * Test proc_3: HandleStop → Delete
     *
     * Critical flow: User stops recording via hotkey and gets transcription
     */
    test('should stop recording via hotkey and generate transcription', async ({ page }) => {
        // Start recording first
        await page.evaluate(() => window.electron.ipcRenderer.invoke('transcribe:start'));
        await expect(page.locator('[data-testid="recording-indicator"]')).toBeVisible();

        // Wait for some "recording" time
        await page.waitForTimeout(2000);

        // Stop recording
        const result = await page.evaluate(() => {
            return window.electron.ipcRenderer.invoke('transcribe:stop');
        });

        expect(result).toBeDefined();
        expect(result.text).toBeDefined();

        // Verify UI shows transcription result
        await expect(page.locator('[data-testid="transcription-result"]')).toBeVisible({ timeout: 10000 });

        // Verify recording indicator is hidden
        await expect(page.locator('[data-testid="recording-indicator"]')).not.toBeVisible();

        // Take screenshot
        await page.screenshot({ path: 'test-results/screenshots/hotkey-recording-stop.png' });
    });

    /**
     * Test proc_8: CancelRecording → TranscriptionRecord
     * Test proc_9: CancelRecording → Delete
     *
     * Critical flow: User cancels recording mid-operation
     */
    test('should cancel recording without generating transcription', async ({ page }) => {
        // Start recording
        await page.evaluate(() => window.electron.ipcRenderer.invoke('transcribe:start'));
        await expect(page.locator('[data-testid="recording-indicator"]')).toBeVisible();

        // Cancel recording
        await page.evaluate(() => window.electron.ipcRenderer.invoke('transcribe:cancel'));

        // Verify recording indicator is hidden
        await expect(page.locator('[data-testid="recording-indicator"]')).not.toBeVisible({ timeout: 2000 });

        // Verify no transcription result appeared
        const transcriptionVisible = await page.locator('[data-testid="transcription-result"]').isVisible();
        expect(transcriptionVisible).toBe(false);

        // Verify state is back to READY
        const state = await page.evaluate(() => {
            return window.electron.ipcRenderer.invoke('transcribe:state');
        });

        expect(state).toBe('READY');
    });
});

test.describe('Hotspot: Push-to-Talk Mode', () => {
    test.beforeEach(async ({ page }) => {
        await page.waitForSelector('text=Dashboard', { timeout: 10000 });
    });

    /**
     * Test proc_120: RegisterGlobalHotkey → ParseHotkeyToKeycodes
     * Test proc_121: RegisterGlobalHotkey → AllPttKeysPressed
     *
     * Critical flow: Push-to-talk hotkey registration and key press detection
     */
    test('should register push-to-talk hotkey and detect key press', async ({ page }) => {
        // Navigate to settings
        await page.click('text=Settings');
        await expect(page).toHaveURL(/.*#\/settings/);

        // Set hotkey mode to push-to-talk
        await page.selectOption('[data-testid="hotkey-mode-select"]', 'push-to-talk');

        // Set hotkey combination
        const hotkeyInput = page.locator('[data-testid="hotkey-input"]');
        await hotkeyInput.click();

        // Simulate key press
        await page.keyboard.down('Control');
        await page.keyboard.down('Shift');
        await page.keyboard.press('Space');
        await page.keyboard.up('Shift');
        await page.keyboard.up('Control');

        // Verify hotkey was registered
        await expect(hotkeyInput).toHaveValue('Ctrl+Shift+Space');

        // Save settings
        await page.click('[data-testid="save-settings-button"]');

        // Verify success message
        await expect(page.locator('text=Settings saved')).toBeVisible({ timeout: 5000 });

        // Take screenshot
        await page.screenshot({ path: 'test-results/screenshots/push-to-talk-registered.png' });
    });

    /**
     * Test proc_39: RegisterGlobalHotkey → TranscriptionRecord
     * Test proc_40: RegisterGlobalHotkey → Delete
     *
     * Critical flow: Push-to-talk key press triggers recording
     */
    test('should trigger recording when push-to-talk keys are pressed', async ({ page }) => {
        // Set push-to-talk mode
        await page.click('text=Settings');
        await page.selectOption('[data-testid="hotkey-mode-select"]', 'push-to-talk');
        await page.click('[data-testid="save-settings-button"]');

        // Return to dashboard
        await page.click('text=Dashboard');

        // Simulate push-to-talk key press (hold)
        const recordingPromise = page.waitForSelector('[data-testid="recording-indicator"]', { timeout: 5000 });

        await page.keyboard.down('Control');
        await page.keyboard.down('Shift');
        await page.keyboard.down('Space');

        // Verify recording started
        await recordingPromise;
        await expect(page.locator('[data-testid="recording-indicator"]')).toBeVisible();

        // Release keys to stop recording
        await page.keyboard.up('Space');
        await page.keyboard.up('Shift');
        await page.keyboard.up('Control');

        // Verify transcription appears
        await expect(page.locator('[data-testid="transcription-result"]')).toBeVisible({ timeout: 10000 });

        // Take screenshot
        await page.screenshot({ path: 'test-results/screenshots/push-to-talk-recording.png' });
    });
});

test.describe('Hotspot: Toggle Mode', () => {
    test.beforeEach(async ({ page }) => {
        await page.waitForSelector('text=Dashboard', { timeout: 10000 });
    });

    /**
     * Test proc_42: RegisterGlobalHotkey → UpdatePosition
     * Test proc_72: RegisterGlobalHotkey → HideRecordingIndicator
     *
     * Critical flow: Toggle mode hotkey registration and toggle behavior
     */
    test('should register toggle mode and toggle recording on/off', async ({ page }) => {
        // Navigate to settings
        await page.click('text=Settings');

        // Set hotkey mode to toggle
        await page.selectOption('[data-testid="hotkey-mode-select"]', 'toggle');

        // Set hotkey
        const hotkeyInput = page.locator('[data-testid="hotkey-input"]');
        await hotkeyInput.click();
        await page.keyboard.press('F9');

        // Verify hotkey
        await expect(hotkeyInput).toHaveValue('F9');

        // Save
        await page.click('[data-testid="save-settings-button"]');
        await expect(page.locator('text=Settings saved')).toBeVisible();

        // Return to dashboard
        await page.click('text=Dashboard');

        // First press: start recording
        await page.keyboard.press('F9');
        await expect(page.locator('[data-testid="recording-indicator"]')).toBeVisible({ timeout: 5000 });

        // Second press: stop recording
        await page.keyboard.press('F9');
        await expect(page.locator('[data-testid="recording-indicator"]')).not.toBeVisible({ timeout: 5000 });

        // Verify transcription appeared
        await expect(page.locator('[data-testid="transcription-result"]')).toBeVisible({ timeout: 10000 });

        // Take screenshot
        await page.screenshot({ path: 'test-results/screenshots/toggle-mode.png' });
    });
});

test.describe('Hotspot: IPC Handler Integration', () => {
    /**
     * Test proc_30: SetupIpcHandlers → CreateTrayIcon
     * Test proc_31: SetupIpcHandlers → GetMainWindow
     * Test proc_32: SetupIpcHandlers → Send
     *
     * Critical flow: IPC handlers correctly route hotkey events
     */
    test('should route IPC events from main to renderer correctly', async ({ page }) => {
        // Listen for state change events
        const stateChanges = [];

        await page.exposeFunction('captureStateChange', (state) => {
            stateChanges.push(state);
        });

        // Trigger start via IPC
        await page.evaluate(() => window.electron.ipcRenderer.invoke('transcribe:start'));

        // Wait for state change event
        await page.waitForTimeout(1000);

        // Verify state change was propagated
        const hasRecordingState = stateChanges.some(s => s === 'RECORDING');
        expect(hasRecordingState || stateChanges.length > 0).toBeTruthy();

        // Trigger stop
        await page.evaluate(() => window.electron.ipcRenderer.invoke('transcribe:stop'));

        // Wait for final state
        await page.waitForTimeout(2000);

        // Take screenshot
        await page.screenshot({ path: 'test-results/screenshots/ipc-integration.png' });
    });
});

test.describe('Hotspot: Hotkey Normalization and Parsing', () => {
    /**
     * Test proc_119: RegisterGlobalHotkey → NormalizeHotkey
     *
     * Critical flow: Hotkey parsing and normalization
     */
    test('should normalize various hotkey formats correctly', async ({ page }) => {
        // Navigate to settings
        await page.click('text=Settings');
        await expect(page).toHaveURL(/.*#\/settings/);

        const hotkeyInput = page.locator('[data-testid="hotkey-input"]');

        // Test various key combinations
        const testCases = [
            { keys: ['Control', 'a'], expected: 'Ctrl+A' },
            { keys: ['Alt', 'Shift', 'F'], expected: 'Alt+Shift+F' },
            { keys: ['Meta', 'Space'], expected: /Meta\+Space|Cmd\+Space/ },  // Platform-dependent
        ];

        for (const testCase of testCases) {
            await hotkeyInput.click();

            // Press keys
            for (const key of testCase.keys) {
                if (key.length > 1) {
                    await page.keyboard.down(key);
                } else {
                    await page.keyboard.press(key);
                }
            }

            // Release modifier keys
            for (const key of testCase.keys) {
                if (key.length > 1) {
                    await page.keyboard.up(key);
                }
            }

            // Verify normalized format
            const value = await hotkeyInput.inputValue();

            if (typeof testCase.expected === 'string') {
                expect(value).toBe(testCase.expected);
            } else {
                expect(value).toMatch(testCase.expected);
            }

            // Clear for next test
            await hotkeyInput.clear();
        }

        // Take screenshot
        await page.screenshot({ path: 'test-results/screenshots/hotkey-normalization.png' });
    });
});

test.describe('Hotspot: WebSocket State Propagation', () => {
    /**
     * Test proc_13: Transcribe → Broadcast
     * Test proc_18: Transcribe_stop → Broadcast
     * Test proc_19: Load_model → Broadcast
     *
     * Critical flow: WebSocket broadcasts state changes to UI
     */
    test('should broadcast state changes via WebSocket to UI', async ({ page }) => {
        const wsMessages = [];

        // Monitor WebSocket messages
        await page.evaluate(() => {
            // Store original WebSocket
            const OriginalWebSocket = window.WebSocket;

            // Monkey-patch WebSocket to capture messages
            window.WebSocket = function(...args) {
                const ws = new OriginalWebSocket(...args);

                ws.addEventListener('message', (event) => {
                    window['__ws_messages'] = window['__ws_messages'] || [];
                    window['__ws_messages'].push(event.data);
                });

                return ws;
            };
        });

        // Trigger state changes
        await page.evaluate(() => window.electron.ipcRenderer.invoke('transcribe:start'));
        await page.waitForTimeout(1000);

        await page.evaluate(() => window.electron.ipcRenderer.invoke('transcribe:stop'));
        await page.waitForTimeout(2000);

        // Check captured messages
        const messages = await page.evaluate(() => window['__ws_messages'] || []);

        // Verify state change messages were received
        expect(messages.length).toBeGreaterThan(0);

        // Parse and check message types
        const parsedMessages = messages.map(m => {
            try {
                return JSON.parse(m);
            } catch {
                return null;
            }
        }).filter(Boolean);

        const hasStateChange = parsedMessages.some(m => m.type === 'state_change' || m.state);
        expect(hasStateChange).toBeTruthy();

        // Take screenshot
        await page.screenshot({ path: 'test-results/screenshots/websocket-broadcast.png' });
    });
});

test.describe('Hotspot: Recording State Consistency', () => {
    /**
     * Test proc_60: Transcribe_stop → _set_state
     * Test proc_103: Transcribe_start → _set_state
     * Test proc_113: Reload_model → _set_state
     *
     * Critical flow: State machine maintains consistency through operations
     */
    test('should maintain state consistency through rapid operations', async ({ page }) => {
        const states = [];

        // Monitor state changes
        await page.exposeFunction('trackState', async () => {
            const state = await window.electron.ipcRenderer.invoke('transcribe:state');
            states.push({ time: Date.now(), state });
            return state;
        });

        // Rapid start/stop cycles
        for (let i = 0; i < 3; i++) {
            await page.evaluate(() => window['trackState']());
            await page.evaluate(() => window.electron.ipcRenderer.invoke('transcribe:start'));

            await page.waitForTimeout(500);
            await page.evaluate(() => window['trackState']());

            await page.evaluate(() => window.electron.ipcRenderer.invoke('transcribe:stop'));
            await page.waitForTimeout(1000);
            await page.evaluate(() => window['trackState']());
        }

        // Verify state transitions were valid
        // Should not see ERROR state
        const hasError = states.some(s => s.state === 'ERROR');
        expect(hasError).toBe(false);

        // Final state should be READY or IDLE
        const finalState = states[states.length - 1].state;
        expect(['READY', 'IDLE']).toContain(finalState);

        // Take screenshot
        await page.screenshot({ path: 'test-results/screenshots/state-consistency.png' });
    });
});
