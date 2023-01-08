from hashlib import sha256
import json
import time

#区块链中块的定义
class Block:

    def __init__(self, index, transactions, timestamp, previous_hash,hash="",nonce=0):
        """
        index 每个块唯一的ID
        transactions 交易列表
        timestamp 时间戳
        previous_hash 前一个块的hash值
        nonce 用在 POW 共识算法之中的一个数字。通过改变这个数字来寻找满足困难度的hash值
        """
        self.index = index
        self.transactions = transactions
        self.timestamp = timestamp
        self.previous_hash = previous_hash
        self.hash = hash
        self.nonce= nonce

    def compute_hash(self):
        """
        区块的hash值
        这个函数获得的结果不是最后的hash值
        """
        block_string = json.dumps(self.__dict__, sort_keys=True)
        return sha256(block_string.encode()).hexdigest()

    def print_block(self):
        print("#:%d--time:%f--previous_hash:%s\nnonce:%d\nhash:%s"%(self.index,self.timestamp,self.previous_hash,self.nonce,self.hash))

#区块链的定义
class Blockchain:
    #PoW算法的困难度(开始的hash值需要difficulty个零)
    difficulty = 2

    def __init__(self):#名为 __init__() 的构造方法，该方法在类实例化时会自动调用
        """
        unconfirmed_transactions 未入块的交易
        chain 块链
        """
        self.unconfirmed_transactions = []
        self.chain = []

    def create_genesis_block(self):
        """
        创建创世区块的函数
        创世区块中index=0, previous_hash="0"
        """
        genesis_block = Block(0, [], 0, "0")
        genesis_block.hash = genesis_block.compute_hash()
        self.chain.append(genesis_block)

    @property
    def last_block(self):
        """
        私有方法，返回链中最后一个块
        """
        return self.chain[-1]

    def add_block(self, block, proof):
        """
        将经过验证的块加入区块链中
        block为块，proof为得出hash值
        验证条件
        * 检查这个块的previous_hash是否和区块链末端的hash值相同
        * 检查这个块的hash值是否是这个块的hash值且是否满足困难度
        """
        previous_hash = self.last_block.hash

        if previous_hash != block.previous_hash:
            return False

        if not Blockchain.is_valid_proof(block, proof):
            return False

        block.hash = proof
        self.chain.append(block)
        return True

    @staticmethod
    def proof_of_work(block):
        """
        尝试不同的nonce值来找到满足困难度标准的hash值
        返回满足条件的hash值
        """
        block.nonce = 0

        computed_hash = block.compute_hash()
        while not computed_hash.startswith('0' * Blockchain.difficulty):
            block.nonce += 1
            computed_hash = block.compute_hash()

        return computed_hash

    def add_new_transaction(self, transaction):
        """
        将交易记录放入未确认交易
        """
        self.unconfirmed_transactions.append(transaction)

    @classmethod
    def is_valid_proof(cls, block, block_hash):
        """
        块和块的hash值
        检查块的hash值是否是这个块的hash值且是否满足困难度，且是这个块
        """
        return (block_hash.startswith('0' * Blockchain.difficulty) and
                block_hash == block.compute_hash())

    def mine(self):
        """
        交易一开始是保存在未确认交易池中的
        将未确认交易放入区块并计算工作量证明的过程，就是挖矿
        """
        if not self.unconfirmed_transactions:
            return False

        last_block = self.last_block

        new_block = Block(index=last_block.index + 1,
                          transactions=self.unconfirmed_transactions,
                          timestamp=time.time(),
                          previous_hash=last_block.hash)

        proof = self.proof_of_work(new_block)#这个proof的值就是新块的hash
        #print(proof)
        self.add_block(new_block, proof)#add_block中有对proof值的验证

        self.unconfirmed_transactions = []

        return True
    
    def print_block(self):
        for block in self.chain:
            block.print_block()

#结点的定义（待定）

#广播（待定）
#当有结点挖矿成功的时候，向所有节点广播结果，指引其他结点更新区块链
def announce_new_block():
    return None

#共识（待定）
#节点之间需要就区块链的版本 达成一致，以便维护整个系统的一致性。即达成共识。
def consensus():
    """
    选择最长链作为有效链
    选择结点间比例最高的链作为有效链
    """
    return False


"""
myBlockchain = Blockchain()
myBlockchain.create_genesis_block()
myBlockchain.add_new_transaction("A->B:500")
myBlockchain.mine()
myBlockchain.add_new_transaction("A->B:500")
myBlockchain.mine()
myBlockchain.print_block()
"""



