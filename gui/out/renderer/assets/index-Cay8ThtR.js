const __vite__mapDeps=(i,m=__vite__mapDeps,d=(m.f||(m.f=["./Dashboard-Coj9-nEc.js","./vendor-CCKbG8cq.js","./tanstack-DLTSNxug.js","./ExportDialog-B_ehTTyr.js","./BatchTranscription-B5hZRYSX.js","./Stats-Kfjc8hAj.js","./RecordingIndicator-TJhk5iT8.js","./ModelSettings-DVI8vVqS.js","./useKeyboardShortcuts-8hu33O7_.js","./AudioSettings-Drc6FVXY.js","./HotkeySettings-DbmDktvh.js","./BehaviorSettings-B-GcEV1i.js","./AppearanceSettings-HzT1QAGH.js","./DataSettings-Dmw7asZB.js","./AboutSettings-R7zNTuGh.js"])))=>i.map(i=>d[i]);
import { r as reactExports, a as reactDomExports, c as create, u as useLocation, L as Link, H as HashRouter, R as Routes, b as Route, d as useNavigate, N as Navigate, e as React } from "./vendor-CCKbG8cq.js";
var jsxRuntime = { exports: {} };
var reactJsxRuntime_production_min = {};
/**
 * @license React
 * react-jsx-runtime.production.min.js
 *
 * Copyright (c) Facebook, Inc. and its affiliates.
 *
 * This source code is licensed under the MIT license found in the
 * LICENSE file in the root directory of this source tree.
 */
