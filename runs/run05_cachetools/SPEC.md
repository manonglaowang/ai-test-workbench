# cachetools 规格说明（仅签名与文档，零实现）

> 本文件只包含类/方法签名与文档说明，不含任何实现代码。

## 模块说明

```
Extensible memoizing collections and decorators.
```

## class `Cache(collections.abc.MutableMapping)`

```
Mutable mapping to serve as a simple cache or cache base class.
```

### `Cache.__init__(self, maxsize, getsizeof=None)`

### `Cache.__getitem__(self, key)`

### `Cache.__setitem__(self, key, value)`

### `Cache.__delitem__(self, key)`

### `Cache.__contains__(self, key)`

### `Cache.__iter__(self)`

### `Cache.__len__(self)`

### `Cache.get(self, key, default=None)`

### `Cache.pop(self, key, default=__marker)`

### `Cache.setdefault(self, key, default=None)`

### `Cache.clear(self)`

### `Cache.maxsize(self)`

```
The maximum size of the cache.
```

### `Cache.currsize(self)`

```
The current size of the cache.
```

### `Cache.getsizeof(value)`

```
Return the size of a cache element's value.
```

## class `FIFOCache(Cache)`

```
First In First Out (FIFO) cache implementation.
```

### `FIFOCache.__init__(self, maxsize, getsizeof=None)`

### `FIFOCache.__setitem__(self, key, value, cache_setitem=Cache.__setitem__)`

### `FIFOCache.__delitem__(self, key, cache_delitem=Cache.__delitem__)`

### `FIFOCache.popitem(self)`

```
Remove and return the `(key, value)` pair first inserted.
```

### `FIFOCache.clear(self)`

## class `LFUCache(Cache)`

```
Least Frequently Used (LFU) cache implementation.
```

### `LFUCache.__init__(self, maxsize, getsizeof=None)`

### `LFUCache.__getitem__(self, key, cache_getitem=Cache.__getitem__)`

### `LFUCache.__setitem__(self, key, value, cache_setitem=Cache.__setitem__)`

### `LFUCache.__delitem__(self, key, cache_delitem=Cache.__delitem__)`

### `LFUCache.popitem(self)`

```
Remove and return the `(key, value)` pair least frequently used.
```

### `LFUCache.clear(self)`

## class `LRUCache(Cache)`

```
Least Recently Used (LRU) cache implementation.
```

### `LRUCache.__init__(self, maxsize, getsizeof=None)`

### `LRUCache.__getitem__(self, key, cache_getitem=Cache.__getitem__)`

### `LRUCache.__setitem__(self, key, value, cache_setitem=Cache.__setitem__)`

### `LRUCache.__delitem__(self, key, cache_delitem=Cache.__delitem__)`

### `LRUCache.popitem(self)`

```
Remove and return the `(key, value)` pair least recently used.
```

### `LRUCache.clear(self)`

## class `RRCache(Cache)`

```
Random Replacement (RR) cache implementation.
```

### `RRCache.__init__(self, maxsize, choice=random.choice, getsizeof=None)`

### `RRCache.choice(self)`

```
The `choice` function used by the cache.
```

### `RRCache.__setitem__(self, key, value, cache_setitem=Cache.__setitem__)`

### `RRCache.__delitem__(self, key, cache_delitem=Cache.__delitem__)`

### `RRCache.popitem(self)`

```
Remove and return a random `(key, value)` pair.
```

### `RRCache.clear(self)`

## class `TTLCache(_TimedCache)`

```
LRU Cache implementation with per-item time-to-live (TTL) value.
```

### `TTLCache.__init__(self, maxsize, ttl, timer=time.monotonic, getsizeof=None)`

### `TTLCache.__contains__(self, key)`

### `TTLCache.__getitem__(self, key, cache_getitem=Cache.__getitem__)`

### `TTLCache.__setitem__(self, key, value, cache_setitem=Cache.__setitem__)`

### `TTLCache.__delitem__(self, key, cache_delitem=Cache.__delitem__)`

### `TTLCache.__iter__(self)`

### `TTLCache.ttl(self)`

```
The time-to-live value of the cache's items.
```

### `TTLCache.expire(self, time=None)`

```
Remove expired items from the cache and return an iterable of the
expired `(key, value)` pairs.
```

### `TTLCache.popitem(self)`

```
Remove and return the `(key, value)` pair least recently used that
has not already expired.
```

### `TTLCache.clear(self)`

## class `TLRUCache(_TimedCache)`

```
Time aware Least Recently Used (TLRU) cache implementation.
```

### `TLRUCache.__init__(self, maxsize, ttu, timer=time.monotonic, getsizeof=None)`

### `TLRUCache.__contains__(self, key)`

### `TLRUCache.__getitem__(self, key, cache_getitem=Cache.__getitem__)`

### `TLRUCache.__setitem__(self, key, value, cache_setitem=Cache.__setitem__)`

### `TLRUCache.__delitem__(self, key, cache_delitem=Cache.__delitem__)`

### `TLRUCache.__iter__(self)`

### `TLRUCache.ttu(self)`

```
The local time-to-use function used by the cache.
```

### `TLRUCache.expire(self, time=None)`

```
Remove expired items from the cache and return an iterable of the
expired `(key, value)` pairs.
```

### `TLRUCache.popitem(self)`

```
Remove and return the `(key, value)` pair least recently used that
has not already expired.
```

### `TLRUCache.clear(self)`
