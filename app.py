"""
Copyright (c) 2012 Shotgun Software, Inc
----------------------------------------------------

An app that launches revolver from nuke

"""

import sys
import os
import platform

from tank.platform import Application

class NukeLaunchRevolver(Application):
    
    def init_app(self):
        self.engine.register_command("Jump into Revolver", 
                                     self._start_revolver,
                                     {"type": "context_menu"})
        
    def _get_rv_binary(self):
        """
        Returns the RV binary to run
        """
        # get the setting        
        system = platform.system()
        try:
            app_setting = {"Linux": "rv_path_linux", "Darwin": "rv_path_mac", "Windows": "rv_path_windows"}[system]
            app_path = self.get_setting(app_setting)
            if not app_path: raise KeyError()
        except KeyError:
            raise Exception("Platform '%s' is not supported." % system) 
        
        if system == "Darwin":
            # append Contents/MacOS/RV64 to the app bundle path
            app_path = os.path.join(app_path, "Contents/MacOS/RV64") 
        
        return app_path
        
    def _start_revolver(self):
        tk_multi_revolver = self.import_module("tk_multi_revolver")
        
        # figure out the context for revolver
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
            # in revolver, while entities are not so nice...)
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
            
        
        self.log_debug("Launching revolver for context %s" % rv_context)
        
        try:
            tk_multi_revolver.revolver.launch_timeline(base_url=self.shotgun.base_url,
                                                    context=rv_context,
                                                    path_to_rv=self._get_rv_binary())
        except Exception, e:
            self.log_error("Could not launch revolver - check your configuration! "
                                  "Error reported: %s" % e)
    
