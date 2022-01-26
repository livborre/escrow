from typing import Tuple, List

from algosdk.v2client.algod import AlgodClient
from algosdk.future import transaction
from algosdk.logic import get_application_address
from algosdk import account, encoding
from algosdk.v2client import algod
import json
import base64

from account import Account
from contract import approval_program, clear_state_program
from util import (
    waitForTransaction,
    fullyCompileContract,
    getAppGlobalState,
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

def first_transaction(private_key, my_address):
    algod_address = "http://localhost:4001"
    algod_token = "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
    algod_client = algod.AlgodClient(algod_token, algod_address)

    print("My address: {}".format(my_address))
    account_info = algod_client.account_info(my_address)
    print("Account balance: {} microAlgos".format(account_info.get('amount')))

    sender = Account(private_key)

    application_id = createAuctionApp(algod_client, sender)

    print(f"Application ID: {application_id}")

    print("Account balance: {} microAlgos".format(account_info.get('amount')))

    
private_key = "pESL6ROf12JNlue4i6YEUCMhQRTkEvkDJVY5Emgb9TFIplmL0LIxwUUMoso8JL5WvW8MFE7iS6iYpx/Xq1w1SQ=="
my_address = "JCTFTC6QWIY4CRIMULFDYJF6K26W6DAUJ3REXKEYU4P5PK24GVETZC676E"

# first_transaction(private_key, my_address)
def query_contract():
    algod_address = "http://localhost:4001"
    algod_token = "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
    algod_client = algod.AlgodClient(algod_token, algod_address)

    info = algod_client.application_info(67039289)

    print(json.dumps(info, indent=4))

    print(base64.b64decode(
        info["params"]["global-state"][0]["value"]["bytes"]
    ))

query_contract()



