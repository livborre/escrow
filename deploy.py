from ast import Global
from datetime import datetime, timedelta
import json
from typing import Tuple, List

from algosdk.v2client.algod import AlgodClient
from algosdk.future import transaction
from algosdk.logic import get_application_address

from account import Account
from contract import approval_program, clear_state_program
from util import (
    get_buyer,
    get_nftid,
    get_seller,
    waitForTransaction,
    fullyCompileContract,
    getAppGlobalState,
    get_account,
    get_client,
    get_appid
)

APPROVAL_PROGRAM = b""
CLEAR_STATE_PROGRAM = b""


def getContracts(client: AlgodClient) -> Tuple[bytes, bytes]:
    """Get the compiled TEAL contracts for the auction.

    Args:
        client: An algod client that has the ability to compile TEAL programs.

    Returns:
        A tuple of 2 byte strings. The first is the approval program, and the
        second is the clear state program.
    """
    global APPROVAL_PROGRAM
    global CLEAR_STATE_PROGRAM

    if len(APPROVAL_PROGRAM) == 0:
        APPROVAL_PROGRAM = fullyCompileContract(client, approval_program())
        CLEAR_STATE_PROGRAM = fullyCompileContract(client, clear_state_program())

    return APPROVAL_PROGRAM, CLEAR_STATE_PROGRAM


def create_auctionApp(
    client: AlgodClient,
    sender: Account,
) -> int:
    """Create a new auction.

    Args:
        client: An algod client.
        sender: The account that will create the auction application.

    Returns:
        The ID of the newly created auction app.
    """
    approval, clear = getContracts(client)

    globalSchema = transaction.StateSchema(num_uints=3, num_byte_slices=1)
    localSchema = transaction.StateSchema(num_uints=0, num_byte_slices=0)

    price = 1_000_000  # 1 Algo

    app_args = [
        get_seller().getAddress(),
        get_nftid(),
        price
    ]

    txn = transaction.ApplicationCreateTxn(
        sender=sender.getAddress(),
        on_complete=transaction.OnComplete.NoOpOC,
        approval_program=approval,
        clear_program=clear,
        global_schema=globalSchema,
        local_schema=localSchema,
        app_args=app_args,
        sp=client.suggested_params(),
    )

    signedTxn = txn.sign(sender.getPrivateKey())

    client.send_transaction(signedTxn)

    response = waitForTransaction(client, signedTxn.get_txid())
    assert response.applicationIndex is not None and response.applicationIndex > 0
    return response.applicationIndex
    
def fund_escrow(client: AlgodClient, funder: Account, appID: int):
    suggestedParams = client.suggested_params()
    appAddr = get_application_address(appID)

    fundingAmount = (
        # min account balance
        100_000
        # additional min balance to opt into NFT
        + 100_000
        # 3 * min txn fee
        + 3 * 1_000
    )

    fundAppTxn = transaction.PaymentTxn(
        sender=funder.getAddress(),
        receiver=appAddr,
        amt=fundingAmount,
        sp=suggestedParams,
    )

    signedFundTxn = fundAppTxn.sign(funder.getPrivateKey())
    client.send_transaction(signedFundTxn)

    response = waitForTransaction(client, signedFundTxn.get_txid())
    return response

def setup_app(
    client: AlgodClient,
    sender: Account,
    appID: int,
    nftID: int
) -> int:
    """Create a new auction.

    Args:
        client: An algod client.
        sender: The account that will create the auction application.

    Returns:
        The ID of the newly created auction app.
    """

    suggestedParams = client.suggested_params()

    setupContractTxn = transaction.ApplicationCallTxn(
        sender=sender.getAddress(),
        index=appID,
        on_complete=transaction.OnComplete.NoOpOC,
        app_args=[b"setup"],
        foreign_assets=[nftID],
        sp=suggestedParams,
    )

    signedTxn = setupContractTxn.sign(sender.getPrivateKey())

    client.send_transaction(signedTxn)

    response = waitForTransaction(client, signedTxn.get_txid())
    print(f"Done")

def create_and_fund(creator: Account, seller: Account):
    algod_client = get_client()
    creator_info_before = algod_client.account_info(creator.getAddress())

    print("Creating Escrow Contract...")
    print("Creator address: {}".format(creator.getAddress()))
    print("Creator balance: {} microAlgos".format(creator_info_before.get('amount')))

    application_id = create_auctionApp(algod_client, creator)
    print(f"Application ID: {application_id}")

    print("Funding Escrow Contract...")
    response = fund_escrow(algod_client, creator, application_id)

    appAddr = get_application_address(application_id)
    app_info = algod_client.account_info(appAddr)
    creator_info_after = algod_client.account_info(creator.getAddress())

    print("Escrow balance: {} microAlgos".format(app_info.get('amount')))
    print("Creator balance: {} microAlgos".format(creator_info_after.get('amount')))

    print("Opt in Escrow Contract to receive nft...")
    setup_app(algod_client, seller, application_id, get_nftid())

def buy_nft(client: AlgodClient, appID: int, buyer: Account) -> None:
    """Place a bid on an active auction.

    Args:
        client: An Algod client.
        appID: The app ID of the auction.
        bidder: The account providing the bid.
        bidAmount: The amount of the bid.
    """
    appAddr = get_application_address(appID)
    appGlobalState = getAppGlobalState(client, appID)

    nftID = appGlobalState[b"nft_id"]

    # if any(appGlobalState[b"bid_account"]):
    #     # if "bid_account" is not the zero address
    #     prevBidLeader = encoding.encode_address(appGlobalState[b"bid_account"])
    # else:
    #     prevBidLeader = None

    suggestedParams = client.suggested_params()

    price = 1_000_000  # 1 Algo
    payTxn = transaction.PaymentTxn(
        sender=buyer.getAddress(),
        receiver=appAddr,
        amt=price,
        sp=suggestedParams,
    )

    appCallTxn = transaction.ApplicationCallTxn(
        sender=buyer.getAddress(),
        index=appID,
        on_complete=transaction.OnComplete.NoOpOC,
        app_args=[b"buy"],
        foreign_assets=[nftID],
        # must include the previous lead bidder here to the app can refund that bidder's payment
        # accounts=[prevBidLeader] if prevBidLeader is not None else [],
        sp=suggestedParams,
    )

    transaction.assign_group_id([payTxn, appCallTxn])

    signedPayTxn = payTxn.sign(buyer.getPrivateKey())
    signedAppCallTxn = appCallTxn.sign(buyer.getPrivateKey())

    client.send_transactions([signedPayTxn, signedAppCallTxn])

    waitForTransaction(client, appCallTxn.get_txid())

def do_buy_nft(application_id: int, buyer: Account):
    algod_client = get_client()
    buyer_info_before = algod_client.account_info(buyer.getAddress())

    appGlobalState = getAppGlobalState(algod_client, application_id)
    nftID = appGlobalState[b"nft_id"]
    print(f"App nft before: {nftID}")

    print("Buying nft...")
    print("Buyer address: {}".format(buyer.getAddress()))
    print("Buyer balance: {} microAlgos".format(buyer_info_before.get('amount')))
    print("Buyer info: {}".format(json.dumps(buyer_info_before)))

    buy_nft(algod_client, application_id, buyer)

    appGlobalState = getAppGlobalState(algod_client, application_id)
    nftID = appGlobalState[b"nft_id"]
    print(f"App nft after: {nftID}")

    buyer_info_after = algod_client.account_info(buyer.getAddress())
    print("Buyer info: {}".format(json.dumps(buyer_info_after)))

# create_and_fund(get_account(), get_seller())
do_buy_nft(67207667, get_buyer())