import json

from typing import Tuple
from algosdk import encoding
from algosdk.v2client.algod import AlgodClient
from algosdk.future import transaction
from algosdk.logic import get_application_address
from algosdk.future.transaction import AssetTransferTxn

from account import Account
from contract import approval_program, clear_state_program
from util import (
    get_buyer,
    get_creator,
    get_seller,
    waitForTransaction,
    fullyCompileContract,
    getAppGlobalState,
    get_client
)

from create_NFT import create_NFT

APPROVAL_PROGRAM = b""
CLEAR_STATE_PROGRAM = b""

def get_contracts(client: AlgodClient) -> Tuple[bytes, bytes]:
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

def create_escrow_contract(client: AlgodClient,
                           creator: Account) -> int:
    """Create a new auction.

    Args:
        client: An algod client.
        sender: The account that will create the auction application.

    Returns:
        The ID of the newly created auction app.
    """
    # compile contracts
    approval, clear = get_contracts(client) 
    global_schema = transaction.StateSchema(num_uints=3, num_byte_slices=2)
    local_schema = transaction.StateSchema(num_uints=0, num_byte_slices=0)

    # send a transaction to create the escrow contract
    txn = transaction.ApplicationCreateTxn(
        sender=creator.getAddress(),
        on_complete=transaction.OnComplete.NoOpOC,
        approval_program=approval,
        clear_program=clear,
        global_schema=global_schema,
        local_schema=local_schema,
        sp=client.suggested_params(),
    )

    # sign the transaction and sent it
    signed_txn = txn.sign(creator.getPrivateKey())
    client.send_transaction(signed_txn)
    # check that the app ID of the escrow contract is valid, if so, return it.
    response = waitForTransaction(client, signed_txn.get_txid())
    assert response.applicationIndex is not None and response.applicationIndex > 0
    return response.applicationIndex
    
def fund_escrow_contract(client: AlgodClient, funder: Account, application_ID: int):
    """ A function to fund the escrow contract specified using app_ID using a funder account. 
    
    Args: 
        client: An algod client.
        funder: The account providing the funding for the escrow account.
        application_ID: The application ID of the escrow account.
    
    Returns: 
        None
    """

    suggested_params = client.suggested_params()
    app_address = get_application_address(application_ID)

    funding_amount = (
        # min account balance
        100_000
        # additional min balance to opt into NFT
        + 100_000
        # 3 * min txn fee
        + 3 * 1_000
    )

    fund_escrow_txn = transaction.PaymentTxn(
        sender=funder.getAddress(),
        receiver=app_address,
        amt=funding_amount,
        sp=suggested_params,
    )

    signed_fund_txn = fund_escrow_txn.sign(funder.getPrivateKey())
    client.send_transaction(signed_fund_txn)

    waitForTransaction(client, signed_fund_txn.get_txid())

def opt_in_contract_and_deposit_NFT(
    client: AlgodClient,
    seller: Account,
    application_ID: int,
    NFT_ID: int
):
    """Opt in Contract (via on_setup method) and deposit NFT from seller.

    Args:
        client: An algod client.
        seller: An account that possesses a NFT to deposit to the contract.
        appID: The Application ID of the contract.
        nftID: The NFT ID of the contract.

    Returns:
        None
    """

    application_address = get_application_address(application_ID)
    suggested_params = client.suggested_params()

    # sets the price of the NFT to 1 Algo.
    price = 1_000_000  

    # set up special 'app_args' for setup call transaction below.
    app_args = [
        b"setup",
        encoding.decode_address(get_seller().getAddress()),
        NFT_ID.to_bytes(8, "big"),
        price.to_bytes(8, "big")
    ]

    # calls the 'on_setup' method in the contract.
    setup_contract_txn = transaction.ApplicationCallTxn(
        sender=seller.getAddress(),
        index=application_ID,
        on_complete=transaction.OnComplete.NoOpOC,
        app_args=app_args,
        foreign_assets=[NFT_ID],
        sp=suggested_params,
    )

    # set up the NFT deposit transaction from seller to contract.
    deposit_NFT_txn = transaction.AssetTransferTxn(
        sender=seller.getAddress(),
        receiver=application_address,
        index=NFT_ID,
        amt=1,
        sp=suggested_params,
    )

    # assign a group of transactions.
    transaction.assign_group_id([setup_contract_txn, deposit_NFT_txn])

    # sign both transactions by the seller and send.
    signed_setup_txn = setup_contract_txn.sign(seller.getPrivateKey())
    signed_deposit_NFT_txn = deposit_NFT_txn.sign(seller.getPrivateKey())
    client.send_transactions([signed_setup_txn, signed_deposit_NFT_txn])

    # wait for NFT to be deposited in contract.
    waitForTransaction(client, signed_deposit_NFT_txn.get_txid())
    print(f"NFT (NFT ID: {NFT_ID}) deposited in contract with app ID: {application_ID} and application address: {application_address}")

