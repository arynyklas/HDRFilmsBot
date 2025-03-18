# HDRFilmsBot

[@HDRFilmsBot](https://t.me/HDRFilmsBot) is a Python project designed to streamline the management and retrieval of film-related data using High Dynamic Range (HDR) techniques. This README outlines the purpose, setup, usage, and configuration details of the project.

## Table of Contents

- [Overview](#overview)
- [Installation](#installation)
- [Usage](#usage)
- [Configuration](#configuration)
- [Contributing](#contributing)

## Overview

[@HDRFilmsBot](https://t.me/HDRFilmsBot) aims to give users an easiest way to watch films and series, using Telegram Bot. It includes functionality to interact with [Rezka API](https://t.me/aryn_dev/138), show short info about film/series and process media files.

## Installation

1. Install Poetry if it's not already installed. See [Poetry installation guide](https://python-poetry.org/docs/#installation) for details.
2. Clone the repository:
    ```bash
    git clone https://github.com/arynyklas/HDRFilmsBot.git
    ```
3. Navigate to the project directory:
    ```bash
    cd HDRFilmsBot
    ```
4. Rename configuration templates:
    - Rename `config.sample.yml` to `config.yml`.
    - Rename `alembic.sample.yml` to `alembic.ini`.
5. Open `alembic.ini` and set the `sqlalchemy.url` to match your database configuration.
6. Install project dependencies:
    ```bash
    poetry install
    ```
7. Set up the database migrations:
    ```bash
    poetry run alembic upgrade head
    ```

## Usage

- To start the application:
  ```bash
  poetry run python -m src
  ```
- Follow the on-screen prompts for film selection.
- You can also use command-line arguments as detailed in the documentation.

## Configuration

Adjust settings in the `config.yml` file to customize the behavior:
- API key for [Rezka API](https://t.me/aryn_dev/138)
- Paths for media storage and logs
- Logging preferences (using [telegram-bot-logger](https://github.com/arynyklas/telegram-bot-logger))

## Contributing

Contributions are welcome! Please submit issues or pull requests via GitHub or [Telegram DM](https://aryn.sek.su/tg/dm). For significant changes, open an issue first to discuss your ideas.
