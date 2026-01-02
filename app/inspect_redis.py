from redis import Redis

r = Redis(host="127.0.0.1", port=6379, db=0)

print("celery queue length:", r.llen("celery"))
print("celery keys:", r.keys("*"))