def create_and_fund(creator: Account):
    """ Utility function to create an escrow contract and fund it. Note that here the creator and the funder is the same address. Prints all relevant information before and after creation and funding.

    Args: 
        creator: A creator account instance.

    Returns: 
        application_id: The application id.
        application_address: The application address.
    """
    algod_client = get_client()
    creator_info = algod_client.account_info(creator.getAddress())
    creator_balance = creator_info.get('amount')

    print(f"Creator Address: {creator.getAddress()}")
    print(f"Initial Creator Balance: {creator_balance} microAlgos")

    print("Creating Escrow Contract...")
    application_id = create_escrow_contract(algod_client, creator)
    print(f"Contract deployed to Application ID: {application_id}")

    print("Funding Escrow Contract...")
    fund_escrow_contract(algod_client, creator, application_id)

    application_address = get_application_address(application_id)
    application_info = algod_client.account_info(application_address)
    creator_info = algod_client.account_info(creator.getAddress())
    creator_balance = creator_info.get('amount')
    application_balance = application_info.get('amount')

    print(f"Escrow balance: {application_balance} microAlgos")
    print(f"Creator balance: {creator_balance} microAlgos")

    return application_id, application_address, 

def pay_and_call_on_buy(client: AlgodClient, application_ID: int, buyer: Account):
    """ From the buyer address, buy the NFT deposited in the contract. Also, call the on_buy method in the contract to transfer the NFT asset from the contract to the buyer.

    Args:
        client: An Algod client.
        application_ID: The app ID of the auction.
        buyer: A buyer account.

    Returns: 
        None
    """

    application_address = get_application_address(application_ID)
    application_global_state = getAppGlobalState(client, application_ID)
    NFT_ID = application_global_state[b"nft_id"]

    accounts = [encoding.encode_address(application_global_state[b"seller"])]
    accounts.append(buyer.getAddress())

    suggested_params = client.suggested_params()

    # set up the payment transaction.
    price = 1_000_000  # 1 Algo
    pay_txn = transaction.PaymentTxn(
        sender=buyer.getAddress(),
        receiver=application_address,
        amt=price,
        sp=suggested_params,
    )
    
    opt_in_buyer_txn = AssetTransferTxn(
        sender=buyer.getAddress(),
        sp=suggested_params,
        receiver=buyer.getAddress(),
        amt=0,
        index=NFT_ID,
    )

    signed_opt_buyer_txn = opt_in_buyer_txn.sign(buyer.getPrivateKey())
    opt_buyer_txn_id = client.send_transaction(signed_opt_buyer_txn)
    print(f"Opting in buyer transaction ID: {opt_buyer_txn_id}")
    waitForTransaction(client, opt_buyer_txn_id)

    app_args = [
        b"buy",
        encoding.decode_address(buyer.getAddress()),
        # price.to_bytes(8, "big")
    ]

    creator = get_creator()
    # set up the call on_buy transaction.
    call_on_buy_txn = transaction.ApplicationCallTxn(
        sender=creator.getAddress(),
        index=application_ID,
        on_complete=transaction.OnComplete.NoOpOC,
        app_args=app_args,
        foreign_assets=[NFT_ID],
        accounts=accounts,
        sp=suggested_params,
    )

    # group the pay and the call on_buy transactions.
    transaction.assign_group_id([pay_txn, call_on_buy_txn])

    # sign the transactions and send them.
    signed_pay_txn = pay_txn.sign(buyer.getPrivateKey())
    signed_call_txn = call_on_buy_txn.sign(creator.getPrivateKey())
    client.send_transactions([signed_pay_txn, signed_call_txn])

    # wait for the call transaction to complete.
    waitForTransaction(client, signed_call_txn.get_txid())

def buy_and_transfer_NFT(application_ID: int, buyer: Account):
    """ Carry out buy_and_call_on_buy function with relevant information printed to buy the NFT from the buyer account, and move the NFT from the contract to the buyer.

    Args: 
        application_id: The ID of the application. 
        buyer: The buyer account.
    Returns:
        None.
    """
    algod_client = get_client()
    buyer_info = algod_client.account_info(buyer.getAddress())
    buyer_balance = buyer_info.get('amount')

    application_global_state = getAppGlobalState(algod_client, application_ID)
    NFT_ID = application_global_state[b"nft_id"]
    application_address = get_application_address(application_ID)
    print(f"Application id: {application_ID}")
    print(f"Application address: {application_address}")
    print(f"NFT ID: {NFT_ID}")

    pretty_buyer_info = json.dumps(buyer_info, indent=4)
    print(f"Buyer address: {buyer.getAddress()}")
    print(f"Buyer balance: {buyer_balance} microAlgos.")
    print(f"Buyer info before buying: {pretty_buyer_info}")

    print("Buying nft...")
    pay_and_call_on_buy(algod_client, application_ID, buyer)

    buyer_info = algod_client.account_info(buyer.getAddress())
    pretty_buyer_info = json.dumps(buyer_info, indent=4)
    print(f"Buyer info after buying: {pretty_buyer_info}")


# get account details.
client = get_client()
creator = get_creator()
seller = get_seller()
buyer = get_buyer()

# create and fund contract from creator account.
application_ID, application_address = create_and_fund(creator) 
print(f"Contract deployed at Application ID: {application_ID} and Application Address: {application_address}")

# create the NFT in the seller account.
NFT_ID = create_NFT(seller)
print(f"NFT deployed at NFT ID: {NFT_ID} stored at seller address: {seller.getAddress()}")

# opt in and deposit NFT from seller to contract.
opt_in_contract_and_deposit_NFT(client, seller, application_ID, NFT_ID)

# now send a buy transaction from buyer to contract and transfer NFT from contract to buyer.
buy_and_transfer_NFT(application_ID, buyer)

# THE NFT SEEMS TO BE WANTING TO BE TRANSFERRED FROM THE BUYER ACCOUNT, NOT FROM THE CONTRACT.