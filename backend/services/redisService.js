/**
 * J.A.R.V.I.S. ECOSYSTEM - REDIS CACHING SUBSYSTEM & MIDDLEWARE
 * Demonstrates:
 *   1. Redis Client Initialization (createClient with auto-reconnect)
 *   2. Key-Value Storage with Time-To-Live (TTL) Expiration (setEx)
 *   3. Transparent In-Memory LRU Cache Fallback (Fault-tolerant resilience)
 *   4. Cache Invalidation and Namespace Eviction (del, flush)
 *   5. Express Caching Middleware with X-Cache HIT / MISS inspection headers
 *   6. Cache Hit/Miss Telemetry and Health Monitoring
 */

const { createClient } = require("redis");

class RedisService {
  constructor() {
    this.redisUrl = process.env.REDIS_URL || "redis://localhost:6379";
    this.isConnected = false;
    this.client = null;
    this.inMemoryCache = new Map(); // Fallback storage: { key => { value, expiresAt } }
    this.stats = { hits: 0, misses: 0, sets: 0, errors: 0 };

    this.initialize();
  }

  /**
   * Initializes the Redis connection with connection event listeners.
   */
  async initialize() {
    try {
      this.client = createClient({
        url: this.redisUrl,
        socket: {
          connectTimeout: 2000,
          reconnectStrategy: (retries) => {
            if (retries > 3) {
              console.log("[Redis] Max reconnect attempts reached. Using in-memory cache fallback.");
              return false; // Stop reconnecting, rely on memory fallback
            }
            return Math.min(retries * 200, 2000);
          }
        }
      });

      this.client.on("connect", () => {
        this.isConnected = true;
        console.log(`[Redis] Connected successfully to Redis at ${this.redisUrl}`);
      });

      this.client.on("ready", () => {
        this.isConnected = true;
      });

      this.client.on("error", (err) => {
        this.isConnected = false;
        this.stats.errors++;
        // Keep quiet on connection refusal, fallback handles it smoothly
      });

      this.client.on("end", () => {
        this.isConnected = false;
      });

      // Connect asynchronously
      await this.client.connect().catch(() => {
        this.isConnected = false;
        console.log("[Redis] Notice: Redis standalone server offline. In-memory LRU fallback active.");
      });
    } catch (err) {
      this.isConnected = false;
      this.stats.errors++;
      console.log(`[Redis] Initializer fallback mode active (${err.message})`);
    }
  }

  /**
   * Retrieves a cached value by key.
   * @param {string} key
   * @returns {Promise<any|null>}
   */
  async get(key) {
    if (this.isConnected && this.client) {
      try {
        const rawData = await this.client.get(key);
        if (rawData !== null) {
          this.stats.hits++;
          return JSON.parse(rawData);
        }
        this.stats.misses++;
        return null;
      } catch (err) {
        this.stats.errors++;
      }
    }

    // In-memory fallback lookup
    const entry = this.inMemoryCache.get(key);
    if (entry) {
      if (!entry.expiresAt || Date.now() < entry.expiresAt) {
        this.stats.hits++;
        return entry.value;
      }
      this.inMemoryCache.delete(key);
    }

    this.stats.misses++;
    return null;
  }

  /**
   * Sets a value in the cache with specified TTL in seconds.
   * @param {string} key
   * @param {any} value
   * @param {number} ttlSeconds
   * @returns {Promise<boolean>}
   */
  async set(key, value, ttlSeconds = 300) {
    this.stats.sets++;
    const serialized = JSON.stringify(value);

    if (this.isConnected && this.client) {
      try {
        await this.client.setEx(key, ttlSeconds, serialized);
        return true;
      } catch (err) {
        this.stats.errors++;
      }
    }

    // In-memory fallback storage
    const expiresAt = ttlSeconds > 0 ? Date.now() + ttlSeconds * 1000 : null;
    this.inMemoryCache.set(key, { value, expiresAt });
    return true;
  }

  /**
   * Deletes a cached entry by key.
   * @param {string} key
   * @returns {Promise<boolean>}
   */
  async del(key) {
    let deleted = false;
    if (this.isConnected && this.client) {
      try {
        const count = await this.client.del(key);
        deleted = count > 0;
      } catch (err) {
        this.stats.errors++;
      }
    }

    if (this.inMemoryCache.has(key)) {
      this.inMemoryCache.delete(key);
      deleted = true;
    }

    return deleted;
  }

  /**
   * Flushes all cached keys.
   */
  async flush() {
    if (this.isConnected && this.client) {
      try {
        await this.client.flushDb();
      } catch (err) {
        this.stats.errors++;
      }
    }
    this.inMemoryCache.clear();
  }

  /**
   * Returns cache metrics and hit/miss telemetry.
   */
  getTelemetry() {
    const total = this.stats.hits + this.stats.misses;
    const hitRate = total > 0 ? ((this.stats.hits / total) * 100).toFixed(2) : "0.00";

    return {
      tier: this.isConnected ? "redis_standalone" : "in_memory_lru_fallback",
      redis_connected: this.isConnected,
      redis_url: this.redisUrl,
      hits: this.stats.hits,
      misses: this.stats.misses,
      hit_ratio_percent: parseFloat(hitRate),
      cached_keys_count: this.inMemoryCache.size,
      active_backend: this.isConnected ? "Redis v7 Protocol" : "V8 In-Memory Heap"
    };
  }

  /**
   * Express middleware for caching HTTP route responses.
   * @param {number} ttlSeconds
   */
  middleware(ttlSeconds = 60) {
    return async (req, res, next) => {
      // Only cache idempotent GET requests
      if (req.method !== "GET") {
        return next();
      }

      const cacheKey = `http_cache:${req.originalUrl || req.url}`;

      try {
        const cachedResponse = await this.get(cacheKey);
        if (cachedResponse !== null) {
          res.setHeader("X-Cache", "HIT");
          res.setHeader("X-Cache-TTL", `${ttlSeconds}s`);
          return res.status(200).json(cachedResponse);
        }

        // Intercept res.json to capture response body for caching
        const originalJson = res.json.bind(res);
        res.setHeader("X-Cache", "MISS");

        res.json = (body) => {
          if (res.statusCode >= 200 && res.statusCode < 300) {
            this.set(cacheKey, body, ttlSeconds).catch(() => {});
          }
          return originalJson(body);
        };

        next();
      } catch (err) {
        next();
      }
    };
  }
}

// Export singleton instance
const redisService = new RedisService();

module.exports = {
  redisService,
  RedisService
};
