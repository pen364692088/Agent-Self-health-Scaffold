#!/usr/bin/env bash
set -euo pipefail

if [ $# -lt 1 ]; then
  echo "Usage: $(basename "$0") <query> [limit]"
  exit 1
fi

QUERY="$1"
LIMIT="${2:-5}"

curl -sS --get 'http://localhost/search' \
  --data-urlencode "q=${QUERY}" \
  --data-urlencode 'format=json' \
| python3 -c 'import json,sys
limit=int(sys.argv[1])
data=json.load(sys.stdin)
for i,r in enumerate(data.get("results",[])[:limit],1):
    t=(r.get("title") or "").strip().replace("\n"," ")
    u=r.get("url") or ""
    c=(r.get("content") or "").strip().replace("\n"," ")
    print(f"{i}. {t}\n   {u}")
    if c:
        print(f"   {c[:180]}")' "$LIMIT"
