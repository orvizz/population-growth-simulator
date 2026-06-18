// chapters/07_manuals/tables.typ
// All tables for Chapter 7. Included from index.typ.

#let railway-env-vars-table = [
  #figure(
    table(
      columns: (auto, auto, 1fr),
      inset: 8pt,
      align: left,
      table.header([*Variable*], [*Service*], [*Value*]),
      [`DATABASE_URL`],   [`api`],      [`${{Postgres.DATABASE_URL}}`],
      [`JWT_SECRET_KEY`], [`api`],      [32-byte hex string (`openssl rand -hex 32`)],
      [`CORS_ORIGINS`],   [`api`],      [`https://${{frontend.RAILWAY_PUBLIC_DOMAIN}}`],
      [`API_BASE_URL`],   [`frontend`], [`https://${{api.RAILWAY_PUBLIC_DOMAIN}}`],
    ),
    caption: [Environment variables configured per Railway service.],
  ) <tab:railway-env-vars>
]

#let docker-make-targets-table = [
  #figure(
    table(
      columns: (auto, auto, 1fr),
      inset: 8pt,
      align: left,
      table.header([*Target*], [*Underlying command*], [*Purpose*]),
      [`make up`],       [`docker compose up -d --build`], [Build images and start all services],
      [`make down`],     [`docker compose down`],          [Stop containers; volumes preserved],
      [`make logs`],     [`docker compose logs -f`],       [Follow logs from all services],
      [`make logs-api`], [`docker compose logs -f api`],   [Follow logs from the API service only],
      [`make clean`],    [`docker compose down -v`],       [Stop containers and delete all volumes (full reset)],
    ),
    caption: [Makefile targets and their underlying Docker Compose commands.],
  ) <tab:docker-make-targets>
]
