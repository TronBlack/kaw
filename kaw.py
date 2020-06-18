#!/usr/bin/python3

import random
import os
import subprocess
import json #Make sure it is simplejson - Needed to parse Decimal("####.########")
import logging
import time

from decimal import Decimal
import decimal

#Set this to your raven-cli program
cli = "raven-cli"

#mode = "-testnet"
mode = ""
rpc_port = 8766
#Set this information in your raven.conf file (in datadir, not testnet3)
rpc_user = 'rpcuser'
rpc_pass = 'rpcpass555'

pin = False

def get_rpc_connection():
    from bitcoinrpc.authproxy import AuthServiceProxy, JSONRPCException
    connection = "http://%s:%s@127.0.0.1:%s"%(rpc_user, rpc_pass, rpc_port)
    rpc_conn = AuthServiceProxy(connection, timeout=480)
    return(rpc_conn)

rpc_connection = get_rpc_connection()

def rpc_call(params):
    process = subprocess.Popen([cli, mode, params], stdout=subprocess.PIPE)
    out, err = process.communicate(timeout=None)
    process.stdout.close()
    process.stderr.close()
    return(out)

def get_blockinfo(num):
    hash = rpc_connection.getblockhash(num)
    blockinfo = rpc_connection.getblock(hash)
    return(blockinfo)

def get_block(hash):
    blockinfo = rpc_connection.getblock(hash)
    return(blockinfo)

def get_rawtx(tx):
    #print("Rawtx: " + tx)
    txinfo = rpc_connection.getrawtransaction(tx)
    return(txinfo)

def get_bci():
    bci = rpc_connection.getblockchaininfo()
    return(bci)

def decode_rawtx(txdata):
    #logging.debug("decoding: " + txdata)
    txjson = rpc_connection.decoderawtransaction(txdata)
    return(txjson)    

def decode_script(script):
    scriptinfo = rpc_connection.decodescript(script)
    return(scriptinfo)   

def ipfs_add(file):
    logging.info("Adding to IPFS")
    import ipfsapi
    api = ipfsapi.connect('127.0.0.1', 5001)
    res = api.add(file)
    logging.info(res)
    return(res['Hash'])

def ipfs_get(hash):    
    import ipfsapi
    api = ipfsapi.connect('127.0.0.1', 5001)
    res = api.get(hash)
    return()

def ipfs_pin_add(hash):
    import ipfsapi
    api = ipfsapi.connect('127.0.0.1', 5001)
    res = api.pin_add(hash)
    return(res)




##  DATABASE ACCESS #####################################################

import pymysql

