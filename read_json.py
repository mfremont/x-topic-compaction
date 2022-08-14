"""
Pulsar consumer that reads JSON-encoded messages.
"""

__all__ = ['decode_json', 'read_available']

import argparse
import contextlib
import json
import logging

import pulsar


def decode_json(message: pulsar.Message):
    """
    Decodes the message body as JSON.

    :param message: the message
    :return: the decoded message body
    """
    return json.loads(message.data())


def read_available(reader: pulsar.Reader, timeout_millis=None):
    """
    Returns a generator that yields the decoded JSON body of each available message.

    :param reader: the Pulsar Reader
    :param timeout_millis: the read timeout; blocks if ``None``
    :return: the generator
    :except: raises exception if the read times out
    """
    while reader.has_message_available():
        try:
            yield decode_json(reader.read_next(timeout_millis=timeout_millis))
        except pulsar.Timeout:
            break


if __name__ == '__main__':
    argp = argparse.ArgumentParser(
        description='Read JSON-encoded messages from a Pulsar topic')
    argp.add_argument('--url', type=str, default='pulsar://localhost:6650',
                      help='Pulsar URL, typically the proxy for a cluster or the '
                           'standalone broker.')
    argp.add_argument('--topic', type=str,
                      help='The topic to consume. The Pulsar defaults apply if not '
                           'fully-qualified.')
    argp.add_argument('--compacted', action='store_true',
                      help='Enable is_compacted_read.')
    argp.add_argument('--timeout-millis', type=int, default=None,
                      help='The timeout for reads. Blocks if not specified.')
    argp.add_argument('--print-each', type=str, default=None,
                      help='Comma-delimited list of attributes to print from each '
                           'message.')
    argp.add_argument('-v', '--verbose', action='store_true',
                      help='Allow the voluminous log output of the Pulsar client to be '
                           'output, otherwise log level is set to ERROR.')

    args = argp.parse_args()

    logger = logging.getLogger()
    if not args.verbose:
        logger.setLevel(logging.ERROR)

    with contextlib.closing(pulsar.Client(args.url, logger=logger)) as client:
        topic = args.topic
        compacted = args.compacted
        timeout = args.timeout_millis
        print_each = args.print_each.split(',') if args.print_each is not None else []

        with contextlib.closing(client.create_reader(
                topic, pulsar.MessageId.earliest, is_read_compacted=compacted)) as reader:
            n = 0
            for msgbody in read_available(reader, timeout_millis=timeout):
                n += 1
                if print_each:
                    print(dict((k, msgbody.get(k, None)) for k in print_each))
                else:
                    print(msgbody)

            print('Read %d messages from %s' % (n, topic))
