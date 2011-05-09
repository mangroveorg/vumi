from twisted.python import log
from twisted.python.log import logging
from twisted.internet.defer import inlineCallbacks, returnValue

from vumi.service import Worker, Consumer, Publisher
from vumi.session import VumiSession, TraversedDecisionTree
from vumi.message import Message, VUMI_DATE_FORMAT
from vumi.webapp.api import utils

from twisted.python import log
from twisted.python.log import logging
from twisted.internet.defer import inlineCallbacks, returnValue

class SessionConsumer(Consumer):
    exchange_name = "vumi"
    exchange_type = "direct"
    durable = True
    delivery_mode = 2
    queue_name = "vumi.inbound.session.default" #TODO revise name
    routing_key = "vumi.inbound.session.default" #TODO revise name
    sessions = {}
    yaml_template = None
    url_for_data = {"username":None, "password":None, "url":None}


    def __init__(self, publisher):
        self.publisher = publisher

    def set_yaml_template(self, yaml_template):
        self.yaml_template = yaml_template

    def set_url_for_data(self, data_source):
        self.url_for_data = data_source


    def consume_message(self, message):
        log.msg("session message %s consumed by %s" % (
            json.dumps(dictionary),self.__class__.__name__))
        #dictionary = message.get('short_message')


    def call_for_json(self, MSISDN):
        if self.url_for_data['url']:
            params = [("telNo", str(MSISDN))]
            url = self.url_for_data['url']
            auth_string = ''
            if self.url_for_data['username']:
                auth_string += self.url_for_data['username']
                if self.url_for_data['password']:
                    auth_string += ":" + self.url_for_data['password']
                auth_string += "@"
            resp_url, resp = utils.callback("http://"+auth_string+url, params)
            print "RESP", resp
            return resp
        return None


    def get_session(self, MSISDN):
        session = self.sessions.get(MSISDN)
        if not session:
            self.sessions[MSISDN] = self.create_new_session(MSISDN)
            session = self.sessions.get(MSISDN)
        return session


    def gsdt(self, MSISDN): # shorthand for get_session_decision_tree
        return self.get_session(MSISDN).get_decision_tree()


    def create_new_session(self, MSISDN, **kwargs):
        session = VumiSession()
        decision_tree = TraversedDecisionTree()
        session.set_decision_tree(decision_tree)
        yaml_template = self.yaml_template
        decision_tree.load_yaml_template(yaml_template)
        self.set_url_for_data(decision_tree.get_data_source())
        if self.url_for_data.get('url'):
            json_data = self.call_for_json(MSISDN)
            decision_tree.load_json_data(json_data)
        else:
            decision_tree.load_dummy_data()
        return session



class SessionPublisher(Publisher):
    exchange_name = "vumi"
    exchange_type = "direct"
    routing_key = "vumi.outbound.session.fallback"
    durable = True
    auto_delete = False
    delivery_mode = 2

    def publish_message(self, message, **kwargs):
        log.msg("Publishing Message %s with extra args: %s" % (message, kwargs))
        super(SessionPublisher, self).publish_message(message, **kwargs)


class SessionWorker(Worker):
    """
    A worker that runs a set statefull interactive sessions
    with multiple MSISDN's
    """

    @inlineCallbacks
    def startWorker(self):
        log.msg("Starting the SessionWorker")
        self.publisher = yield self.start_publisher(sessionPublisher)
        yield self.start_consumer(SessionConsumer, self.publisher)

    def stopWorker(self):
        log.msg("Stopping the SessionWorker")

