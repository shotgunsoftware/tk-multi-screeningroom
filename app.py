"""
Copyright (c) 2012 Shotgun Software, Inc
----------------------------------------------------

An app that launches Screening Room

"""

import sys
import os

from tank.platform import Application

class NukeLaunchScreeningRoom(Application):
    
    def init_app(self):
        self.engine.register_command("Jump to Screening Room", 
                                     self._start_screeningroom,
                                     {"type": "context_menu", "short_name": "screening_room"})
        
    def _get_rv_binary(self):
        """
        Returns the RV binary to run
        """
        # get the setting        
        system = sys.platform
        try:
            app_setting = {"linux2": "rv_path_linux", "darwin": "rv_path_mac", "win32": "rv_path_windows"}[system]
            app_path = self.get_setting(app_setting)
            if not app_path: raise KeyError()
        except KeyError:
            raise Exception("Platform '%s' is not supported." % system) 
        
        if system == "darwin":
            # append Contents/MacOS/RV64 to the app bundle path
            app_path = os.path.join(app_path, "Contents/MacOS/RV64") 
        
        return app_path
        
    def _start_screeningroom(self):
        tk_multi_screeningroom = self.import_module("tk_multi_screeningroom")
        
        # figure out the context for Screening Room
        # first try to get a version
        # if that fails try to get the current entity
        rv_context = None
        task = self.context.task
        if task:
            # look for versions matching this task!
            self.log_debug("Looking for versions connected to %s..." % task)
            filters = [["sg_task", "is", task]]
            order   = [{"field_name": "created_at", "direction": "desc"}]
            fields  = ["id"]
            version = self.shotgun.find_one("Version", 
                                            filters=filters, 
                                            fields=fields, 
                                            order=order)
            if version:
                # got a version
                rv_context = version

        if rv_context is None:
            # fall back on entity
            # try to extract a version (because versions are launched in a really nice way
            # in Screening Room, while entities are not so nice...)
            self.log_debug("Looking for versions connected to %s..." % self.context.entity)
            filters = [["entity", "is", self.context.entity]]
            order   = [{"field_name": "created_at", "direction": "desc"}]
            fields  = ["id"]
            version = self.shotgun.find_one("Version", 
                                            filters=filters, 
                                            fields=fields, 
                                            order=order)
            
            if version:
                # got a version
                rv_context = version
            else:
                # no versions, fall back onto just the entity
                rv_context = self.context.entity
            
        
        self.log_debug("Launching Screening Room for context %s" % rv_context)
        
        try:
            tk_multi_screeningroom.screeningroom.launch_timeline(base_url=self.shotgun.base_url,
                                                    context=rv_context,
                                                    path_to_rv=self._get_rv_binary())
        except Exception, e:
            self.log_error("Could not launch Screening Room - check your configuration! "
                                  "Error reported: %s" % e)
    
