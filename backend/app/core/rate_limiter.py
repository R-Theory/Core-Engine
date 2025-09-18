"""
Advanced rate limiting and throttling system for Core Engine.
Supports multiple rate limiting strategies and algorithms.
"""

import time
import asyncio
from typing import Dict, Optional, Tuple, Any
from fastapi import Request, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response, JSONResponse
import logging
from dataclasses import dataclass
from enum import Enum
import redis.asyncio as redis
from app.core.config import settings

logger = logging.getLogger(__name__)


class RateLimitStrategy(Enum):
    """Rate limiting strategies"""
    FIXED_WINDOW = "fixed_window"
    SLIDING_WINDOW = "sliding_window"
    TOKEN_BUCKET = "token_bucket"
    LEAKY_BUCKET = "leaky_bucket"


@dataclass
class RateLimit:
    """Rate limit configuration"""
    requests: int
    window: int  # seconds
    strategy: RateLimitStrategy = RateLimitStrategy.FIXED_WINDOW
    burst: Optional[int] = None  # For token bucket


class RateLimiter:
    """Advanced rate limiter with multiple algorithms"""

    def __init__(self):
        self.redis_client = None
        self.memory_store = {}  # Fallback to memory if Redis unavailable

    async def connect(self):
        """Initialize Redis connection for distributed rate limiting"""
        try:
            self.redis_client = redis.Redis(
                host=getattr(settings, 'REDIS_HOST', 'localhost'),
                port=getattr(settings, 'REDIS_PORT', 6379),
                db=1,  # Use separate DB for rate limiting
                password=getattr(settings, 'REDIS_PASSWORD', None),
                max_connections=10,
            )
            await self.redis_client.ping()
            logger.info("Rate limiter Redis connection established")
        except Exception as e:
            logger.warning(f"Redis unavailable for rate limiting, using memory store: {e}")
            self.redis_client = None

    async def check_rate_limit(
        self,
        identifier: str,
        rate_limit: RateLimit
    ) -> Tuple[bool, Dict[str, Any]]:
        """
        Check if request is within rate limit

        Returns:
            (allowed, metadata) where metadata contains rate limit info
        """
        if rate_limit.strategy == RateLimitStrategy.FIXED_WINDOW:
            return await self._fixed_window(identifier, rate_limit)
        elif rate_limit.strategy == RateLimitStrategy.SLIDING_WINDOW:
            return await self._sliding_window(identifier, rate_limit)
        elif rate_limit.strategy == RateLimitStrategy.TOKEN_BUCKET:
            return await self._token_bucket(identifier, rate_limit)
        elif rate_limit.strategy == RateLimitStrategy.LEAKY_BUCKET:
            return await self._leaky_bucket(identifier, rate_limit)
        else:
            raise ValueError(f"Unknown rate limit strategy: {rate_limit.strategy}")

    async def _fixed_window(self, identifier: str, rate_limit: RateLimit) -> Tuple[bool, Dict]:
        """Fixed window rate limiting"""
        now = int(time.time())
        window_start = now - (now % rate_limit.window)
        key = f"rate_limit:fixed:{identifier}:{window_start}"

        if self.redis_client:
            try:
                # Atomic increment with expiry
                pipe = self.redis_client.pipeline()
                pipe.incr(key)
                pipe.expire(key, rate_limit.window)
                results = await pipe.execute()
                current_count = results[0]
            except Exception as e:
                logger.error(f"Redis error in fixed window: {e}")
                return True, {}  # Allow on Redis error
        else:
            # Memory fallback
            if key not in self.memory_store:
                self.memory_store[key] = {"count": 0, "expires": window_start + rate_limit.window}

            # Clean expired entries
            if time.time() > self.memory_store[key]["expires"]:
                del self.memory_store[key]
                self.memory_store[key] = {"count": 0, "expires": window_start + rate_limit.window}

            self.memory_store[key]["count"] += 1
            current_count = self.memory_store[key]["count"]

        allowed = current_count <= rate_limit.requests
        reset_time = window_start + rate_limit.window

        metadata = {
            "limit": rate_limit.requests,
            "remaining": max(0, rate_limit.requests - current_count),
            "reset": reset_time,
            "strategy": "fixed_window"
        }

        return allowed, metadata

    async def _sliding_window(self, identifier: str, rate_limit: RateLimit) -> Tuple[bool, Dict]:
        """Sliding window rate limiting using sorted sets"""
        now = time.time()
        key = f"rate_limit:sliding:{identifier}"
        window_start = now - rate_limit.window

        if self.redis_client:
            try:
                pipe = self.redis_client.pipeline()
                # Remove old entries
                pipe.zremrangebyscore(key, 0, window_start)
                # Count current entries
                pipe.zcard(key)
                # Add current request
                pipe.zadd(key, {str(now): now})
                # Set expiry
                pipe.expire(key, rate_limit.window)
                results = await pipe.execute()
                current_count = results[1] + 1  # +1 for current request
            except Exception as e:
                logger.error(f"Redis error in sliding window: {e}")
                return True, {}
        else:
            # Memory fallback with sorted list
            if key not in self.memory_store:
                self.memory_store[key] = []

            # Remove old entries
            self.memory_store[key] = [
                timestamp for timestamp in self.memory_store[key]
                if timestamp > window_start
            ]

            # Add current request
            self.memory_store[key].append(now)
            current_count = len(self.memory_store[key])

        allowed = current_count <= rate_limit.requests

        metadata = {
            "limit": rate_limit.requests,
            "remaining": max(0, rate_limit.requests - current_count),
            "reset": int(now + rate_limit.window),
            "strategy": "sliding_window"
        }

        return allowed, metadata

    async def _token_bucket(self, identifier: str, rate_limit: RateLimit) -> Tuple[bool, Dict]:
        """Token bucket rate limiting"""
        now = time.time()
        key = f"rate_limit:token:{identifier}"
        burst = rate_limit.burst or rate_limit.requests
        refill_rate = rate_limit.requests / rate_limit.window

        if self.redis_client:
            try:
                # Get current bucket state
                bucket_data = await self.redis_client.hmget(
                    key, "tokens", "last_refill"
                )

                if bucket_data[0] is None:
                    # Initialize bucket
                    tokens = float(burst)
                    last_refill = now
                else:
                    tokens = float(bucket_data[0])
                    last_refill = float(bucket_data[1])

                # Calculate tokens to add
                time_passed = now - last_refill
                tokens_to_add = time_passed * refill_rate
                tokens = min(burst, tokens + tokens_to_add)

                # Check if request can be satisfied
                if tokens >= 1:
                    tokens -= 1
                    allowed = True
                else:
                    allowed = False

                # Update bucket
                await self.redis_client.hmset(key, {
                    "tokens": tokens,
                    "last_refill": now
                })
                await self.redis_client.expire(key, rate_limit.window * 2)

            except Exception as e:
                logger.error(f"Redis error in token bucket: {e}")
                return True, {}
        else:
            # Memory fallback
            if key not in self.memory_store:
                self.memory_store[key] = {
                    "tokens": float(burst),
                    "last_refill": now
                }

            bucket = self.memory_store[key]
            time_passed = now - bucket["last_refill"]
            tokens_to_add = time_passed * refill_rate
            bucket["tokens"] = min(burst, bucket["tokens"] + tokens_to_add)
            bucket["last_refill"] = now

            if bucket["tokens"] >= 1:
                bucket["tokens"] -= 1
                allowed = True
                tokens = bucket["tokens"]
            else:
                allowed = False
                tokens = bucket["tokens"]

        metadata = {
            "limit": rate_limit.requests,
            "burst": burst,
            "tokens": int(tokens),
            "strategy": "token_bucket"
        }

        return allowed, metadata

    async def _leaky_bucket(self, identifier: str, rate_limit: RateLimit) -> Tuple[bool, Dict]:
        """Leaky bucket rate limiting"""
        now = time.time()
        key = f"rate_limit:leaky:{identifier}"
        leak_rate = rate_limit.requests / rate_limit.window
        bucket_size = rate_limit.burst or rate_limit.requests

        if self.redis_client:
            try:
                bucket_data = await self.redis_client.hmget(
                    key, "volume", "last_leak"
                )

                if bucket_data[0] is None:
                    volume = 0.0
                    last_leak = now
                else:
                    volume = float(bucket_data[0])
                    last_leak = float(bucket_data[1])

                # Calculate leaked volume
                time_passed = now - last_leak
                leaked = time_passed * leak_rate
                volume = max(0, volume - leaked)

                # Check if bucket can accept new request
                if volume < bucket_size:
                    volume += 1
                    allowed = True
                else:
                    allowed = False

                # Update bucket
                await self.redis_client.hmset(key, {
                    "volume": volume,
                    "last_leak": now
                })
                await self.redis_client.expire(key, rate_limit.window * 2)

            except Exception as e:
                logger.error(f"Redis error in leaky bucket: {e}")
                return True, {}
        else:
            # Memory fallback
            if key not in self.memory_store:
                self.memory_store[key] = {
                    "volume": 0.0,
                    "last_leak": now
                }

            bucket = self.memory_store[key]
            time_passed = now - bucket["last_leak"]
            leaked = time_passed * leak_rate
            bucket["volume"] = max(0, bucket["volume"] - leaked)
            bucket["last_leak"] = now

            if bucket["volume"] < bucket_size:
                bucket["volume"] += 1
                allowed = True
            else:
                allowed = False

        metadata = {
            "limit": rate_limit.requests,
            "bucket_size": bucket_size,
            "volume": int(volume),
            "strategy": "leaky_bucket"
        }

        return allowed, metadata


