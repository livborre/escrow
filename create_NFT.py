from algosdk.v2client import algod
from account import Account
from algosdk.future.transaction import AssetConfigTxn, wait_for_confirmation
from algosdk.v2client import indexer

def create_NFT(private_key, my_address):
    algod_address = "http://localhost:4001"
    algod_token = "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
    algod_client = algod.AlgodClient(algod_token, algod_address)

    sender = Account(private_key)

    txn = AssetConfigTxn(sender=my_address,
                        sp=algod_client.suggested_params(),
                        total=1,          
                        default_frozen=False,
                        unit_name="CC",
                        asset_name="Carbon Credit: 1 Ton",
                        manager=my_address,
                        reserve=my_address,
                        freeze=my_address,
                        clawback=my_address,
                        decimals=0)       

    signedTxn = txn.sign(sender.getPrivateKey())

    txid = algod_client.send_transaction(signedTxn)
    print(f"txid: {txid}")

    wait_for_confirmation(algod_client,txid)

    try:
        # Pull account info for the creator
        account_info = algod_client.account_info(my_address)
        # get asset_id from tx
        # Get the new asset's information from the creator account
        ptx = algod_client.pending_transaction_info(txid)
        asset_id = ptx["asset-index"]
        print(f"asset_id: {asset_id}")
        asset = account_info["created-assets"][0]
        print(f"something interesting: {asset}")
    except Exception as e:
        print(e)

private_key = "pESL6ROf12JNlue4i6YEUCMhQRTkEvkDJVY5Emgb9TFIplmL0LIxwUUMoso8JL5WvW8MFE7iS6iYpx/Xq1w1SQ=="
my_address = "JCTFTC6QWIY4CRIMULFDYJF6K26W6DAUJ3REXKEYU4P5PK24GVETZC676E"

application_id = create_NFT(private_key, my_address)
print(f"application_id: {application_id}")