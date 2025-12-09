# Valeros Backend
> [!WARNING]
> This setup is intended as a work-in-progress **proof of concept / demo**. It is **not** (yet) production ready: for example, Elasticsearch currently runs without authentication.

This project provides a **fully open source** data pipeline and backend for turning RDF data in Turtle (`.ttl`) format into searchable Elasticsearch indices and QLever SPARQL endpoints.

- Data is automatically ingested by an indexer container, indexed into [Elasticsearch](https://github.com/elastic/elasticsearch), and exposed as SPARQL endpoints via [QLever](https://github.com/ad-freiburg/qlever/).
- [QLever UI](https://github.com/qlever-dev/qlever-ui) offers a web interface for interactive SPARQL querying.
- [Caddy](https://github.com/caddyserver/caddy) is used as a reverse proxy for all services and includes automatic HTTPS/SSL via [Let’s Encrypt](https://letsencrypt.org/).
- [Valeros](https://github.com/view-a-LOD/Valeros/tree/feature/datasets-demo) can be used as a flexible and configurable viewer/search interface for your datasets using these endpoints.

If you have any questions or comments about the project, please reach out to mail@simondirks.com.

## Stack

- **Elasticsearch** (single-node, Docker)
- **QLever** (started via [QLever CLI](https://github.com/ad-freiburg/qlever/) as Docker containers)
- **QLever UI** (`adfreiburg/qlever-ui` Docker image)
- **Caddy** (reverse proxy, configured via `Caddyfile`)
- **Data** in Turtle (`.ttl`) format under `data/`

---

## Prerequisites

- Docker
- Docker Compose (if not included with Docker)
- (Optional) Caddy on your server if you are using the provided `Caddyfile`

---

## Configuration

1. **Environment variables**

   Copy the example environment file and adjust values:

   ```bash
   cp .env.example .env
   ```

   Important variables:

   - `QLEVERUI_SECRET_KEY` – required, secret key for QLever UI.
   - `QLEVERUI_DEBUG` – optional, defaults to `False`.
   - `QLEVERUI_DATABASE_URL` – optional, defaults to `sqlite:////app/db/qleverui.sqlite3`.
   - `QLEVERUI_CSRF_TRUSTED_ORIGINS` – required, comma-separated list of trusted origins (typically the domain on which you will host QLever UI).

2. **Elasticsearch indexing (optional)**

   The `elastic-indexer` reads `.ttl` files from the local `./data` directory, which is mounted into the container at `/app/data`, and pushes them into Elasticsearch.

   Which files are indexed is controlled by the `TTL_FILES` environment variable in `docker-compose.yml`, for example:

   ```yaml
   elastic-indexer:
     environment:
       - TTL_FILES=Test-Amerongen/Test-Amerongen.ttl,PoC2024/PoC2024.ttl,PoCAmerongen2024/PoCAmerongen2024.ttl,locaties/locaties.ttl,actoren/actoren.ttl
   ```

   To index different datasets, simply change the comma-separated list of paths (relative to `./data`) in `TTL_FILES`.

   Indexing is **optional**: you can leave `elastic-indexer` disabled or `TTL_FILES` empty and still run QLever/QLever UI to provide SPARQL endpoints for your QLever datasets only.

---

## Running the stack

From the project root:

```bash
docker compose up -d
```

This will start:

- `elasticsearch` on `localhost:9200`
- `qlever-ui` on `localhost:8176`
- `elastic-indexer` (one-off indexer container, depends on a healthy Elasticsearch)

Check container status:

```bash
docker compose ps
```

Logs (e.g. for the indexer):

```bash
docker compose logs -f elastic-indexer
```

---

## Starting QLever SPARQL endpoints

The QLever SPARQL endpoints are managed via the [QLever CLI](https://github.com/ad-freiburg/qlever/) and the helper script in `qlever/start_qlever_for_all_datasets.sh`.

Each dataset directory under `./data` that should become a SPARQL endpoint must contain a `Qleverfile` describing how to build and run that endpoint.

1. **Create and activate a Python virtual environment** (recommended)

   From the project root:

   ```bash
   cd qlever
   python -m venv .venv
   source .venv/bin/activate
   ```

2. **Install the QLever CLI**

   ```bash
   pip install qlever
   ```

   For more details and options, see the QLever Quickstart section in the official docs: https://github.com/ad-freiburg/qlever

3. **Start QLever for all datasets**

   From the `qlever` folder, run:

   ```bash
   ./start_qlever_for_all_datasets.sh ../data
   ```

   This script will iterate over all subdirectories in `data`, and for each directory that contains a `Qleverfile`, use the QLever CLI to start the corresponding SPARQL endpoint on its configured port.

   Note that to make these endpoints available in the web interface, you still need to add/configure them in QLever UI.

## Reverse proxy (Caddy)

For installation instructions, see the official Caddy docs: https://caddyserver.com/docs/install

Of course, you are also free to use another reverse proxy (for example nginx or Traefik).

The `Caddyfile` contains example vhosts:

- `elastic.linkeddataviewer.nl` → reverse proxy to `:9200`
- `query.linkeddataviewer.nl` → reverse proxy to `:8176` (QLever UI)
- `sparql.linkeddataviewer.nl` → paths like `/Test-Amerongen/*`, `/PoC2024/*`, `/actoren/*`, etc. → reverse proxy to various QLever SPARQL endpoints, each running on its own port (`:7001` – `:7013`)

To use this on a server with Caddy:

1. Copy `Caddyfile` to your Caddy configuration directory.
2. Adjust domain names and upstream ports if needed.
3. Reload Caddy, for example:

   ```bash
   caddy reload --config /path/to/Caddyfile
   ```
