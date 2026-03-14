/**
 * Plan Injection Hook v1.0
 * 
 * Injects OpenEmotion /plan into reply generation context (read-only)
 * 
 * Features:
 * - Injection gate (skip commands/tool paths/task control)
 * - Fallback on all failure modes
 * - Observability logging
 * - Configurable via environment
 */

const fs = require('fs');
const path = require('path');
const http = require('http');

// Configuration
const EMOTIOND_BASE_URL = process.env.EMOTIOND_BASE_URL || 'http://127.0.0.1:18080';
const EMOTIOND_OPENCLAW_TOKEN = process.env.EMOTIOND_OPENCLAW_TOKEN || '';
const INJECT_PLAN_INTO_REPLY = process.env.inject_plan_into_reply !== 'false';
const PLAN_INJECTION_FOR_CHAT_ONLY = process.env.plan_injection_for_chat_only !== 'false';
const SKIP_PLAN_FOR_COMMANDS = process.env.skip_plan_for_commands !== 'false';
const SKIP_PLAN_FOR_TASK_CONTROL = process.env.skip_plan_for_task_control !== 'false';
const SKIP_PLAN_FOR_TOOL_PATHS = process.env.skip_plan_for_tool_paths !== 'false';
const PLAN_INJECTION_SOFT_FAIL = process.env.plan_injection_soft_fail !== 'false';
const PLAN_INJECTION_TIMEOUT_MS = parseInt(process.env.plan_injection_timeout_ms || '5000', 10);

// Paths
const WORKSPACE_DIR = process.env.OPENCLAW_WORKSPACE_DIR || process.env.HOME + '/.openclaw/workspace';
const CONTEXT_FILE = path.join(WORKSPACE_DIR, 'emotiond', 'context.json');

// Gate result constants
const GATE_ALLOWED = 'allowed';
const GATE_SKIPPED = 'skipped';
const GATE_DISABLED = 'disabled';
const GATE_ERROR = 'error';

/**
 * Detect if message is a command (starts with /)
 */
function isCommand(message) {
  if (!message || !message.body) return false;
  const body = message.body.trim();
  return body.startsWith('/') && !body.startsWith('//');
}

/**
 * Detect if message is task control
 */
function isTaskControl(message) {
  if (!message || !message.body) return false;
  const controlKeywords = [
    '/approve', '/deny', '/cancel', '/pause', '/resume',
    '/status', '/reset', '/new', '/wrap'
  ];
  const body = message.body.trim().toLowerCase();
  return controlKeywords.some(kw => body.startsWith(kw));
}

/**
 * Detect if this is a tool path (has tool_result in context)
 */
function isToolPath(context) {
  if (!context) return false;
  return !!(context.tool_result || context.tool_call_pending);
}

/**
 * Determine if plan injection should proceed
 */
function evaluateGate(message, context) {
  // Feature disabled
  if (!INJECT_PLAN_INTO_REPLY) {
    return { result: GATE_DISABLED, reason: 'feature_disabled' };
  }

  // Chat-only mode
  if (PLAN_INJECTION_FOR_CHAT_ONLY) {
    // Skip commands
    if (SKIP_PLAN_FOR_COMMANDS && isCommand(message)) {
      return { result: GATE_SKIPPED, reason: 'is_command' };
    }

    // Skip task control
    if (SKIP_PLAN_FOR_TASK_CONTROL && isTaskControl(message)) {
      return { result: GATE_SKIPPED, reason: 'is_task_control' };
    }

    // Skip tool paths
    if (SKIP_PLAN_FOR_TOOL_PATHS && isToolPath(context)) {
      return { result: GATE_SKIPPED, reason: 'is_tool_path' };
    }
  }

  return { result: GATE_ALLOWED, reason: 'chat_path' };
}

/**
 * Safe fetch plan from emotiond
 */
async function fetchPlan(userId, userText, focusTarget = null) {
  return new Promise((resolve) => {
    const postData = JSON.stringify({
      user_id: userId,
      user_text: userText,
      focus_target: focusTarget
    });

    const url = new URL('/plan', EMOTIOND_BASE_URL);
    const req = http.request(url, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': 'Bearer ' + EMOTIOND_OPENCLAW_TOKEN,
        'Content-Length': Buffer.byteLength(postData)
      },
      timeout: PLAN_INJECTION_TIMEOUT_MS
    }, (res) => {
      let data = '';
      res.on('data', chunk => data += chunk);
      res.on('end', () => {
        if (res.statusCode >= 400) {
          resolve({
            success: false,
            error: `HTTP ${res.statusCode}`,
            plan: null
          });
          return;
        }

        try {
          const plan = JSON.parse(data);
          // Validate schema
          if (!plan.tone || !Array.isArray(plan.key_points)) {
            resolve({
              success: false,
              error: 'schema_invalid',
              plan: null
            });
            return;
          }
          resolve({
            success: true,
            error: null,
            plan: plan
          });
        } catch (e) {
          resolve({
            success: false,
            error: 'parse_error: ' + e.message,
            plan: null
          });
        }
      });
    });

    req.on('error', (err) => {
      resolve({
        success: false,
        error: err.code || err.message,
        plan: null
      });
    });

    req.on('timeout', () => {
      req.destroy();
      resolve({
        success: false,
        error: 'timeout',
        plan: null
      });
    });

    req.write(postData);
    req.end();
  });
}

