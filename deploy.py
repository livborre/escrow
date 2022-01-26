import json
from typing import Tuple, List

from algosdk.v2client.algod import AlgodClient
from algosdk.future import transaction
from algosdk.logic import get_application_address

from account import Account
from contract import approval_program, clear_state_program
from util import (
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


def createAuctionApp(
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

    globalSchema = transaction.StateSchema(num_uints=7, num_byte_slices=2)
    localSchema = transaction.StateSchema(num_uints=0, num_byte_slices=0)

    app_args = [
       "Liv" 
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

def create_and_fund(sender: Account):
    algod_client = get_client()
    account_info = algod_client.account_info(sender.getAddress())

    print("My address: {}".format(sender.getAddress()))
    print("Account balance: {} microAlgos".format(account_info.get('amount')))

    application_id = createAuctionApp(algod_client, sender)
    print(f"Application ID: {application_id}")

    print("Funding Escrow Contract...")
    response = fund_escrow(algod_client, sender, application_id)

    appAddr = get_application_address(application_id)
    app_info = algod_client.account_info(appAddr)
    
    print("App balance: {} microAlgos".format(app_info.get('amount')))

create_and_fund(get_account())







