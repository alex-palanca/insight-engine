from pathlib import Path
import yaml


def load_feeds(config_path: str | None = None) -> dict:
    """
    Load RSS feed configuration from a YAML file.

    Returns:
        dict:
        {
            "technology": [
                {
                    "name": "Hacker News",
                    "url": "https://hnrss.org/frontpage"
                }
            ],
            ...
        }
    """

    #Defaults path to feeds.yaml if another is not provided
    if config_path is None:
        config_path = (
            Path(__file__)
            .parent
            .joinpath("feeds.yaml")
        )

    with open(config_path, "r", encoding="utf-8") as file:
        feeds = yaml.safe_load(file)

    if feeds is None:
        raise ValueError("feeds.yaml is empty")

    return feeds