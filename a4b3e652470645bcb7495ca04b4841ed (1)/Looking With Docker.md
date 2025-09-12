# Looking With Docker

Short, practical commands to inspect the current state of a Docker-based app. Safe to run unless noted.

## Basics
- `docker version`: Client/server versions.
- `docker info`: System-wide info (containers, images, runtimes, storage, cgroup).
- `docker context ls`: Show contexts; switch with `docker context use <name>`.
- `docker system df`: Disk usage by images/containers/volumes/build cache.

## Containers (running state)
- `docker ps`: List running containers.
- `docker ps -a`: Include exited/stopped containers.
- `docker ps --filter status=exited`: Only exited containers.
- `docker ps --format '{{.ID}}  {{.Names}}  {{.Status}}  {{.Ports}}'`: Custom view.
- `docker top <container>`: Show processes inside a container.
- `docker logs <container>`: Fetch logs.
- `docker logs -f --since=1h <container>`: Follow logs from last hour.
- `docker stats [<container>...]`: Live CPU/mem I/O stats.
- `docker port <container>`: Published port mappings.

## Container details (deep dive)
- `docker inspect <container>`: Full JSON details.
- `docker inspect -f '{{.Name}} {{.State.Status}} {{.State.Health.Status}}' <container>`: Quick fields.
- `docker inspect -f '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}' <container>`: Container IP.
- `docker diff <container>`: FS changes (A: added, C: changed, D: deleted) vs image.
- `docker exec -it <container> sh` (or `bash`): Shell into a running container to look around.
- `docker cp <container>:/path/in/container ./local/dir`: Copy files out for inspection.

## Images
- `docker images` (alias: `docker image ls`): List images.
- `docker images -a`: Include intermediate layers.
- `docker image inspect <image>`: Metadata (env, entrypoint, layers).
- `docker history <image>`: Layer history with sizes and commands.
- `docker images --filter dangling=true`: Dangling images (no tag).

## Networks
- `docker network ls`: List networks.
- `docker network inspect <network>`: Subnets, attached containers, drivers.
- `docker network inspect -f '{{range .IPAM.Config}}{{.Subnet}}{{end}}' <network>`: Subnet summary.

## Volumes
- `docker volume ls`: List volumes.
- `docker volume inspect <volume>`: Host mountpoint and usage.
- `docker system df --volumes`: Disk usage including volumes.

## Compose (v2)
- `docker compose ls`: Projects found by Compose.
- `docker compose ps`: Services and state for current project.
- `docker compose top`: Processes across services.
- `docker compose logs -f --since=10m`: Follow recent logs for all services.
- `docker compose logs -f <service>`: Logs for one service.
- `docker compose config`: Render the merged, validated config.
- `docker compose exec <service> sh`: Shell into a service container.
- `docker compose port <service> <containerPort>`: Published port for a service.

Note: If you use legacy v1, replace `docker compose` with `docker-compose`.

## Filtering and formatting tips
- By name: `docker ps --filter name=api`.
- By label: `docker ps --filter label=com.docker.compose.service=web`.
- Since/until: `docker logs --since=30m <container>` or `--until=2024-09-01T12:00:00`.
- No truncation: append `--no-trunc` to many commands (e.g., `docker ps --no-trunc`).
- Go templates: use `-f '{{json .}}'` or custom fields for `inspect` outputs.

## Troubleshooting quick checks
- Health: `docker inspect -f '{{.State.Health.Status}}' <container>`.
- Restarts: `docker inspect -f '{{.RestartCount}}' <container>`.
- Exit code (last): `docker inspect -f '{{.State.ExitCode}}' <container>`.
- Last 100 log lines: `docker logs --tail=100 <container>`.
- Port conflicts: `docker ps --format '{{.Names}} -> {{.Ports}}' | rg ':\d+->'`.

## System events (live)
- `docker events --since=1h`: Stream engine events (start/stop/restart, pulls, health).

## Safe cleanup (optional, be careful)
- `docker container prune`: Remove stopped containers. DESTRUCTIVE.
- `docker image prune`: Remove unused images. DESTRUCTIVE.
- `docker volume prune`: Remove unused volumes. DESTRUCTIVE.
- `docker network prune`: Remove unused networks. DESTRUCTIVE.
- `docker system prune [-a]`: Remove all unused data (add `-a` for images without containers). DESTRUCTIVE.

## Handy one-liners
- All container names + status: `docker ps -a --format '{{.Names}}  {{.Status}}'`.
- Container -> image mapping: `docker ps -a --format '{{.Names}}  {{.Image}}'`.
- Largest images: `docker images --format '{{.Repository}}:{{.Tag}}  {{.Size}}' | sort -h -k2`.
- Per-service logs (Compose): `docker compose logs -f --since=1h <service>`.

## Where to look, in practice
- Start with: `docker ps`, `docker compose ps`, `docker logs -f`.
- If something restarts: check `health`, `RestartCount`, recent `logs`.
- If networking odd: check `docker network inspect` and service `ports`.
- If disk high: `docker system df`, then `image/volume prune` if safe.
- If config confusion: `docker compose config` to view effective config.

---
Tip: Add labels to services (`labels:` in Compose) and filter by them to quickly scope commands in multi-service setups.
