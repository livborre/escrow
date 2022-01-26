import string
from typing import Tuple, List
from urllib import response

from algosdk.v2client.algod import AlgodClient
from algosdk.future import transaction

from algosdk import account, encoding
from algosdk.v2client import algod
from account import Account
from contract import approval_program, clear_state_program
from util import (
    waitForTransaction,
    fullyCompileContract,
    getAppGlobalState,
    get_account,
    get_client,
    get_appid,
    decodeState
)

def callChange(
    client: AlgodClient,
    appID: int,
    sender: Account,
    new_name: string,
) -> None:
    """Finish setting up an auction.

    The escrow account requires a total of 0.203 Algos for funding. See the code
    below for a breakdown of this amount.

    Args:
        client: An algod client.
        appID: The app ID of the auction.
        funder: The account providing the funding for the escrow account.
        nftHolder: The account holding the NFT.
        nftID: The NFT ID.
        nftAmount: The NFT amount being auctioned. Some NFTs has a total supply
            of 1, while others are fractional NFTs with a greater total supply,
            so use a value that makes sense for the NFT being auctioned.
    """

    suggestedParams = client.suggested_params()

    changeNameTxn = transaction.ApplicationCallTxn(
        sender=sender.getAddress(),
        index=appID,
        on_complete=transaction.OnComplete.NoOpOC,
        app_args=[b"change", str.encode(new_name)],
        sp=suggestedParams,
    )

    signedSetupTxn = changeNameTxn.sign(sender.getPrivateKey())
    client.send_transaction(signedSetupTxn)

    response = waitForTransaction(client, signedSetupTxn.get_txid())
    return response



print(getAppGlobalState(get_client(), get_appid()))
response = callChange(get_client(), get_appid(), get_account(), "Sasha")
print(getAppGlobalState(get_client(), get_appid()))


# def setupAuctionApp(
#     client: AlgodClient,
#     appID: int,
#     funder: Account,
#     nftHolder: Account,
#     nftID: int,
#     nftAmount: int,
# ) -> None:
#     """Finish setting up an auction.

#     This operation funds the app auction escrow account, opts that account into
#     the NFT, and sends the NFT to the escrow account, all in one atomic
#     transaction group. The auction must not have started yet.

#     The escrow account requires a total of 0.203 Algos for funding. See the code
#     below for a breakdown of this amount.

#     Args:
#         client: An algod client.
#         appID: The app ID of the auction.
#         funder: The account providing the funding for the escrow account.
#         nftHolder: The account holding the NFT.
#         nftID: The NFT ID.
#         nftAmount: The NFT amount being auctioned. Some NFTs has a total supply
#             of 1, while others are fractional NFTs with a greater total supply,
#             so use a value that makes sense for the NFT being auctioned.
#     """
#     appAddr = getAppAddress(appID)

#     suggestedParams = client.suggested_params()

#     fundingAmount = (
#         # min account balance
#         100_000
#         # additional min balance to opt into NFT
#         + 100_000
#         # 3 * min txn fee
#         + 3 * 1_000
#     )

#     fundAppTxn = transaction.PaymentTxn(
#         sender=funder.getAddress(),
#         receiver=appAddr,
#         amt=fundingAmount,
#         sp=suggestedParams,
#     )

#     setupTxn = transaction.ApplicationCallTxn(
#         sender=funder.getAddress(),
#         index=appID,
#         on_complete=transaction.OnComplete.NoOpOC,
#         app_args=[b"setup"],
#         foreign_assets=[nftID],
#         sp=suggestedParams,
#     )

#     fundNftTxn = transaction.AssetTransferTxn(
#         sender=nftHolder.getAddress(),
#         receiver=appAddr,
#         index=nftID,
#         amt=nftAmount,
#         sp=suggestedParams,
#     )

#     transaction.assign_group_id([fundAppTxn, setupTxn, fundNftTxn])

#     signedFundAppTxn = fundAppTxn.sign(funder.getPrivateKey())
#     signedSetupTxn = setupTxn.sign(funder.getPrivateKey())
#     signedFundNftTxn = fundNftTxn.sign(nftHolder.getPrivateKey())

#     client.send_transactions([signedFundAppTxn, signedSetupTxn, signedFundNftTxn])

#     waitForTransaction(client, signedFundAppTxn.get_txid())