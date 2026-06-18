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
"""Compress archive sources in zstd."""


import os


class RoseArchZstd:

    """Compress archive sources in zstd."""

    SCHEMES = ["zst", "zstd"]

    def __init__(self, app_runner, *args, **kwargs):
        self.app_runner = app_runner

    def compress_sources(self, target, work_dir):
        """Zstd each source in target.

        Use work_dir to dump results.

        """
        for source in target.sources.values():
            if source.path.endswith("." + target.compress_scheme):
                continue  # assume already done
            name_zst = source.name + "." + target.compress_scheme
            work_path_zst = os.path.join(work_dir, name_zst)
            self.app_runner.fs_util.makedirs(
                self.app_runner.fs_util.dirname(work_path_zst)
            )
            try:
                try:
                    from compression import zstd
                    compress_func = zstd.compress
                except ImportError:
                    try:
                        import zstd
                        compress_func = zstd.compress
                    except ImportError:
                        import zstandard
                        compress_func = zstandard.ZstdCompressor().compress
                with open(source.path, 'rb') as f_in:
                    data = f_in.read()
                compressed_data = compress_func(data)
                with open(work_path_zst, 'wb') as f_out:
                    f_out.write(compressed_data)
            except ImportError:
                command = "zstd -c '%s' >'%s'" % (source.path, work_path_zst)
                self.app_runner.popen.run_simple(command, shell=True)
            source.path = work_path_zst
