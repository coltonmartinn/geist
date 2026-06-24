# Geist

Spooky hot/cold game for an existing RuView Rev3 kit.

Geist does not replace RuView. Run RuView first, then run Geist beside it.

## Prereq

- Complete the RuView Setup Guide Rev3.
- Confirm RuView works at `http://192.168.50.50:3000`.
- Docker is installed on the Pi.

## Run on the Pi

```sh
git clone https://github.com/coltonmartinn/geist.git
cd geist
cp .env.example .env
./run.sh
```

Open:

```text
http://192.168.50.50:8000
```

If your Rev3 guide used a different Pi IP, edit `.env`:

```sh
RUVIEW_BASE_URL=http://YOUR_PI_IP:3000
```

## Test without RuView

```sh
GEIST_SOURCE=mock docker compose up -d --build
```

## Play

1. Make sure RuView is running.
2. Create a layout with the room empty.
3. Capture at least 3 bases.
4. Start with "show target" on.
5. Switch target hidden after it works.

## Node placement

Use whatever node count RuView reports. For best fidelity, use 6 nodes.

- Spread nodes around the room perimeter.
- Corners plus mid-wall positions are a good first layout.
- Do not default to three tight 2-foot pairs; the readings will be too similar.
- Put bases far apart first.
- Recreate the layout after moving router, nodes, or large furniture.

## Local tests

```sh
./test.sh
```
