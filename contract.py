from pyteal import *

def approval_program():
    current_name = Bytes("current_name")

    on_create = Seq(
        App.globalPut(current_name, Txn.application_args[0]),
        Approve(),
    )

    on_change = Seq(
       App.globalPut(current_name, Txn.application_args[1]),
       Approve(),
    )


    on_call_method = Txn.application_args[0]
    on_call = Cond(
        [on_call_method == Bytes("change"), on_change],
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

if __name__ == "__main__":
    with open("auction_approval.teal", "w") as f:
        compiled = compileTeal(approval_program(), mode=Mode.Application, version=5)
        f.write(compiled)

    with open("auction_clear_state.teal", "w") as f:
        compiled = compileTeal(clear_state_program(), mode=Mode.Application, version=5)
        f.write(compiled)
