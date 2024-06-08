docker run -it \
    -v ./odds.config.server.yaml:/srv/odds.config.yaml \
    -v ./dummy-cache/:/srv/.caches/ \
    odds-server -- "python utils/scrape_all.py"