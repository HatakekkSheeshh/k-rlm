# 1) Build RAPTOR tree
curl -sS -o /tmp/raptor_build.json -w 'build_http=%{http_code} time=%{time_total}\n' --max-time 90 \
  -X POST http://localhost:8000/api/v1/graph/raptor/build \
  -F 'file=@/tmp/raptor_fast.txt' \
  -F 'model=phi3:mini' \
  -F 'chunk_size=800' \
  -F 'max_levels=1'

cat /tmp/raptor_build.json

# 2) Verify tree exists
curl -sS --max-time 10 \
  "http://localhost:8000/api/v1/graph/raptor/stats?document=raptor_fast.txt"

# 3) Query RAPTOR
curl -sS -o /tmp/raptor_query.json -w 'query_http=%{http_code} time=%{time_total} err=%{errormsg}\n' --max-time 60 \
  -X POST http://localhost:8000/api/v1/inference \
  -H 'Content-Type: application/json' \
  -d '{"prompt":"Summarize in one sentence.","model":"phi3:mini","strategy":"RAPTOR (Hierarchical)","document":"raptor_fast.txt"}'

cat /tmp/raptor_query.json