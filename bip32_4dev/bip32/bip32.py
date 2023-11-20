# -*- coding: utf-8 -*-
"""
BIP32:
    Implementation
Ref.
https://github.com/bitcoin/bips/blob/master/bip-0032.mediawiki
"""
import hashlib
from typing import Optional, Tuple
import hmac
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.backends import default_backend

# CONSTANTS
# Elliptic curve parameters
P = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEFFFFFC2F
N = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEBAAEDCE6AF48A03BBFD25E8CD0364141
G = (0x79BE667EF9DCBBAC55A06295CE870B07029BFCDB2DCE28D959F2815B16F81798,
     0x483ADA7726A3C4655DA4FBFC0E1108A8FD17B448A68554199C47D08FFB10D4B8)
HARDENED = 1 << 31
UINT32_MAX = (1 << 32) - 1

Point = Tuple[int, int]

def b58decode(base58_string):
    alphabet = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"
    num = 0
    for char in base58_string:
        num *= 58
        num += alphabet.index(char)
    return num.to_bytes(82, byteorder='big')


def b58encode(v: bytes) -> str:
    alphabet = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"

    pp, acc = 1, 0
    for c in reversed(v):
        acc += pp * c
        pp = pp << 8

    string = ""
    while acc:
        acc, idx = divmod(acc, 58)
        string = alphabet[idx : idx + 1] + string
    return string

