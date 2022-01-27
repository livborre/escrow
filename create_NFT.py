from algosdk.future.transaction import AssetConfigTxn, wait_for_confirmation
from account import Account

from util import (
   get_client,
   get_seller,
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
        print(f"NFT ID: {NFT_ID}")
    except Exception as e:
        print(e)

    return NFT_ID
