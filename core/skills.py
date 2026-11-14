import json
from pathlib import Path
from typing import Dict, Any, List
from core.config import BASE_DIR

SKILLS_DIR = BASE_DIR / "skills"
SKILLS_DIR.mkdir(parents=True, exist_ok=True)

class SkillManager:
    def __init__(self):
        self.skills_dir = SKILLS_DIR

    def list_skills(self) -> List[Dict[str, Any]]:
        """Scans the skills directory and loads all manifest.json files."""
        skills = []
        if not self.skills_dir.exists():
            return skills

        for folder in self.skills_dir.iterdir():
            if folder.is_dir():
                manifest_file = folder / "manifest.json"
                skill_md_file = folder / "SKILL.md"
                if manifest_file.exists():
                    try:
                        with open(manifest_file, "r", encoding="utf-8") as f:
                            data = json.load(f)
                        data["folder"] = folder.name
                        data["has_guide"] = skill_md_file.exists()
                        skills.append(data)
                    except Exception:
                        pass
        return skills

    def get_skill_instructions(self) -> str:
        """Collects guidelines from all active skills into a prompt addendum."""
        instructions = []
        for folder in self.skills_dir.iterdir():
            if folder.is_dir():
                skill_md = folder / "SKILL.md"
                if skill_md.exists():
                    try:
                        with open(skill_md, "r", encoding="utf-8") as f:
                            instructions.append(f"### Skill: {folder.name}\n{f.read()}")
                    except Exception:
                        pass
        return "\n\n".join(instructions)
