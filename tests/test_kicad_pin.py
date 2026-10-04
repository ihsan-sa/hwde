"""CI and the container image run the exact KiCad the box host runs
(env.KICAD_PIN). A bump changes all three together or this fails."""
from __future__ import annotations

import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / ".claude" / "skills" / "hwde" / "scripts" / "lib"))

import env  # noqa: E402

PIN = ".".join(map(str, env.KICAD_PIN))


def _tags(text: str) -> list[str]:
    return re.findall(r"kicad/kicad:([0-9][0-9.]*)", text)


def test_pin_is_a_full_kicad10_version():
    assert len(env.KICAD_PIN) == 3
    assert env.KICAD_PIN[0] == env.PIN_MIN_MAJOR


def test_ci_image_matches_pin():
    tags = _tags((REPO / ".github" / "workflows" / "checks.yml").read_text())
    assert tags == [PIN]


def test_docker_image_matches_pin():
    text = (REPO / "docker" / "Dockerfile").read_text()
    assert re.findall(r"^FROM kicad/kicad:(\S+)", text, re.M) == [PIN]
