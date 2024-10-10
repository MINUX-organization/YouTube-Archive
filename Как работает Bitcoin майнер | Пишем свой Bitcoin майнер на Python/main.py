import binascii
import hashlib
import json
import random
import socket
import time
import requests
import signal

def get_current_block_height() :
    # returns the current network height
    r = requests.get('https://blockchain.info/latestblock')
    return int(r.json()['height'])

def signal_handler(sig, frame):
    elapsed_time = time.time() - start_time
    hashrate = float(hashes_count / elapsed_time)
    print(f"hashrate : {hashrate} H/s")
    exit(0)

class PoolJob():
    def __init__(self, job_id, prevhash, coinb1, coinb2, merkle_branch, version, nbits, ntime, clean_jobs):
        self.job_id = job_id
        self.prevhash = prevhash
        self.updatedPrevHash = prevhash
        self.coinb1 = coinb1
        self.coinb2 = coinb2
        self.merkle_branch = merkle_branch
        self.version = version
        self.nbits = nbits
        self.ntime = ntime
        self.clean_jobs = clean_jobs

class MiningParams():
    def __init__(self, sub_details, extranonce1, extranonce2_size):
        self.sub_details = sub_details
        self.extranonce1 = extranonce1
        self.extranonce2_size = extranonce2_size

signal.signal(signal.SIGINT, signal_handler)
start_time = time.time()

# - Кошелек, куда мы будем майнить
address = '16p9y6EstGYcnofGNvUJMEGKiAWhAr1uR8' 
# - Адрес пула, к которому мы будем подключаться
pool_address = "ss.antpool.com"
# - Порт пула, к которому мы будем подключаться
pool_port = 3333

# - Создадим объект, который будет подключаться к пулу
sock = None

# - Инициализируем объект, который будет подключаться к пулу
sock = socket.socket(socket.AF_INET , socket.SOCK_STREAM)

# - Подключаемся к пулу
sock.connect((pool_address , pool_port))

# - Отправляем сообщение в пул - подписываемся на рассылку работы для майнинга
sock.sendall(b'{"id": 1, "method": "mining.subscribe", "params": []}\n')

# - Получаем работу с пула
lines = sock.recv(30000).decode().split('\n')
# - Парсим сырую строку в JSON формат
response = json.loads(lines[0])

print("-------------- Параметры для майнинга от пула -----------------------")
print(response)
print("-------------------------------------")

# - Достаем параметры для майнинга
mining_params = MiningParams(
    response["result"][0],
    response["result"][1],
    response["result"][2]
)

# - Авторизуемся на пуле - отправляем свой кошелек и пароль на пул
sock.sendall(b'{"params": ["' + address.encode() + b'", "password"], "id": 2, "method": "mining.authorize"}\n')

# - Прочитываем все сообщения
response = b''
while response.count(b'\n') < 3 : response += sock.recv(30000)

# - Разделяем строку со всеми полученными сообщениями на разные сообщения
decoded_responses = response.decode().split('\n')

# - Напишем пришедшие сообщения
print("-------------- Все пришедшие сообщения из пула -----------------------")
for res in decoded_responses:
    print(res)
print("-------------------------------------")

# - Достаем только те сообщения, где есть параметры для работы
valid_responses = list()
for res in decoded_responses:
    if len(res.strip()) > 0 and 'mining.notify' in res:
        valid_responses.append(res)

responses = [json.loads(res) for res in valid_responses]

print("------------ Сообщение, которое содержит параметры работы -------------------------")
print(responses[0])
print("-------------------------------------")

job = PoolJob(
    responses[0]["params"][0],
    responses[0]["params"][1],
    responses[0]["params"][2],
    responses[0]["params"][3],
    responses[0]["params"][4],
    responses[0]["params"][5],
    responses[0]["params"][6],
    responses[0]["params"][7],
    responses[0]["params"][8]
)

target = (job.nbits[2 :] + '00' * (int(job.nbits[:2] , 16) - 3)).zfill(64)
extranonce2 = hex(random.randint(0 , 2 ** 32 - 1))[2 :].zfill(2 * mining_params.extranonce2_size)

coinbase = job.coinb1 + mining_params.extranonce1 + extranonce2 + job.coinb2
coinbase_hash_bin = hashlib.sha256(hashlib.sha256(binascii.unhexlify(coinbase)).digest()).digest()

merkle_root = coinbase_hash_bin
for h in job.merkle_branch :
    merkle_root = hashlib.sha256(hashlib.sha256(merkle_root + binascii.unhexlify(h)).digest()).digest()

merkle_root = binascii.hexlify(merkle_root).decode()

merkle_root = ''.join([merkle_root[i] + merkle_root[i + 1] for i in range(0 , len(merkle_root) , 2)][: :-1])

work_on = get_current_block_height()

nHeightDiff = {}
nHeightDiff[work_on + 1] = 0

_diff = int("00000000FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF" , 16)

hashes_count = 0

while True :
    if job.prevhash != job.updatedPrevHash :
        job.updatedPrevHash = job.prevhash
        bitcoin_miner(t , restarted = True)
        continue

    nonce = hex(random.randint(0 , 2 ** 32 - 1))[2 :].zfill(8)
    blockheader = job.version + job.prevhash + merkle_root + job.ntime + job.nbits + nonce + \
                    '000000800000000000000000000000000000000000000000000000000000000000000000000000000000000080020000'
    hash = hashlib.sha256(hashlib.sha256(binascii.unhexlify(blockheader)).digest()).digest()
    hash = binascii.hexlify(hash).decode()

    this_hash = int(hash , 16)

    difficulty = _diff / this_hash

    hashes_count += 1

    if nHeightDiff[work_on + 1] < difficulty :
        nHeightDiff[work_on + 1] = difficulty

    if hash < target :
        payload = bytes('{"params": ["' + address + '", "' + job.job_id + '", "' + mining_params.extranonce2 \
                        + '", "' + job.ntime + '", "' + nonce + '"], "id": 1, "method": "mining.submit"}\n' ,
                        'utf-8')
        sock.sendall(payload)
        ret = sock.recv(1024)
