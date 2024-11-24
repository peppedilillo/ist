#!/bin/sh
exec redis-server --requirepass "${REDIS_PASSWORD}"