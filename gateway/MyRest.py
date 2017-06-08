import json
import logging
import string
import sys

import requests

class Myrest(object):
    def __init__(self, api_url, node_name):
        # self.api_url = api_url
        self.api_urlv1 = api_url + "/api/v1"
        self.api_url_for_unlock = api_url + "/api/v2"
        self.node_name = node_name
        self.logger = logging.getLogger("myrest")

        self.node_url = self.init_rest()
        if self.node_url is None:
            sys.exit("REST was requested but not found")

    def init_rest(self):
        req = requests.get(self.api_urlv1)
        if req.status_code != 200:
            self.logger.error("check API URL")
            return None

        address = self.api_urlv1 + "/nodes/search/findByName?name=" + self.node_name
        req = requests.get(address)
        if req.status_code == 404:
            self.logger.warn("Node not found, creating!")
            req = requests.post(self.api_urlv1 + "/nodes", json={"name": "node_name"})
            if req.status_code == 201:
                json_data = json.loads(req.text)
                return json_data["_links"]["self"]["href"]
            else:
                self.logger.debug("status code: %s body: %s", req.status_code, req.text)
                sys.exit("failed")
        else:
            self.logger.debug("REST OK")
            json_data = json.loads(req.text)
            return json_data["_links"]["self"]["href"]

    def register_callbacks(self, cmd_messenger, event_handler):
        def on_send_temp(msg):
            requests.post(self.api_urlv1 + "/temperatures",
                          json={"node": self.node_url, "value": msg})

        def on_send_pir(_):
            requests.post(self.api_urlv1 + "/pirs",
                          json={"node": self.node_url})

        def on_request_uid_status(msg):
            node_id = string.split(self.node_url, "/")[-1]
            req = requests.get(self.api_url_for_unlock + "/checkpermission/"
                               + node_id + "/" + msg)
            if req.status_code == 200:
                cmd_messenger.send("send_uid_status", True)
            else:
                cmd_messenger.send("send_uid_status", False)

        event_handler.add_callback("send_temp", on_send_temp)
        event_handler.add_callback("send_pir", on_send_pir)
        event_handler.add_callback("request_uid_status", on_request_uid_status)
