# -*- coding: utf-8 -*-

from bip32 import BIP32Node
import json
import unittest

class BIP32Test(unittest.TestCase):
    def test_vectors(self) -> None:
        with open("test_vectors.json", "r") as f:
            vectors = json.load(f)
        count = 1
        for seed_hex, vecs in vectors.items():
            seed = bytes.fromhex(seed_hex)
            count += 1
            for i, vec in enumerate(vecs):
                tree = vec["chain"]
                xprv, xpub = BIP32Node.key_derivation(seed, tree)
                self.assertEqual(xpub, vec["ext_pub"])
                self.assertEqual(xprv, vec["ext_prv"])


# TODO 
# invalid extended key test
def __main__() -> None:
    unittest.main()


if __name__ == "__main__":
    __main__()