import logging
import requests

class Myrest(object):
    def __init__(self, api_url, node_name):
        self.api_url = api_url
        self.node_name = node_name
        self .node_url = None
        self.logger = logging.getLogger("myrest")

    # helpers
    def init_rest(self):
        req = requests.get(self.api_url)
        if req.status_code != 200:
            self.logger.error("check API URL")
            return None

        address = self.api_url + "/nodes/search/findByName?name=" + self.node_name
        req = requests.get(address)
        if req.status_code == 404:
            self.logger.warn("Node not found, creating!")
            req = requests.post(api_url + "/nodes", json={"name": "node_name"})
            if req.status_code == 201:
                json_data = json.loads(req.text)
                return json_data["_links"]["self"]["href"]
            else:
                self.logger.debug("%s %s", req.status_code, req.text)
                sys.exit("failed")
        else:
            self.logger.debug("REST OK")
            json_data = json.loads(req.text)
            return json_data["_links"]["self"]["href"]

    def register_callbacks(self, cmd_messenger, event_handler):
        def on_send_temp(api_url, node_url):
            def call(msg):
                requests.post(api_url + "/temperatures",
                              json={"node": node_url, "value": msg})
            return call

        def on_send_pir(api_url, node_url):
            def call(_):
                requests.post(api_url + "/pirs",
                              json={"node": node_url})
            return call

        def on_request_uid_status(api_url, node_url, cmd_messenger):
            def call(msg):
                req = requests.get(api_url + "/checkpermission/"
                                   + string.split(node_url, "/")[-1] + "/" + msg)
                if req.status_code == 200:
                    cmd_messenger.send("send_uid_status", True)
                else:
                    cmd_messenger.send("send_uid_status", False)
            return call

        event_handler.add_callback("send_temp",
                                   on_send_temp(self.api_urlv1, node_url))
        event_handler.add_callback("send_pir",
                                   on_send_pir(self.api_urlv1, node_url))
        event_handler.add_callback("request_uid_status",
                                   on_request_uid_status(self.api_url_for_unlock, node_url, self.cmd_messenger))
