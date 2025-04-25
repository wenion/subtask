"""
The subtask server for Hypothesis.

This file contains a worker class for Gunicorn (:py:class:`h.subtask.Worker`)
and a stripped-down Pyramid application which exposes a single endpoint for
serving the "streamer" over the websocket.

Most of the code in this file: specifically the WebSocketWSGIHandler,
GEventWebSocketPool, and WSGIServer classes, are essentially lifted straight
from the ws4py codebase. We've made a number of modifications to fix bugs in
the (apparently unmaintained) ws4py code, and these are documented below:

1. Override WebSocketWSGIHandler.run_application due to the websocket server
   crashing with EBADF. A change in gevent (1.1) causes all sockets to be
   closed when a WSGI handler returns. ws4py starts a new greenlet for each
   new websocket connection used to return from the WSGI handler. The fix is
   taken from [1] and waits for the greenlet to finish before returning from
   the WSGI handler.

   [1]: https://github.com/Lawouach/WebSocket-for-Python/pull/180

   More information at:

   - https://github.com/Lawouach/WebSocket-for-Python/issues/170
   - https://github.com/gevent/gevent/issues/633

2. Fix GEventWebSocketPool so that if the set of greenlets changes while it is
   being closed it doesn't throw a "Set changed size during iteration"
   RuntimeError. See:

   - https://github.com/Lawouach/WebSocket-for-Python/issues/132

N.B. Portions of the ws4py code are used here under the terms of the MIT
license distributed with the ws4py project. Such code remains copyright (c)
2011-2015, Sylvain Hellegouarch.
"""

import logging
import weakref

import psycogreen.gevent
from gevent.pool import Pool
from gunicorn.workers.ggevent import GeventPyWSGIWorker # PyWSGIHandler, PyWSGIServer
# from ws4py import format_addresses

log = logging.getLogger(__name__)


class Worker(GeventPyWSGIWorker):
    def patch(self):  # pragma: no cover
        psycogreen.gevent.patch_psycopg()
        self.log.info("Made psycopg green")

        super().patch()