# Global rate limiter instance
rate_limiter = RateLimiter()


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Middleware for applying rate limits to HTTP requests"""

    def __init__(self, app, rate_limits: Dict[str, RateLimit] = None):
        super().__init__(app)
        self.rate_limits = rate_limits or {}
        # Default rate limits
        self.default_limits = {
            "default": RateLimit(100, 60),  # 100 requests per minute
            "auth": RateLimit(5, 60),  # 5 auth requests per minute
            "upload": RateLimit(10, 60),  # 10 uploads per minute
        }

    def get_client_identifier(self, request: Request) -> str:
        """Generate client identifier for rate limiting"""
        # Try to get user ID from request (if authenticated)
        user_id = getattr(request.state, 'user_id', None)
        if user_id:
            return f"user:{user_id}"

        # Fall back to IP address
        forwarded_for = request.headers.get('X-Forwarded-For')
        if forwarded_for:
            client_ip = forwarded_for.split(',')[0].strip()
        else:
            client_ip = request.client.host

        return f"ip:{client_ip}"

    def get_rate_limit_for_endpoint(self, request: Request) -> RateLimit:
        """Determine rate limit for specific endpoint"""
        path = request.url.path

        # Check for specific endpoint limits
        for pattern, limit in self.rate_limits.items():
            if pattern in path:
                return limit

        # Apply specific limits for certain endpoints
        if "/auth/" in path:
            return self.default_limits["auth"]
        elif "/upload" in path or "/documents" in path:
            return self.default_limits["upload"]
        else:
            return self.default_limits["default"]

    async def dispatch(self, request: Request, call_next):
        # Skip rate limiting for health checks
        if request.url.path in ["/health", "/metrics"]:
            return await call_next(request)

        # Get client identifier and rate limit
        client_id = self.get_client_identifier(request)
        rate_limit = self.get_rate_limit_for_endpoint(request)

        # Check rate limit
        allowed, metadata = await rate_limiter.check_rate_limit(client_id, rate_limit)

        if not allowed:
            # Rate limit exceeded
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={
                    "error": "Rate limit exceeded",
                    "message": f"Too many requests. Limit: {metadata.get('limit', 'unknown')} per {rate_limit.window}s",
                    "retry_after": metadata.get('reset', time.time() + rate_limit.window) - time.time()
                },
                headers={
                    "X-RateLimit-Limit": str(metadata.get('limit', rate_limit.requests)),
                    "X-RateLimit-Remaining": str(metadata.get('remaining', 0)),
                    "X-RateLimit-Reset": str(metadata.get('reset', time.time() + rate_limit.window)),
                    "Retry-After": str(int(metadata.get('reset', time.time() + rate_limit.window) - time.time()))
                }
            )

        # Add rate limit headers to response
        response = await call_next(request)

        # Add rate limit info to response headers
        response.headers["X-RateLimit-Limit"] = str(metadata.get('limit', rate_limit.requests))
        response.headers["X-RateLimit-Remaining"] = str(metadata.get('remaining', 0))
        response.headers["X-RateLimit-Reset"] = str(metadata.get('reset', time.time() + rate_limit.window))

        return response


# Decorator for applying rate limits to specific functions
def rate_limit(requests: int, window: int, strategy: RateLimitStrategy = RateLimitStrategy.FIXED_WINDOW):
    """Decorator for rate limiting specific functions"""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            # Extract request from args (assuming FastAPI dependency)
            request = None
            for arg in args:
                if isinstance(arg, Request):
                    request = arg
                    break

            if request:
                client_id = RateLimitMiddleware.get_client_identifier(None, request)
                limit = RateLimit(requests, window, strategy)
                allowed, metadata = await rate_limiter.check_rate_limit(client_id, limit)

                if not allowed:
                    raise HTTPException(
                        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                        detail={
                            "error": "Rate limit exceeded",
                            "retry_after": metadata.get('reset', time.time() + window) - time.time()
                        }
                    )

            return await func(*args, **kwargs) if asyncio.iscoroutinefunction(func) else func(*args, **kwargs)

        return wrapper
    return decorator