class BIP32Node():
    ser_const = {'mainnet': {'public': 0x0488B21E, 
                            'private': 0x0488ADE4},
                'testnet': {'public': 0x043587CF, 
                            'private': 0x04358394}
                }
    def __init__(self, m: bytes, tree: str, net: str="mainnet"):
        if net not in ['mainnet', 'testnet']:
            raise Exception("Select one from ['mainnet', 'testnet']")
        
        self.path = self.path_derivation(tree)
        self._net = net
        self.ser_priv = self.ser_const[net]['private']
        self.ser_pub = self.ser_const[net]['public']
        self.master_priv_key, self.master_chain_code = self.master_gen(m)
        self.xprv, self.xpub = self.key_derivation(m, tree)
        
    @classmethod
    def path_derivation(cls, tree: str):
        tree_list = tree.split("/")
        if tree_list[0] != "m":
            raise Exception("Node derivation must start with 'm'")
        path = ["m"]
        sep_list = ["H", "'", "h"]
        hard_sep = "Z"
        for node in tree_list[1:]:
            for sep in sep_list:
                if node.find(sep) != -1 and hard_sep == "Z":
                    hard_sep = sep
            
            if node.find(hard_sep) != -1:
                path.append(int(node.split(hard_sep)[0]) + HARDENED)
            else:
                path.append(int(node.split(hard_sep)[0]))
        return path
    
    @classmethod
    def key_derivation(cls, m: bytes, tree: str, net: str="mainnet"):
        path = cls.path_derivation(tree)
        k_i, c_i = cls.master_gen(m)
        parent_k_i = k_i
        depth = 0
        fingerprint = int(0x00000000).to_bytes(4, 'big')
        node = int(0x00000000)
        for node in path[1:]:
            parent_k_i = k_i
            k_i, c_i = cls.ckd_priv(k_i, c_i, node)
            depth += 1
        K_i = cls.point(parent_k_i)
        if depth > 0:
            fingerprint = cls.hash160(cls.ser_p(K_i))[:4]
        return cls.serialization(key=k_i,
                                 chain_code=c_i,
                                 fingerprint=fingerprint, 
                                 depth=depth, 
                                 child_number=node,
                                 net=net)

    @classmethod
    def point(cls, p_int: int):
        private_key = ec.derive_private_key(p_int,
                                            ec.SECP256K1(),
                                            default_backend())
        public_key = private_key.public_key().public_numbers()
        return (public_key.x, public_key.y)
    
    # Get y-coordinate from x
    def y_elliptic(b: bytes) -> Optional[Point]:
        """Get y of elliptic curve from x."""
        x = int.from_bytes(b, 'big')
        # 0 < x < p
        if x >= P:
            return None
        y_sq = (pow(x, 3, P) + 7) % P
        # https://en.wikipedia.org/wiki/Modular_arithmetic
        # Quadratic residual
        y = pow(y_sq, (P + 1) // 4, P)
        if pow(y, 2, P) != y_sq:
            return None
        return x, y

    # Point addition
    @classmethod
    def point_add(cls, P1: Optional[Point], P2: Optional[Point], cost_p: int=P) -> Optional[Point]:
        if P1 is None:
            return P2
        if P2 is None:
            return P1
        if (P1[0] == P2[0]) and (P1[1] != P2[1]):
            return None
        if P1 == P2:
            lam = (3 * P1[0] * P1[0] * pow(2 * P1[1], cost_p - 2, cost_p)) % cost_p
        else:
            lam = ((P2[1] - P1[1]) * pow(P2[0] - P1[0], cost_p - 2, cost_p)) % cost_p
        x3 = (lam * lam - P1[0] - P2[0]) % cost_p
        return x3, (lam * (P1[0] - x3) - P1[1]) % cost_p
    
    @classmethod
    def ser32(cls, i) -> bytes:
        if i > 1<<32:
            raise Exception("Integer excedes 32 bit")
        if i < 0:
            raise Exception("Integer is negative")
        return i.to_bytes(4, 'big')

    @classmethod
    def ser256(cls, num:int) -> bytes:
        if num > 1<<256:
            raise Exception("Integer excedes 32 bytes")
        if num < 0:
            raise Exception("Integer is negative")
        return num.to_bytes(32, 'big')
    
    @classmethod
    def ser_p(cls, P: tuple) -> bytes:
        x = P[0]
        y = P[1]
        header = int(0x03).to_bytes(1, 'big') if y % 2 != 0 else int(0x02).to_bytes(1,'big')
        return header + cls.ser256(x)
    
    @classmethod
    def parse256(cls, p: bytes) -> int:
        return int.from_bytes(p[:32], 'big')
    
    @classmethod
    def hash160(cls, data):
        return hashlib.new("ripemd160", hashlib.new("sha256", data).digest()).digest()
    
    @classmethod
    def master_gen(cls, seed: bytes):
        i = hmac.new(b'Bitcoin seed', seed , hashlib.sha512).digest()
        i_l = i[:32]
        i_r = i[32:]
        
        if cls.parse256(i_l) >= N:
            raise Exception("I_L greated than N")
        elif cls.parse256(i_r) >= N:
            raise Exception("I_R greated than N")
        elif cls.parse256(i_l) == 0:
            raise Exception("I_L is null")
        elif cls.parse256(i_r) == N:
            raise Exception("I_R is null")
        
        return (cls.parse256(i_l), cls.parse256(i_r))
    
    @classmethod
    def ckd_priv(cls, parent_priv_key: int, parent_chain_code: int, index: int):        
        k, c = parent_priv_key, parent_chain_code
        K = cls.point(k)
        key = cls.ser256(c)
        if index >= HARDENED:
            msg = int(0x00).to_bytes(1, 'big') + cls.ser256(k)
        else:
            msg = cls.ser_p(K)
        I = hmac.new(key, msg + cls.ser32(index), hashlib.sha512).digest()
        i_l = I[:32]
        i_r = I[32:]
        k_i = (cls.parse256(i_l) + k) % N
        if cls.parse256(i_l) >= N or k_i == 0:
            print(f"i_l is not valid. Child key calculated wit i+1 = {index+1}")
            return cls.ckd_priv(k, c, index+1)
        return k_i, cls.parse256(i_r)
    
    @classmethod
    def ckd_pub(cls, parent_pub_key: bytes, parent_chain_code: bytes, index: int):
        if index >= HARDENED:
            raise Exception("Hardened child: failure.")
        K, c = parent_pub_key, parent_chain_code
        key = cls.ser256(c)
        msg = cls.ser_p(K) + cls.ser32(index)
        I = hmac.new(key, msg, hashlib.sha512).digest()
        i_l = I[:32]
        i_r = I[32:]
        K_i = cls.point_add(cls.point(cls.parse256(i_l)), K)
        if cls.parse256(i_l) >= N or K == G:
            print(f"i_l is not valid. Child key calculated wit i+1 = {index+1}")
            return cls.ckd_pub(K, c, index+1)
        return K_i, cls.parse256(i_r)
    
    @classmethod
    def priv2pub(cls, parent_priv_key: bytes, parent_chain_code: bytes):
        k, c = parent_priv_key, parent_chain_code
        return cls.point(k), c
    
    @classmethod
    def checksum_calc(cls, data: bytes) -> bytes:
        sha256_1 = hashlib.new('sha256', data).digest()
        return hashlib.new('sha256', sha256_1).digest()[:4]

    @classmethod
    def serialization(cls,
                      key:int, 
                      chain_code: int, 
                      fingerprint: bytes,
                      depth:int, 
                      child_number: int=0,
                      net: str="mainnet"):
        
        if depth < 0:
            raise TypeError("Depth could not be negative.")
            
        # SERIALIZATION
        K_pub = cls.point(key)
        
        ser_xprv = (cls.ser_const[net]['private'].to_bytes(4, 'big') + 
                    depth.to_bytes(1, 'big') + 
                    fingerprint + 
                    child_number.to_bytes(4, 'big') + 
                    cls.ser256(chain_code) +
                    int(0x00).to_bytes(1, 'big') +
                    cls.ser256(key))
        checksum_xprv = cls.checksum_calc(ser_xprv)
        
        ser_xpub = (cls.ser_const[net]['public'].to_bytes(4, 'big') + 
                    depth.to_bytes(1, 'big') + 
                    fingerprint + 
                    child_number.to_bytes(4, 'big') + 
                    cls.ser256(chain_code) +
                    cls.ser_p(K_pub))
        checksum_xpub = cls.checksum_calc(ser_xpub)
        return b58encode(ser_xprv+checksum_xprv), b58encode(ser_xpub+checksum_xpub)
