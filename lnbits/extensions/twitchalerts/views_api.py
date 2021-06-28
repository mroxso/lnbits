from quart import g, redirect, request, jsonify
from http import HTTPStatus

from lnbits.decorators import api_validate_post_request, api_check_wallet_key
from lnbits.core.crud import get_wallet, get_user
from lnbits.utils.exchange_rates import btc_price

from . import twitchalerts_ext
from .crud import (
    get_charge_details,
    create_donation,
    post_donation,
    get_donation,
    get_donations,
    delete_donation,
    create_service,
    get_service,
    get_services,
    authenticate_service,
    update_donation,
    update_service,
    delete_service
)
from ..satspay.crud import create_charge, get_charge


@twitchalerts_ext.route("/api/v1/services", methods=["POST"])
@api_check_wallet_key("invoice")
@api_validate_post_request(
    schema={
        "twitchuser": {"type": "string", "required": True},
        "client_id": {"type": "string", "required": True},
        "client_secret": {"type": "string", "required": True},
        "wallet": {"type": "string", "required": True},
        "servicename": {"type": "string", "required": True},
        "onchain": {"type": "string"}
    }
)
async def api_create_service():
    """Create a service, which holds data about how/where to post donations"""
    service = await create_service(**g.data)
    wallet = await get_wallet(service.wallet)
    user = wallet.user
    redirect_url = request.scheme + "://" + request.headers["Host"]
    redirect_url += f"/twitchalerts/?usr={user}&created={str(service.id)}"
    return redirect(redirect_url)


@twitchalerts_ext.route("/api/v1/getaccess/<service_id>", methods=["GET"])
async def api_get_access(service_id):
    service = await get_service(service_id)
    if service:
        uri_base = request.scheme + "://"
        uri_base += request.headers["Host"] + "/twitchalerts/api/v1"
        redirect_uri = uri_base + f"/authenticate/{service_id}"
        params = {
            "response_type": "code",
            "client_id": service.client_id,
            "redirect_uri": redirect_uri,
            "scope": "donations.create",
            "state": service.state
        }
        endpoint_url = "https://streamlabs.com/api/v1.0/authorize/?"
        querystring = "&".join(
            [f"{key}={value}" for key, value in params.items()]
        )
        redirect_url = endpoint_url + querystring
        return redirect(redirect_url)
    else:
        return (
            jsonify({"message": "Service does not exist!"}),
            HTTPStatus.BAD_REQUEST
        )


@twitchalerts_ext.route("/api/v1/authenticate/<service_id>", methods=["GET"])
async def api_authenticate_service(service_id):
    code = request.args.get('code')
    state = request.args.get('state')
    service = await get_service(service_id)
    if service.state != state:
        return (
            jsonify({"message": "State doesn't match!"}),
            HTTPStatus.BAD_Request
        )
    redirect_uri = request.scheme + "://" + request.headers["Host"]
    redirect_uri += f"/twitchalerts/api/v1/authenticate/{service_id}"
    url, success = await authenticate_service(service_id, code, redirect_uri)
    if success:
        return redirect(url)
    else:
        return (
            jsonify({"message": "Service already authenticated!"}),
            HTTPStatus.BAD_REQUEST
        )


@twitchalerts_ext.route("/api/v1/donations", methods=["POST"])
@api_validate_post_request(
    schema={
        "name": {"type": "string"},
        "sats": {"type": "integer", "required": True},
        "service": {"type": "integer", "required": True},
        "message": {"type": "string"}
    }
)
async def api_create_donation():
    """Takes data from donation form and creates+returns SatsPay charge"""
    cur_code = "USD"
    price = await btc_price(cur_code)
    message = g.data.get("message", "")
    amount = g.data["sats"] * (10 ** (-8)) * price
    webhook_base = request.scheme + "://" + request.headers["Host"]
    service_id = g.data["service"]
    service = await get_service(service_id)
    charge_details = await get_charge_details(service.id)
    name = g.data.get("name", "Anonymous")
    charge = await create_charge(
        amount=g.data["sats"],
        completelink=f"https://twitch.tv/{service.twitchuser}",
        completelinktext="Back to Stream!",
        webhook=webhook_base + "/twitchalerts/api/v1/postdonation",
        **charge_details)
    await create_donation(
        id=charge.id,
        wallet=service.wallet,
        message=message,
        name=name,
        cur_code=cur_code,
        sats=g.data["sats"],
        amount=amount,
        service=g.data["service"],
    )
    return (
        jsonify({"redirect_url": f"/satspay/{charge.id}"}),
        HTTPStatus.OK
    )


