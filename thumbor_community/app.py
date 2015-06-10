# -*- coding: utf-8 -*-

import tornado.web
import tornado.ioloop

from thumbor.handlers.healthcheck import HealthcheckHandler
from thumbor.handlers import ContextHandler
from thumbor.utils import logger
from thumbor_community import Extensions
from thumbor_community.context import Context


class App(tornado.web.Application):

    def __init__(self, context):
        '''
        :param context: `Context` instance
        '''

        self.context = context

        if self.context.config.get('COMMUNITY_EXTENSIONS', None):
            for extension in self.context.config.get('COMMUNITY_EXTENSIONS'):
                Extensions.load(extension)

        if self.context.config.get('COMMUNITY_MONKEYPATCH', True):
            logger.debug("Monkey patching ContextHandler.initialize")
            # Monkey patch the ContextHandler.initialize method to generate a
            # community context instead of the one from vanilla thumbor.

            def initialize(self, context):
                '''Initialize a new Context object
                :param context:
                '''

                self.context = Context(
                    context.server,
                    context.config,
                    context.modules.importer,
                    request_handler=self
                )

            ContextHandler.initialize = initialize

        super(App, self).__init__(self.get_handlers())

    def get_handlers(self):
        '''Return a list of tornado web handlers.
        '''

        handlers = [
            (r'/healthcheck', HealthcheckHandler)
        ]

        for extensions in Extensions.extensions:
            for handler in extensions.handlers:

                # Inject the context if the handler expects it.
                if issubclass(handler[1], ContextHandler):
                    if len(handler) < 3:
                        handler = list(handler)
                        handler.append(dict(context=self.context))
                    else:
                        handler[2]['context'] = self.context

                handlers.append(handler)

        return handlers
