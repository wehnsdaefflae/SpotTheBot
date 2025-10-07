# Spot The Bot - A Community-Agnostic AI Text Recognition Game
![Logo Placeholder](images/spotthebot.svg)

Spot The Bot is an innovative web application game designed to enhance the ability of users to distinguish between AI-generated and human-written text. Tailored for various communities, Spot The Bot offers an engaging and educational platform to identify and understand the subtle differences in language usage between humans and AI models.

## Table of Contents
- [About the Project](#about-the-project)
- [Getting Started](#getting-started)
  - [Prerequisites](#prerequisites)
  - [Installation](#installation)
- [Contributing](#contributing)
- [License](#license)
- [Acknowledgments](#acknowledgments)

## About the Project

[screencast_spotthebot.webm](https://github.com/wehnsdaefflae/SpotTheBot/assets/9195325/12c8b5de-76f6-4240-9ff8-475d2e06d01f)

![Screenshot](images/screenshot_game.png)

Spot The Bot allows communities to input their authentic texts and then challenges players to differentiate between these and AI-generated versions of the texts. Players tag suspicious words or phrases with custom labels such as "irrelevant" or "generic," aiding in the identification of AI-generated content and publishing helpful information even for those who prefer not to play the game. The game is designed to be community-agnostic, meaning that it can be tailored to any community, from online forums to social media platforms.

### Features
- **Community Customization:** Tailor the game to any community by inputting authentic, community-specific texts and adapting the style to the community's brand or CI.
- **Interactive Tagging Mechanism:** Engage with content by tagging suspicious words or phrases, learning to discern between AI and human language nuances.
- **Educational Tool:** Enhance critical reading skills and become more discerning of the content consumed online.

### Built With
- [Python](https://www.python.org/)
- [NiceGUI](https://nicegui.io/)
- [Redis](https://www.reddit.com/)
- [FastAPI](https://fastapi.tiangolo.com/)
- [Tailwind CSS](https://tailwindcss.com/)

## Getting Started
To get a local copy up and running, follow these simple steps.

### Prerequisites
- [Docker](https://docs.docker.com/get-docker/)
- [Docker Compose](https://docs.docker.com/compose/install/)

### Installation

1.  **Clone the repository**
    ```sh
    git clone https://github.com/wehnsdaefflae/SpotTheBot.git
    cd SpotTheBot
    ```

2.  **Set up environment variables**

    Copy the example environment file and edit it to add your secret keys.
    ```sh
    cp .env.example .env
    nano .env
    ```
    You will need to provide your `OPENAI_API_KEY` and a `STORAGE_SECRET`.

3.  **Run the application**

    Start the application and the Redis database using Docker Compose.
    ```sh
    docker-compose up
    ```
    The application will be available at [http://localhost:8000](http://localhost:8000).

## Contributing
Contributions make the open-source community an amazing place to learn, inspire, and create. Any contributions you make are **greatly appreciated**.

1. Fork the Project
2. Create your Feature Branch (`git checkout -b feature/AmazingFeature`)
3. Commit your Changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the Branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## License
Distributed under the MIT License. See `LICENSE` for more information.

## Acknowledgments
This project was funded by the German BMBF and the Prototype Fund.

![BMBF Logo](images/BMBF_gefördert%20vom_deutsch.svg)
![Prototype Fund Logo](images/PrototypeFund-P-Logo.svg)

* [BMBF Website](https://www.bmbf.de)
* [Prototype Fund Website](https://prototypefund.de/)

We want to extend our gratitude to all the contributors and funders who made this project possible.
