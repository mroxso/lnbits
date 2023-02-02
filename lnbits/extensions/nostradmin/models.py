import json
from typing import List, Dict
from sqlite3 import Row
from typing import Optional

from fastapi import Request
from pydantic import BaseModel
from pydantic.main import BaseModel
from fastapi.param_functions import Query


class Relay(BaseModel):
    id: str
    url: str
    connected: Optional[bool]
    connected_string: Optional[str]
    status: Optional[str]
    active: Optional[bool]
    ping: Optional[int]


class RelayList(BaseModel):
    __root__: List[Relay]


# class nostrKeys(BaseModel):
#     pubkey: str
#     privkey: str

# class nostrNotes(BaseModel):
#     id: str
#     pubkey: str
#     created_at: str
#     kind: int
#     tags: str
#     content: str
#     sig: str

# class nostrCreateRelays(BaseModel):
#     relay: str = Query(None)

# class nostrCreateConnections(BaseModel):
#     pubkey: str = Query(None)
#     relayid: str = Query(None)

# class nostrRelays(BaseModel):
#     id: Optional[str]
#     relay: Optional[str]
#     status: Optional[bool] = False


# class nostrRelaySetList(BaseModel):
#     allowlist: Optional[str]
#     denylist: Optional[str]

# class nostrConnections(BaseModel):
#     id: str
#     pubkey: Optional[str]
#     relayid: Optional[str]

# class nostrSubscriptions(BaseModel):
#     id: str
#     userPubkey: Optional[str]
#     subscribedPubkey: Optional[str]
