from collections import namedtuple

Routing=namedtuple("Routing",["traffic","labels"])
RoutingInput=namedtuple("RoutingInput",["traffic"])
RoutingOutput=namedtuple("RoutingOutput",["labels"])