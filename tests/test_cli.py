from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def test_run_example_writes_markdown_report_and_prints_verdict(tmp_path):
    output_path = tmp_path / "nested" / "example.md"
    env = os.environ.copy()
    env["PYTHONPATH"] = str(PROJECT_ROOT / "src")

    completed = subprocess.run(
        [
            sys.executable,
            "-m",
            "trading_lab.cli",
            "run-example",
            "--output",
            str(output_path),
        ],
        cwd=tmp_path,
        env=env,
        check=False,
        capture_output=True,
        text=True,
    )

    assert completed.returncode == 0, completed.stderr
    assert output_path.exists()
    assert "Verdict:" in completed.stdout

    markdown = output_path.read_text(encoding="utf-8")
    assert "# Research Report" in markdown
    assert "toy moving-average crossover" in markdown
    assert "## Falsification Gates" in markdown
    assert "## Limitations" in markdown
    assert "## Next Tests" in markdown
    assert "not investment advice" in markdown
    assert "schema columns" in markdown
    assert "chronology" in markdown


def test_dashboard_command_writes_static_html_dashboard(tmp_path):
    output_path = tmp_path / "nested" / "dashboard.html"
    env = os.environ.copy()
    env["PYTHONPATH"] = str(PROJECT_ROOT / "src")

    completed = subprocess.run(
        [
            sys.executable,
            "-m",
            "trading_lab.cli",
            "dashboard",
            "--output",
            str(output_path),
        ],
        cwd=tmp_path,
        env=env,
        check=False,
        capture_output=True,
        text=True,
    )

    assert completed.returncode == 0, completed.stderr
    assert output_path.exists()
    assert "Dashboard:" in completed.stdout

    html = output_path.read_text(encoding="utf-8")
    assert "Falsification cockpit" in html
    assert "schema columns" in html
    assert "chronology" in html
    assert "not investment advice" in html
    assert "No broker APIs" in html


def test_run_example_can_write_json_artifact_for_dashboard_comparison(tmp_path):
    report_path = tmp_path / "example.md"
    json_path = tmp_path / "runs" / "example-run.json"
    dashboard_path = tmp_path / "dashboard.html"
    env = os.environ.copy()
    env["PYTHONPATH"] = str(PROJECT_ROOT / "src")

    run_completed = subprocess.run(
        [
            sys.executable,
            "-m",
            "trading_lab.cli",
            "run-example",
            "--output",
            str(report_path),
            "--json-output",
            str(json_path),
        ],
        cwd=tmp_path,
        env=env,
        check=False,
        capture_output=True,
        text=True,
    )

    assert run_completed.returncode == 0, run_completed.stderr
    assert json_path.exists()
    assert "JSON:" in run_completed.stdout

    dashboard_completed = subprocess.run(
        [
            sys.executable,
            "-m",
            "trading_lab.cli",
            "dashboard",
            "--output",
            str(dashboard_path),
            "--run",
            str(json_path),
        ],
        cwd=tmp_path,
        env=env,
        check=False,
        capture_output=True,
        text=True,
    )

    assert dashboard_completed.returncode == 0, dashboard_completed.stderr
    html = dashboard_path.read_text(encoding="utf-8")
    assert "Runner Evidence" in html
    assert "toy-moving-average-crossover" in html
    assert "Disproof score" in html


def test_run_command_uses_hypothesis_registry_and_writes_artifacts(tmp_path):
    report_path = tmp_path / "registered.md"
    json_path = tmp_path / "registered.json"
    env = os.environ.copy()
    env["PYTHONPATH"] = str(PROJECT_ROOT / "src")

    completed = subprocess.run(
        [
            sys.executable,
            "-m",
            "trading_lab.cli",
            "run",
            "--hypothesis",
            "toy-moving-average-crossover",
            "--registry",
            str(PROJECT_ROOT / "hypotheses" / "toy-moving-average-crossover.json"),
            "--data",
            str(PROJECT_ROOT / "examples" / "toy_prices.csv"),
            "--output",
            str(report_path),
            "--json-output",
            str(json_path),
        ],
        cwd=tmp_path,
        env=env,
        check=False,
        capture_output=True,
        text=True,
    )

    assert completed.returncode == 0, completed.stderr
    assert "Verdict:" in completed.stdout
    assert "JSON:" in completed.stdout
    assert "Report:" in completed.stdout
    assert json_path.exists()
    assert report_path.exists()
    payload = json_path.read_text(encoding="utf-8")
    assert "walk-forward robustness" in payload
    assert "parameter sensitivity" in payload
    assert "cost grid robustness" in payload
