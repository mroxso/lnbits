from http import HTTPStatus
import asyncio
import ssl
import json
from fastapi import Request
from fastapi.param_functions import Query
from fastapi.params import Depends
from starlette.exceptions import HTTPException

from . import nostradmin_ext

from .tasks import client

from .crud import get_relays, add_relay, delete_relay
from .models import RelayList, Relay, Event, Filter, Filters

from .nostr.nostr.event import Event as NostrEvent
from .nostr.nostr.event import EncryptedDirectMessage
from .nostr.nostr.filter import Filter as NostrFilter
from .nostr.nostr.filter import Filters as NostrFilters
from .nostr.nostr.message_type import ClientMessageType

from lnbits.decorators import (
    WalletTypeInfo,
    get_key_type,
    require_admin_key,
    check_admin,
)

from lnbits.helpers import urlsafe_short_hash
from .tasks import init_relays


@nostradmin_ext.get("/api/v1/relays")
async def api_get_relays():  # type: ignore
    relays = RelayList(__root__=[])
    for url, r in client.relay_manager.relays.items():
        status_text = (
            f"⬆️ {r.num_sent_events} ⬇️ {r.num_received_events} ⚠️ {r.error_counter}"
        )
        connected_text = "🟢" if r.connected else "🔴"
        relay_id = urlsafe_short_hash()
        relays.__root__.append(
            Relay(
                id=relay_id,
                url=url,
                connected_string=connected_text,
                status=status_text,
                ping=r.ping,
                connected=True,
                active=True,
            )
        )
    return relays


@nostradmin_ext.post("/api/v1/relay")
async def api_add_relay(relay: Relay):  # type: ignore
    assert relay.url, "no URL"
    relay.id = urlsafe_short_hash()
    await add_relay(relay)
    await init_relays()


@nostradmin_ext.delete("/api/v1/relay")
async def api_delete_relay(relay: Relay):  # type: ignore
    await delete_relay(relay)


# curl -k -X POST https://0.0.0.0:5001/nostradmin/api/v1/publish -d '{"id": "8889891a359994f80198fd662c0164252b20d8cd07c1e804737a02d74900cce6", "pubkey": "bd40bf53ae4bb068473bd41ed74b44ecd0456cc3d9c4fba5f9d26991bc8fae7e", "created_at": 1675940542, "kind": 4, "tags": [["p", "bd40bf53ae4bb068473bd41ed74b44ecd0456cc3d9c4fba5f9d26991bc8fae7e"]], "content": "1kh+nQ0MMfHeXNGpDaOmRA==?iv=yS2o4bNcajehMi3+EQxbgg==", "sig": "6f0f562a4e9462414eed2101ee02f88ebd703acb437670f8df31678a84051116d74edb2ce8389d336fef60996b3724530f0d998dbe77ce089b056a0190122a96"}' -H "X-Api-Key: f79aa34c8d6a433797319fcca081f8d5" -H "Content-type: application/json"
@nostradmin_ext.post("/api/v1/publish")
async def api_post_event(event: Event):
    nostr_event = NostrEvent(
        content=event.content,
        public_key=event.pubkey,
        created_at=event.created_at,  # type: ignore
        kind=event.kind,
        tags=event.tags or None,  # type: ignore
        signature=event.sig,
    )
    client.relay_manager.publish_event(nostr_event)

    # dummy for testing
    dm = EncryptedDirectMessage(
        recipient_pubkey=client.public_key.hex(),
        cleartext_content="this is from the API",
    )
    client.private_key.sign_event(dm)
    client.relay_manager.publish_event(dm)


# curl -k -X POST https://0.0.0.0:5001/nostradmin/api/v1/filter -d '{"kinds": [4], "#p": ["bd40bf53ae4bb068473bd41ed74b44ecd0456cc3d9c4fba5f9d26991bc8fae7e"]}' -H "X-Api-Key: f79aa34c8d6a433797319fcca081f8d5" -H "Content-type: application/json"
@nostradmin_ext.post("/api/v1/filter")
async def api_subscribe(filter: Filter):
    nostr_filter = NostrFilter(
        event_ids=filter.ids,
        kinds=filter.kinds,  # type: ignore
        authors=filter.authors,
        since=filter.since,
        until=filter.until,
        event_refs=filter.e,
        pubkey_refs=filter.p,
        limit=filter.limit,
    )

    filters = NostrFilters([nostr_filter])
    subscription_id = urlsafe_short_hash()
    client.relay_manager.add_subscription(subscription_id, filters)

    request = [ClientMessageType.REQUEST, subscription_id]
    request.extend(filters.to_json_array())
    message = json.dumps(request)
    client.relay_manager.publish_message(message)


# from .crud import (
#     create_nostrkeys,
#     get_nostrkeys,
#     create_nostrnotes,
#     get_nostrnotes,
#     create_nostrrelays,
#     get_nostrrelays,
#     get_nostrrelaylist,
#     update_nostrrelaysetlist,
#     create_nostrconnections,
#     get_nostrconnections,
# )

# # from .models import nostrKeys, nostrCreateRelays, nostrRelaySetList
# from .views import relay_check

# @nostradmin_ext.get("/api/v1/relays")
# async def api_relays_retrieve(wallet: WalletTypeInfo = Depends(get_key_type)):
#     relays = await get_nostrrelays()
#     if not relays:
#         await create_nostrrelays(nostrCreateRelays(relay="wss://relayer.fiatjaf.com"))
#         await create_nostrrelays(
#             nostrCreateRelays(relay="wss://nostr-pub.wellorder.net")
#         )
#         relays = await get_nostrrelays()
#     if not relays:
#         raise HTTPException(
#             status_code=HTTPStatus.UNAUTHORIZED, detail="User not authorized."
#         )
#     else:
#         for relay in relays:
#             relay.status = await relay_check(relay.relay)
#         return relays


# @nostradmin_ext.post("/api/v1/setlist")
# async def api_relayssetlist(data: nostrRelaySetList, wallet: WalletTypeInfo = Depends(get_key_type)):
#     if wallet.wallet.user not in settings.lnbits_admin_users:
#         raise HTTPException(
#             status_code=HTTPStatus.UNAUTHORIZED, detail="User not authorized."
#         )
#     return await update_nostrrelaysetlist(data)
