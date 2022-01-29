# Importing some utility classes and functions.
from utils import Account, get_client, create_NFT, get_app_global_state, get_account

# Import operation functions.
from operations import create_escrow_contract, fund_escrow_contract, deposit_NFT, pay_contract

# Some Algorand library functions.
from algosdk.logic import get_application_address

# some printing functions that use the opertions to carry out the example smart contract workflow.
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

    print("Funding Escrow Contract...")
    fund_escrow_contract(algod_client, creator, application_id)

    application_address = get_application_address(application_id)
    application_info = algod_client.account_info(application_address)
    application_balance = application_info.get('amount')

    print(f"Escrow balance: {application_balance} microAlgos")

    return application_id, application_address

def buy_and_transfer_NFT(application_ID: int, buyer: Account):
    """ Carry out buy_and_call_on_buy function with relevant information printed to buy the NFT from the buyer account, and move the NFT from the contract to the buyer.

    Args: 
        application_id: The ID of the application. 
        buyer: The buyer account.
    Returns:
        signed_pay_txn_id: the transaction ID for the payment transaction from buyer to the smart contract.
    """

    algod_client = get_client()
    buyer_info = algod_client.account_info(buyer.getAddress())
    buyer_balance = buyer_info.get('amount')

    application_global_state = get_app_global_state(algod_client, application_ID)
    NFT_ID = application_global_state[b"nft_id"]
    print(f"NFT to transfer: {NFT_ID}")

    print(f"Buyer address: {buyer.getAddress()}")
    print(f"Buyer balance: {buyer_balance} microAlgos.")

    print("Depositing 1 Algo into Escrow Contract...")
    signed_pay_txn_id = pay_contract(algod_client, application_ID, buyer)
    print(f"Matched 1 Algo with NFT ID: {NFT_ID}...")
    print("Automatic Execution: Transfer 1 Algo from Escrow Contract to seller, transfer NFT to buyer")
 
    print(f"Transfer NFT ID: {NFT_ID} to buyer")

    return signed_pay_txn_id

# print("=======================================================================================")
# Get the client to communicate with Algorand and the required account details.
client = get_client()
creator = get_account("creator")
seller = get_account("seller")
buyer = get_account("buyer")

# Create and fund contract from creator account.
application_ID, application_address = create_and_fund(creator) 
print(f"Contract deployed at address: {application_address}")
print("\n")
print("https://testnet.algoexplorer.io/address/" + f"{application_address}") 
input("\n" + "...")
print("=======================================================================================")

# Create the NFT in the seller account.
print("Creating NFT in seller account...")
NFT_ID = create_NFT(seller)
print(f"NFT ID: {NFT_ID} stored at seller address: {seller.getAddress()}")
print("\n")
print("https://testnet.algoexplorer.io/address/" + f"{seller.getAddress()}") 
input("\n" + "...")
print("=======================================================================================")

# Deposit the NFT from seller to smart contract.
print("Seller depositing NFT into Escrow Account...")
print(f"NFT {NFT_ID} deposited in contract {application_address}.")
signed_deposit_NFT_txn_id = deposit_NFT(client, seller, application_ID, NFT_ID)
print("\n")
print("https://testnet.algoexplorer.io/tx/" + f"{signed_deposit_NFT_txn_id}")
input("\n" + "...")
print("=======================================================================================")

# Send a buy transaction from buyer to contract, and transfer the NFT from the smart contract to buyer.
signed_pay_txn_id = buy_and_transfer_NFT(application_ID, buyer)
print(f"Payment transaction ID from buyer to Escrow Contract: {signed_pay_txn_id}")
print("\n")
print("https://testnet.algoexplorer.io/tx/" + f"{signed_pay_txn_id}")
print("=======================================================================================")
print("All done! Escrow contract ready to accept another NFT or Algos. Feel free to run example.py again.")