var f = reactExports, k = Symbol.for("react.element"), l = Symbol.for("react.fragment"), m$1 = Object.prototype.hasOwnProperty, n = f.__SECRET_INTERNALS_DO_NOT_USE_OR_YOU_WILL_BE_FIRED.ReactCurrentOwner, p = { key: true, ref: true, __self: true, __source: true };
function q(c, a, g) {
  var b, d = {}, e = null, h = null;
  void 0 !== g && (e = "" + g);
  void 0 !== a.key && (e = "" + a.key);
  void 0 !== a.ref && (h = a.ref);
  for (b in a) m$1.call(a, b) && !p.hasOwnProperty(b) && (d[b] = a[b]);
  if (c && c.defaultProps) for (b in a = c.defaultProps, a) void 0 === d[b] && (d[b] = a[b]);
  return { $$typeof: k, type: c, key: e, ref: h, props: d, _owner: n.current };
}
reactJsxRuntime_production_min.Fragment = l;
reactJsxRuntime_production_min.jsx = q;
reactJsxRuntime_production_min.jsxs = q;
{
  jsxRuntime.exports = reactJsxRuntime_production_min;
}
var jsxRuntimeExports = jsxRuntime.exports;
var createRoot;
var m = reactDomExports;
{
  createRoot = m.createRoot;
  m.hydrateRoot;
}
const scriptRel = function detectScriptRel() {
  const relList = typeof document !== "undefined" && document.createElement("link").relList;
  return relList && relList.supports && relList.supports("modulepreload") ? "modulepreload" : "preload";
}();
const assetsURL = function(dep, importerUrl) {
  return new URL(dep, importerUrl).href;
};
const seen = {};
const __vitePreload = function preload(baseModule, deps, importerUrl) {
  let promise = Promise.resolve();
  if (deps && deps.length > 0) {
    const links = document.getElementsByTagName("link");
    const cspNonceMeta = document.querySelector(
      "meta[property=csp-nonce]"
    );
    const cspNonce = cspNonceMeta?.nonce || cspNonceMeta?.getAttribute("nonce");
    promise = Promise.allSettled(
      deps.map((dep) => {
        dep = assetsURL(dep, importerUrl);
        if (dep in seen) return;
        seen[dep] = true;
        const isCss = dep.endsWith(".css");
        const cssSelector = isCss ? '[rel="stylesheet"]' : "";
        const isBaseRelative = !!importerUrl;
        if (isBaseRelative) {
          for (let i = links.length - 1; i >= 0; i--) {
            const link2 = links[i];
            if (link2.href === dep && (!isCss || link2.rel === "stylesheet")) {
              return;
            }
          }
        } else if (document.querySelector(`link[href="${dep}"]${cssSelector}`)) {
          return;
        }
        const link = document.createElement("link");
        link.rel = isCss ? "stylesheet" : scriptRel;
        if (!isCss) {
          link.as = "script";
        }
        link.crossOrigin = "";
        link.href = dep;
        if (cspNonce) {
          link.setAttribute("nonce", cspNonce);
        }
        document.head.appendChild(link);
        if (isCss) {
          return new Promise((res, rej) => {
            link.addEventListener("load", res);
            link.addEventListener(
              "error",
              () => rej(new Error(`Unable to preload CSS for ${dep}`))
            );
          });
        }
      })
    );
  }
  function handlePreloadError(err) {
    const e = new Event("vite:preloadError", {
      cancelable: true
    });
    e.payload = err;
    window.dispatchEvent(e);
    if (!e.defaultPrevented) {
      throw err;
    }
  }
  return promise.then((res) => {
    for (const item of res || []) {
      if (item.status !== "rejected") continue;
      handlePreloadError(item.reason);
    }
    return baseModule().catch(handlePreloadError);
  });
};
function createCache() {
  const store = /* @__PURE__ */ new Map();
  return {
    get(key) {
      const entry = store.get(key);
      if (!entry) return void 0;
      const now = Date.now();
      const isExpired = now - entry.timestamp > entry.ttl;
      if (isExpired) {
        store.delete(key);
        return void 0;
      }
      return entry.data;
    },
    set(key, data, ttl) {
      store.set(key, {
        data,
        timestamp: Date.now(),
        ttl
      });
    },
    invalidate(pattern) {
      if (pattern.endsWith("*")) {
        const prefix = pattern.slice(0, -1);
        const keysToDelete = [];
        for (const key of store.keys()) {
          if (key.startsWith(prefix)) {
            keysToDelete.push(key);
          }
        }
        keysToDelete.forEach((key) => store.delete(key));
      } else {
        store.delete(pattern);
      }
    },
    clear() {
      store.clear();
    }
  };
}
class PerformanceMonitor {
  measures = /* @__PURE__ */ new Map();
  isDevMode = false;
  /**
   * Mark the start of an operation
   */
  markStart(name) {
    if (!this.isDevMode) return;
    const markName = `${name}-start`;
    performance.mark(markName);
  }
  /**
   * Mark the end of an operation and create a measurement
   */
  markEnd(name) {
    if (!this.isDevMode) return null;
    const startMarkName = `${name}-start`;
    const endMarkName = `${name}-end`;
    try {
      performance.mark(endMarkName);
      performance.measure(name, startMarkName, endMarkName);
      const measure = performance.getEntriesByName(name, "measure")[0];
      const result = {
        name,
        duration: measure.duration,
        startTime: measure.startTime
      };
      this.measures.set(name, result);
      return result;
    } catch (error) {
      console.warn(`Failed to measure ${name}:`, error);
      return null;
    }
  }
  /**
   * Get a specific measurement by name
   */
  getMeasure(name) {
    if (!this.isDevMode) return void 0;
    return this.measures.get(name);
  }
  /**
   * Get all measurements
   */
  getAllMeasures() {
    if (!this.isDevMode) return [];
    return Array.from(this.measures.values());
  }
  /**
   * Log all measurements to console as a table
   */
  logMeasures() {
    if (!this.isDevMode) return;
    const measures = this.getAllMeasures();
    if (measures.length === 0) {
      console.log("No performance measurements recorded");
      return;
    }
    console.table(
      measures.map((m2) => ({
        Operation: m2.name,
        "Duration (ms)": m2.duration.toFixed(2),
        "Start Time (ms)": m2.startTime.toFixed(2)
      }))
    );
  }
  /**
   * Get current memory usage (Chrome/Chromium only)
   */
  getMemoryInfo() {
    if (!this.isDevMode) return null;
    const perf = performance;
    if (!perf.memory) {
      console.warn("performance.memory not available (Chrome/Chromium only)");
      return null;
    }
    return {
      usedJSHeapSize: perf.memory.usedJSHeapSize,
      totalJSHeapSize: perf.memory.totalJSHeapSize,
      jsHeapSizeLimit: perf.memory.jsHeapSizeLimit
    };
  }
  /**
   * Log memory usage to console
   */
  logMemory() {
    if (!this.isDevMode) return;
    const memory = this.getMemoryInfo();
    if (!memory) return;
    const usedMB = (memory.usedJSHeapSize / 1024 / 1024).toFixed(2);
    const totalMB = (memory.totalJSHeapSize / 1024 / 1024).toFixed(2);
    const limitMB = (memory.jsHeapSizeLimit / 1024 / 1024).toFixed(2);
    console.log(
      `Memory: ${usedMB}MB used / ${totalMB}MB allocated / ${limitMB}MB limit`
    );
  }
  /**
   * Clear all measurements
   */
  clear() {
    if (!this.isDevMode) return;
    this.measures.clear();
    performance.clearMarks();
    performance.clearMeasures();
  }
  /**
   * Check if dev mode is enabled
   */
  isEnabled() {
    return this.isDevMode;
  }
}
const perfMonitor = new PerformanceMonitor();
const DEFAULT_PORT = 8765;
const BASE_URL = `http://127.0.0.1:${DEFAULT_PORT}`;
class ApiClient {
  baseUrl;
  cache = createCache();
  constructor(baseUrl = BASE_URL) {
    this.baseUrl = baseUrl;
  }
  setPort(port) {
    this.baseUrl = `http://127.0.0.1:${port}`;
  }
  async request(endpoint, options = {}) {
    const url = `${this.baseUrl}${endpoint}`;
    const response = await fetch(url, {
      ...options,
      headers: {
        "Content-Type": "application/json",
        ...options.headers
      }
    });
    if (!response.ok) {
      const error = await response.text();
      throw new Error(`API Error (${response.status}): ${error}`);
    }
    return response.json();
  }
  async cachedRequest(endpoint, ttl) {
    const cached = this.cache.get(endpoint);
    if (cached !== void 0) {
      return cached;
    }
    const data = await this.request(endpoint);
    this.cache.set(endpoint, data, ttl);
    return data;
  }
  // Health
  async getHealth() {
    return this.request("/api/health");
  }
  // Transcription
  async startTranscription() {
    return this.request("/api/transcribe/start", {
      method: "POST"
    });
  }
  async stopTranscription(options = {}) {
    return this.request("/api/transcribe/stop", {
      method: "POST",
      body: JSON.stringify(options)
    });
  }
  async cancelTranscription() {
    return this.request("/api/transcribe/cancel", {
      method: "POST"
    });
  }
  // History
  async getHistory(params) {
    const searchParams = new URLSearchParams();
    if (params?.limit) searchParams.set("limit", String(params.limit));
    if (params?.offset) searchParams.set("offset", String(params.offset));
    if (params?.search) searchParams.set("search", params.search);
    const query = searchParams.toString();
    perfMonitor.markStart("api-get-history");
    try {
      return await this.request(
        `/api/history${query ? `?${query}` : ""}`
      );
    } finally {
      perfMonitor.markEnd("api-get-history");
    }
  }
  async getHistoryItem(id) {
    return this.request(`/api/history/${id}`);
  }
  async deleteHistoryItem(id) {
    return this.request(`/api/history/${id}`, {
      method: "DELETE"
    });
  }
  async getHistoryStats() {
    return this.request("/api/history/stats");
  }
  // Settings
  async getSettings() {
    return this.cachedRequest("/api/settings", 1 * 60 * 1e3);
  }
  async updateSettings(settings) {
    const result = await this.request("/api/settings", {
      method: "PUT",
      body: JSON.stringify(settings)
    });
    this.cache.invalidate("/api/settings");
    return result;
  }
  // Models
  async getModels() {
    perfMonitor.markStart("api-get-models");
    try {
      return await this.cachedRequest("/api/models", 5 * 60 * 1e3);
    } finally {
      perfMonitor.markEnd("api-get-models");
    }
  }
  async getModelsByType(type) {
    return this.request(`/api/models/${type}`);
  }
  async loadModel(request) {
    perfMonitor.markStart("api-load-model");
    try {
      const result = await this.request("/api/models/load", {
        method: "POST",
        body: JSON.stringify(request)
      });
      this.cache.invalidate("/api/models*");
      return result;
    } finally {
      perfMonitor.markEnd("api-load-model");
    }
  }
  async unloadModel() {
    const result = await this.request("/api/models/unload", {
      method: "POST"
    });
    this.cache.invalidate("/api/models*");
    return result;
  }
  async getModelRecommendation(needsTranslation = false) {
    return this.request(
      `/api/models/recommend?needs_translation=${needsTranslation}`
    );
  }
  async getDownloadStatus() {
    return this.request("/api/models/download/status");
  }
  async cancelDownload() {
    return this.request("/api/models/download/cancel", {
      method: "POST"
    });
  }
  async getDownloadedModels() {
    return this.request("/api/models/downloaded");
  }
  async getCacheInfo() {
    return this.request("/api/models/cache");
  }
  async clearCache(modelName) {
    const query = modelName ? `?model_name=${encodeURIComponent(modelName)}` : "";
    return this.request(`/api/models/cache${query}`, {
      method: "DELETE"
    });
  }
  // Devices
  async getDevices() {
    return this.cachedRequest("/api/devices", 2 * 60 * 1e3);
  }
  async setDevice(deviceName) {
    const result = await this.request(
      `/api/devices/${encodeURIComponent(deviceName)}`,
      { method: "PUT" }
    );
    this.cache.invalidate("/api/devices");
    return result;
  }
  async exportHistory(format = "json", includeMetadata = true) {
    const url = `${this.baseUrl}/api/history/export?format=${format}&include_metadata=${includeMetadata}`;
    const response = await fetch(url);
    if (!response.ok) {
      throw new Error(`Export failed: ${response.statusText}`);
    }
    return response.blob();
  }
  async exportHistoryFiltered(request) {
    const url = `${this.baseUrl}/api/history/export`;
    const response = await fetch(url, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(request)
    });
    if (!response.ok) {
      throw new Error(`Export failed: ${response.statusText}`);
    }
    return response.blob();
  }
  async importHistory(request) {
    return this.request("/api/history/import", {
      method: "POST",
      body: JSON.stringify(request)
    });
  }
  async createBatchJob(request) {
    return this.request("/api/transcribe/batch", {
      method: "POST",
      body: JSON.stringify(request)
    });
  }
  async getBatchJobs() {
    return this.request("/api/transcribe/batch");
  }
  async getBatchJob(jobId) {
    return this.request(`/api/transcribe/batch/${jobId}`);
  }
  async cancelBatchJob(jobId) {
    return this.request(`/api/transcribe/batch/${jobId}/cancel`, {
      method: "POST"
    });
  }
  async retryBatchJob(jobId, fileIds) {
    return this.request(
      `/api/transcribe/batch/${jobId}/retry`,
      {
        method: "POST",
        body: JSON.stringify({ file_ids: fileIds })
      }
    );
  }
  async deleteBatchJob(jobId) {
    return this.request(`/api/transcribe/batch/${jobId}`, {
      method: "DELETE"
    });
  }
}
const apiClient = new ApiClient();
const useAppStore = create((set, get) => ({
  // Initial state
  backendConnected: false,
  wsConnected: false,
  backendPort: 8765,
  appState: "idle",
  isRecording: false,
  recordingStartTime: null,
  recordingDuration: 0,
  modelLoaded: false,
  modelName: null,
  modelType: null,
  gpuAvailable: false,
  gpuName: null,
  gpuVramGb: null,
  lastError: null,
  isTranscribing: false,
  isSaving: false,
  lastOperationStatus: null,
  isReconnecting: false,
  // Actions
  setBackendConnected: (connected) => set({ backendConnected: connected }),
  setWsConnected: (connected) => set({ wsConnected: connected }),
  setBackendPort: (port) => {
    apiClient.setPort(port);
    set({ backendPort: port });
  },
  setAppState: (state) => set({
    appState: state,
    isRecording: state === "recording"
  }),
  startRecording: () => set({
    appState: "recording",
    isRecording: true,
    recordingStartTime: Date.now(),
    recordingDuration: 0
  }),
  stopRecording: () => set({
    appState: "transcribing",
    isRecording: false,
    recordingStartTime: null
  }),
  setModelInfo: (loaded, name, type) => set({
    modelLoaded: loaded,
    modelName: name,
    modelType: type
  }),
  setGpuInfo: (available, name, vramGb) => set({
    gpuAvailable: available,
    gpuName: name,
    gpuVramGb: vramGb
  }),
  setError: (error) => set({
    lastError: error,
    appState: error ? "error" : get().appState
  }),
  clearError: () => set({ lastError: null }),
  setTranscribing: (isTranscribing) => set({ isTranscribing }),
  setSaving: (isSaving) => set({ isSaving }),
  setOperationStatus: (status) => set({ lastOperationStatus: status }),
  setReconnecting: (isReconnecting) => set({ isReconnecting }),
  syncWithHealth: (health) => {
    const state = health.state;
    set({
      backendConnected: health.status === "ok",
      appState: state,
      isRecording: state === "recording",
      modelLoaded: health.model_loaded,
      modelName: health.model_name,
      gpuAvailable: health.gpu_available,
      gpuName: health.gpu_name,
      gpuVramGb: health.gpu_vram_gb
    });
  },
  fetchHealth: async () => {
    if (!get().backendConnected) {
      set({ isReconnecting: true });
    }
    try {
      const health = await apiClient.getHealth();
      get().syncWithHealth(health);
      set({ isReconnecting: false });
    } catch (error) {
      set({
        backendConnected: false,
        lastError: error instanceof Error ? error.message : "Failed to connect to backend",
        isReconnecting: false
      });
    }
  },
  updateRecordingDuration: () => {
    const { recordingStartTime, isRecording } = get();
    if (isRecording && recordingStartTime) {
      set({ recordingDuration: Date.now() - recordingStartTime });
    }
  }
}));
const useSettingsStore = create((set, get) => ({
  // Initial state
  settings: null,
  isLoading: false,
  isSaving: false,
  error: null,
  availableModels: {},
  availableDevices: [],
  currentDevice: null,
  needsModelReload: false,
  isLoadingModel: false,
  isConnectingDevice: false,
  hasUnsavedChanges: false,
  originalSettings: null,
  // Actions
  fetchSettings: async () => {
    set({ isLoading: true, error: null });
    try {
      const settings = await apiClient.getSettings();
      set({ settings, isLoading: false });
    } catch (error) {
      set({
        error: error instanceof Error ? error.message : "Failed to fetch settings",
        isLoading: false
      });
    }
  },
  updateSettings: async (updates) => {
    set({ isSaving: true, error: null });
    try {
      const response = await apiClient.updateSettings(updates);
      set({
        settings: response.settings,
        needsModelReload: response.reload_required,
        isSaving: false
      });
      return true;
    } catch (error) {
      set({
        error: error instanceof Error ? error.message : "Failed to update settings",
        isSaving: false
      });
      return false;
    }
  },
  fetchModels: async () => {
    try {
      const response = await apiClient.getModels();
      set({ availableModels: response.models });
    } catch (error) {
      set({
        error: error instanceof Error ? error.message : "Failed to fetch models"
      });
    }
  },
  fetchDevices: async () => {
    try {
      const response = await apiClient.getDevices();
      set({
        availableDevices: response.devices,
        currentDevice: response.current
      });
    } catch (error) {
      set({
        error: error instanceof Error ? error.message : "Failed to fetch devices"
      });
    }
  },
  loadModel: async (modelType, modelName) => {
    set({ isSaving: true, error: null });
    try {
      const { settings } = get();
      await apiClient.loadModel({
        model_type: modelType,
        model_name: modelName,
        device: settings?.device,
        compute_type: settings?.compute_type
      });
      set({ needsModelReload: false, isSaving: false });
      return true;
    } catch (error) {
      set({
        error: error instanceof Error ? error.message : "Failed to load model",
        isSaving: false
      });
      return false;
    }
  },
  setDevice: async (deviceName) => {
    try {
      await apiClient.setDevice(deviceName);
      set({ currentDevice: deviceName });
      const { settings } = get();
      if (settings) {
        set({ settings: { ...settings, device_name: deviceName } });
      }
      return true;
    } catch (error) {
      set({
        error: error instanceof Error ? error.message : "Failed to set device"
      });
      return false;
    }
  },
  setError: (error) => set({ error }),
  clearError: () => set({ error: null }),
  setLoadingModel: (loading) => set({ isLoadingModel: loading }),
  setConnectingDevice: (connecting) => set({ isConnectingDevice: connecting }),
  setHasUnsavedChanges: (hasChanges) => set({ hasUnsavedChanges: hasChanges }),
  checkUnsavedChanges: (currentSettings) => {
    const { originalSettings } = get();
    if (!originalSettings) return false;
    return JSON.stringify(originalSettings) !== JSON.stringify(currentSettings);
  }
}));
class WebSocketClient {
  ws = null;
  url;
  reconnectAttempts = 0;
  maxReconnectAttempts = 5;
  reconnectDelay = 1e3;
  listeners = /* @__PURE__ */ new Map();
  isIntentionallyClosed = false;
  // Message queue and throttling
  messageQueue = [];
  flushInterval = null;
  FLUSH_INTERVAL_MS = 100;
  MAX_MESSAGES_PER_SECOND = 10;
  lastEmitTimes = /* @__PURE__ */ new Map();
  criticalEvents = /* @__PURE__ */ new Set(["error", "close", "open"]);
  constructor(port = 8765) {
    this.url = `ws://127.0.0.1:${port}/api/ws`;
  }
  setPort(port) {
    this.url = `ws://127.0.0.1:${port}/api/ws`;
    if (this.ws?.readyState === WebSocket.OPEN) {
      this.disconnect();
      this.connect();
    }
  }
  connect() {
    if (this.ws?.readyState === WebSocket.OPEN) {
      return;
    }
    this.isIntentionallyClosed = false;
    this.startFlushInterval();
    try {
      this.ws = new WebSocket(this.url);
      this.ws.onopen = () => {
        console.log("WebSocket connected");
        this.reconnectAttempts = 0;
        this.emitMessage("open", { type: "open" }, "critical");
      };
      this.ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          const priority = this.criticalEvents.has(data.type) ? "critical" : "normal";
          this.emitMessage(data.type, data, priority);
          this.emitMessage("message", data, priority);
        } catch (error) {
          console.error("Failed to parse WebSocket message:", error);
        }
      };
      this.ws.onclose = () => {
        console.log("WebSocket closed");
        this.stopFlushInterval();
        this.emitMessage("close", { type: "close" }, "critical");
        if (!this.isIntentionallyClosed && this.reconnectAttempts < this.maxReconnectAttempts) {
          this.reconnectAttempts++;
          const delay = this.reconnectDelay * Math.pow(2, this.reconnectAttempts - 1);
          console.log(`Reconnecting in ${delay}ms (attempt ${this.reconnectAttempts})`);
          setTimeout(() => this.connect(), delay);
        }
      };
      this.ws.onerror = (error) => {
        console.error("WebSocket error:", error);
        this.emitMessage("error", { type: "error", message: "WebSocket connection error" }, "critical");
      };
    } catch (error) {
      console.error("Failed to create WebSocket:", error);
    }
  }
  disconnect() {
    this.isIntentionallyClosed = true;
    this.stopFlushInterval();
    this.flushQueue();
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
  }
  send(data) {
    if (this.ws?.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(data));
    }
  }
  ping() {
    if (this.ws?.readyState === WebSocket.OPEN) {
      this.ws.send("ping");
    }
  }
  // Event subscription
  on(event, callback) {
    if (!this.listeners.has(event)) {
      this.listeners.set(event, /* @__PURE__ */ new Set());
    }
    this.listeners.get(event).add(callback);
    return () => this.off(event, callback);
  }
  off(event, callback) {
    this.listeners.get(event)?.delete(callback);
  }
  emitMessage(event, data, priority) {
    if (priority === "critical") {
      this.emitImmediately(event, data);
      return;
    }
    if (this.shouldThrottle(event)) {
      this.queueMessage(event, data, priority);
    } else {
      this.emitImmediately(event, data);
      this.lastEmitTimes.set(event, Date.now());
    }
  }
  emitImmediately(event, data) {
    this.listeners.get(event)?.forEach((callback) => {
      try {
        callback(data);
      } catch (error) {
        console.error(`Error in ${event} listener:`, error);
      }
    });
  }
  shouldThrottle(event) {
    const lastEmit = this.lastEmitTimes.get(event);
    if (!lastEmit) return false;
    const timeSinceLastEmit = Date.now() - lastEmit;
    const minInterval = 1e3 / this.MAX_MESSAGES_PER_SECOND;
    return timeSinceLastEmit < minInterval;
  }
  queueMessage(event, data, priority) {
    const existingIndex = this.messageQueue.findIndex(
      (msg) => msg.event === event && msg.data.type === data.type
    );
    if (existingIndex !== -1) {
      this.messageQueue[existingIndex] = { event, data, priority, timestamp: Date.now() };
    } else {
      this.messageQueue.push({ event, data, priority, timestamp: Date.now() });
    }
  }
  startFlushInterval() {
    if (this.flushInterval !== null) return;
    this.flushInterval = window.setInterval(() => {
      this.flushQueue();
    }, this.FLUSH_INTERVAL_MS);
  }
  stopFlushInterval() {
    if (this.flushInterval !== null) {
      clearInterval(this.flushInterval);
      this.flushInterval = null;
    }
  }
  flushQueue() {
    if (this.messageQueue.length === 0) return;
    const messagesToFlush = [...this.messageQueue];
    this.messageQueue = [];
    messagesToFlush.forEach(({ event, data }) => {
      this.emitImmediately(event, data);
      this.lastEmitTimes.set(event, Date.now());
    });
  }
  // Typed event helpers
  onStatus(callback) {
    return this.on("status", callback);
  }
  onTranscription(callback) {
    return this.on("transcription", callback);
  }
  onError(callback) {
    return this.on("error", callback);
  }
  get isConnected() {
    return this.ws?.readyState === WebSocket.OPEN;
  }
}
const wsClient = new WebSocketClient();
const DEFAULT_LIMIT = 50;
const useHistoryStore = create((set, get) => ({
  // Initial state
  items: [],
  total: 0,
  stats: null,
  limit: DEFAULT_LIMIT,
  offset: 0,
  hasMore: false,
  currentPage: 1,
  totalPages: 1,
  searchQuery: "",
  isLoading: false,
  isLoadingMore: false,
  error: null,
  // Actions
  fetchHistory: async (reset = true) => {
    const { limit, searchQuery, currentPage } = get();
    const offset = reset ? 0 : (currentPage - 1) * limit;
    if (reset) {
      set({ isLoading: true, offset: 0, currentPage: 1, error: null });
    }
    try {
      const response = await apiClient.getHistory({
        limit,
        offset,
        search: searchQuery || void 0
      });
      const totalPages = Math.max(1, Math.ceil(response.total / limit));
      set({
        items: response.items,
        total: response.total,
        hasMore: response.items.length === limit && offset + response.items.length < response.total,
        offset,
        totalPages,
        isLoading: false
      });
    } catch (error) {
      set({
        error: error instanceof Error ? error.message : "Failed to fetch history",
        isLoading: false
      });
    }
  },
  loadMore: async () => {
    const { hasMore, isLoadingMore, currentPage, totalPages } = get();
    if (!hasMore || isLoadingMore || currentPage >= totalPages) return;
    await get().goToPage(currentPage + 1);
  },
  goToPage: async (page) => {
    const { limit, searchQuery, totalPages, isLoading } = get();
    if (isLoading || page < 1 || page > totalPages) return;
    const offset = (page - 1) * limit;
    set({ isLoading: true, error: null });
    try {
      const response = await apiClient.getHistory({
        limit,
        offset,
        search: searchQuery || void 0
      });
      const newTotalPages = Math.max(1, Math.ceil(response.total / limit));
      set({
        items: response.items,
        total: response.total,
        hasMore: offset + response.items.length < response.total,
        offset,
        currentPage: page,
        totalPages: newTotalPages,
        isLoading: false
      });
    } catch (error) {
      set({
        error: error instanceof Error ? error.message : "Failed to load page",
        isLoading: false
      });
    }
  },
  setPageSize: async (size) => {
    set({ limit: size, currentPage: 1, offset: 0 });
    await get().fetchHistory(true);
  },
  setSearchQuery: (query) => set({ searchQuery: query }),
  search: async (query) => {
    set({ searchQuery: query, offset: 0 });
    await get().fetchHistory(true);
  },
  addItem: (item) => {
    const { items, total } = get();
    set({
      items: [item, ...items],
      total: total + 1
    });
  },
  deleteItem: async (id) => {
    try {
      await apiClient.deleteHistoryItem(id);
      const { items, total } = get();
      set({
        items: items.filter((item) => item.id !== id),
        total: Math.max(0, total - 1)
      });
      return true;
    } catch (error) {
      set({
        error: error instanceof Error ? error.message : "Failed to delete item"
      });
      return false;
    }
  },
  fetchStats: async () => {
    try {
      const stats = await apiClient.getHistoryStats();
      set({ stats });
    } catch (error) {
      console.error("Failed to fetch stats:", error);
    }
  },
  setError: (error) => set({ error }),
  clearError: () => set({ error: null }),
  reset: () => set({
    items: [],
    total: 0,
    offset: 0,
    hasMore: false,
    currentPage: 1,
    totalPages: 1,
    searchQuery: "",
    isLoading: false,
    isLoadingMore: false,
    error: null
  })
}));
let wsSubscribed = false;
function initHistoryWebSocket() {
  if (wsSubscribed) return;
  wsSubscribed = true;
  wsClient.onTranscription((event) => {
    const { items, searchQuery } = useHistoryStore.getState();
    const record = {
      id: event.id,
      text: event.text,
      duration_ms: event.duration_ms,
      model_used: null,
      language: null,
      created_at: (/* @__PURE__ */ new Date()).toISOString()
    };
    const alreadyExists = items.some((item) => item.id === record.id);
    if (!alreadyExists && !searchQuery) {
      useHistoryStore.getState().addItem(record);
    } else if (!alreadyExists && searchQuery) {
      useHistoryStore.setState((state) => ({ total: state.total + 1 }));
    }
  });
}
const initialState = {
  isDownloading: false,
  downloadProgress: 0,
  downloadedBytes: 0,
  totalBytes: 0,
  modelName: null,
  modelType: null,
  status: null,
  errorMessage: null,
  elapsedSeconds: 0,
  bytesPerSecond: 0,
  estimatedRemainingSeconds: null,
  cachedModels: [],
  cacheDir: null,
  totalCacheSize: 0,
  totalCacheSizeHuman: null,
  isLoadingCache: false,
  isClearingCache: false
};
const useDownloadStore = create((set, get) => ({
  ...initialState,
  updateFromWebSocket: (event) => {
    const isActive = event.status === "pending" || event.status === "downloading";
    set({
      isDownloading: isActive,
      downloadProgress: event.progress_percent,
      downloadedBytes: event.downloaded_bytes,
      totalBytes: event.total_bytes,
      modelName: event.model_name,
      modelType: event.model_type,
      status: event.status,
      errorMessage: event.error_message,
      elapsedSeconds: event.elapsed_seconds,
      bytesPerSecond: event.bytes_per_second,
      estimatedRemainingSeconds: event.estimated_remaining_seconds
    });
    if (event.status === "completed") {
      get().fetchCachedModels();
    }
  },
  cancelDownload: async () => {
    try {
      await apiClient.cancelDownload();
      set({ status: "cancelled", isDownloading: false });
      return true;
    } catch (error) {
      console.error("Failed to cancel download:", error);
      return false;
    }
  },
  fetchCachedModels: async () => {
    set({ isLoadingCache: true });
    try {
      const response = await apiClient.getDownloadedModels();
      set({
        cachedModels: response.models,
        isLoadingCache: false
      });
    } catch (error) {
      console.error("Failed to fetch cached models:", error);
      set({ isLoadingCache: false });
    }
  },
  fetchCacheInfo: async () => {
    set({ isLoadingCache: true });
    try {
      const response = await apiClient.getCacheInfo();
      set({
        cachedModels: response.models,
        cacheDir: response.cache_dir,
        totalCacheSize: response.total_size_bytes,
        totalCacheSizeHuman: response.total_size_human,
        isLoadingCache: false
      });
    } catch (error) {
      console.error("Failed to fetch cache info:", error);
      set({ isLoadingCache: false });
    }
  },
  clearCache: async (modelName) => {
    set({ isClearingCache: true });
    try {
      await apiClient.clearCache(modelName);
      await get().fetchCacheInfo();
      set({ isClearingCache: false });
      return true;
    } catch (error) {
      console.error("Failed to clear cache:", error);
      set({ isClearingCache: false });
      return false;
    }
  },
  reset: () => set(initialState)
}));
class ErrorBoundary extends reactExports.Component {
  constructor(props) {
    super(props);
    this.state = {
      hasError: false,
      error: null,
      errorInfo: null
    };
  }
  static getDerivedStateFromError(error) {
    return { hasError: true, error, errorInfo: null };
  }
  componentDidCatch(error, errorInfo) {
    console.error("Uncaught error:", error, errorInfo);
    this.setState({ errorInfo });
  }
  handleReload = () => {
    window.location.reload();
  };
  handleTryAgain = () => {
    this.setState({ hasError: false, error: null, errorInfo: null });
  };
  render() {
    if (this.state.hasError) {
      return /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: "min-h-screen bg-gray-900 flex flex-col items-center justify-center p-6 text-center select-none", children: /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "max-w-md w-full space-y-8", children: [
        /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "relative mx-auto w-24 h-24 flex items-center justify-center", children: [
          /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: "absolute inset-0 bg-red-500/10 rounded-full animate-pulse" }),
          /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: "absolute inset-0 border border-red-500/20 rounded-full" }),
          /* @__PURE__ */ jsxRuntimeExports.jsx(
            "svg",
            {
              className: "w-10 h-10 text-red-500 relative z-10",
              fill: "none",
              stroke: "currentColor",
              viewBox: "0 0 24 24",
              children: /* @__PURE__ */ jsxRuntimeExports.jsx(
                "path",
                {
                  strokeLinecap: "round",
                  strokeLinejoin: "round",
                  strokeWidth: 1.5,
                  d: "M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"
                }
              )
            }
          )
        ] }),
        /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "space-y-3", children: [
          /* @__PURE__ */ jsxRuntimeExports.jsx("h2", { className: "text-2xl font-semibold text-white tracking-tight", children: "System Malfunction" }),
          /* @__PURE__ */ jsxRuntimeExports.jsx("p", { className: "text-gray-400 text-base leading-relaxed", children: "The application encountered a critical error and needs to restart." })
        ] }),
        this.state.error && /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "bg-black/40 rounded-lg p-4 text-left overflow-hidden border border-gray-800/50 backdrop-blur-sm", children: [
          /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "flex items-center gap-2 mb-2", children: [
            /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: "w-2 h-2 rounded-full bg-red-500/50" }),
            /* @__PURE__ */ jsxRuntimeExports.jsx("p", { className: "text-red-400/80 font-mono text-xs uppercase tracking-wider", children: "Error Trace" })
          ] }),
          /* @__PURE__ */ jsxRuntimeExports.jsx("code", { className: "text-gray-500 font-mono text-xs block whitespace-pre-wrap break-words opacity-80", children: this.state.error.toString() })
        ] }),
        /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "flex flex-col sm:flex-row gap-3 justify-center pt-2", children: [
          /* @__PURE__ */ jsxRuntimeExports.jsx(
            "button",
            {
              onClick: this.handleTryAgain,
              className: "px-6 py-2.5 rounded-lg bg-gray-800 text-gray-200 font-medium text-sm hover:bg-gray-700 hover:text-white transition-all duration-200 border border-gray-700 hover:border-gray-600 focus:outline-none focus:ring-2 focus:ring-gray-500/50 focus:ring-offset-2 focus:ring-offset-gray-900",
              children: "Try Again"
            }
          ),
          /* @__PURE__ */ jsxRuntimeExports.jsx(
            "button",
            {
              onClick: this.handleReload,
              className: "px-6 py-2.5 rounded-lg bg-red-500/10 text-red-400 font-medium text-sm hover:bg-red-500/20 hover:text-red-300 transition-all duration-200 border border-red-500/20 hover:border-red-500/30 focus:outline-none focus:ring-2 focus:ring-red-500/50 focus:ring-offset-2 focus:ring-offset-gray-900",
              children: "Reload System"
            }
          )
        ] })
      ] }) });
    }
    return this.props.children;
  }
}
function LoadingSpinner() {
  return /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: "flex items-center justify-center h-full w-full min-h-[200px]", children: /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: "animate-spin rounded-full h-8 w-8 border-b-2 border-white" }) });
}
const navItems = [
  {
    id: "dashboard",
    label: "Dashboard",
    path: "/",
    icon: /* @__PURE__ */ jsxRuntimeExports.jsx("svg", { className: "w-5 h-5", fill: "none", stroke: "currentColor", viewBox: "0 0 24 24", children: /* @__PURE__ */ jsxRuntimeExports.jsx("path", { strokeLinecap: "round", strokeLinejoin: "round", strokeWidth: 1.5, d: "M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6" }) })
  },
  {
    id: "batch",
    label: "Batch Transcription",
    path: "/batch",
    icon: /* @__PURE__ */ jsxRuntimeExports.jsx("svg", { className: "w-5 h-5", fill: "none", stroke: "currentColor", viewBox: "0 0 24 24", children: /* @__PURE__ */ jsxRuntimeExports.jsx("path", { strokeLinecap: "round", strokeLinejoin: "round", strokeWidth: 1.5, d: "M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" }) })
  },
  {
    id: "stats",
    label: "Statistics",
    path: "/stats",
    icon: /* @__PURE__ */ jsxRuntimeExports.jsx("svg", { className: "w-5 h-5", fill: "none", stroke: "currentColor", viewBox: "0 0 24 24", children: /* @__PURE__ */ jsxRuntimeExports.jsx("path", { strokeLinecap: "round", strokeLinejoin: "round", strokeWidth: 1.5, d: "M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" }) })
  }
];
const settingsItems = [
  {
    id: "model",
    label: "Model",
    path: "/settings/model",
    icon: /* @__PURE__ */ jsxRuntimeExports.jsx("svg", { className: "w-5 h-5", fill: "none", stroke: "currentColor", viewBox: "0 0 24 24", children: /* @__PURE__ */ jsxRuntimeExports.jsx("path", { strokeLinecap: "round", strokeLinejoin: "round", strokeWidth: 1.5, d: "M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" }) })
  },
  {
    id: "audio",
    label: "Audio",
    path: "/settings/audio",
    icon: /* @__PURE__ */ jsxRuntimeExports.jsx("svg", { className: "w-5 h-5", fill: "none", stroke: "currentColor", viewBox: "0 0 24 24", children: /* @__PURE__ */ jsxRuntimeExports.jsx("path", { strokeLinecap: "round", strokeLinejoin: "round", strokeWidth: 1.5, d: "M19 11a7 7 0 01-7 7m0 0a7 7 0 01-7-7m7 7v4m0 0H8m4 0h4m-4-8a3 3 0 01-3-3V5a3 3 0 116 0v6a3 3 0 01-3 3z" }) })
  },
  {
    id: "hotkey",
    label: "Hotkey",
    path: "/settings/hotkey",
    icon: /* @__PURE__ */ jsxRuntimeExports.jsx("svg", { className: "w-5 h-5", fill: "none", stroke: "currentColor", viewBox: "0 0 24 24", children: /* @__PURE__ */ jsxRuntimeExports.jsx("path", { strokeLinecap: "round", strokeLinejoin: "round", strokeWidth: 1.5, d: "M15 7a2 2 0 012 2m4 0a6 6 0 01-7.743 5.743L11 17H9v2H7v2H4a1 1 0 01-1-1v-2.586a1 1 0 01.293-.707l5.964-5.964A6 6 0 1121 9z" }) })
  },
  {
    id: "behavior",
    label: "Behavior",
    path: "/settings/behavior",
    icon: /* @__PURE__ */ jsxRuntimeExports.jsxs("svg", { className: "w-5 h-5", fill: "none", stroke: "currentColor", viewBox: "0 0 24 24", children: [
      /* @__PURE__ */ jsxRuntimeExports.jsx("path", { strokeLinecap: "round", strokeLinejoin: "round", strokeWidth: 1.5, d: "M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" }),
      /* @__PURE__ */ jsxRuntimeExports.jsx("path", { strokeLinecap: "round", strokeLinejoin: "round", strokeWidth: 1.5, d: "M15 12a3 3 0 11-6 0 3 3 0 016 0z" })
    ] })
  },
  {
    id: "appearance",
    label: "Appearance",
    path: "/settings/appearance",
    icon: /* @__PURE__ */ jsxRuntimeExports.jsx("svg", { className: "w-5 h-5", fill: "none", stroke: "currentColor", viewBox: "0 0 24 24", children: /* @__PURE__ */ jsxRuntimeExports.jsx("path", { strokeLinecap: "round", strokeLinejoin: "round", strokeWidth: 1.5, d: "M7 21a4 4 0 01-4-4V5a2 2 0 012-2h4a2 2 0 012 2v12a4 4 0 01-4 4zm0 0h12a2 2 0 002-2v-4a2 2 0 00-2-2h-2.343M11 7.343l1.657-1.657a2 2 0 012.828 0l2.829 2.829a2 2 0 010 2.828l-8.486 8.485M7 17h.01" }) })
  },
  {
    id: "data",
    label: "Data",
    path: "/settings/data",
    icon: /* @__PURE__ */ jsxRuntimeExports.jsx("svg", { className: "w-5 h-5", fill: "none", stroke: "currentColor", viewBox: "0 0 24 24", children: /* @__PURE__ */ jsxRuntimeExports.jsx("path", { strokeLinecap: "round", strokeLinejoin: "round", strokeWidth: 1.5, d: "M4 7v10c0 2.21 3.582 4 8 4s8-1.79 8-4V7M4 7c0 2.21 3.582 4 8 4s8-1.79 8-4M4 7c0-2.21 3.582-4 8-4s8 1.79 8 4m0 5c0 2.21-3.582 4-8 4s-8-1.79-8-4" }) })
  },
  {
    id: "about",
    label: "About",
    path: "/settings/about",
    icon: /* @__PURE__ */ jsxRuntimeExports.jsx("svg", { className: "w-5 h-5", fill: "none", stroke: "currentColor", viewBox: "0 0 24 24", children: /* @__PURE__ */ jsxRuntimeExports.jsx("path", { strokeLinecap: "round", strokeLinejoin: "round", strokeWidth: 1.5, d: "M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" }) })
  }
];
function NavItem({ item, isActive }) {
  return /* @__PURE__ */ jsxRuntimeExports.jsxs(
    Link,
    {
      to: item.path,
      className: `
        flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium
        transition-all duration-150 ease-out
        ${isActive ? "bg-[var(--color-sidebar-active)] text-[var(--color-text-primary)]" : "text-[var(--color-text-secondary)] hover:bg-[var(--color-sidebar-hover)] hover:text-[var(--color-text-primary)]"}
      `,
      children: [
        /* @__PURE__ */ jsxRuntimeExports.jsx("span", { className: isActive ? "text-[var(--color-accent)]" : "", children: item.icon }),
        /* @__PURE__ */ jsxRuntimeExports.jsx("span", { children: item.label })
      ]
    }
  );
}
function Sidebar() {
  const location = useLocation();
  const { backendConnected, isReconnecting } = useAppStore();
  location.pathname.startsWith("/settings");
  return /* @__PURE__ */ jsxRuntimeExports.jsxs("aside", { className: "w-56 bg-[var(--color-sidebar-bg)] border-r border-[var(--color-sidebar-border)] flex flex-col h-full", children: [
    /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: "px-4 py-4 border-b border-[var(--color-sidebar-border)]", children: /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "flex items-center gap-2", children: [
      /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: "w-8 h-8 rounded-lg bg-[var(--color-accent)] flex items-center justify-center", children: /* @__PURE__ */ jsxRuntimeExports.jsx("svg", { className: "w-5 h-5 text-[var(--color-text-on-accent)]", fill: "none", stroke: "currentColor", viewBox: "0 0 24 24", children: /* @__PURE__ */ jsxRuntimeExports.jsx("path", { strokeLinecap: "round", strokeLinejoin: "round", strokeWidth: 2, d: "M19 11a7 7 0 01-7 7m0 0a7 7 0 01-7-7m7 7v4m0 0H8m4 0h4m-4-8a3 3 0 01-3-3V5a3 3 0 116 0v6a3 3 0 01-3 3z" }) }) }),
      /* @__PURE__ */ jsxRuntimeExports.jsx("span", { className: "font-semibold text-[var(--color-text-primary)]", children: "SpeakEasy" })
    ] }) }),
    /* @__PURE__ */ jsxRuntimeExports.jsxs("nav", { className: "flex-1 px-3 py-4 space-y-1 overflow-y-auto", children: [
      navItems.map((item) => /* @__PURE__ */ jsxRuntimeExports.jsx(
        NavItem,
        {
          item,
          isActive: location.pathname === item.path
        },
        item.id
      )),
      /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "pt-4 mt-4 border-t border-[var(--color-sidebar-border)]", children: [
        /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: "px-3 mb-2", children: /* @__PURE__ */ jsxRuntimeExports.jsx("span", { className: "text-xs font-medium uppercase tracking-wider text-[var(--color-text-muted)]", children: "Settings" }) }),
        /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: "space-y-1", children: settingsItems.map((item) => /* @__PURE__ */ jsxRuntimeExports.jsx(
          NavItem,
          {
            item,
            isActive: location.pathname === item.path || location.pathname === "/settings" && item.id === "model"
          },
          item.id
        )) })
      ] })
    ] }),
    /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: "px-4 py-3 border-t border-[var(--color-sidebar-border)]", children: /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "flex items-center gap-2", children: [
      /* @__PURE__ */ jsxRuntimeExports.jsx(
        "div",
        {
          className: `rounded-full transition-all duration-300 ${backendConnected ? "w-2 h-2 bg-[var(--color-success)]" : isReconnecting ? "w-2.5 h-2.5 bg-[var(--color-warning)] animate-pulse" : "w-2.5 h-2.5 bg-[var(--color-error)]"}`
        }
      ),
      /* @__PURE__ */ jsxRuntimeExports.jsx("span", { className: "text-xs text-[var(--color-text-muted)]", children: backendConnected ? "Connected" : isReconnecting ? "Reconnecting..." : "Disconnected" })
    ] }) })
  ] });
}
const Toast = ({ id, type, message, onClose }) => {
  const [isVisible, setIsVisible] = reactExports.useState(false);
  reactExports.useEffect(() => {
    requestAnimationFrame(() => {
      setIsVisible(true);
    });
  }, []);
  const handleClose = () => {
    setIsVisible(false);
    setTimeout(() => {
      onClose(id);
    }, 300);
  };
  const getIcon = () => {
    switch (type) {
      case "success":
        return /* @__PURE__ */ jsxRuntimeExports.jsx("svg", { className: "w-6 h-6 text-green-400", fill: "none", stroke: "currentColor", viewBox: "0 0 24 24", children: /* @__PURE__ */ jsxRuntimeExports.jsx("path", { strokeLinecap: "round", strokeLinejoin: "round", strokeWidth: "2", d: "M5 13l4 4L19 7" }) });
      case "error":
        return /* @__PURE__ */ jsxRuntimeExports.jsx("svg", { className: "w-6 h-6 text-red-400", fill: "none", stroke: "currentColor", viewBox: "0 0 24 24", children: /* @__PURE__ */ jsxRuntimeExports.jsx("path", { strokeLinecap: "round", strokeLinejoin: "round", strokeWidth: "2", d: "M6 18L18 6M6 6l12 12" }) });
      case "warning":
        return /* @__PURE__ */ jsxRuntimeExports.jsx("svg", { className: "w-6 h-6 text-yellow-400", fill: "none", stroke: "currentColor", viewBox: "0 0 24 24", children: /* @__PURE__ */ jsxRuntimeExports.jsx("path", { strokeLinecap: "round", strokeLinejoin: "round", strokeWidth: "2", d: "M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" }) });
    }
  };
  const getBorderColor = () => {
    switch (type) {
      case "success":
        return "border-green-500";
      case "error":
        return "border-red-500";
      case "warning":
        return "border-yellow-500";
    }
  };
  return /* @__PURE__ */ jsxRuntimeExports.jsxs(
    "div",
    {
      className: `
        flex items-center w-full max-w-sm p-4 mb-4 text-gray-200 bg-gray-800 
        rounded-lg shadow-lg border-l-4 ${getBorderColor()}
        transform transition-all duration-300 ease-in-out
        ${isVisible ? "translate-x-0 opacity-100" : "translate-x-full opacity-0"}
      `,
      role: "alert",
      children: [
        /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: "inline-flex items-center justify-center flex-shrink-0 w-8 h-8", children: getIcon() }),
        /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: "ml-3 text-sm font-normal break-words flex-1", children: message }),
        /* @__PURE__ */ jsxRuntimeExports.jsxs(
          "button",
          {
            type: "button",
            className: "ml-auto -mx-1.5 -my-1.5 bg-gray-800 text-gray-400 hover:text-gray-200 rounded-lg focus:ring-2 focus:ring-gray-600 p-1.5 hover:bg-gray-700 inline-flex h-8 w-8",
            onClick: handleClose,
            "aria-label": "Close",
            children: [
              /* @__PURE__ */ jsxRuntimeExports.jsx("span", { className: "sr-only", children: "Close" }),
              /* @__PURE__ */ jsxRuntimeExports.jsx("svg", { className: "w-5 h-5", fill: "currentColor", viewBox: "0 0 20 20", children: /* @__PURE__ */ jsxRuntimeExports.jsx("path", { fillRule: "evenodd", d: "M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z", clipRule: "evenodd" }) })
            ]
          }
        )
      ]
    }
  );
};
const ToastContext = reactExports.createContext(void 0);
const ToastProvider = ({ children }) => {
  const [toasts, setToasts] = reactExports.useState([]);
  const removeToast = reactExports.useCallback((id) => {
    setToasts((prevToasts) => prevToasts.filter((toast) => toast.id !== id));
  }, []);
  const addToast = reactExports.useCallback((type, message, duration = 5e3) => {
    const id = Math.random().toString(36).substring(2, 9);
    const newToast = { id, type, message, duration };
    setToasts((prevToasts) => [...prevToasts, newToast]);
    if (duration > 0) {
      setTimeout(() => {
        removeToast(id);
      }, duration);
    }
  }, [removeToast]);
  return /* @__PURE__ */ jsxRuntimeExports.jsxs(ToastContext.Provider, { value: { addToast, removeToast }, children: [
    children,
    /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: "fixed top-4 right-4 z-50 flex flex-col gap-2 w-full max-w-sm pointer-events-none", children: toasts.map((toast) => /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: "pointer-events-auto", children: /* @__PURE__ */ jsxRuntimeExports.jsx(
      Toast,
      {
        id: toast.id,
        type: toast.type,
        message: toast.message,
        onClose: removeToast
      }
    ) }, toast.id)) })
  ] });
};
const Dashboard = reactExports.lazy(() => __vitePreload(() => import("./Dashboard-Coj9-nEc.js"), true ? __vite__mapDeps([0,1,2,3]) : void 0, import.meta.url));
const BatchTranscription = reactExports.lazy(() => __vitePreload(() => import("./BatchTranscription-B5hZRYSX.js"), true ? __vite__mapDeps([4,1]) : void 0, import.meta.url));
const Stats = reactExports.lazy(() => __vitePreload(() => import("./Stats-Kfjc8hAj.js"), true ? __vite__mapDeps([5,1]) : void 0, import.meta.url));
const RecordingIndicator = reactExports.lazy(() => __vitePreload(() => import("./RecordingIndicator-TJhk5iT8.js"), true ? __vite__mapDeps([6,1]) : void 0, import.meta.url));
const ModelSettings = reactExports.lazy(() => __vitePreload(() => import("./ModelSettings-DVI8vVqS.js"), true ? __vite__mapDeps([7,1,8]) : void 0, import.meta.url));
const AudioSettings = reactExports.lazy(() => __vitePreload(() => import("./AudioSettings-Drc6FVXY.js"), true ? __vite__mapDeps([9,1]) : void 0, import.meta.url));
const HotkeySettings = reactExports.lazy(() => __vitePreload(() => import("./HotkeySettings-DbmDktvh.js"), true ? __vite__mapDeps([10,1,8]) : void 0, import.meta.url));
const BehaviorSettings = reactExports.lazy(() => __vitePreload(() => import("./BehaviorSettings-B-GcEV1i.js"), true ? __vite__mapDeps([11,1,8]) : void 0, import.meta.url));
const AppearanceSettings = reactExports.lazy(() => __vitePreload(() => import("./AppearanceSettings-HzT1QAGH.js"), true ? __vite__mapDeps([12,1,8]) : void 0, import.meta.url));
const DataSettings = reactExports.lazy(() => __vitePreload(() => import("./DataSettings-Dmw7asZB.js"), true ? __vite__mapDeps([13,1,3]) : void 0, import.meta.url));
const AboutSettings = reactExports.lazy(() => __vitePreload(() => import("./AboutSettings-R7zNTuGh.js"), true ? __vite__mapDeps([14,1]) : void 0, import.meta.url));
function NavigationListener() {
  const navigate = useNavigate();
  const location = useLocation();
  reactExports.useEffect(() => {
    const unsubscribe = window.api?.onNavigate((path) => {
      if (path !== location.pathname) {
        navigate(path);
      }
    });
    return () => {
      unsubscribe?.();
    };
  }, [navigate, location.pathname]);
  return null;
}
function ThemeInitializer() {
  const { settings, fetchSettings } = useSettingsStore();
  reactExports.useEffect(() => {
    fetchSettings();
  }, [fetchSettings]);
  reactExports.useEffect(() => {
    if (settings?.theme) {
      document.documentElement.setAttribute("data-theme", settings.theme);
    }
  }, [settings?.theme]);
  return null;
}
function MainLayout() {
  const { backendConnected, fetchHealth, startRecording, setAppState, isReconnecting } = useAppStore();
  const { addItem, fetchHistory } = useHistoryStore();
  const { fetchSettings, settings } = useSettingsStore();
  reactExports.useEffect(() => {
    fetchHealth();
    fetchHistory();
    fetchSettings();
    initHistoryWebSocket();
    const interval = setInterval(fetchHealth, 5e3);
    return () => clearInterval(interval);
  }, [fetchHealth, fetchHistory, fetchSettings]);
  reactExports.useEffect(() => {
    if (settings?.hotkey && window.api) {
      window.api.registerHotkey(settings.hotkey, settings.hotkey_mode || "toggle");
    }
  }, [settings?.hotkey, settings?.hotkey_mode]);
  reactExports.useEffect(() => {
    const unsubStart = window.api?.onRecordingStart(() => {
      startRecording();
    });
    const unsubComplete = window.api?.onRecordingComplete((result) => {
      setAppState("idle");
      const response = result;
      if (response?.id && response?.text) {
        const record = {
          id: response.id,
          text: response.text,
          duration_ms: response.duration_ms ?? 0,
          model_used: response.model_used ?? null,
          language: response.language ?? null,
          created_at: (/* @__PURE__ */ new Date()).toISOString()
        };
        addItem(record);
      }
    });
    const unsubError = window.api?.onRecordingError((error) => {
      setAppState("idle");
      console.error("Recording error:", error);
    });
    return () => {
      unsubStart?.();
      unsubComplete?.();
      unsubError?.();
    };
  }, [startRecording, setAppState, addItem]);
  return /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "h-screen flex bg-[var(--color-bg-primary)]", children: [
    /* @__PURE__ */ jsxRuntimeExports.jsx(Sidebar, {}),
    /* @__PURE__ */ jsxRuntimeExports.jsx("main", { className: "flex-1 min-h-0 overflow-auto", children: /* @__PURE__ */ jsxRuntimeExports.jsx(reactExports.Suspense, { fallback: /* @__PURE__ */ jsxRuntimeExports.jsx(LoadingSpinner, {}), children: /* @__PURE__ */ jsxRuntimeExports.jsxs(Routes, { children: [
      /* @__PURE__ */ jsxRuntimeExports.jsx(Route, { path: "/", element: /* @__PURE__ */ jsxRuntimeExports.jsx(Dashboard, {}) }),
      /* @__PURE__ */ jsxRuntimeExports.jsx(Route, { path: "/batch", element: /* @__PURE__ */ jsxRuntimeExports.jsx(BatchTranscription, {}) }),
      /* @__PURE__ */ jsxRuntimeExports.jsx(Route, { path: "/stats", element: /* @__PURE__ */ jsxRuntimeExports.jsx(Stats, {}) }),
      /* @__PURE__ */ jsxRuntimeExports.jsx(Route, { path: "/settings", element: /* @__PURE__ */ jsxRuntimeExports.jsx(Navigate, { to: "/settings/model", replace: true }) }),
      /* @__PURE__ */ jsxRuntimeExports.jsx(Route, { path: "/settings/model", element: /* @__PURE__ */ jsxRuntimeExports.jsx(ModelSettings, {}) }),
      /* @__PURE__ */ jsxRuntimeExports.jsx(Route, { path: "/settings/audio", element: /* @__PURE__ */ jsxRuntimeExports.jsx(AudioSettings, {}) }),
      /* @__PURE__ */ jsxRuntimeExports.jsx(Route, { path: "/settings/hotkey", element: /* @__PURE__ */ jsxRuntimeExports.jsx(HotkeySettings, {}) }),
      /* @__PURE__ */ jsxRuntimeExports.jsx(Route, { path: "/settings/behavior", element: /* @__PURE__ */ jsxRuntimeExports.jsx(BehaviorSettings, {}) }),
      /* @__PURE__ */ jsxRuntimeExports.jsx(Route, { path: "/settings/appearance", element: /* @__PURE__ */ jsxRuntimeExports.jsx(AppearanceSettings, {}) }),
      /* @__PURE__ */ jsxRuntimeExports.jsx(Route, { path: "/settings/data", element: /* @__PURE__ */ jsxRuntimeExports.jsx(DataSettings, {}) }),
      /* @__PURE__ */ jsxRuntimeExports.jsx(Route, { path: "/settings/about", element: /* @__PURE__ */ jsxRuntimeExports.jsx(AboutSettings, {}) })
    ] }) }) })
  ] });
}
function App() {
  return /* @__PURE__ */ jsxRuntimeExports.jsx(ErrorBoundary, { children: /* @__PURE__ */ jsxRuntimeExports.jsx(ToastProvider, { children: /* @__PURE__ */ jsxRuntimeExports.jsxs(HashRouter, { children: [
    /* @__PURE__ */ jsxRuntimeExports.jsx(NavigationListener, {}),
    /* @__PURE__ */ jsxRuntimeExports.jsx(ThemeInitializer, {}),
    /* @__PURE__ */ jsxRuntimeExports.jsx(reactExports.Suspense, { fallback: /* @__PURE__ */ jsxRuntimeExports.jsx(LoadingSpinner, {}), children: /* @__PURE__ */ jsxRuntimeExports.jsxs(Routes, { children: [
      /* @__PURE__ */ jsxRuntimeExports.jsx(Route, { path: "/recording-indicator", element: /* @__PURE__ */ jsxRuntimeExports.jsx(RecordingIndicator, {}) }),
      /* @__PURE__ */ jsxRuntimeExports.jsx(Route, { path: "/*", element: /* @__PURE__ */ jsxRuntimeExports.jsx(MainLayout, {}) })
    ] }) })
  ] }) }) });
}
const container = document.getElementById("root");
if (!container) {
  throw new Error("Root element not found");
}
const root = createRoot(container);
root.render(
  /* @__PURE__ */ jsxRuntimeExports.jsx(React.StrictMode, { children: /* @__PURE__ */ jsxRuntimeExports.jsx(App, {}) })
);
export {
  useAppStore as a,
  apiClient as b,
  useSettingsStore as c,
  useDownloadStore as d,
  jsxRuntimeExports as j,
  perfMonitor as p,
  useHistoryStore as u,
  wsClient as w
};