@twitchalerts_ext.route("/api/v1/postdonation", methods=["POST"])
@api_validate_post_request(
    schema={
        "id": {"type": "string", "required": True},
    }
)
async def api_post_donation():
    """Posts a paid donation to Stremalabs/StreamElements.

    This endpoint acts as a webhook for the SatsPayServer extension."""
    data = await request.get_json(force=True)
    donation_id = data.get("id", "No ID")
    charge = await get_charge(donation_id)
    if charge and charge.paid:
        return await post_donation(donation_id)
    else:
        return (
            jsonify({"message": "Not a paid charge!"}),
            HTTPStatus.BAD_REQUEST
        )


@twitchalerts_ext.route("/api/v1/services", methods=["GET"])
@api_check_wallet_key("invoice")
async def api_get_services():
    wallet_ids = (await get_user(g.wallet.user)).wallet_ids
    services = []
    for wallet_id in wallet_ids:
        new_services = await get_services(wallet_id)
        services += new_services if new_services else []
    return (
        jsonify([
            service._asdict() for service in services
        ] if services else []),
        HTTPStatus.OK,
    )


@twitchalerts_ext.route("/api/v1/donations", methods=["GET"])
@api_check_wallet_key("invoice")
async def api_get_donations():
    wallet_ids = (await get_user(g.wallet.user)).wallet_ids
    donations = []
    for wallet_id in wallet_ids:
        new_donations = await get_donations(wallet_id)
        donations += new_donations if new_donations else []
    return (
        jsonify([
            donation._asdict() for donation in donations
        ] if donations else []),
        HTTPStatus.OK,
    )


@twitchalerts_ext.route("/api/v1/donations/<donation_id>", methods=["PUT"])
@api_check_wallet_key("invoice")
async def api_update_donation(donation_id=None):
    if donation_id:
        donation = await get_donation(donation_id)

        if not donation:
            return (
                jsonify({"message": "Donation does not exist."}),
                HTTPStatus.NOT_FOUND
            )

        if donation.wallet != g.wallet.id:
            return (
                jsonify({"message": "Not your donation."}),
                HTTPStatus.FORBIDDEN
            )

        donation = await update_donation(donation_id, **g.data)
    else:
        return (
            jsonify({"message": "No donation ID specified"}),
            HTTPStatus.BAD_REQUEST
        )
    return jsonify(donation._asdict()), HTTPStatus.CREATED


@twitchalerts_ext.route("/api/v1/services/<service_id>", methods=["PUT"])
@api_check_wallet_key("invoice")
async def api_update_service(service_id=None):
    if service_id:
        service = await get_service(service_id)

        if not service:
            return (
                jsonify({"message": "Service does not exist."}),
                HTTPStatus.NOT_FOUND
            )

        if service.wallet != g.wallet.id:
            return (
                jsonify({"message": "Not your service."}),
                HTTPStatus.FORBIDDEN
            )

        service = await update_service(service_id, **g.data)
    else:
        return (
            jsonify({"message": "No service ID specified"}),
            HTTPStatus.BAD_REQUEST
        )
    return jsonify(service._asdict()), HTTPStatus.CREATED


@twitchalerts_ext.route("/api/v1/donations/<donation_id>", methods=["DELETE"])
@api_check_wallet_key("invoice")
async def api_delete_donation(donation_id):
    donation = await get_donation(donation_id)
    if not donation:
        return (
            jsonify({"message": "No donation with this ID!"}),
            HTTPStatus.NOT_FOUND
        )
    if donation.wallet != g.wallet.id:
        return (
            jsonify({"message": "Not authorized to delete this donation!"}),
            HTTPStatus.FORBIDDEN
        )
    await delete_donation(donation_id)

    return "", HTTPStatus.NO_CONTENT


@twitchalerts_ext.route("/api/v1/services/<service_id>", methods=["DELETE"])
@api_check_wallet_key("invoice")
async def api_delete_service(service_id):
    service = await get_service(service_id)
    if not service:
        return (
            jsonify({"message": "No service with this ID!"}),
            HTTPStatus.NOT_FOUND
        )
    if service.wallet != g.wallet.id:
        return (
            jsonify({"message": "Not authorized to delete this service!"}),
            HTTPStatus.FORBIDDEN
        )
    await delete_service(service_id)

    return "", HTTPStatus.NO_CONTENT
