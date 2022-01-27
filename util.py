from typing import List, Tuple, Dict, Any, Optional, Union
from base64 import b64decode
from algosdk.v2client.algod import AlgodClient
from algosdk import mnemonic
from pyteal import compileTeal, Mode, Expr
import os
from os.path import join, dirname
from dotenv import load_dotenv

dotenv_path = join(dirname(__file__), '.env')
load_dotenv(dotenv_path)





from account import Account

class PendingTxnResponse:
    def __init__(self, response: Dict[str, Any]) -> None:
        self.poolError: str = response["pool-error"]
        self.txn: Dict[str, Any] = response["txn"]

        self.applicationIndex: Optional[int] = response.get("application-index")
        self.assetIndex: Optional[int] = response.get("asset-index")
        self.closeRewards: Optional[int] = response.get("close-rewards")
        self.closingAmount: Optional[int] = response.get("closing-amount")
        self.confirmedRound: Optional[int] = response.get("confirmed-round")
        self.globalStateDelta: Optional[Any] = response.get("global-state-delta")
        self.localStateDelta: Optional[Any] = response.get("local-state-delta")
        self.receiverRewards: Optional[int] = response.get("receiver-rewards")
        self.senderRewards: Optional[int] = response.get("sender-rewards")

        self.innerTxns: List[Any] = response.get("inner-txns", [])
        self.logs: List[bytes] = [b64decode(l) for l in response.get("logs", [])]


def waitForTransaction(
    client: AlgodClient, txID: str, timeout: int = 10
) -> PendingTxnResponse:
    lastStatus = client.status()
    lastRound = lastStatus["last-round"]
    startRound = lastRound

    while lastRound < startRound + timeout:
        pending_txn = client.pending_transaction_info(txID)

        if pending_txn.get("confirmed-round", 0) > 0:
            return PendingTxnResponse(pending_txn)

        if pending_txn["pool-error"]:
            raise Exception("Pool error: {}".format(pending_txn["pool-error"]))

        lastStatus = client.status_after_block(lastRound + 1)

        lastRound += 1

    raise Exception(
        "Transaction {} not confirmed after {} rounds".format(txID, timeout)
    )


def fullyCompileContract(client: AlgodClient, contract: Expr) -> bytes:
    teal = compileTeal(contract, mode=Mode.Application, version=5)
    response = client.compile(teal)
    return b64decode(response["result"])


def decodeState(stateArray: List[Any]) -> Dict[bytes, Union[int, bytes]]:
    state: Dict[bytes, Union[int, bytes]] = dict()

    for pair in stateArray:
        key = b64decode(pair["key"])

        value = pair["value"]
        valueType = value["type"]

        if valueType == 2:
            # value is uint64
            value = value.get("uint", 0)
        elif valueType == 1:
            # value is byte array
            value = b64decode(value.get("bytes", ""))
        else:
            raise Exception(f"Unexpected state type: {valueType}")

        state[key] = value

    return state


def getAppGlobalState(
    client: AlgodClient, appID: int
) -> Dict[bytes, Union[int, bytes]]:
    appInfo = client.application_info(appID)
    return decodeState(appInfo["params"]["global-state"])


def getBalances(client: AlgodClient, account: str) -> Dict[int, int]:
    balances: Dict[int, int] = dict()

    accountInfo = client.account_info(account)

    # set key 0 to Algo balance
    balances[0] = accountInfo["amount"]

    assets: List[Dict[str, Any]] = accountInfo.get("assets", [])
    for assetHolding in assets:
        assetID = assetHolding["asset-id"]
        amount = assetHolding["amount"]
        balances[assetID] = amount

    return balances


def getLastBlockTimestamp(client: AlgodClient) -> Tuple[int, int]:
    status = client.status()
    lastRound = status["last-round"]
    block = client.block_info(lastRound)
    timestamp = block["block"]["ts"]

    return block, timestamp

def get_client():
    algod_address = "http://localhost:4001"
    algod_token = "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
    algod_client = AlgodClient(algod_token, algod_address)
    return algod_client


creator_pk = os.environ.get("CREATOR_PK")
buyer_pk = os.environ.get("BUYER_PK")
seller_pk = os.environ.get("SELLER_PK")

creator_address = os.environ.get("CREATOR_ADDRESS")
buyer_address = os.environ.get("BUYER_ADDRESS")
seller_address = os.environ.get("SELLER_ADDRESS")

def get_creator():
    private_key = creator_pk
    my_address = creator_address
    # bullet cigar couple same panther ugly drill fold talk shrug sunset come love crystal evoke there hollow setup swift olympic similar trigger floor absorb argue
    return Account(private_key)

def get_seller():
    private_key = seller_pk
    my_address = seller_address
    # goose ketchup mistake void drill drastic cat pact impose swamp later pigeon gift load frozen dry enroll vague seed clinic caution nice soap abstract wire
    return Account(private_key)

def get_buyer():
    private_key = buyer_pk
    my_address = buyer_address
    # neither surface artefact garage clutch catch kiss bacon job spread border blade later meat sound muffin hello moral razor endorse alter just sustain able shadow
    return Account(private_key)

def get_nftid():
    return 67248837

def printState(appID: int):
    state = getAppGlobalState(get_client(), appID)
    print(state)

def get_mnemonic(Account: Account):
    private_key = Account.getPrivateKey()
    return mnemonic.from_private_key(private_key)

