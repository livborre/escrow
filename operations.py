# Python imports
from typing import Tuple

# Algorand library 
from algosdk import encoding
from algosdk.v2client.algod import AlgodClient
from algosdk.future import transaction
from algosdk.logic import get_application_address
from algosdk.future.transaction import AssetTransferTxn

# Import the contract programs.
from contract import approval_program, clear_state_program

# Import utility classes and functions.
from utils import Account, fully_compile_contract, wait_for_transaction, get_app_global_state, get_account

# Operation functions; compiling, creating/funding the contract, depositing an NFT, and paying the contract.
def get_contracts(client: AlgodClient) -> Tuple[bytes, bytes]:
    """Get the compiled TEAL contracts for the auction.

    Args:
        client: An algod client that has the ability to compile TEAL programs.

    Returns:
        A tuple of 2 byte strings. The first is the approval program, and the
        second is the clear state program.
    """

    APPROVAL_PROGRAM = b""
    CLEAR_STATE_PROGRAM = b""

    if len(APPROVAL_PROGRAM) == 0:
        APPROVAL_PROGRAM = fully_compile_contract(client, approval_program())
        CLEAR_STATE_PROGRAM = fully_compile_contract(client, clear_state_program())

    return APPROVAL_PROGRAM, CLEAR_STATE_PROGRAM

def create_escrow_contract(client: AlgodClient, creator: Account) -> int:
    """Create a new escrow contract.

    Args:
        client: An algod client.
        sender: The account that will create the escrow contract..

    Returns:
        The ID of the newly created escrow contract..
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
    response = wait_for_transaction(client, signed_txn.get_txid())
    assert response.applicationIndex is not None and response.applicationIndex > 0
    return response.applicationIndex
    
def fund_escrow_contract(client: AlgodClient, funder: Account, application_ID: int):
    """ A function to fund the escrow contract specified using the application ID using a funder account. 
    
    Args: 
        client: An algod client.
        funder: The account providing the funding for the escrow account.
        application_ID: The application ID of the escrow account.
    
    Returns: 
        signed_fund_txn_id: the transaction ID of the funding transaction.
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

    signed_fund_txn_id = signed_fund_txn.get_txid()
    wait_for_transaction(client, signed_fund_txn_id)

    return signed_fund_txn_id

def deposit_NFT(client: AlgodClient, seller: Account, application_ID: int, NFT_ID: int):
    """Opt in Contract to receive the required seller NFT (via on_setup method) and deposit NFT from seller.

    Args:
        client: An algod client.
        seller: An account that possesses a NFT to deposit to the contract.
        appID: The Application ID of the contract.
        nftID: The NFT ID of the contract.

    Returns:
        signed_deposit_NFT_txn_id: the transaction ID of the NFT deposit transaction.
    """

    application_address = get_application_address(application_ID)
    suggested_params = client.suggested_params()

    # sets the price of the NFT to 1 Algo.
    price = 1_000_000  

    # set up special 'app_args' for deposit call transaction below.
    app_args = [
        b"deposit",
        encoding.decode_address(get_account("seller").getAddress()),
        NFT_ID.to_bytes(8, "big"),
        price.to_bytes(8, "big")
    ]

    # calls the 'on_deposit' method in the contract.
    on_deposit_txn = transaction.ApplicationCallTxn(
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
    transaction.assign_group_id([on_deposit_txn, deposit_NFT_txn])

    # sign both transactions by the seller and send.
    signed_on_deposit_txn = on_deposit_txn.sign(seller.getPrivateKey())
    signed_deposit_NFT_txn = deposit_NFT_txn.sign(seller.getPrivateKey())
    client.send_transactions([signed_on_deposit_txn, signed_deposit_NFT_txn])

    # wait for NFT to be deposited in contract.
    signed_deposit_NFT_txn_id = signed_deposit_NFT_txn.get_txid()
    wait_for_transaction(client, signed_deposit_NFT_txn_id)
    
    return signed_deposit_NFT_txn_id

def pay_contract(client: AlgodClient, application_ID: int, buyer: Account):
    """ From the buyer address, buy the NFT deposited in the contract. Also, call the on_buy method in the contract to transfer the NFT asset from the contract to the buyer.

    Args:
        client: An Algod client.
        application_ID: The app ID of the auction.
        buyer: A buyer account.

    Returns: 
        signed_pay_txn_id: the transaction ID of the payment transaction from the buyer to the smart contract.
    """

    application_address = get_application_address(application_ID)
    application_global_state = get_app_global_state(client, application_ID)
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
    wait_for_transaction(client, opt_buyer_txn_id)

    app_args = [
        b"buy",
        encoding.decode_address(buyer.getAddress()),
        # price.to_bytes(8, "big")
    ]

    creator = get_account("creator")
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
    signed_pay_txn_id = signed_pay_txn.get_txid()
    wait_for_transaction(client, signed_pay_txn_id)

    return signed_pay_txn_id


