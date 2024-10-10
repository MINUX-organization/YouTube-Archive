import requests

MAX_TARGET = 0x00000000FFFF0000000000000000000000000000000000000000000000000000

def target_to_bits(target):
    """
    converts from bitcoin target representation to compact bits representation
    :param target: int:  ex. 0x00000000000000000011d4f20000000000000000000000000000000000000000
    :return  int:
    """
    if target == 0:
        return 0
    target = min(target, MAX_TARGET)
    size = (target.bit_length() + 7) / 8
    mask64 = 0xffffffffffffffff
    if size <= 3:
        compact = (target & mask64) << (8 * (3 - size))
    else:
        compact = (target >> (8 * (size - 3))) & mask64

    if compact & 0x00800000:
        compact >>= 8
        size += 1
    assert compact == (compact & 0x007fffff)
    assert size < 256
    return compact | size << 24

def bits_to_target(bits):
    """
    converts from  bitcoin compact bits representation to target
    :param bits: int
    :return: int
    """
    if not bits:
        return 0

    bits_bytes = bits.to_bytes(4, 'big')
    exponent = bits_bytes[0]
    coefficient = int.from_bytes(b'\x00' + bits_bytes[1:], 'big')
    return coefficient * 256 ** (exponent - 3)


def target_to_hex(target):
    """
    Block target in hexadecimal string of 64 characters.
    :return str:
    """
    return hex(int(target))[2:].zfill(64)


def target_to_difficulty(target):
    """
    Block difficulty calculated from bits / target. Human readable representation of block's target.
    Genesis block has difficulty of 1.0
    :return float:
    """
    return MAX_TARGET / target


def difficulty_to_target(difficulty):
    """
    Genesis block has difficulty of 1.0
    :param difficulty:float
    :return:
    """
    return MAX_TARGET / difficulty


def check_proof_of_work(block_hash, bits):
    """
    Check proof of work for this block. Block hash must be below target.
    This function is not optimised for mining, but you can use this for testing or learning purposes.
    >>> check_proof_of_work('0000000000000000000154ba9d02ddd6cee0d71d1ea232753e02c9ac6affd709',387044594)
    True
    :return bool:
    """
    if not block_hash or not bits:
        return False
    block_hash_bytes = to_bytes(block_hash)
    if int.from_bytes(block_hash_bytes, 'big') < bits_to_target(bits):
        return True
    return False


def to_bytes(string, unhexlify=True):
    """
    Convert string, hexadecimal string  to bytes
    :param string: String to convert
    :type string: str, bytes
    :param unhexlify: Try to unhexlify hexstring
    :type unhexlify: bool
    :return: Bytes var
    """
    if not string:
        return b''
    if unhexlify:
        try:
            if isinstance(string, bytes):
                string = string.decode()
            s = bytes.fromhex(string)
            return s
        except (TypeError, ValueError):
            pass
    if isinstance(string, bytes):
        return string
    else:
        return bytes(string, 'utf8')

# - https://www.blockchain.com/explorer/api/blockchain_api
block_hash = "0000000000000bae09a7a393a8acded75aa67e46cb81f7acaa5ad94f9eacd103"
r = requests.get(f'https://blockchain.info/rawblock/{block_hash}?format=json')
data = r.json()

print(data["hash"])
print(data["prev_block"])
print(data["time"])
print(data["nonce"])
print(data["block_index"])
print(data["bits"])
print(data["height"])

print("Проверить PoW: ", check_proof_of_work(data["hash"], data["bits"]))
print("Target блока: ", bits_to_target(data["bits"]))
