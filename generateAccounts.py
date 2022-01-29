from utils import generate_algorand_keypair

# this file creates accounts, prints out the required information for importing them into an Algorand wallet, and also to fund them using the testnet dispenser, and writes private keys to the .env file locally (this is not pushed as it is present in .gitignore, so you can push safely to your own repo if you would like). These private keys are then pulled into the example.py from .env to be used in the example workflow.

creator_private_key, creator_address, creator_seed_phrase = generate_algorand_keypair()
seller_private_key, seller_address, seller_seed_phrase = generate_algorand_keypair()
buyer_private_key, buyer_address, buyer_seed_phrase = generate_algorand_keypair()

creator_pk = f"CREATOR_PK={creator_private_key}"
creator_addrs = f"CREATOR_ADDRESS={creator_address}"

seller_pk = f"SELLER_PK={seller_private_key}"
seller_addrs = f"SELLER_ADDRESS={seller_address}"

buyer_pk = f"BUYER_PK={buyer_private_key}"
buyer_addrs = f"BUYER_ADDRESS={buyer_address}"

information_list = [creator_pk, creator_addrs, seller_pk, seller_addrs, buyer_pk, buyer_addrs]

# open, overwrite and close the file.
file = open(".env", "w")
for information in information_list:
    file.write(information)
    file.write("\n")
file.close()

print("Creator Seed Phrase for Importing into your Algorand Wallet of Choice: ")
print(creator_seed_phrase)
print("\n")

print("Seller Seed Phrase for Importing into your Algorand Wallet of Choice: ")
print(seller_seed_phrase)
print("\n")

print("Buyer Seed Phrase for Importing into your Algorand Wallet of Choice: ")
print(buyer_seed_phrase)
print("\n")

print("Remember to fund the testnet accounts generator for creator, seller and buyer using the URL below otherwise nothing will work.")
print("1 dispensation per account is plenty!")
print("https://bank.testnet.algorand.network" )
print("\n")
print(creator_addrs)
print("\n")
print(seller_addrs)
print("\n")
print(buyer_addrs)
print("\n")
