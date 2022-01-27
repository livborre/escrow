from algosdk import account, mnemonic

def generate_algorand_keypair():
    private_key, address = account.generate_account()
    print(f"My address: {address}")
    print(f"My private_key: {private_key}")
    print(f"My seed phrase: {mnemonic.from_private_key(private_key)}")

generate_algorand_keypair()

# My address: JCTFTC6QWIY4CRIMULFDYJF6K26W6DAUJ3REXKEYU4P5PK24GVETZC676E
# My private_key: pESL6ROf12JNlue4i6YEUCMhQRTkEvkDJVY5Emgb9TFIplmL0LIxwUUMoso8JL5WvW8MFE7iS6iYpx/Xq1w1SQ==
# My seed phrase: nest code visit van quality flavor raven travel jacket olive across crush drastic aware camera base left neglect prison castle south egg moral ability crop



