# Internal Blockchain Winter School 2022 - IT University of Copenhagen
## Team [ZTLment](https://www.ztlment.com/), Use Case Provided: [here](https://user.fm/files/v2-c91175da817492374ccacb5e001b997b/ZTLment%20Use%20Case.pdf)

Here you will find the code for an escrow smart contract on the Algorand blockchain. It's purpose is to tokenise carbon credits as NFTs, allow sellers of carbon credits to deposit their NFT carbon credits within the non-custodial escrow contract, and finally allow buyers to pay the contract in exchange for the NFT carbon credit.

Two people coded up this implementation in the space of two working days ready for a presentation at the Internal Blockchain Winter School 2022 in Copenhagen. The coders are [Liv Hartoft Borre](https://www.linkedin.com/in/liv-hartoft-borre-70666b11b/) and [Sasha Aldrick](https://www.linkedin.com/in/sashaaldrick/).

# Example workflow

## For Linux/Mac/WSL:

* Install Docker Desktop from [here](https://www.docker.com/get-started).

* Setup the sandbox (an Algorand node to communicate with a local network, the testnet or the mainnet):
``` git clone https://github.com/algorand/sandbox ```
``` cd sandbox ```
``` ./sandbox up tesnet ```

* This sandbox initial startup takes a while so wait until it's done and you have access to your terminal prompt again.

* Clone the code and move into the folder.
``` git clone https://github.com/livborre/escrow ```
``` cd escrow ```

* Create a python environment and install the python requirements.
```python3 -m venv escrow_venv```
``` pip3 install -r requirements.txt ```

* Activate the Python environment.
``` source escrow_venv/bin/activate ```

* Generate the account details to be stored in a local .env file.
``` python generateAccounts.py ```

(Remember to fund the testnet accounts generator for creator, seller and buyer [here](https://bank.testnet.algorand.network/)!!!)

* Run the example.py file.
``` python example.py ```

## Extras
* We recommend using the 'Algosigner' Wallet Extension for Chrome/Brave: [here](https://chrome.google.com/webstore/detail/algosigner/kmmolakhbgdlpkjkcjkebenjheonagdm/related)
* You can also use [Algodesk](https://www.algodesk.io/#/) to 'visually' see the NFTs in the seller account. Note that it will not appear in the buyer account using Algodesk, as it deals with created assets.

Have fun! :)
