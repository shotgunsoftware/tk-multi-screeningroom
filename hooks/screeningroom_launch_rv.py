#
# Copyright (c) 2012 Shotgun Software, Inc
# ----------------------------------------------------
#
"""
Screeningroom Launch Rv.

This hook is executed to launch rv.
"""

import os
import sys
import tank

class ScreeningroomLaunchRv(tank.Hook):
    """
    Hook to launch rv.
    """
    def execute(self, rv_path, rv_args, **kwargs):
        """
        The execute functon of the hook will be called to start rv using the
        arguments rv_args.

        :param rv_path: (str) The path to rv
        :param rv_args: (str) Any arguments rv may require
        """
        print("Running %s" % ' '.join([rv_path] + rv_args));
        subprocess.Popen([rv_path] + rv_args)
