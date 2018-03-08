"""=click_demultiplex cli tests."""

from click.testing import CliRunner
import pytest

from click_demultiplex import cli

TEST_R1 = ''

def test_no_trim():
    """Sample test for main command."""
    message = "This is a test message for the Universe."
    runner = CliRunner()
    params = ["r1", ]
    result = runner.invoke(cli.main, params)
    assert message in result.output


