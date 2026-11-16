/**
 * J.A.R.V.I.S. ECOSYSTEM - JAVASCRIPT CORE CONCEPTS DEMONSTRATION & UTILITIES
 * Implements and documents:
 *   1. Event Loop (Call stack, Web APIs, Microtask queue, Macrotask queue)
 *   2. Promises vs Callbacks (Asynchronous error handling and chaining)
 *   3. async / await (Syntactic sugar over Promises for linear asynchronous control)
 *   4. Closures (Encapsulation, factory functions, state retention across executions)
 *   5. Hoisting (Variable and function declaration phases in V8 execution context)
 */

// =====================================================================
// 1. CLOSURES (Lexical Scoping & State Encapsulation)
// =====================================================================
/**
 * Demonstrates a Closure:
 * Inner function retains access to outer lexical scope variables (`telemetryHistory`)
 * even after the outer function `createTelemetryRecorder` has returned.
 */
export function createTelemetryRecorder(moduleName) {
  const telemetryHistory = []; // Private enclosed state

  return {
    recordPulse(metricName, value) {
      const pulse = {
        module: moduleName,
        metric: metricName,
        value,
        timestamp: Date.now()
      };
      telemetryHistory.push(pulse);
      return pulse;
    },
    getHistory() {
      // Returns a shallow copy to prevent external mutation of private state
      return [...telemetryHistory];
    },
    getAverageMetric(metricName) {
      const filtered = telemetryHistory.filter(p => p.metric === metricName);
      if (filtered.length === 0) return 0;
      const sum = filtered.reduce((acc, curr) => acc + curr.value, 0);
      return sum / filtered.length;
    }
  };
}


// =====================================================================
// 2. PROMISES VS CALLBACKS
// =====================================================================
/**
 * Legacy Callback Pattern:
 * Prone to callback hell and inversion of control.
 */
export function fetchSystemMetricsCallback(callback) {
  setTimeout(() => {
    try {
      const data = { cpu: 22.4, ram: 45.1, status: "ONLINE" };
      callback(null, data);
    } catch (err) {
      callback(err, null);
    }
  }, 100);
}

/**
 * Modern Promise Pattern:
 * Guaranteed fulfillment/rejection, composable with .then(), .catch(), .finally().
 */
export function fetchSystemMetricsPromise() {
  return new Promise((resolve, reject) => {
    setTimeout(() => {
      try {
        const data = { cpu: 22.4, ram: 45.1, status: "ONLINE", timestamp: Date.now() };
        resolve(data);
      } catch (err) {
        reject(new Error("Failed to sample system telemetry: " + err.message));
      }
    }, 100);
  });
}


// =====================================================================
// 3. ASYNC / AWAIT
// =====================================================================
/**
 * Modern async/await:
 * Non-blocking asynchronous execution that reads synchronously with try/catch error boundaries.
 */
export async function fetchHealthWithRetry(url, maxRetries = 2) {
  let attempt = 0;
  while (attempt <= maxRetries) {
    try {
      const response = await fetch(url, { headers: { "Accept": "application/json" } });
      if (!response.ok) {
        throw new Error(`HTTP Error ${response.status}`);
      }
      const json = await response.json();
      return json;
    } catch (error) {
      attempt++;
      if (attempt > maxRetries) {
        throw new Error(`Exhausted ${maxRetries} retries connecting to ${url}: ${error.message}`);
      }
      // Non-blocking backoff
      await new Promise(r => setTimeout(r, 200 * attempt));
    }
  }
}


// =====================================================================
// 4. JAVASCRIPT EVENT LOOP (Microtasks vs Macrotasks)
// =====================================================================
/**
 * Explains and executes order of operations in the JS Event Loop:
 * 1. Synchronous code runs on the Call Stack.
 * 2. Microtasks (Promise.then, queueMicrotask) execute immediately after the stack clears.
 * 3. Macrotasks (setTimeout, setInterval, I/O events) execute in subsequent ticks.
 */
export function runEventLoopDemonstration() {
  const executionOrder = [];

  executionOrder.push("1. Call Stack (Synchronous)");

  setTimeout(() => {
    executionOrder.push("4. Macrotask Queue (setTimeout)");
  }, 0);

  Promise.resolve().then(() => {
    executionOrder.push("2. Microtask Queue (Promise.then)");
  });

  queueMicrotask(() => {
    executionOrder.push("3. Microtask Queue (queueMicrotask)");
  });

  return executionOrder;
}


// =====================================================================
// 5. HOISTING (Declaration vs Initialization)
// =====================================================================
/**
 * Demonstrates Hoisting:
 * - Function declarations are fully hoisted with their definitions.
 * - Variables declared with `var` are hoisted as `undefined`.
 * - Variables declared with `let` and `const` are hoisted in Temporal Dead Zone (TDZ).
 */
export function demonstrateHoisting() {
  // Hoisted function invocation works before lexical declaration:
  const greeting = getGreetingText();

  function getGreetingText() {
    return "JARVIS Systems Initialized";
  }

  // Demonstration of TDZ safety:
  const systemName = "JARVIS";

  return {
    greeting,
    systemName,
    explanation: "Function declarations are hoisted completely; let/const remain in TDZ until evaluated."
  };
}
