from pyteal import *

# PyTeal deals with writing a smart contract on Algorand and compiling it down to TEAL which will be pushed to the chain.
# Each smart contract requires an approval

def approval_program():
    # some global state variables.
    seller_address_key = Bytes("seller")
    buyer_address_key = Bytes("buyer")
    nft_id_key = Bytes("nft_id")
    price_key = Bytes("price")

    # a "constructor" method for contracts to allow for some logic to be executed upon deployment.
    on_create = Seq(
        Approve(),
    )

    # A method called by the seller to deposit the NFT in the contract.
    on_deposit = Seq(
        App.globalPut(seller_address_key, Txn.application_args[1]),
        App.globalPut(nft_id_key, Btoi(Txn.application_args[2])),
        App.globalPut(price_key, Btoi(Txn.application_args[3])),
        InnerTxnBuilder.Begin(),
        InnerTxnBuilder.SetFields(
            {
                TxnField.type_enum: TxnType.AssetTransfer,
                TxnField.xfer_asset: App.globalGet(nft_id_key),
                TxnField.asset_receiver: Global.current_application_address(),
            }
        ),
        InnerTxnBuilder.Submit(),
        Approve(),
    )

    @Subroutine(TealType.none)
    def close_nft_to(assetID: Expr, account: Expr) -> Expr:
        """ Helper function to check asset (NFT) exists and then transfer to required account."""
        asset_holding = AssetHolding.balance(
            Global.current_application_address(), assetID
        )
        return Seq(
            asset_holding,
            If(asset_holding.hasValue()).Then(
                Seq(
                    InnerTxnBuilder.Begin(),
                    InnerTxnBuilder.SetFields(
                        {
                            TxnField.type_enum: TxnType.AssetTransfer,
                            TxnField.xfer_asset: assetID,
                            TxnField.asset_close_to: account,
                        }
                    ),
                    InnerTxnBuilder.Submit(),
                )
            ),
        )

    # A method called by the buyer to deposit the required NFT price in Algos in the smart contract.
    # It also handles the transfer of the NFT from the smart contract to the buyer.
    on_buy = Seq(
        App.globalPut(buyer_address_key, Txn.application_args[1]),

        # start inner transaction payment of money from contract to seller
        InnerTxnBuilder.Begin(),
        InnerTxnBuilder.SetFields(
            {
                TxnField.type_enum: TxnType.Payment,
                TxnField.amount: App.globalGet(price_key),
                TxnField.receiver: App.globalGet(seller_address_key),
            }
        ),
        InnerTxnBuilder.Submit(),

        # send NFT to buyer.
        close_nft_to(
            App.globalGet(nft_id_key),
            App.globalGet(buyer_address_key)
        ),
        Approve(),
    )

    # handling the calling of methods.
    on_call = Cond(
        [Txn.application_args[0] == Bytes("deposit"), on_deposit],
        [Txn.application_args[0] == Bytes("buy"), on_buy]
    )

    program = Cond(
        [Txn.application_id() == Int(0), on_create],
        [Txn.on_completion() == OnComplete.NoOp, on_call],
        [
            Or(
                Txn.on_completion() == OnComplete.OptIn,
                Txn.on_completion() == OnComplete.CloseOut,
                Txn.on_completion() == OnComplete.UpdateApplication,
            ),
            Reject(),
        ],
    )

    return program

def clear_state_program():
    # no logic here, as not necessary 
    return Approve()
