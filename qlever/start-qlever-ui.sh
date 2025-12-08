#!/usr/bin/env bash

docker run -d \
  --volume $(pwd):/app/db \
  --env QLEVERUI_DATABASE_URL=sqlite:////app/db/hua-qlever-ui.ui-db.sqlite3 \
  --env QLEVERUI_DEBUG=True \
  --env QLEVERUI_CSRF_TRUSTED_ORIGINS=https://hua-query.linkeddataviewer.nl \
  --publish 8176:7000 \
  --name hua-qlever-ui \
  docker.io/adfreiburg/qlever-ui