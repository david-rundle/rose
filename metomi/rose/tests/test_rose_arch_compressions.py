# Copyright (C) British Crown (Met Office) & Contributors.
# This file is part of Rose, a framework for meteorological suites.
#
# Rose is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Rose is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Rose. If not, see <http://www.gnu.org/licenses/>.
# -----------------------------------------------------------------------------
"""Tests for RoseArch compression handlers."""

import sys
import os
import tarfile
from unittest.mock import MagicMock, patch
import pytest

from metomi.rose.apps.rose_arch_compressions.rose_arch_gzip import RoseArchGzip
from metomi.rose.apps.rose_arch_compressions.rose_arch_zstd import RoseArchZstd
from metomi.rose.apps.rose_arch_compressions.rose_arch_xz import RoseArchXz
from metomi.rose.apps.rose_arch_compressions.rose_arch_tar import RoseArchTarGzip


class DummySource:
    def __init__(self, name, path):
        self.name = name
        self.orig_name = name
        self.path = path
        self.orig_path = path


class DummyTarget:
    def __init__(self, sources, compress_scheme):
        self.sources = sources
        self.compress_scheme = compress_scheme
        self.work_source_path = None
        self.name = "dummy_target"


@pytest.fixture
def mock_app_runner():
    runner = MagicMock()
    runner.fs_util.dirname = os.path.dirname
    runner.fs_util.makedirs = MagicMock()
    runner.fs_util.delete = MagicMock()
    runner.popen.run_simple = MagicMock()
    return runner


def test_gzip_compress_sources(mock_app_runner, tmp_path):
    source_file = tmp_path / "test.txt"
    source_file.write_text("Hello World")
    
    source = DummySource("test.txt", str(source_file))
    target = DummyTarget({"key": source}, "gz")
    
    handler = RoseArchGzip(mock_app_runner)
    handler.compress_sources(target, str(tmp_path))
    
    assert source.path.endswith(".gz")
    mock_app_runner.popen.run_simple.assert_called_once()
    command = mock_app_runner.popen.run_simple.call_args[0][0]
    assert "gzip -c" in command


@pytest.mark.parametrize("import_scenario", ["compression", "zstd", "zstandard", "cli"])
def test_zstd_compress_sources_scenarios(mock_app_runner, tmp_path, import_scenario):
    source_file = tmp_path / "test.txt"
    source_file.write_text("Hello World")
    
    source = DummySource("test.txt", str(source_file))
    target = DummyTarget({"key": source}, "zst")
    
    handler = RoseArchZstd(mock_app_runner)
    
    # Setup mocks for libraries depending on scenario
    modules_to_mock = {
        "compression": None,
        "compression.zstd": None,
        "zstd": None,
        "zstandard": None
    }
    
    orig_import = __import__
    
    def mock_import(name, *args, **kwargs):
        if name == "compression" or name == "compression.zstd":
            if import_scenario == "compression":
                mock_mod = MagicMock()
                mock_mod.zstd.compress = lambda d: b"COMPRESSED_BY_COMPRESSION_ZSTD:" + d
                mock_mod.compress = lambda d: b"COMPRESSED_BY_COMPRESSION_ZSTD:" + d
                return mock_mod
            raise ImportError
        if name == "zstd":
            if import_scenario == "zstd":
                mock_mod = MagicMock()
                mock_mod.compress = lambda d: b"COMPRESSED_BY_ZSTD:" + d
                return mock_mod
            raise ImportError
        if name == "zstandard":
            if import_scenario == "zstandard":
                mock_mod = MagicMock()
                mock_mod.ZstdCompressor.return_name = "ZstdCompressor"
                # Mock class constructor and return object with compress method
                cctx = MagicMock()
                cctx.compress = lambda d: b"COMPRESSED_BY_ZSTANDARD:" + d
                mock_mod.ZstdCompressor.return_value = cctx
                return mock_mod
            raise ImportError
        return orig_import(name, *args, **kwargs)

    with patch("builtins.__import__", side_effect=mock_import):
        handler.compress_sources(target, str(tmp_path))

    assert source.path.endswith(".zst")
    
    if import_scenario == "cli":
        mock_app_runner.popen.run_simple.assert_called_once()
        command = mock_app_runner.popen.run_simple.call_args[0][0]
        assert "zstd -c" in command
    else:
        mock_app_runner.popen.run_simple.assert_not_called()
        with open(source.path, "rb") as f:
            content = f.read()
        if import_scenario == "compression":
            assert content == b"COMPRESSED_BY_COMPRESSION_ZSTD:Hello World"
        elif import_scenario == "zstd":
            assert content == b"COMPRESSED_BY_ZSTD:Hello World"
        elif import_scenario == "zstandard":
            assert content == b"COMPRESSED_BY_ZSTANDARD:Hello World"


