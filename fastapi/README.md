# : FastAPI App fastapi

## Tech Stack

- FastAPI


## Development

To start the development server:

```
uv run fastapi run --reload
```

To run tests:

```
uv run pytest --cov --cov-report term --cov-report html
```


To test through a DataRobot like proxy:

Install traefik by downloading from: https://github.com/traefik/traefik/releases


Configure it like with `traefik.toml` like:

```toml
[entryPoints]
  [entryPoints.http]
    address = ":9999"

[providers]
  [providers.file]
    filename = "routes.toml"
```

Create a `routes.toml` file like:

```toml
[http]
  [http.middlewares]
    [http.middlewares.add-foo.addPrefix]
      prefix = "/fastapi"
    
    [http.middlewares.add-prefix-header.headers]
      customRequestHeaders = { X-Forwarded-Prefix = "/fastapi" }

  [http.routers]
    [http.routers.app-http]
      entryPoints = ["http"]
      service = "app"
      rule = "PathPrefix(`/fastapi`)"
      middlewares = ["add-prefix-header"]

  [http.services]
    [http.services.app]
      [http.services.app.loadBalancer]
        [[http.services.app.loadBalancer.servers]]
          url = "http://127.0.0.1:8000"
```


And run locally with:

`traefik --configFile=traefik.toml`

With the fastapi running now accessing:

http://localhost:9999/fastapi

will take you to a proxy compatible installation
