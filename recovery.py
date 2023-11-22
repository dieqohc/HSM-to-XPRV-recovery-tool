# This is small tool with the aim to derive the private key to move any funds on-chain parting from an hsm_secret file.

# Thanks to Baam Twentyfifth -> https://community.corelightning.org/u/64d0a6f3


from bip32_4dev.bip32.bip32 import b58encode, b58decode, BIP32Node
from hkdf.hkdf import hkdf

try:
    with open("./hsm_secret", "rb") as ff: #modify the route as you please to where your hsm_secret is located.
        code = ff.read()
except (FileNotFoundError, NameError):
    print('hsm_secret file not found, please move the file to this directory\nor edit the recovery.py to the directory where the file is located.\n')
    exit()

seed=hkdf(bytes(0), code, b"bip32 seed", len(code))
bip32seed = BIP32Node(m=seed, tree="m", net="mainnet")

xprv = bip32seed.xprv # Generation of xprv in order to print it or generate a mnemonic.

print(f'XPRV: {xprv}')
print(f'XPUB: {bip32seed.xpub}')

print('\nWhen importing the XPRV the derivation path for the funds is "m/*" which can be represented as "m/0".')