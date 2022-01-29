# Python imports
import os
from typing import List, Dict, Any, Optional, Union
from base64 import b64decode

# Algorand library and Pyteal imports.
from algosdk.v2client.algod import AlgodClient
from algosdk.future.transaction import AssetConfigTxn, wait_for_confirmation
from algosdk import account, mnemonic
from pyteal import compileTeal, Mode, Expr

# Useful Classes 
# =============================================================================================

class Account:
    """Represents a private key and address for an Algorand account"""

    def __init__(self, privateKey: str) -> None:
        self.sk = privateKey
        self.addr = account.address_from_private_key(privateKey)

    def getAddress(self) -> str:
        return self.addr

    def getPrivateKey(self) -> str:
        return self.sk

    def getMnemonic(self) -> str:
        return mnemonic.from_private_key(self.sk)

    @classmethod
    def FromMnemonic(cls, m: str) -> "Account":
        return cls(mnemonic.to_private_key(m))

class Pending_txn_response:
    """Represents a transaction response object and interesting variables."""
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


# Compiling function and functions to talk with the Algorand chain via the local Algorand sandbox client
# ============================================================================================= 

def fully_compile_contract(client: AlgodClient, contract: Expr) -> bytes:
    teal = compileTeal(contract, mode=Mode.Application, version=5)
    response = client.compile(teal)
    return b64decode(response["result"])

def get_client():
    algod_address = "http://localhost:4001"
    algod_token = "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
    algod_client = AlgodClient(algod_token, algod_address)
    return algod_client

def wait_for_transaction(
    client: AlgodClient, txID: str, timeout: int = 10
) -> Pending_txn_response:
    lastStatus = client.status()
    lastRound = lastStatus["last-round"]
    startRound = lastRound

    while lastRound < startRound + timeout:
        pending_txn = client.pending_transaction_info(txID)

        if pending_txn.get("confirmed-round", 0) > 0:
            return Pending_txn_response(pending_txn)

        if pending_txn["pool-error"]:
            raise Exception("Pool error: {}".format(pending_txn["pool-error"]))

        lastStatus = client.status_after_block(lastRound + 1)

        lastRound += 1

    raise Exception(
        "Transaction {} not confirmed after {} rounds".format(txID, timeout)
    )

def create_NFT(seller: Account):
    """ Create NFT in the sender account. 
    Args: 
        Seller: A seller account.
    
    Returns: 
        NFT_ID: The NFT ID.
    """

    algod_client = get_client()
    seller_address = seller.getAddress()

    create_NFT_txn = AssetConfigTxn(sender=seller_address,
                        sp=algod_client.suggested_params(),
                        total=1,          
                        default_frozen=False,
                        unit_name="CC",
                        asset_name="Carbon Credit: 1 Ton",
                        manager=seller_address,
                        reserve=seller_address,
                        freeze=seller_address,
                        clawback=seller_address,
                        decimals=0)       

    signed_NFT_txn = create_NFT_txn.sign(seller.getPrivateKey())
    NFT_creation_txn = algod_client.send_transaction(signed_NFT_txn)
    print(f"NFT creation transaction ID: {NFT_creation_txn}")
    wait_for_confirmation(algod_client, NFT_creation_txn)

    try:
        pending_txn= algod_client.pending_transaction_info(NFT_creation_txn)
        NFT_ID = pending_txn["asset-index"]
    except Exception as error:
        print(error)

    return NFT_ID

# Global State functions.
# =============================================================================================

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

def get_app_global_state(
    client: AlgodClient, appID: int
) -> Dict[bytes, Union[int, bytes]]:
    appInfo = client.application_info(appID)
    return decodeState(appInfo["params"]["global-state"])


# Account Operations
# =============================================================================================
# Account related specific imports

from os.path import join, dirname
from dotenv import load_dotenv
dotenv_path = join(dirname(__file__), '.env')
load_dotenv(dotenv_path)

def generate_algorand_keypair():
    private_key, address = account.generate_account()
    seed_phrase = mnemonic.from_private_key(private_key)

    return private_key, address, seed_phrase

creator_pk = os.environ.get("CREATOR_PK")
buyer_pk = os.environ.get("BUYER_PK")
seller_pk = os.environ.get("SELLER_PK")

def get_account(role: str):
    """ Get an Account class instance representing either the creator, seller or buyer account."""
    if role == "creator":
        private_key = creator_pk
    elif role == "seller":
        private_key = seller_pk
    elif role == "buyer":
        private_key = buyer_pk
    else:
        print("Invalid role. Please pass through creator, seller or buyer.")
    return Account(private_key)


