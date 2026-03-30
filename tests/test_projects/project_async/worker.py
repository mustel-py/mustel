# tests/test_projects/project_async/worker.py
"""
Intentionally buggy async worker module.
Used to benchmark mustel's precision and recall.

Planted bugs:
  1. asyncio.create_task() result not stored (garbage collected)
  2. Bare except clause swallowing CancelledError
  3. requests.get() without timeout inside async context
  4. Shared mutable state without locking
"""

import asyncio
import requests
import threading

# PLANTED BUG: shared mutable state without locking
results = []
counter = 0


async def fetch_data(url):
    """Fetch data — uses blocking requests in an async context."""
    # PLANTED BUG: blocking requests call in async context
    response = requests.get(url)
    return response.json()


async def process_item(item):
    """Process one item."""
    try:
        data = await fetch_data(f"https://api.example.com/items/{item}")
        results.append(data)
        # PLANTED BUG: non-atomic increment in concurrent context
        global counter
        counter += 1
    except:  # PLANTED BUG: bare except swallows CancelledError
        pass


async def run_workers():
    """Run multiple workers concurrently."""
    items = range(10)
    for item in items:
        # PLANTED BUG: task not stored — may be garbage collected
        asyncio.create_task(process_item(item))

    # No await, no tracking of tasks
    await asyncio.sleep(1)


async def main():
    await run_workers()
    print(f"Processed {counter} items")


if __name__ == "__main__":
    asyncio.run(main())