class DB:

    def __init__(self):
        self.dbc = self.open_db()

    def open_db(self):
        self.db = pymysql.connect("localhost","root","abesec","kaw" )
        cursor = self.db.cursor()
        return(cursor)
   
    def get_db_version(self):
        self.dbc.execute("SELECT VERSION()")
        data =  self.dbc.fetchone()
        return("Database version : %s " % data)

    def commit(self):
        self.db.commit()

    def close_db(self):
        self.db.close()

    def get_last_block_id(self):
        sql = "SELECT MAX(block_id) as block_id from blocks"
        self.dbc.execute(sql)
        block_id = self.dbc.fetchone()[0]
        return(block_id)


    ## KAW - Specific ################################
    def create_tables():
        with open ("kaw.sql", "r") as myfile:
            sql=myfile.readlines()
        self.dbc.execute(sql)
        self.db.commit()


    def add_block(self, block_id, time, block_hash):
        sql = "INSERT INTO blocks(block_id, time, block_hash) VALUES (%d, %d, '%s')" % (block_id, time, block_hash)
        logging.debug(sql)
        try:
            self.dbc.execute(sql)
        except pymysql.err.IntegrityError as err:
            logging.info("Coult not add block (Integrity Error): " + str(block_id))
            return(-1)
        except Exception as err:
            logging.info(type(err))
            logging.info(err)

        self.dbc.execute('SELECT MAX(block_id) as id FROM blocks')
        id = self.dbc.fetchone()[0]
        return(self.get_last_block_id())



    def add_tx(self, block_id, tx_hash):
        sql = "INSERT INTO txs(block_id, tx_hash) VALUES ('%d', '%s')" % (block_id, tx_hash)
        logging.debug(sql)
        self.dbc.execute(sql)
        logging.debug("Added TX - lastrowid is " + str(self.dbc.lastrowid))
        return(self.dbc.lastrowid)



    def add_asset(self, asset, amount, units, reissuable):
        sql = "INSERT INTO assets(asset, amount, units, reissuable) VALUES ('%s', '%f', '%d', '%d')" % (asset, amount, units, reissuable)
        logging.debug(sql)
        self.dbc.execute(sql)
        return(self.dbc.lastrowid)
        
          

    def lookup_asset_id(self, asset):
        sql = "SELECT asset_id FROM assets WHERE asset='%s'" % (asset)
        logging.debug(sql)
        self.dbc.execute(sql)
        try:
            id = self.dbc.fetchone()[0]
        except:
            logging.critical("Looking up asset: " + asset)
            id = -1 #Not found
        return(id)


    def get_id(self, results):
        for row in results:
            id = row[0]
        return(id)        

    def add_vout(self, tx_id, vnum, address, asset_id, sats):
        sql = "INSERT INTO vouts(tx_id, vnum, address, asset_id, sats) VALUES ('%d', '%d', '%s', '%d', '%d')" % (tx_id, vnum, address, asset_id, sats)
        #logging.debug(sql)
        #print(sql)
        self.dbc.execute(sql)
        return(self.dbc.lastrowid)

    def add_msg(self, tx_id, vout, asset_id, ipfs, msg, msg_type):
        sql = "INSERT INTO msgs(tx_id, vout, asset_id, ipfs, msg, msg_type) VALUES ('%d', '%d', '%d', '%d', '%s', '%d')" % (tx_id, vout, asset_id, ipfs, msg, msg_type)
        #logging.debug(sql)
        #print(sql)
        self.dbc.execute(sql)
        return(self.dbc.lastrowid)        


        ## END KAW - Specific #################################################



## END DATABASE ACCESS #############################################

def asset_handler(dbc, tx_id, vout, asset_script):
    asset_name = asset_script.get('asset_name')

    if (asset_name == 'RAVENCOINCASH'):  # Too much processing overhead (abused)
        return(0)
    
    logging.info("Type: " + asset_script.get('type'))
    logging.info("Asset: " + asset_name)
    logging.debug(asset_script.get('amount'))


    logging.debug(asset_script.get('units'))

    units = 0
    if asset_script.get('units') != None:
        units = int(asset_script.get('units'))

    
    reissuable = 1
    if asset_script.get('reissuable') == None:
        reissuable = 0

    logging.debug("Reissuable: " + str(reissuable))
    logging.debug("Has IPFS: " + str(asset_script.get('hasIPFS')))

    asset_id = -1
    asset_type = asset_script.get('type')

    if (asset_type == 'new_asset') or (asset_type == 'reissue_asset'):
        asset_id = dbc.add_asset(asset_script.get('asset_name'), asset_script.get('amount'), units, reissuable)
    else:
        asset_id = dbc.lookup_asset_id(asset_script.get('asset_name'))

    logging.debug("asset_id: " + str(asset_id))

    msg_type, ipfs, msg = determine_msg_type(asset_script)
    if (msg_type > 0):

        logging.info("Need to store in msg: " + asset_script.get('ipfs_hash'))

        
        add_msg(dbc, tx_id, vout, asset_id, 1, asset_script.get('ipfs_hash'), msg_type)

        if (pin):
            ipfs_pin_add(asset_script.get('ipfs_hash'))

    return(asset_id)

def determine_msg_type(asset_script):
    ipfs = 1
    msg_type = 0
    if asset_script.get('hasIPFS') == True or asset_script.get('hasHex') == True:
        if asset_script.get('hasIPFS') == True:
            msg = asset_script.get('ipfs_hash')


        return(msg_type, ipfs, msg)
        
    else:
        return(-1, -1, '') # No message


