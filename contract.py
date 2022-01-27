from typing import List
from pyteal import *

def approval_program():
    seller_address_key = Bytes("seller")
    nft_id_key = Bytes("nft_id")
    # end_time_key = Bytes("end")
    min_price_key = Bytes("min_price")

    # @Subroutine(TealType.none)
    # def reset() -> Expr:
    #     return Seq(
    #         App.globalPut(seller_address_key, Global.zero_address),
    #         App.globalPut(nft_id_key, Int(0)),
    #         App.globalPut(end_time_key, Global.latest_timestamp()),
    #         App.globalPut(min_price_key, 0),
    #     )

    @Subroutine(TealType.none)
    def send_payment(receiver: Expr, amount: Expr) -> Expr:
        return Seq(
            InnerTxnBuilder.Begin(),
            InnerTxnBuilder.SetFields(
                {
                    TxnField.type_enum: TxnType.Payment,
                    TxnField.amount: amount - Global.min_txn_fee(),
                    TxnField.receiver: receiver,
                }
            ),
            InnerTxnBuilder.Submit(),
        )

    @Subroutine(TealType.none)
    def send_asset(receiver: Expr, assetID: Expr) -> Expr:
        # Create an Asset Transfer Transaction
        return Seq(
            InnerTxnBuilder.Begin(),
            InnerTxnBuilder.SetFields(
                {
                    TxnField.type_enum: TxnType.AssetTransfer,
                    TxnField.xfer_asset: assetID,
                    TxnField.asset_close_to: receiver,
                    # Specify this field to remove the asset holding from the sender account and reduce the account's minimum balance (i.e. opt-out of the asset).
                }
            ),
            InnerTxnBuilder.Submit(),
        )

    # @Subroutine(TealType.none)
    # def opt_in(assetID: Expr, account) -> Expr:
    #     # Create an Asset Accept Transaction. This is a special form of an Asset Transfer Transaction.
    #     return Seq(
    #         InnerTxnBuilder.Begin(),
    #         InnerTxnBuilder.SetFields(
    #             {
    #                 TxnField.type_enum: TxnType.AssetTransfer,
    #                 TxnField.xfer_asset: assetID, # The unique ID of the asset to opt-in to.
    #                 TxnField.asset_receiver: account, # The account which is allocating the asset to their account's Asset map.
    #             }
    #         ),
    #         InnerTxnBuilder.Submit(),
    #     )

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

    @Subroutine(TealType.none)
    def close_account_to_creator() -> Expr:
        return If(Balance(Global.current_application_address()) != Int(0)).Then(
            Seq(
                InnerTxnBuilder.Begin(),
                InnerTxnBuilder.SetFields(
                    {
                        TxnField.type_enum: TxnType.Payment,
                        TxnField.close_remainder_to: Global.creator_address(),
                    }
                ),
                InnerTxnBuilder.Submit(),
            )
        )

    @Subroutine(TealType.none)
    def assert_asset_balance(nft_id: Expr) -> Expr:
        asset_holding = AssetHolding.balance(Global.current_application_address(), nft_id)
        return Seq( 
            asset_holding,
            Assert(
                And(
                    # the auction has been set up
                    asset_holding.hasValue(),
                    asset_holding.value() > Int(0),
                )
            )
        )
    # end_time = Btoi(Txn.application_args[3])
    on_create = Seq(
        # App.globalPut(seller_address_key, Txn.application_args[0]),
        # App.globalPut(nft_id_key, Btoi(Txn.application_args[1])),
        # App.globalPut(min_price_key, Btoi(Txn.application_args[2])),
        # App.globalPut(end_time_key, end_time),
        # Assert(Global.latest_timestamp() < end_time),
        Approve(),
    )

    on_setup = Seq(
        App.globalPut(seller_address_key, Txn.application_args[1]),
        App.globalPut(nft_id_key, Btoi(Txn.application_args[2])),
        App.globalPut(min_price_key, Btoi(Txn.application_args[3])),
        # Assert(Global.creator_address() == Txn.sender),
        # Assert(Global.latest_timestamp() < App.globalGet(start_time_key)),
        # opt into NFT asset -- because you can't opt in if you're already opted in, this is what
        # we'll use to make sure the contract has been set up
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

    # on_buy_txn_index = Txn.group_index() - Int(1)
    on_buy = Seq(
        InnerTxnBuilder.Begin(),
        InnerTxnBuilder.SetFields(
            {
                TxnField.type_enum: TxnType.AssetTransfer,
                TxnField.xfer_asset: App.globalGet(nft_id_key),
                TxnField.asset_close_to: Txn.sender(),
                # TxnField.amount: Int(1),
            }
        ),
        InnerTxnBuilder.Submit(),
        Approve(),
    )

    # on_buy_complex = Seq(
    #     # assert the asset has been set up
    #     # assert_asset_balance(App.globalGet(nft_id_key)),
    #     Assert(
    #         And(
    #             # the auction has not ended
    #             # Global.latest_timestamp() < App.globalGet(end_time_key),
    #             # the actual bid payment is before the app call
    #             Gtxn[on_buy_txn_index].type_enum() == TxnType.Payment,
    #             Gtxn[on_buy_txn_index].sender() == Txn.sender(),
    #             Gtxn[on_buy_txn_index].receiver() == Global.current_application_address(),
    #             Gtxn[on_buy_txn_index].amount() >= Global.min_txn_fee(),
    #         )
    #     ),
    #     If(
    #         Gtxn[on_buy_txn_index].amount() >= App.globalGet(min_price_key)
    #     ).Then(
    #         Seq(
    #             close_nft_to(App.globalGet(nft_id_key), Gtxn[on_buy_txn_index].sender()),

    #             # Send money to seller
    #             # InnerTxnBuilder.Begin(),
    #             # InnerTxnBuilder.SetFields(
    #             #     {
    #             #         TxnField.type_enum: TxnType.Payment,
    #             #         TxnField.amount: Gtxn[on_buy_txn_index].amount() - Global.min_txn_fee(),
    #             #         TxnField.receiver: App.globalGet(seller_address_key),
    #             #     }
    #             # ),
    #             # InnerTxnBuilder.Submit(),
    #             Approve(),
    #         )
    #     ),
    #     Reject(),
    # )

    on_delete = Seq(
        # the auction has not yet started, it's ok to delete
        Assert(Txn.sender() == Global.creator_address()),
        # if the ascrow contract account has opted into the nft, close it out
        close_nft_to(App.globalGet(seller_address_key), App.globalGet(nft_id_key)),
        # if the auction contract still has funds, send them all to the creator
        close_account_to_creator(),
        Approve(),
    )


    on_call = Cond(
        [Txn.application_args[0] == Bytes("setup"), on_setup],
        [Txn.application_args[0] == Bytes("buy"), on_buy]
    )

    program = Cond(
        [Txn.application_id() == Int(0), on_create],
        [Txn.on_completion() == OnComplete.NoOp, on_call],
        [Txn.on_completion() == OnComplete.DeleteApplication, on_delete],
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

if __name__ == "__main__":
    with open("auction_approval.teal", "w") as f:
        compiled = compileTeal(approval_program(), mode=Mode.Application, version=5)
        f.write(compiled)

    with open("auction_clear_state.teal", "w") as f:
        compiled = compileTeal(clear_state_program(), mode=Mode.Application, version=5)
        f.write(compiled)