/**
 * Read existing context
 */
function readContext() {
  try {
    if (fs.existsSync(CONTEXT_FILE)) {
      const data = fs.readFileSync(CONTEXT_FILE, 'utf8');
      return JSON.parse(data);
    }
  } catch (e) {
    // Ignore errors
  }
  return {};
}

/**
 * Write context with plan
 */
function writeContext(context, plan, injectionMetadata) {
  try {
    const dir = path.dirname(CONTEXT_FILE);
    if (!fs.existsSync(dir)) {
      fs.mkdirSync(dir, { recursive: true });
    }

    const updatedContext = {
      ...context,
      plan: plan,
      injection_metadata: injectionMetadata
    };

    fs.writeFileSync(CONTEXT_FILE, JSON.stringify(updatedContext, null, 2));
    return true;
  } catch (e) {
    console.error('Failed to write context:', e.message);
    return false;
  }
}

/**
 * Log injection event
 */
function logInjection(event, data) {
  const logEntry = {
    timestamp: new Date().toISOString(),
    level: event.includes('error') || event.includes('fail') ? 'ERROR' : 
           event.includes('skip') || event.includes('fallback') ? 'WARN' : 'INFO',
    component: 'plan-injection-hook',
    event: event,
    ...data
  };
  
  // Write to stderr for gateway logs
  console.error(JSON.stringify(logEntry));
}

/**
 * Main handler
 */
async function handler(event) {
  const startTime = Date.now();

  // Validate event
  if (!event || !event.message) {
    return { status: 'ignored', reason: 'no_message' };
  }

  const message = event.message;
  const context = readContext();

  // Evaluate gate
  const gateResult = evaluateGate(message, context);

  // Gate blocked
  if (gateResult.result !== GATE_ALLOWED) {
    logInjection('gate_skipped', {
      reason: gateResult.reason,
      target_id: context.target_id
    });

    // Write metadata but don't fetch plan
    writeContext(context, null, {
      gate_result: gateResult.result,
      reason: gateResult.reason,
      fallback_triggered: false,
      timestamp: new Date().toISOString()
    });

    return {
      status: 'skipped',
      reason: gateResult.reason,
      injection: false
    };
  }

  // Extract user info
  const userId = context.target_id || message.sender_id || 'unknown';
  const userText = message.body || '';

  if (!userText.trim()) {
    return { status: 'ignored', reason: 'empty_message' };
  }

  // Fetch plan
  const fetchResult = await fetchPlan(userId, userText);
  const latency = Date.now() - startTime;

  // Handle failure
  if (!fetchResult.success) {
    const fallbackTriggered = PLAN_INJECTION_SOFT_FAIL;

    logInjection('plan_fetch_failed', {
      error: fetchResult.error,
      latency_ms: latency,
      target_id: userId,
      fallback_triggered: fallbackTriggered
    });

    // Write context without plan (soft fail)
    if (fallbackTriggered) {
      writeContext(context, null, {
        gate_result: GATE_ERROR,
        reason: fetchResult.error,
        latency_ms: latency,
        fallback_triggered: true,
        timestamp: new Date().toISOString()
      });
    }

    return {
      status: 'error',
      error: fetchResult.error,
      latency_ms: latency,
      fallback_triggered: fallbackTriggered,
      injection: false
    };
  }

  // Success
  logInjection('plan_injection_success', {
    target_id: userId,
    latency_ms: latency,
    tone: fetchResult.plan.tone,
    key_points_count: fetchResult.plan.key_points.length
  });

  // Write context with plan
  writeContext(context, fetchResult.plan, {
    gate_result: GATE_ALLOWED,
    latency_ms: latency,
    fallback_triggered: false,
    timestamp: new Date().toISOString()
  });

  return {
    status: 'success',
    latency_ms: latency,
    tone: fetchResult.plan.tone,
    injection: true
  };
}

module.exports = { handler };
