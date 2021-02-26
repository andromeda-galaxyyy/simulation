from collections import namedtuple


RoutingInput=namedtuple(field_names=["traffic"],typename="RoutingInput")
RoutingOutput=namedtuple(field_names=["labels"],typename="RoutingOutput")
Routing=namedtuple(field_names=["traffic","labels"],typename="Routing")