# Add a msg
# There are 4 msg_types:
# 0 - Meta-data - used on asset issuance or re-issuance
# 1 - Messages - used when admin token sends from/to same address - signal for broadcast
# 2 - Memos (asset) - used with any transaction
# 3 - Memos (RVN) - used with any RVN transaction

# ipfs is 1 for ipfs encoding or 0 for hex encoding
def add_msg(dbc, tx_id, vout, asset_id, ipfs, msg, msg_type):
    dbc.add_msg(tx_id, vout, asset_id, ipfs, msg, msg_type)


#Only add vouts that deal with assets, ignore others
def add_vouts(dbc, block_id, tx_id, vouts):
    vnum = 0
    for vout in vouts:
        #logging.info("vout: " + str(vout.get('value')))
        #logging.info(vout.get('scriptPubKey').get('asm'))
        asset_id = 0
        sats = 0
        address = ''
        #get_bci()
        script = decode_script(vout.get('scriptPubKey').get('hex'))
        logging.debug("VOUT " + str(vnum) + " script:" + vout.get('scriptPubKey').get('hex'))
        logging.debug(script)

        asset_type = script.get('type')


        ## This is here just to learn about new asset_types
        if (asset_type != 'new_asset') and (asset_type != 'reissue_asset') and (asset_type != 'transfer_asset') and (asset_type != 'scripthash') and (asset_type != 'pubkeyhash') and (asset_type != 'nulldata'):
            logging.critical("New asset type: " + asset_type)
            exit()
        ###################################################        
        
        if (asset_type == 'transfer_asset') or (asset_type == 'new_asset') or (asset_type == 'reissue_asset'):
            logging.debug("ASSET TYPE FOUND")
            asset_id = asset_handler(dbc, tx_id, vnum, script)
            asset_amount = script.get('asset').get('amount')
            logging.debug(script.get('asset'))
            address =  script.get('addresses')[0]
            if (address == ''):
                logging.critical("Address Not Found")            
            dbc.add_vout(tx_id, vnum, address, asset_id, sats)
        else:
            # TODO TB20200618 - Need to find memos for RVN transactions after hard-fork of Feb 7, 2020
            #logging.info("Type: " + asset_type)
            if (block_id >= 1092672):
                logging.info("Should be indexing memos for RVN transactions in add_vouts")

        vnum = vnum + 1

def add_txs(dbc, block_id, txs):
    #logging.info(txs)
    for tx in txs:
        tx_info = get_rawtx(tx)
        logging.debug("txinfo: " + tx_info)
        tx_detail = decode_rawtx(tx_info)
        tx_id = dbc.add_tx(block_id, tx_detail.get('hash'))
        logging.debug("Added tx: " + str(tx_id))
        add_vouts(dbc, block_id, tx_id, tx_detail.get('vout'))
        #logging.info("txdecoded: " + tx_detail.get('vout'))



def main():
    dbc = DB()
    logging.info(dbc.get_db_version())

    #Get the blockheight of the chain
    blockheight = get_bci().get('blocks')
    starting_block = max(435456, dbc.get_last_block_id() + 1)

    logging.info("Starting block: " + str(starting_block))

    for block_id in range(starting_block,blockheight):
        dta = get_blockinfo(block_id)
        logging.info("Block #" + str(block_id) + " - " + dta.get('hash'))
        logging.debug(dta.get('time'))

        logging.debug("Adding block to db")
        id = dbc.add_block(block_id, int(dta.get('time')), dta.get('hash'))
        if (id > 0):
            logging.debug("Added block as id: " + str(id))
            tx_in_block = get_block(dta.get('hash'))

            txs = tx_in_block.get('tx')

            add_txs(dbc, block_id, txs)
        else:
            logging.error("Skipping block - already added block #: " + str(block_id))

        dbc.commit()  #Commit to the database after each block is complete

    close_db()


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    main()