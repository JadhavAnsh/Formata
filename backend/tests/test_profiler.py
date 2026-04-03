import os

import pandas as pd

from app.services import profiler


class FakeProfileReport:
    def __init__(self, df, **kwargs):
        self.df = df
        self.kwargs = kwargs

    def to_file(self, output_path):
        with open(output_path, "w", encoding="utf-8") as handle:
            handle.write("<html><body>profile ok</body></html>")


def test_generate_profile_html_with_profile_engine(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(profiler, "ProfileReport", FakeProfileReport)

    df = pd.DataFrame({"name": ["Alice", "Bob"], "age": [10, 20]})
    report_path = profiler.generate_profile_html(df, "job-123", "clean")

    assert os.path.exists(report_path)
    with open(report_path, "r", encoding="utf-8") as handle:
        content = handle.read()

    assert "profile ok" in content


def test_generate_profile_html_fallback_when_engine_missing(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(profiler, "ProfileReport", None)

    df = pd.DataFrame({"name": ["Alice", "Bob"], "age": [10, 20]})
    report_path = profiler.generate_profile_html(df, "job-456", "raw")

    assert os.path.exists(report_path)
    with open(report_path, "r", encoding="utf-8") as handle:
        content = handle.read()

    assert "ydata-profiling is not installed" in content