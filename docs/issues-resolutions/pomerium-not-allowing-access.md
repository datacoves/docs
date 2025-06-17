# Pomerium does not allow access to environments

## Problem

Launchapd works OK, but pomerium returning timeout, logs like these are found:

```
{"level":"info","X-Forwarded-For":["10.255.255.2,10.10.0.8"],"X-Forwarded-Host":["authenticate-dev123.orrum.datacoves.com"],"X-Forwarded-Port":["443"],"X-Forwarded-Proto":["http"],"X-Real-Ip":["10.255.255.2"],"ip":"127.0.0.1","user_agent":"Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36","request-id":"834a4284-9d39-474a-abb5-cd7203755386","error":"Bad Request: internal/sessions: session is not found","time":"2023-08-17T13:13:39Z","message":"authenticate: session load error"}
{"level":"info","service":"envoy","upstream-cluster":"pomerium-control-plane-http","method":"GET","authority":"authenticate-dev123.orrum.datacoves.com","path":"/.pomerium","user-agent":"Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36","referer":"","forwarded-for":"10.255.255.2,10.10.0.8","request-id":"834a4284-9d39-474a-abb5-cd7203755386","duration":15000.251354,"size":24,"response-code":504,"response-code-details":"upstream_response_timeout","time":"2023-08-17T13:13:55Z","message":"http-request"}
```

## Cause

This is a DNS resolution issue that pomerium is having. Typically this happens when the cluster model has wrong values on `internal_ip` or `external_ip`.
This could have happened when the DB was copied to a different cluster, of the cluster changed their IPs.

## Solution

Remove the values on those 2 fields and save the cluster model again. On `save`, it will regenerate those IPs and Pomerium will be reinstalled.