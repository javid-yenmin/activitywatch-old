import json

import threading
from datetime import datetime

import pyzenobase


class Activity(dict):                                                                    
    def __init__(self, tags: "string or string[]", started_at, ended_at, **kwargs):
        dict.__init__(self)
        self["tags"] = tags
        if "cmd" in kwargs:
            # TODO: Keep?
            cmd = kwargs.pop("cmd")
            cmd = list(filter(lambda s: s[0] != "-", cmd))
            self["cmd"] = cmd
        self["start"] = started_at
        self["end"] = ended_at

        self.update(kwargs)

        print("")
        print("Logged activity '{}':".format(tags))
        print("  Started: {}".format(self["start"]))
        print("  Ended: {}".format(self["end"]))
        print("  Duration: {}".format(self.duration()))
        if "cmd" in self:
            print("  Command: {}".format(self["cmd"]))
        print("")

    def duration(self):
        return self["end"] - self["start"]

    def to_zenobase_event(self):
        # TODO: Add misc fields into note field
        data = {"tag": self["tags"],
                "timestamp": [self["start"], self["end"]],
                "duration": self.duration().total_seconds()}
        return pyzenobase.ZenobaseEvent(data)

    def to_json_dict(self):
        data = self.copy()
        data["start"] = data["start"].isoformat()
        data["end"] = data["end"].isoformat()
        return data

    def to_json(self):
        data = self.to_json_dict()
        return json.dumps(data)


class Logger(threading.Thread):
    """Listens to watchers and logs activities"""

    def __init__(self):
        threading.Thread.__init__(self)
        self.watchers = []

        # Must be thread-safe
        self._activities = []
        self._activities_lock = threading.Lock()

    def run(self):
        raise NotImplementedError("run method must be implemented in Logger subclass")

    def add_activity(self, activity):
        if not isinstance(activity, Activity):
            raise TypeError("{} is not an Activity".format(activity))
        with self._activities_lock:
            self._activities.append(activity)

    def flush_activities(self):
        with self._activities_lock:
            activities = self._activities
            self._activities = []
        return activities

    def add_watcher(self, watcher):
        """Start listening to watchers here"""
        if not isinstance(watcher, Watcher):
            raise TypeError("{} is not a Watcher".format(watcher))
        watcher._add_logger(self)
        self.watchers.append(watcher)


class Watcher(threading.Thread):
    """Base class for a watcher"""

    def __init__(self):
        threading.Thread.__init__(self)
        self.loggers = []

    def _add_logger(self, logger):
        """Should only be called from Logger.add_watcher"""
        if not isinstance(logger, Logger):
            raise TypeError("{} was not a Logger".format(logger))
        self.loggers.append(logger)

    def run(self):
        raise NotImplementedError("Watchers must implement the run method")

    def add_activity(self, activity):
        for logger in self.loggers:
            logger.add_activity(activity)