@pytest.mark.parametrize("import_scenario", ["lzma", "cli"])
def test_xz_compress_sources_scenarios(mock_app_runner, tmp_path, import_scenario):
    source_file = tmp_path / "test.txt"
    source_file.write_text("Hello World")
    
    source = DummySource("test.txt", str(source_file))
    target = DummyTarget({"key": source}, "xz")
    
    handler = RoseArchXz(mock_app_runner)
    
    orig_import = __import__
    
    def mock_import(name, *args, **kwargs):
        if name == "lzma":
            if import_scenario == "lzma":
                mock_mod = MagicMock()
                mock_mod.compress = lambda d: b"COMPRESSED_BY_LZMA:" + d
                return mock_mod
            raise ImportError
        return orig_import(name, *args, **kwargs)

    with patch("builtins.__import__", side_effect=mock_import):
        handler.compress_sources(target, str(tmp_path))

    assert source.path.endswith(".xz")
    
    if import_scenario == "cli":
        mock_app_runner.popen.run_simple.assert_called_once()
        command = mock_app_runner.popen.run_simple.call_args[0][0]
        assert "xz -c" in command
    else:
        mock_app_runner.popen.run_simple.assert_not_called()
        with open(source.path, "rb") as f:
            content = f.read()
        assert content == b"COMPRESSED_BY_LZMA:Hello World"


@pytest.mark.parametrize("scheme, scenario", [
    ("tar.gz", "gzip"),
    ("tar.zst", "compression"),
    ("tar.zst", "zstd"),
    ("tar.zst", "zstandard"),
    ("tar.zst", "cli"),
    ("tar.xz", "lzma"),
    ("tar.xz", "cli")
])
def test_tar_compress_sources_scenarios(mock_app_runner, tmp_path, scheme, scenario):
    source_file = tmp_path / "test.txt"
    source_file.write_text("Hello World")
    
    source = DummySource("test.txt", str(source_file))
    target = DummyTarget({"key": source}, scheme)
    
    handler = RoseArchTarGzip(mock_app_runner)
    
    # We need to mock os.statvfs since it might not be available or returns filesystem values.
    # On Windows, os.statvfs is not available at all, so we MUST mock it!
    mock_statvfs = MagicMock()
    mock_statvfs.f_bsize = 4096
    
    orig_import = __import__
    
    def mock_import(name, *args, **kwargs):
        if name == "compression" or name == "compression.zstd":
            if scenario == "compression":
                mock_mod = MagicMock()
                mock_mod.zstd.compress = lambda d: b"COMPRESSED_BY_COMPRESSION_ZSTD:" + d
                mock_mod.compress = lambda d: b"COMPRESSED_BY_COMPRESSION_ZSTD:" + d
                return mock_mod
            raise ImportError
        if name == "zstd":
            if scenario == "zstd":
                mock_mod = MagicMock()
                mock_mod.compress = lambda d: b"COMPRESSED_BY_ZSTD:" + d
                return mock_mod
            raise ImportError
        if name == "zstandard":
            if scenario == "zstandard":
                mock_mod = MagicMock()
                mock_mod.ZstdCompressor.return_value.compress = lambda d: b"COMPRESSED_BY_ZSTANDARD:" + d
                return mock_mod
            raise ImportError
        if name == "lzma":
            if scenario == "lzma":
                mock_mod = MagicMock()
                mock_mod.compress = lambda d: b"COMPRESSED_BY_LZMA:" + d
                return mock_mod
            raise ImportError
        return orig_import(name, *args, **kwargs)

    with patch("os.statvfs", return_value=mock_statvfs), \
         patch("builtins.__import__", side_effect=mock_import):
        handler.compress_sources(target, str(tmp_path))

    assert target.work_source_path is not None
    assert target.work_source_path.endswith(scheme)
    
    if scenario == "gzip" or scenario == "cli":
        mock_app_runner.popen.run_simple.assert_called_once()
        command = mock_app_runner.popen.run_simple.call_args[0][0]
        if "gz" in scheme:
            assert "gzip -c" in command
        elif "zst" in scheme:
            assert "zstd -c" in command
        elif "xz" in scheme:
            assert "xz -c" in command
    else:
        mock_app_runner.popen.run_simple.assert_not_called()
        with open(target.work_source_path, "rb") as f:
            content = f.read()
        if scenario == "compression":
            assert content.startswith(b"COMPRESSED_BY_COMPRESSION_ZSTD:")
        elif scenario == "zstd":
            assert content.startswith(b"COMPRESSED_BY_ZSTD:")
        elif scenario == "zstandard":
            assert content.startswith(b"COMPRESSED_BY_STANDARD:" or b"COMPRESSED_BY_ZSTANDARD:")
        elif scenario == "lzma":
            assert content.startswith(b"COMPRESSED_BY_LZMA:")
