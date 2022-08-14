"""
Pulsar producer that publishes JSON messages. Messages are read from an input file and
published to a specified topic.
"""

__all__ = ['publish_messages']

import argparse
import contextlib
import json
import logging

import pulsar


def publish_messages(producer: pulsar.Producer, messages: list, key=None) -> int:
    """
    Publishes the messages using JSON encoding. If ``key`` is not ``None``, then the
    corresponding mapped value from each message will be used as the `partition_key`
    for that message.

    :param producer: the Pulsar producer
    :param messages: the messages to publish, each represented as a ``dict``
    :param key: message key to lookup in each message, or ``None`` if the messages should
        be published without a key
    :return: the number of messages published
    """
    count = 0
    for msg in messages:
        msgkey = msg[key] if key is not None else None
        producer.send(json.dumps(msg).encode('utf-8'), partition_key=msgkey)
        producer.flush()
        count += 1

    return count


if __name__ == '__main__':
    argp = argparse.ArgumentParser(
        description='Produce JSON-encoded messages to a Pulsar topic')
    argp.add_argument('--url', type=str, default='pulsar://localhost:6650',
                      help='Pulsar URL, typically the proxy for a cluster or the '
                           'standalone broker.')
    argp.add_argument('--first', type=int, default=0,
                      help='The index for the first message to produce.')
    argp.add_argument('--count', type=int, default=None,
                      help='The number of messages to produce. If omitted or greater '
                           'than the number of messages in the input, then all of the '
                           'messages are published.')
    argp.add_argument('--key', type=str, default=None,
                      help='The key in each message that is mapped to a value to be used '
                           'as the partition_key when publishing that message')
    argp.add_argument('--topic', type=str,
                      help='The topic on which to produce. The Pulsar defaults apply if '
                           'not fully-qualified.')
    argp.add_argument('-v', '--verbose', action='store_true',
                      help='Allow the voluminous log output of the Pulsar client to be '
                           'output, otherwise log level is set to ERROR.')
    argp.add_argument('jsonfile', type=str, nargs='+',
                      help='One or more input file(s) containing the messages to be '
                           'published each represented as an object in a JSON-encoded '
                           'array.')

    args = argp.parse_args()

    logger = logging.getLogger()
    if not args.verbose:
        logger.setLevel(logging.ERROR)

    with contextlib.closing(pulsar.Client(args.url, logger=logger)) as client:
        topic = args.topic
        with contextlib.closing(client.create_producer(topic)) as producer:
            for fn in args.jsonfile:
                with open(fn, 'r') as jsonfile:
                    data = json.load(jsonfile)
                    if isinstance(data, list):
                        i = args.first
                        if args.count is not None:
                            j = i + args.count
                            messages = data[i:j]
                        else:
                            messages = data[i:]
                        n = publish_messages(producer, messages, key=args.key)
                    print('Published %d messages to %s' % (n, topic))
