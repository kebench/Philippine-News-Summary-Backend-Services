# Loads sources.yaml and returns a list of sources to be ingested
import yaml
from typing import List, Dict

def load_sources(config_path: str) -> List[Dict]:
    """
    Load sources from a YAML configuration file.

    Args:
        config_path (str): The path to the YAML configuration file.

    Returns:
        List[Dict]: A list of sources to be ingested.
    """
    with open(config_path, "r") as file:
        sources = yaml.safe_load(file)

    news_sources = [source for source in sources["sources"] if source.get("enabled", True)]
    return news_sources