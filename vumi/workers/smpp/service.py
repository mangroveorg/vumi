
from twisted.python import log
from twisted.python.log import logging
from twisted.internet.defer import inlineCallbacks, returnValue
from twisted.internet import reactor

from vumi.service import Worker, Consumer, Publisher
from vumi.workers.smpp.server import SmscServerFactory, SmscServer

class SmppServiceConsumer(Consumer):
    exchange_name = "vumi"
    exchange_type = "direct"
    durable = True
    auto_delete = False
    queue_name = "smpp.outbound.dummy"
    routing_key = "smpp.outbound.dummy"

    def __init__(self):
        log.msg("Consuming on %s -> %s" % (self.routing_key, self.queue_name))


class SmppServicePublisher(Publisher):
    exchange_name = "vumi"
    exchange_type = "direct"
    routing_key = 'smpp.inbound.dummy'
    durable = False
    auto_delete = False
    delivery_mode = 2


class SmppService(Worker):
    """
    The SmppService
    """

    def startWorker(self):
        log.msg("Starting the SmppService")
        #self.publisher = yield SmppServicePublisher()
        #self.consumer = yield SmppServiceConsumer()
        # start the Smpp Service
        factory = SmscServerFactory()
        reactor.listenTCP(2772, factory)


    def stopWorker(self):
        log.msg("Stopping the SmppService")
