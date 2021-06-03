OUTPUT_ID = "kafka"


class KafkaOutput(object):
    def __init__(self, producer, topics):
        self.producer = producer
        self.topics = topics

    def write(self, data):
        if len(self.topics) == 0:
            return False

        for topic in self.topics:
            future = self.producer.send(topic, value=data)
        return True
