from typing import List
from pyteal import *

def approval_program():
    seller_address_key = Bytes("seller")
    buyer_address_key = Bytes("buyer")
    nft_id_key = Bytes("nft_id")
    price_key = Bytes("price")

    @Subroutine(TealType.none)
    def close_nft_to(assetID: Expr, account: Expr) -> Expr:
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

    on_create = Seq(
        Approve(),
    )

    on_setup = Seq(
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

    on_buy = Seq(
        App.globalPut(buyer_address_key, Txn.application_args[1]),
        close_nft_to(
            App.globalGet(nft_id_key),
            App.globalGet(buyer_address_key)
        ),
        InnerTxnBuilder.Begin(),
        InnerTxnBuilder.SetFields(
            {
                TxnField.type_enum: TxnType.Payment,
                TxnField.amount: App.globalGet(price_key),
                TxnField.receiver: App.globalGet(seller_address_key),
            }
        ),
        InnerTxnBuilder.Submit(),
        Approve(),
    )

    on_call = Cond(
        [Txn.application_args[0] == Bytes("setup"), on_setup],
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
    return Approve()
