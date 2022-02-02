# Internal Blockchain Winter School 2022 - IT University of Copenhagen
## Team [ZTLment](https://www.ztlment.com/), Use Case Provided: [here](https://user.fm/files/v2-c91175da817492374ccacb5e001b997b/ZTLment%20Use%20Case.pdf)

Here you will find the code for an escrow smart contract on the Algorand blockchain. It's purpose is to tokenise carbon credits as NFTs, allow sellers of carbon credits to deposit their NFT carbon credits within the non-custodial escrow contract, and finally allow buyers to pay the contract in exchange for the NFT carbon credit.

Two people coded up this implementation in the space of two working days ready for a presentation at the Internal Blockchain Winter School 2022 in Copenhagen. The coders are [Liv Hartoft Borre](https://www.linkedin.com/in/liv-hartoft-borre-70666b11b/) and [Sasha Aldrick](https://www.linkedin.com/in/sashaaldrick/).

# Example workflow

## For Linux/Mac/WSL:

* If you don't have Docker Desktop, install it from [here](https://www.docker.com/get-started).

* Setup the sandbox (this starts an Algorand node to communicate with a local network, the testnet or the mainnet):
```bash
git clone https://github.com/algorand/sandbox
cd sandbox
./sandbox up testnet
```
&ensp;&ensp;&ensp;&ensp;_(This sandbox initial startup takes a while. You can proceed while you wait.)_

* In another terminal, clone this repository and move into the project:
```bash
cd <where-you-want-to-locate-the-project>
git clone https://github.com/livborre/escrow
cd escrow
```

* Activate a new Python environment and install the project requirements:
```bash
python3 -m venv escrow_venv
source escrow_venv/bin/activate
pip3 install -r requirements.txt
```

* Generate _Algorand accounts_ (creator, seller and buyer), and store the details in a local `.env` file:
```bash
python generateAccounts.py
```

* Remember to _fund_ the testnet accounts, which can be done [here](https://bank.testnet.algorand.network/)!!!

* Run the `example.py` file for a full example of _deploying_ the contract, _creating_ an NFT and _trading_ it between the buyer and seller:
```bash
python example.py
```

## Extras
* We recommend using the 'Algosigner' Wallet Extension for Chrome/Brave: [here](https://chrome.google.com/webstore/detail/algosigner/kmmolakhbgdlpkjkcjkebenjheonagdm/related)
* You can also use [Algodesk](https://www.algodesk.io/#/) to 'visually' see the NFTs in the seller account. Note that it will not appear in the buyer account using Algodesk, as it deals with created assets.

Have fun! :)
