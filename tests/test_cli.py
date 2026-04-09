"""Tests for the CLI entrypoint."""

from click.testing import CliRunner
from cli.main import cli

import pytest


@pytest.fixture
def runner():
    return CliRunner()


def test_basic_compress(runner):
    result = runner.invoke(cli, ["Can you please write a function"])
    assert result.exit_code == 0
    assert "function" not in result.output.lower()


def test_default_level_is_2(runner):
    result = runner.invoke(cli, ["write a function that returns a list"])
    assert result.exit_code == 0
    assert "fn" in result.output
    assert "->" in result.output


def test_level_option(runner):
    result = runner.invoke(cli, ["--level", "3", "write a function that returns a list"])
    assert result.exit_code == 0


def test_level_short_flag(runner):
    result = runner.invoke(cli, ["-l", "1", "Can you please write a function"])
    assert result.exit_code == 0
    assert "can you please" not in result.output.lower()


def test_report_option(runner):
    result = runner.invoke(cli, ["--report", "Can you please write a function that returns a list"])
    assert result.exit_code == 0
    assert "tok" in result.output
    assert "Saved" in result.output
    assert "Original" in result.output
    assert "Compressed" in result.output


def test_report_short_flag(runner):
    result = runner.invoke(cli, ["-r", "write a function"])
    assert result.exit_code == 0
    assert "tok" in result.output


def test_file_option(runner, tmp_path):
    prompt_file = tmp_path / "prompt.txt"
    prompt_file.write_text("Can you please write a function that returns a list?")
    result = runner.invoke(cli, ["--file", str(prompt_file)])
    assert result.exit_code == 0
    assert "fn" in result.output


def test_file_short_flag(runner, tmp_path):
    prompt_file = tmp_path / "p.txt"
    prompt_file.write_text("write a function")
    result = runner.invoke(cli, ["-f", str(prompt_file)])
    assert result.exit_code == 0


def test_no_input_exits_nonzero(runner):
    result = runner.invoke(cli, [])
    assert result.exit_code != 0


def test_output_is_stripped(runner):
    result = runner.invoke(cli, ["write a function"])
    assert result.output == result.output.strip() + "\n"
