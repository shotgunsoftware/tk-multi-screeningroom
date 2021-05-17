# Copyright (c) 2013 Shotgun Software Inc.
#
# CONFIDENTIAL AND PROPRIETARY
#
# This work is provided "AS IS" and subject to the Shotgun Pipeline Toolkit
# Source Code License included in this distribution package. See LICENSE.
# By accessing, using, copying or modifying this work you indicate your
# agreement to the Shotgun Pipeline Toolkit Source Code License. All rights
# not expressly granted therein are reserved by Shotgun Software Inc.

"""
An app that launches Screening Room

"""

import sys
import os

import sgtk
from sgtk.platform import Application
from sgtk import TankError


class MultiLaunchScreeningRoom(Application):
    def init_app(self):

        if self.get_setting("enable_rv_mode"):
            command_settings = {
                "type": "context_menu",
                "short_name": "screening_room_rv",
            }
            # We only support multiple selection for `Version`
            # entities when run in the `tk-shotgun` engine.
            # The supports_multiple_selection setting holds two purposes
            # Setting it to True will mean the engine allows the action
            # to be run on multiple entities simultaneously from the browser.
            # But even just defining the setting as false is enough
            # for the engine to run the action command in a different way.
            # Some engines don't support this old method, so we are only setting
            # it if we want it to be True.
            if self.context.entity and self.context.entity["type"] == "Version":
                command_settings["supports_multiple_selection"] = True

            self.engine.register_command(
                "Jump to Screening Room in RV",
                self._start_screeningroom_rv,
                command_settings,
            )

        if self.get_setting("enable_web_mode"):
            self.engine.register_command(
                "Jump to Screening Room Web Player",
                self._start_screeningroom_web,
                {"type": "context_menu", "short_name": "screening_room_web"},
            )

    @property
    def context_change_allowed(self):
        """
        Specifies that context changes are allowed.
        """
        return True

    def _get_rv_binary(self):
        """
        Returns the RV binary to run
        """
        # get the setting
        try:
            app_setting = (
                "rv_path_windows"
                if sgtk.util.is_windows()
                else "rv_path_mac"
                if sgtk.util.is_macos()
                else "rv_path_linux"
            )
            app_path = self.get_setting(app_setting)
            if not app_path:
                raise KeyError()
        except KeyError:
            raise TankError("Platform '%s' is not supported." % sys.platform)

        if sgtk.util.is_macos():
            # append Contents/MacOS/RV64 to the app bundle path
            # if that doesn't work, try with just RV, which is used by 32 bit RV
            # if that doesn't work, show an error message
            orig_app_path = app_path
            app_path = os.path.join(orig_app_path, "Contents/MacOS/RV64")
            if not os.path.exists(app_path):
                # try 32 bit RV (which has an RV executable rather than RV64
                app_path = os.path.join(orig_app_path, "Contents/MacOS/RV")
            if not os.path.exists(app_path):
                # did not find rv64 nor 32
                raise Exception(
                    "The RV path you have configured ('%s') does not exist!"
                    % orig_app_path
                )

        return app_path

    def _get_entity(self):
        """
        Returns the most relevant playback entity (as a sg std dict) for the current context
        """

        # figure out the context for Screening Room
        # first try to get a version
        # if that fails try to get the current entity
        rv_context = None
        task = self.context.task
        if task:
            # look for versions matching this task!
            self.logger.debug("Looking for versions connected to %s..." % task)
            filters = [["sg_task", "is", task]]
            order = [{"field_name": "created_at", "direction": "desc"}]
            fields = ["id"]
            version = self.shotgun.find_one(
                "Version", filters=filters, fields=fields, order=order
            )
            if version:
                # got a version
                rv_context = version

        if rv_context is None and self.context.entity:
            # fall back on entity
            # try to extract a version (because versions are launched in a really nice way
            # in Screening Room, while entities are not so nice...)
            self.logger.debug(
                "Looking for versions connected to %s..." % self.context.entity
            )
            filters = [["entity", "is", self.context.entity]]
            order = [{"field_name": "created_at", "direction": "desc"}]
            fields = ["id"]
            version = self.shotgun.find_one(
                "Version", filters=filters, fields=fields, order=order
            )

            if version:
                # got a version
                rv_context = version
            else:
                # no versions, fall back onto just the entity
                rv_context = self.context.entity

        if rv_context is None:
            # fall back on project
            rv_context = self.context.project

        if rv_context is None:
            raise TankError(
                "Not able to figure out a current context to launch screening room for!"
            )

        self.logger.debug("Closest match to current context is %s" % rv_context)

        return rv_context

    def _start_screeningroom_web(self):
        """
        Launches the screening room web player
        """
        from sgtk.platform.qt import QtGui, QtCore

        entity = self._get_entity()

        # url format is
        # https://playbook.shotgunstudio.com/page/screening_room?entity_type=Version&entity_id=222
        url = "%s/page/screening_room?entity_type=%s&entity_id=%s" % (
            self.shotgun.base_url,
            entity.get("type"),
            entity.get("id"),
        )

        self.logger.debug("Opening url %s" % url)

        QtGui.QDesktopServices.openUrl(QtCore.QUrl(url))

    def _start_screeningroom_rv(self, entity_type=None, entity_ids=None):
        """
        Launches the screening room rv player
        The entity_type and entity_ids are passed if supports_multiple_selection is
        enabled in the registered command, and that is only enabled if we are dealing
        with Version entities in the tk-shotgun engine.
        """

        if entity_type == "Version" and entity_ids:
            # if we have an entity_type and entity_ids we are running in
            # the tk-shotgun engine on a Version entity.
            # RV can handle opening multiple versions so we pass through
            # a Version ID list instead of the usual single entity.
            entity = {"version_ids": entity_ids}
        else:
            entity = self._get_entity()
        tk_multi_screeningroom = self.import_module("tk_multi_screeningroom")

        try:
            rv_path = self._get_rv_binary()
            self.execute_hook_method("init_hook", "before_rv_launch", path=rv_path)
            tk_multi_screeningroom.screeningroom.launch_timeline(
                base_url=self.shotgun.base_url, context=entity, path_to_rv=rv_path
            )
        except Exception as e:
            self.logger.exception(
                "Could not launch RV Screening Room. Error reported: %s" % e
            )
