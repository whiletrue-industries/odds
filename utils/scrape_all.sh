docker run -it \
    -v ./odds.config.yaml:/srv/odds.config.yaml \
    -v ./cache/:/srv/.caches/ \
    ghcr.io/whiletrue-industries/odds/odds-server:latest -- "python utils/scrape_all.py $*"