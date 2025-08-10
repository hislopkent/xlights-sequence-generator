import os, re, yaml, json
from dataclasses import dataclass

@dataclass
class HouseStyle:
    core_groups: dict
    effects_kit: dict
    section_recipes: dict


def load_plan(path="intel/Starter_Sequence_Plan.yaml") -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def load_style(path="intel/House_Style_CheatSheet.txt") -> HouseStyle:
    txt = open(path, "r", encoding="utf-8").read()
    # extremely light parsing: bullet lists → buckets
    def bucket(name):
        m = re.search(rf"{name}:\s*(.+?)(?:\n\n|\Z)", txt, re.S|re.I)
        return (m.group(1).strip() if m else "")
    core = bucket("Core Groups to Target")
    kit  = bucket("Effects Default Kit")
    recs = bucket("Section Recipes")
    return HouseStyle(
        core_groups={"raw": core},
        effects_kit={"raw": kit},
        section_recipes={"raw": recs}
    )
