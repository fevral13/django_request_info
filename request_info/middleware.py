# -*- coding:utf-8 -*-
from copy import copy
import logging
import sys
from django.http import HttpRequest


logger = logging.getLogger(__name__)

def _format_variable(name, value):
    _val = value
    if isinstance(_val, HttpRequest):
        _val = copy(value)
        _val.META = u'<removed>'
    _val = repr(_val)
    _val = '\n'.join(map(lambda i: '    ' + i, _val.split('\n')))
    return u'{name}={value}'.format(name=name, value=_val.strip())


class RequestInfoLoggingMiddleware(object):
    def process_response(self, request, response):
        status = response.status_code
        msg = u'{method} {path} {status} {size}'.format(method=request.method, path=request.get_full_path(), status=status, size=response.tell())
        if request.user.is_authenticated():
            msg += u' [#{id} {name}]'.format(id=request.user.id, name=request.user.username)

        if status not in (200, 301, 302):
            logger.warning(msg)
        else:
            logger.info(msg)
        return response

    def process_exception(self, request, exception):
        exception_type, exception_instance, tb = sys.exc_info()
        stack = []

        while tb:
            stack.append(tb.tb_frame)
            tb = tb.tb_next

        msg = [
            u'{method} {path}'.format(method=request.method, path=request.get_full_path()),
            u'{exception_name}: {exception_message}'.format(exception_name=exception.__class__.__name__, exception_message=exception.message),
        ]
        if request.user.is_authenticated():
            msg.append(u'User: #{id} {name}'.format(id=request.user.id, name=request.user.username))

        for frame in stack:
            msg.append(u'-' * 20)
            filename = frame.f_code.co_filename
            msg.append(u'{file}: {line}'.format(file=filename, line=frame.f_lineno))

            if not 'site-packages/django' in filename:
                msg.append(u'Locals: {locals}'.format(locals=', '.join(frame.f_locals.iterkeys())))
                for var_name, var_value in frame.f_locals.iteritems():
                    msg.append(_format_variable(var_name, var_value))

        logger.error('\n'.join(msg))
