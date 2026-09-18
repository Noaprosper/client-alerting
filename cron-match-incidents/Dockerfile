# Alert-client cron — Serverless Container image
# The Serverless Container must expose an HTTP listener (port 8080) so the
# CRON trigger can invoke it. server.py runs the sync on each invocation and
# returns an HTTP status, then keeps the listener alive.
#
# Build/arch: MUST target linux/amd64 (Scaleway containers run amd64):
#   docker build --platform linux/amd64 -t rg.fr-par.scw.cloud/rg-alert-client/match-incidents:latest .
FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY main.py server.py ./

EXPOSE 8080

CMD ["python", "server.py", "8080"]
