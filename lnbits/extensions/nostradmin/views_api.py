from http import HTTPStatus
import asyncio
from fastapi import Request
from fastapi.param_functions import Query
from fastapi.params import Depends
from starlette.exceptions import HTTPException

from . import nostradmin_ext

# from .tasks import relay_manager
from .tasks import client

from .crud import get_relays, add_relay
from .models import RelayList, Relay
from lnbits.decorators import (
    WalletTypeInfo,
    get_key_type,
    require_admin_key,
    check_admin,
)

from lnbits.settings import settings
from lnbits.core.models import Payment, User, Wallet


@nostradmin_ext.get("/api/v1/relays")
async def api_get_relays():  # type: ignore
    relays = RelayList(__root__=[])
    for url, r in client.relay_manager.relays.items():
        status_text = (
            f"⬆️ {r.num_sent_events} ⬇️ {r.num_received_events} ⚠️ {r.error_counter}"
        )
        connected_text = "🟢" if r.connected else "🔴"

        relays.__root__.append(
            Relay(
                id="1337",
                url=url,
                connected_string=connected_text,
                status=status_text,
                ping=r.ping,
            )
        )
    # return await get_relays()
    return relays


@nostradmin_ext.post("/api/v1/relay", dependencies=[Depends(check_admin)])
async def api_add_relay(relay: Relay):  # type: ignore
    await add_relay(relay)


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
