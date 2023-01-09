import threading
from threading import Thread
from hashlib import sha256
from enum import Enum
import json
import time

#块的定义
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
        self.nonce= nonce

        self.hash = hash
        

    def compute_hash(self):
        """
        区块的hash值
        这个函数获得的结果不是最后的hash值
        """
        dictToHash = {"index":self.index,
                      "transactions":self.transactions,
                      "timestamp":self.timestamp,
                      "previous_hash":self.previous_hash,
                      "nonce":self.nonce}
        block_string = json.dumps(dictToHash, sort_keys=True)
        return sha256(block_string.encode()).hexdigest()

    def print_block(self):
        print("#:%d--time:%f\nprevious_hash:%s\nnonce:%d\nhash:%s"%(self.index,self.timestamp,self.previous_hash,self.nonce,self.compute_hash()))
#简单的线程锁
threadLock = threading.Lock()
#简单的事件
event = threading.Event()
#信号量
semaphore =  threading.Semaphore(0)
#线程间共享变量
"""
是否挖出区块
广播区块
广播区块hash(proof)
"""
newBlockHasMined = False
broadcastBlock = Block(0, [], 0, "0")
broadcastProof = ""
#结点的定义
"""
结点是线程threading.Thread类的子类
一个节点中应该保存网络中其他结点的信息以便于广播
"""
class BTNode(Thread):

    #PoW算法的困难度(开始的hash值需要difficulty个零)
    difficulty = 4

    def __init__(self,name):
        Thread.__init__(self)
        """
        unconfirmed_transactions 未入块的交易
        chain 块列表
        """
        self.unconfirmed_transactions = []
        self.chain = []
        self.name = name#Thread中的name域

    def create_genesis_block(self):
        """
        创建创世区块
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
        * 检查这个块的proof值是否是这个块的hash值且是否满足困难度
        """
        previous_hash = self.last_block.hash
        computed_hash = block.compute_hash()
        
        print("previous_hash:"+previous_hash)
        print("block.previous_hash:"+block.previous_hash)
        print("proof:"+proof)
        print("computed_hash:"+computed_hash)
        
        #验证前后
        if previous_hash != block.previous_hash:
            print("前后hash值不连锁！")
            return False

        elif not proof.startswith('0' * BTNode.difficulty):
            print("困难度不满足！！")
            return False

        elif not proof == computed_hash:
            print("计算出来的hash值与proof不一致！")
            return False

        block.hash = computed_hash
        self.chain.append(block)
        return True

    def add_new_transaction(self, transaction):
        """
        将交易记录放入未确认交易
        """
        self.unconfirmed_transactions.append(transaction)

    def mine(self):
        """
        交易一开始是保存在未确认交易池中的
        将未确认交易放入区块并计算工作量证明的过程，就是挖矿
        """
        global newBlockHasMined
        global broadcastBlock
        global broadcastProof

        if not self.unconfirmed_transactions:
            return False

        last_block = self.last_block

        new_block = Block(index=last_block.index + 1,
                          transactions=self.unconfirmed_transactions,
                          timestamp=time.time(),
                          previous_hash=last_block.hash)

        #pow部分
        new_block.nonce = 0

        computed_hash = new_block.compute_hash()
        while (not computed_hash.startswith('0' * BTNode.difficulty)) and (not newBlockHasMined):
            new_block.nonce += 1
            computed_hash = new_block.compute_hash()
        
        proof = computed_hash#这个proof的值就是新块的hash
        #pow部分结束
        if(not newBlockHasMined):
            """
            该结点挖出了这个区块，通知其他结点停止挖取同一批次交易数据
            """
            threadLock.acquire()
            print("#########################")
            print(threading.currentThread().getName()+"挖出了区块！")
            if self.add_block(new_block, proof):#add_block中有对proof值的验证
                print(threading.currentThread().getName()+"上链成功！")
            else :
                print(threading.currentThread().getName()+"上链失败。。。")
            self.unconfirmed_transactions = []
            newBlockHasMined = True
            broadcastBlock = new_block#广播块
            broadcastProof = proof#广播proof
            threadLock.release()
            return True
        else:
            """
            该结点没有挖出区块，将这个区块经过验证后上链，之后清空交易数据
            """
            threadLock.acquire()
            print("#########################")
            print(threading.currentThread().getName()+"把其他区块上链。。。")
            if self.add_block(broadcastBlock,broadcastProof):
                print(threading.currentThread().getName()+"上链成功！")
            else :
                print(threading.currentThread().getName()+"上链失败。。。")
            self.unconfirmed_transactions = []
            threadLock.release()
            return False

    def print_block(self):
        for block in self.chain:
            block.print_block()


    def run(self):
        self.create_genesis_block()
        self.add_new_transaction("A->B:500")
        self.add_new_transaction("A->B:500")
        self.mine()
        threadLock.acquire()
        print("----------------------------------")
        print(threading.currentThread().getName()+"的区块")
        self.print_block()
        threadLock.release()
        return 0

#共识（待定）
#节点之间需要就区块链的版本 达成一致，以便维护整个系统的一致性。即达成共识。
def consensus():
    """
    选择最长链作为有效链
    选择结点间比例最高的链作为有效链
    """
    return False

def main():
    #模拟用的共用变量
    Node1 = BTNode("Node#1")
    Node2 = BTNode("Node#2")
    Node1.start()
    Node2.start()
    Node1.join()
    Node2.join()
    return 0

if __name__ == "__main__":
    main()


